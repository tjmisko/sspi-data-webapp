"""
SSPIScoringJobs - Worker-safe job store for custom SSPI scoring jobs.

Background scoring jobs used to live in a process-local ``dict`` plus an
in-memory ``Queue`` inside ``scoring_tasks.py``. Under multiple gunicorn
workers that meant a request landing on a worker other than the one running
the scoring thread saw "Job not found" or an empty SSE stream (#893).

This collection persists all job state in MongoDB so ``/score``,
``/job/<id>`` and ``/score-stream/<id>`` work regardless of which worker
serves the request. The pipeline thread still runs in a single worker, but it
writes its progress/events to Mongo where every worker can read them.

Document format:
{
    "job_id": "a1b2c3...",                # 32-char hex, unique primary key
    "config_id": "adhoc_user_...",        # configuration identifier
    "config_hash": "abc123..." | null,    # computed during validation
    "user_id": "alice",                   # owner (current_user.username)
    "status": "scoring",                  # JobStatus value (see below)
    "progress": 42,                       # 0-100
    "message": "Scoring 54 Indicators",
    "stage": "scoring" | null,            # current stage (for progress synthesis)
    "stage_current": 12 | null,           # high-frequency scalar progress
    "stage_total": 54 | null,
    "result": {                           # summary ONLY (never the full score list)
        "cached": false,
        "total_scores": 12345,
        "config_hash": "abc123..."
    } | null,
    "error": "..." | null,
    "cancel_requested": false,            # reserved for the cancel route (D3)
    "seq": 7,                             # monotonic event counter
    "events": [                           # append-only SSE replay log
        {"seq": 1, "event_type": "stage_complete",
         "data": {...}, "ts": "2026-06-24T..."},
        ...
    ],
    "created_at": <datetime UTC>,         # BSON datetime (TTL source of truth)
    "updated_at": <datetime UTC>,
    "completed_at": <datetime UTC> | null,
    "worker_pid": 12345                   # debugging: which worker ran the thread
}

Indexes:
- job_id        - unique
- user_id       - per-user job listing + cap counts
- (status, created_at) - evictor / concurrency-cap scans (D2)
- created_at    - cache management / TTL (TTL index added in D2)
"""

import logging
from datetime import datetime, timezone

from pymongo import ReturnDocument

from sspi_flask_app.models.database.mongo_wrapper import MongoWrapper
from sspi_flask_app.models.errors import InvalidDocumentFormatError

logger = logging.getLogger(__name__)


# JobStatus values are duplicated here as plain strings to avoid a circular
# import with scoring_tasks.py (which imports this model singleton). They MUST
# stay in sync with scoring_tasks.JobStatus.
ACTIVE_STATUS_VALUES = {
    "pending", "validating", "scoring", "aggregating", "saving"
}
TERMINAL_STATUS_VALUES = {"complete", "error", "cancelled"}
VALID_STATUS_VALUES = ACTIVE_STATUS_VALUES | TERMINAL_STATUS_VALUES


