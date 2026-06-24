"""
Background Task Management for Custom SSPI Scoring

This module manages background scoring jobs with progress tracking for SSE
streaming. Job state lives in the ``sspi_scoring_jobs`` MongoDB collection so a
job started on one gunicorn worker is fully observable (status / progress /
events) from requests served by any other worker (#893).

Key Components:
- ScoringJob: Write-through view of a job persisted in Mongo
- start_scoring_job: Launch background scoring (inserts the job doc, spawns thread)
- run_scoring_pipeline: Main pipeline executed in background thread (writes to Mongo)
- generate_sse_events: Polls the Mongo job doc and streams SSE events
"""

import json
import logging
import os
import re
import secrets
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from threading import Thread
from typing import Callable

from sspi_flask_app.api.resources.metadata_validator import (
    validate_custom_metadata,
    compute_config_hash,
    ValidationResult,
)
from sspi_flask_app.api.resources.custom_scoring import (
    flatten_scores_for_storage,
    identify_empty_datasets,
    transform_scores_to_line_format,
)
from sspi_flask_app.api.resources.fast_custom_scoring import (
    score_custom_configuration_fast,
)
from sspi_flask_app.models.database import (
    sspi_custom_panel_data,
    sspi_custom_item_data,
    sspi_custom_user_structure,
    sspi_metadata,
    sspi_scoring_jobs,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Job Status Enum
# =============================================================================

class JobStatus(Enum):
    """Status of a scoring job."""
    PENDING = "pending"
    VALIDATING = "validating"
    SCORING = "scoring"
    AGGREGATING = "aggregating"
    SAVING = "saving"
    COMPLETE = "complete"
    ERROR = "error"
    CANCELLED = "cancelled"


# Active (non-terminal) vs terminal status sets. Mirrors the string sets in
# sspi_scoring_jobs.py; used by the D2 concurrency cap and the SSE generator.
ACTIVE_STATUSES = frozenset({
    JobStatus.PENDING,
    JobStatus.VALIDATING,
    JobStatus.SCORING,
    JobStatus.AGGREGATING,
    JobStatus.SAVING,
})
TERMINAL_STATUSES = frozenset({
    JobStatus.COMPLETE,
    JobStatus.ERROR,
    JobStatus.CANCELLED,
})


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class ProgressEvent:
    """A single progress update for SSE streaming."""
    event_type: str  # "progress", "indicator_start", "indicator_complete", "complete", "error"
    data: dict
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class ScoringJob:
    """
    Write-through view of a scoring job persisted in ``sspi_scoring_jobs``.

    The pipeline thread mutates a ScoringJob and every mutation is persisted to
    Mongo so other workers can observe it. Readers (``get_job``) reconstruct a
    read-only snapshot from the Mongo document; the attribute names below are the
    public contract consumed by ``customize.py`` routes (``status``,
    ``progress``, ``message``, ``created_at``, ``completed_at``, ``result``,
    ``config_hash``, ``error``, ``user_id``).
    """

    def __init__(
        self,
        job_id: str,
        config_id: str,
        config_hash: str | None,
        user_id: str,
        status: JobStatus,
        progress: int,
        message: str,
        result: dict | None = None,
        error: str | None = None,
        created_at: str | None = None,
        completed_at: str | None = None,
        cancel_requested: bool = False,
    ):
        self.job_id = job_id
        self.config_id = config_id
        self.config_hash = config_hash
        self.user_id = user_id
        self.status = status
        self.progress = progress
        self.message = message
        self.result = result
        self.error = error
        self.created_at = created_at
        self.completed_at = completed_at
        self.cancel_requested = cancel_requested

    # ------------------------------------------------------------------
    # Write-through mutators (persist to Mongo so other workers see them)
    # ------------------------------------------------------------------

    def set_status(self, status: JobStatus, message: str | None = None):
        """Persist a status (and optional message) transition."""
        self.status = status
        fields = {"status": status.value}
        if message is not None:
            self.message = message
            fields["message"] = message
        sspi_scoring_jobs.set_fields(self.job_id, **fields)

    def set_config_hash(self, config_hash: str):
        """Persist the computed config hash."""
        self.config_hash = config_hash
        sspi_scoring_jobs.set_fields(self.job_id, config_hash=config_hash)

    def _append_event(self, event: ProgressEvent, **set_fields):
        """Append an SSE event to the Mongo doc (atomic with set_fields)."""
        sspi_scoring_jobs.append_event(
            self.job_id,
            event.event_type,
            event.data,
            set_fields=set_fields or None,
        )

    def emit_progress(self, percent: int, message: str, event_type: str = "progress"):
        """Emit a legacy progress event (frontend ignores; kept for interface)."""
        self.progress = percent
        self.message = message
        event = ProgressEvent(
            event_type=event_type,
            data={
                "percent": percent,
                "message": message,
                "status": self.status.value,
            }
        )
        self._append_event(event, progress=percent, message=message)

    def emit_stage_complete(self, stage: str, message: str, data: dict = {}):
        """
        Emit stage completion event.

        Args:
            stage: Stage identifier (validate, identify, scoring, aggregate, ranking, visualizations)
            message: Completion message to display
            data: Optional additional data
        """
        self.message = message
        event = ProgressEvent(
            event_type="stage_complete",
            data={
                "stage": stage,
                "message": message,
                **(data or {})
            }
        )
        self._append_event(event, message=message, stage=stage)

    def emit_stage_progress(self, stage: str, current: int, total: int):
        """
        Emit progress within a stage (for stages with progress bars).

        High-frequency (per-indicator) updates are written as scalar fields
        rather than appended to the events array to keep the document small.
        The SSE generator synthesizes ``stage_progress`` events from these
        scalar fields, so the frontend wire format is unchanged.
        """
        progress = int(current / total * 100) if total else 0
        self.progress = progress
        sspi_scoring_jobs.set_fields(
            self.job_id,
            stage=stage,
            stage_current=current,
            stage_total=total,
            progress=progress,
        )

    def emit_indicator_start(self, code: str, name: str, index: int, total: int):
        """Emit indicator scoring start event (legacy; frontend ignores)."""
        event = ProgressEvent(
            event_type="indicator_start",
            data={
                "code": code,
                "name": name,
                "index": index,
                "total": total,
            }
        )
        self._append_event(event)

    def emit_indicator_complete(self, code: str, countries: int, duration_ms: int):
        """Emit indicator scoring complete event (legacy; frontend ignores)."""
        event = ProgressEvent(
            event_type="indicator_complete",
            data={
                "code": code,
                "countries": countries,
                "duration_ms": duration_ms,
            }
        )
        self._append_event(event)

    def emit_complete(self, total_scores: int, duration_ms: int, cached: bool = False):
        """Emit job completion event and persist terminal state atomically."""
        self.status = JobStatus.COMPLETE
        completed_at = datetime.now(timezone.utc)
        self.completed_at = completed_at.isoformat()
        self.progress = 100
        # Store a SUMMARY only - the full flat-score list already lives in
        # sspi_custom_item_data keyed by config_hash (see D1 doc-size discipline).
        self.result = {
            "cached": cached,
            "total_scores": total_scores,
            "config_hash": self.config_hash,
        }
        event = ProgressEvent(
            event_type="complete",
            data={
                "success": True,
                "total_scores": total_scores,
                "duration_ms": duration_ms,
                "cached": cached,
                "config_hash": self.config_hash,
            }
        )
        self._append_event(
            event,
            status=JobStatus.COMPLETE.value,
            completed_at=completed_at,
            progress=100,
            result=self.result,
        )

    def emit_error(self, message: str, code: str = "SCORING_ERROR"):
        """Emit error event and persist terminal state atomically."""
        self.status = JobStatus.ERROR
        self.error = message
        completed_at = datetime.now(timezone.utc)
        self.completed_at = completed_at.isoformat()
        event = ProgressEvent(
            event_type="error",
            data={
                "message": message,
                "code": code,
            }
        )
        self._append_event(
            event,
            status=JobStatus.ERROR.value,
            error=message,
            completed_at=completed_at,
        )


# =============================================================================
# Job Registry (Mongo-backed)
# =============================================================================

def _status_from_value(value: str | None) -> JobStatus:
    """Rehydrate a JobStatus enum from its stored string value."""
    try:
        return JobStatus(value)
    except ValueError:
        logger.warning(f"Unknown job status value {value!r}, defaulting to ERROR")
        return JobStatus.ERROR


def _iso(value) -> str | None:
    """Format a stored timestamp (BSON datetime or str) as an ISO string."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)


def _job_from_doc(doc: dict) -> ScoringJob:
    """Reconstruct a read-only ScoringJob snapshot from a Mongo document."""
    return ScoringJob(
        job_id=doc["job_id"],
        config_id=doc.get("config_id"),
        config_hash=doc.get("config_hash"),
        user_id=doc.get("user_id"),
        status=_status_from_value(doc.get("status")),
        progress=doc.get("progress", 0),
        message=doc.get("message", ""),
        result=doc.get("result"),
        error=doc.get("error"),
        created_at=_iso(doc.get("created_at")),
        completed_at=_iso(doc.get("completed_at")),
        cancel_requested=doc.get("cancel_requested", False),
    )


def get_job(job_id: str) -> ScoringJob | None:
    """Get a job by ID from Mongo (works across workers)."""
    doc = sspi_scoring_jobs.get(job_id)
    if not doc:
        return None
    return _job_from_doc(doc)


def get_user_jobs(user_id: str) -> list[ScoringJob]:
    """Get all jobs for a user from Mongo."""
    return [_job_from_doc(doc) for doc in sspi_scoring_jobs.list_for_user(user_id)]


# =============================================================================
# Job Management
# =============================================================================

def start_scoring_job(
    config_id: str,
    metadata: list[dict],
    actions: list[dict],
    user_id: str
) -> str:
    """
    Start a background scoring job.

    Inserts the job document in Mongo (status PENDING) so other workers can
    observe it immediately, then spawns the daemon thread that runs the
    pipeline and writes progress/events back to Mongo.

    Args:
        config_id: Configuration identifier
        metadata: Custom SSPI metadata
        actions: Action history from editor
        user_id: User who initiated the job

    Returns:
        job_id for tracking via SSE
    """
    # Generate job ID
    job_id = secrets.token_hex(16)
    now = datetime.now(timezone.utc)
    # Persist the job document (worker-safe state lives in Mongo)
    sspi_scoring_jobs.create_job({
        "job_id": job_id,
        "config_id": config_id,
        "config_hash": None,  # Will be computed during validation
        "user_id": user_id,
        "status": JobStatus.PENDING.value,
        "progress": 0,
        "message": "Starting...",
        "stage": None,
        "stage_current": None,
        "stage_total": None,
        "result": None,
        "error": None,
        "cancel_requested": False,
        "seq": 0,
        "events": [],
        "created_at": now,
        "updated_at": now,
        "completed_at": None,
        "worker_pid": os.getpid(),
    })
    # Build the write-through job object handed to the pipeline thread
    job = ScoringJob(
        job_id=job_id,
        config_id=config_id,
        config_hash=None,
        user_id=user_id,
        status=JobStatus.PENDING,
        progress=0,
        message="Starting...",
        created_at=now.isoformat(),
    )
    # Start background thread (runs in this worker; state is shared via Mongo)
    thread = Thread(
        target=run_scoring_pipeline,
        args=(job, metadata, actions),
        daemon=True
    )
    thread.start()
    logger.info(f"Started scoring job {job_id} for config {config_id}")
    return job_id


def cancel_job(job_id: str) -> bool:
    """
    Cancel a job, persisting the request to Mongo so the running thread (which
    may live on another worker) observes it.

    For a job that has not finished, this sets ``cancel_requested=True`` so the
    pipeline transitions it to CANCELLED at its next stage boundary (the worker
    owning the thread writes the final status/completed_at). A job that is still
    PENDING (no thread progress yet) is flipped straight to CANCELLED.

    Args:
        job_id: Job to cancel

    Returns:
        True if the job was found and is cancellable; False if missing or
        already terminal.
    """
    doc = sspi_scoring_jobs.get(job_id)
    if not doc:
        return False

    status = _status_from_value(doc.get("status"))
    if status in TERMINAL_STATUSES:
        return False

    # Always record the cancel request so the running pipeline can honor it
    # cooperatively at its next checkpoint (works across workers).
    fields = {"cancel_requested": True, "message": "Cancelled by user"}
    if status == JobStatus.PENDING:
        # Not yet doing real work - flip straight to terminal CANCELLED.
        fields["status"] = JobStatus.CANCELLED.value
        fields["completed_at"] = datetime.now(timezone.utc)
    sspi_scoring_jobs.set_fields(job_id, **fields)

    logger.info(f"Cancel requested for job {job_id} (status was {status.value})")
    return True


# =============================================================================
# Metadata Helpers
# =============================================================================

def _rebuild_metadata_without_indicators(
    metadata: list[dict],
    dropped_codes: set[str]
) -> list[dict]:
    """
    Rebuild metadata after dropping indicators.

    Removes dropped indicators and updates hierarchy references in parent items
    (Categories) to remove references to dropped indicator codes.

    Args:
        metadata: Original metadata list
        dropped_codes: Set of indicator codes to drop

    Returns:
        New metadata list with dropped indicators removed and hierarchy updated
    """
    rebuilt = []

    for item in metadata:
        item_type = item.get("ItemType")
        item_code = item.get("ItemCode")

        # Skip dropped indicators
        if item_type == "Indicator" and item_code in dropped_codes:
            continue

        # For Categories, update IndicatorCodes and Children to remove dropped codes
        if item_type == "Category":
            item = dict(item)  # Make a copy to avoid mutating original

            # Update IndicatorCodes
            if "IndicatorCodes" in item and item["IndicatorCodes"]:
                item["IndicatorCodes"] = [
                    code for code in item["IndicatorCodes"]
                    if code not in dropped_codes
                ]

            # Update Children
            if "Children" in item and item["Children"]:
                item["Children"] = [
                    code for code in item["Children"]
                    if code not in dropped_codes
                ]

        rebuilt.append(item)

    return rebuilt


# =============================================================================
# Scoring Pipeline
# =============================================================================

def run_scoring_pipeline(
    job: ScoringJob,
    metadata: list[dict],
    actions: list[dict]
):
    """
    Main scoring pipeline executed in background thread.

    Stages emitted to frontend:
    1. validate - Validate metadata & score functions
    2. identify - Static stage marker (change detection removed)
    3. scoring - Score all indicators (with progress bar)
    4. aggregate - Aggregate hierarchy
    5. ranking - Compute ranks
    6. visualizations - Build visualizations (save results)
    """
    start_time = time.time()
    try:
        job.set_status(JobStatus.VALIDATING)

        # =====================================================================
        # Stage 1: Check for Empty Datasets (BEFORE validation)
        # =====================================================================
        # This must happen first so indicators with empty datasets are filtered
        # out before validation - otherwise their invalid ScoreFunctions will
        # cause validation to fail unnecessarily.
        empty_dataset_result = identify_empty_datasets(metadata)

        dropped_count = len(empty_dataset_result.dropped_indicators)
        scorable_count = len(empty_dataset_result.scorable_indicators)

        if dropped_count > 0:
            dropped_codes_set = set(d["code"] for d in empty_dataset_result.dropped_indicators)
            job.emit_stage_complete(
                "data_check",
                f"Dropped {dropped_count} indicators (no data)",
                {
                    "dropped_count": dropped_count,
                    "scorable_count": scorable_count,
                    "dropped_indicators": empty_dataset_result.dropped_indicators,
                }
            )
            logger.warning(
                f"Job {job.job_id}: Dropped {dropped_count} indicators due to empty datasets: "
                f"{', '.join(sorted(dropped_codes_set))}"
            )

            # Rebuild metadata: remove dropped indicators and update hierarchy references
            metadata = _rebuild_metadata_without_indicators(metadata, dropped_codes_set)
        else:
            job.emit_stage_complete(
                "data_check",
                "All datasets have data",
                {"dropped_count": 0, "scorable_count": scorable_count}
            )

        # =====================================================================
        # Stage 2: Validate Metadata (after filtering dropped indicators)
        # =====================================================================
        # Get valid dataset codes for validation
        try:
            valid_datasets = set(sspi_metadata.dataset_codes())
        except Exception:
            valid_datasets = None  # Skip dataset validation if DB unavailable

        validation_result = validate_custom_metadata(
            metadata,
            valid_dataset_codes=valid_datasets,
            validate_score_functions=True
        )

        if not validation_result.valid:
            error_msgs = [e.message for e in validation_result.errors[:5]]
            job.emit_error(
                f"Validation failed:\n{'\n'.join(error_msgs)}",
                "VALIDATION_ERROR"
            )
            return

        job.emit_stage_complete(
            "validate",
            "Metadata Validated",
            {"item_count": validation_result.item_count}
        )

        # =====================================================================
        # Check cache before identifying modified indicators
        # =====================================================================
        config_hash = compute_config_hash(metadata)
        job.set_config_hash(config_hash)

        try:
            # Check if we have cached flat scores in sspi_custom_item_data
            if sspi_custom_item_data.has_cached_results(config_hash):
                # Also verify line data exists
                if sspi_custom_panel_data.has_line_data(config_hash):
                    cached_results = sspi_custom_item_data.get_cached_results(config_hash)
                    # Cache hit! Emit all stages as complete
                    job.emit_stage_complete("identify", "Configuration Unchanged (cached)", {"count": 0})
                    job.emit_stage_complete("scoring", "Scores Retrieved from Cache", {"cached": True})
                    job.emit_stage_complete("aggregate", "Aggregation Complete (cached)")
                    job.emit_stage_complete("ranking", "Ranks Computed (cached)")
                    job.emit_stage_complete("visualizations", "Visualizations Ready")

                    duration_ms = int((time.time() - start_time) * 1000)
                    job.emit_complete(len(cached_results), duration_ms, cached=True)

                    logger.info(f"Cache hit for job {job.job_id}, returning {len(cached_results)} cached results")
                    return
        except Exception as e:
            logger.warning(f"Cache check failed: {e}, proceeding with scoring")

        # =====================================================================
        # Stage 2: Identify Indicators (static)
        # =====================================================================
        # Change detection was removed: the fast scorer always scores ALL
        # indicators because the vectorized matrix multiply needs consistent
        # dimensions. We still emit a static `identify` stage_complete so the
        # frontend progress modal (which hardcodes an `identify` stage row)
        # advances past this stage.
        indicator_count = sum(
            1 for item in metadata if item.get("ItemType") == "Indicator"
        )

        job.emit_stage_complete(
            "identify",
            f"Scoring {indicator_count} Indicators",
            {"modified": indicator_count, "unchanged": 0}
        )

        logger.info(f"Job {job.job_id}: scoring {indicator_count} indicators")

        # =====================================================================
        # Stage 3: Score Indicators
        # =====================================================================
        job.set_status(JobStatus.SCORING)

        def progress_callback(phase: str, percent: int, message: str):
            """Map scoring phases to stage events."""
            if phase == "scoring":
                # Extract indicator progress from message
                match = re.match(r'Scoring (\w+) \((\d+)/(\d+)\)', message)
                if match:
                    current = int(match.group(2))
                    total = int(match.group(3))
                    job.emit_stage_progress("scoring", current, total)
            # Aggregation and ranking handled after score_custom_configuration returns

        # Run the scoring pipeline (using fast vectorized implementation)
        all_scores = score_custom_configuration_fast(
            metadata,
            progress_callback=progress_callback
        )

        # Count scored indicators
        scored_count = indicator_count
        job.emit_stage_complete(
            "scoring",
            f"Scored {scored_count} Indicators",
            {"count": scored_count}
        )

        # =====================================================================
        # Stage 4: Aggregate Hierarchy
        # =====================================================================
        job.set_status(JobStatus.AGGREGATING)
        # Aggregation already happened in score_custom_configuration
        job.emit_stage_complete("aggregate", "Aggregation Complete")

        # =====================================================================
        # Stage 5: Compute Ranks
        # =====================================================================
        # Ranking already happened in score_custom_configuration
        job.emit_stage_complete("ranking", "Ranks Computed")

        # =====================================================================
        # Stage 6: Build Visualizations (Save results)
        # =====================================================================
        job.set_status(JobStatus.SAVING)

        flat_scores = flatten_scores_for_storage(all_scores)

        try:
            # Store flat scores in sspi_custom_item_data
            stored_count = sspi_custom_item_data.store_scoring_results(
                config_hash=config_hash,
                results=flat_scores
            )
            logger.info(f"Stored {stored_count} flat score documents for job {job.job_id}")

            # Get country metadata for line chart transformation
            country_details = sspi_metadata.country_details()
            country_group_map = sspi_metadata.country_group_map()

            # Transform to line chart format
            line_data = transform_scores_to_line_format(
                all_scores=all_scores,
                custom_metadata=metadata,
                country_details=country_details,
                country_group_map=country_group_map
            )

            # Store line data in sspi_custom_panel_data
            line_count = sspi_custom_panel_data.store_line_data(
                config_hash=config_hash,
                line_data=line_data
            )
            logger.info(f"Stored {line_count} line chart documents for job {job.job_id}")

            # Update the config with the scored_hash for future has_scores checks
            # Skip for ad-hoc configs (they aren't stored in sspi_custom_user_structure)
            if not job.config_id.startswith("adhoc_"):
                try:
                    sspi_custom_user_structure.set_scored_hash(
                        config_id=job.config_id,
                        scored_hash=config_hash
                    )
                    logger.info(f"Updated config {job.config_id} with scored_hash {config_hash[:8]}...")
                except Exception as hash_err:
                    logger.warning(f"Failed to update scored_hash for config {job.config_id}: {hash_err}")

        except Exception as e:
            logger.error(f"Failed to store results: {e}")
            # Continue anyway - results are still in memory

        job.emit_stage_complete("visualizations", "Visualizations Ready")

        # =====================================================================
        # Complete
        # =====================================================================
        duration_ms = int((time.time() - start_time) * 1000)
        job.emit_complete(len(flat_scores), duration_ms, cached=False)

        logger.info(
            f"Completed job {job.job_id}: {len(flat_scores)} scores in {duration_ms}ms"
        )

    except Exception as e:
        logger.exception(f"Scoring job {job.job_id} failed: {e}")
        job.emit_error(str(e), "SCORING_ERROR")


# =============================================================================
# SSE Event Generator
# =============================================================================

def _terminal_event(status: JobStatus, doc: dict) -> tuple[str, dict] | None:
    """Build the terminal (event_type, data) for a job's terminal status."""
    if status == JobStatus.ERROR:
        return "error", {
            "message": doc.get("error") or "Unknown error",
            "code": "SCORING_ERROR",
        }
    if status == JobStatus.COMPLETE:
        result = doc.get("result") or {}
        return "complete", {
            "success": True,
            "total_scores": result.get("total_scores", 0),
            "duration_ms": 0,
            "cached": result.get("cached", False),
        }
    if status == JobStatus.CANCELLED:
        return "error", {"message": "Job was cancelled", "code": "CANCELLED"}
    return None


def generate_sse_events(job_id: str, timeout: float = 300.0, poll_interval: float = 0.5):
    """
    Generator for SSE events from a scoring job, polling the Mongo job document.

    Because job state lives in Mongo (not a per-process queue), this works
    regardless of which worker is serving the SSE request or running the
    pipeline thread (#893). The wire format is identical to the previous
    queue-based implementation so the frontend needs no change.

    Args:
        job_id: Job ID to stream events for
        timeout: Maximum time to stream (seconds)
        poll_interval: Seconds between Mongo polls

    Yields:
        SSE-formatted event strings
    """
    doc = sspi_scoring_jobs.get(job_id)
    if not doc:
        yield f"event: error\ndata: {{\"message\": \"Job not found\", \"code\": \"JOB_NOT_FOUND\"}}\n\n"
        return

    # Immediately send terminal state if the job already finished before the
    # SSE connection opened (e.g. cache hit, fast failure, or reconnect).
    status = _status_from_value(doc.get("status"))
    terminal = _terminal_event(status, doc)
    if terminal:
        yield _format_sse_event(*terminal)
        return

    # Send initial status event so the frontend knows the connection succeeded
    status_data = {
        "status": status.value,
        "progress": doc.get("progress", 0),
        "message": doc.get("message", ""),
    }
    yield f'event: status\ndata: {json.dumps(status_data)}\n\n'

    start_time = time.time()
    last_seq = 0
    last_stage_progress = None  # (stage, current, total)
    terminal_emitted = False

    while True:
        # Check timeout
        if time.time() - start_time > timeout:
            yield f"event: error\ndata: {{\"message\": \"Stream timeout\", \"code\": \"TIMEOUT\"}}\n\n"
            return

        doc = sspi_scoring_jobs.get(job_id)
        if not doc:
            # Job evicted mid-stream (D2 TTL/sweep)
            yield f"event: error\ndata: {{\"message\": \"Job not found\", \"code\": \"JOB_NOT_FOUND\"}}\n\n"
            return

        progressed = False

        # Drain newly appended events in seq order
        for event in doc.get("events", []):
            if event["seq"] <= last_seq:
                continue
            last_seq = event["seq"]
            progressed = True
            yield _format_sse_event(event["event_type"], event["data"])
            if event["event_type"] in ("complete", "error"):
                terminal_emitted = True
        if terminal_emitted:
            return

        # Synthesize a stage_progress event from the scalar progress fields when
        # they change (high-frequency progress is not stored as events).
        stage_progress = (
            doc.get("stage"),
            doc.get("stage_current"),
            doc.get("stage_total"),
        )
        if (
            stage_progress[1] is not None
            and stage_progress[2] is not None
            and stage_progress != last_stage_progress
        ):
            last_stage_progress = stage_progress
            progressed = True
            yield _format_sse_event("stage_progress", {
                "stage": stage_progress[0],
                "current": stage_progress[1],
                "total": stage_progress[2],
            })

        # Terminal status reached without a terminal event in the log (e.g. a
        # CANCELLED set by the cancel route): synthesize the terminal event.
        status = _status_from_value(doc.get("status"))
        if status in TERMINAL_STATUSES:
            terminal = _terminal_event(status, doc)
            if terminal:
                yield _format_sse_event(*terminal)
            return

        if not progressed:
            # Heartbeat to keep the connection alive while idle
            yield ": heartbeat\n\n"

        time.sleep(poll_interval)


def _format_sse_event(event_type: str, data: dict) -> str:
    """Format an SSE event from an event type and JSON-serializable data."""
    lines = [f"event: {event_type}"]
    lines.append(f"data: {json.dumps(data)}")
    lines.append("")  # Blank line to end event

    return "\n".join(lines) + "\n"