class SSPIScoringJobs(MongoWrapper):
    """
    MongoDB wrapper for worker-safe custom scoring job state.

    One document per scoring job. The pipeline thread updates scalar fields
    (status/progress/stage) and appends SSE events; readers on any worker
    reconstruct job state from the document.
    """

    # ==========================================================================
    # Document Validation
    # ==========================================================================

    def validate_document_format(self, document: dict, document_number: int = 0):
        """Validate a scoring job document."""
        self._validate_job_id(document, document_number)
        self._validate_user_id(document, document_number)
        self._validate_status(document, document_number)
        self._validate_progress(document, document_number)

    def _validate_job_id(self, document: dict, document_number: int):
        if "job_id" not in document:
            raise InvalidDocumentFormatError(
                f"'job_id' is required (document {document_number})"
            )
        job_id = document["job_id"]
        if not isinstance(job_id, str) or len(job_id) == 0:
            raise InvalidDocumentFormatError(
                f"'job_id' must be a non-empty string (document {document_number})"
            )

    def _validate_user_id(self, document: dict, document_number: int):
        if "user_id" not in document:
            raise InvalidDocumentFormatError(
                f"'user_id' is required (document {document_number})"
            )
        if not isinstance(document["user_id"], str):
            raise InvalidDocumentFormatError(
                f"'user_id' must be a string (document {document_number})"
            )

    def _validate_status(self, document: dict, document_number: int):
        if "status" not in document:
            raise InvalidDocumentFormatError(
                f"'status' is required (document {document_number})"
            )
        status = document["status"]
        if status not in VALID_STATUS_VALUES:
            raise InvalidDocumentFormatError(
                f"'status' must be one of {sorted(VALID_STATUS_VALUES)} "
                f"(document {document_number})"
            )

    def _validate_progress(self, document: dict, document_number: int):
        if "progress" not in document:
            raise InvalidDocumentFormatError(
                f"'progress' is required (document {document_number})"
            )
        progress = document["progress"]
        if not isinstance(progress, int) or isinstance(progress, bool):
            raise InvalidDocumentFormatError(
                f"'progress' must be an integer (document {document_number})"
            )
        if not (0 <= progress <= 100):
            raise InvalidDocumentFormatError(
                f"'progress' must be between 0 and 100 (document {document_number})"
            )

    # ==========================================================================
    # CRUD Operations
    # ==========================================================================

    def create_job(self, document: dict) -> str:
        """Validate and insert a new job document. Returns the job_id."""
        self.insert_one(document)
        return document["job_id"]

    def get(self, job_id: str) -> dict | None:
        """Fetch a job document (native types, no _id). None if missing."""
        return self._mongo_database.find_one({"job_id": job_id}, {"_id": 0})

    def list_for_user(self, user_id: str) -> list[dict]:
        """Return all job documents owned by a user (native types, no _id)."""
        return list(self._mongo_database.find({"user_id": user_id}, {"_id": 0}))

    def set_fields(self, job_id: str, **fields) -> int:
        """
        Set scalar fields on a job document, stamping ``updated_at``.

        Used for high-frequency progress updates (status/stage/progress) so the
        document stays small instead of growing an event per tick.

        Returns the number of documents modified (0 if the job is missing).
        """
        if not fields:
            return 0
        fields["updated_at"] = datetime.now(timezone.utc)
        result = self._mongo_database.update_one(
            {"job_id": job_id}, {"$set": fields}
        )
        return result.modified_count

    def append_event(
        self,
        job_id: str,
        event_type: str,
        data: dict,
        set_fields: dict | None = None,
    ) -> int | None:
        """
        Append an SSE event to the job's append-only ``events`` log.

        The event ``seq`` comes from a monotonic ``$inc`` so readers can poll
        ``events_since(last_seq)`` without missing or double-counting events.

        ``set_fields`` (e.g. status/completed_at on a terminal event) are
        applied in the SAME update as the event push so a reader never observes
        a terminal status without its terminal event.

        Returns the new ``seq`` (or None if the job is missing).
        """
        now = datetime.now(timezone.utc)
        bumped = self._mongo_database.find_one_and_update(
            {"job_id": job_id},
            {"$inc": {"seq": 1}},
            projection={"seq": 1, "_id": 0},
            return_document=ReturnDocument.AFTER,
        )
        if not bumped:
            return None
        seq = bumped["seq"]
        event = {
            "seq": seq,
            "event_type": event_type,
            "data": data,
            "ts": now.isoformat(),
        }
        update_set = {"updated_at": now}
        if set_fields:
            update_set.update(set_fields)
        self._mongo_database.update_one(
            {"job_id": job_id},
            {"$push": {"events": event}, "$set": update_set},
        )
        return seq

    def events_since(self, job_id: str, last_seq: int) -> list[dict]:
        """Return events with ``seq`` greater than ``last_seq`` (ordered)."""
        doc = self._mongo_database.find_one(
            {"job_id": job_id}, {"_id": 0, "events": 1}
        )
        if not doc:
            return []
        return [e for e in doc.get("events", []) if e["seq"] > last_seq]

    def count_active(self, user_id: str | None = None) -> int:
        """
        Count jobs currently in an active (non-terminal) status.

        Used by the D2 concurrency cap. Scoped per-user when ``user_id`` is
        given, global otherwise.
        """
        query = {"status": {"$in": list(ACTIVE_STATUS_VALUES)}}
        if user_id is not None:
            query["user_id"] = user_id
        return self._mongo_database.count_documents(query)

    # ==========================================================================
    # Index Management
    # ==========================================================================

    def create_indexes(self):
        """Create database indexes for optimal query performance."""
        # Unique primary key: one document per job_id.
        self._mongo_database.create_index(
            "job_id", unique=True, name="unique_job_id"
        )
        # Per-user job listing and concurrency-cap counts.
        self._mongo_database.create_index(
            "user_id", name="user_id_lookup"
        )
        # Evictor / cap scans by status and age (D2).
        self._mongo_database.create_index(
            [("status", 1), ("created_at", 1)], name="status_created_at"
        )
        # Cache management / eviction by age (TTL index added in D2).
        self._mongo_database.create_index(
            "created_at", name="created_at_index"
        )
        logger.info("Created indexes for sspi_scoring_jobs")

    def drop_indexes(self):
        """Drop all custom indexes (keeps _id index)."""
        self._mongo_database.drop_indexes()
        logger.info("Dropped indexes for sspi_scoring_jobs")
