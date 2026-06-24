"""
Unit tests for the SSPIScoringJobs worker-safe job store model.

These tests require a live MongoDB (importing the model package connects).
They write only to a dedicated, disposable collection (``test_scoring_jobs``)
which is cleared and dropped around each test.

Run with:
    pytest tests/unit/models/test_sspi_scoring_jobs.py
"""
import pytest
from datetime import datetime, timezone, timedelta

from pymongo.errors import DuplicateKeyError

from sspi_flask_app.models.database import sspidb
from sspi_flask_app.models.database.sspi_scoring_jobs import SSPIScoringJobs
from sspi_flask_app.models.errors import InvalidDocumentFormatError


@pytest.fixture(scope="function")
def jobs_model():
    """Provide a clean SSPIScoringJobs backed by a disposable collection."""
    collection = sspidb.test_scoring_jobs
    collection.delete_many({})
    model = SSPIScoringJobs(collection)
    model.create_indexes()
    yield model
    collection.delete_many({})
    sspidb.drop_collection(collection)


def _make_job_doc(job_id, user_id="alice", status="pending", progress=0):
    now = datetime.now(timezone.utc)
    return {
        "job_id": job_id,
        "config_id": f"cfg_{job_id}",
        "config_hash": None,
        "user_id": user_id,
        "status": status,
        "progress": progress,
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
        "worker_pid": 0,
    }


# =============================================================================
# CRUD
# =============================================================================

def test_should_create_and_get_job_when_inserted(jobs_model):
    jobs_model.create_job(_make_job_doc("job1"))
    doc = jobs_model.get("job1")
    assert doc is not None
    assert doc["job_id"] == "job1"
    assert doc["user_id"] == "alice"
    assert doc["status"] == "pending"
    assert "_id" not in doc


def test_should_return_none_when_job_missing(jobs_model):
    assert jobs_model.get("does-not-exist") is None


def test_should_list_only_jobs_owned_by_user(jobs_model):
    jobs_model.create_job(_make_job_doc("job1", user_id="alice"))
    jobs_model.create_job(_make_job_doc("job2", user_id="alice"))
    jobs_model.create_job(_make_job_doc("job3", user_id="bob"))
    alice_jobs = jobs_model.list_for_user("alice")
    assert {j["job_id"] for j in alice_jobs} == {"job1", "job2"}


# =============================================================================
# Event log
# =============================================================================

def test_should_increment_seq_monotonically_when_appending_events(jobs_model):
    jobs_model.create_job(_make_job_doc("job1"))
    seq1 = jobs_model.append_event("job1", "stage_complete", {"stage": "validate"})
    seq2 = jobs_model.append_event("job1", "stage_complete", {"stage": "identify"})
    seq3 = jobs_model.append_event("job1", "stage_complete", {"stage": "scoring"})
    assert [seq1, seq2, seq3] == [1, 2, 3]
    doc = jobs_model.get("job1")
    assert [e["seq"] for e in doc["events"]] == [1, 2, 3]
    assert [e["data"]["stage"] for e in doc["events"]] == ["validate", "identify", "scoring"]


def test_should_return_only_events_after_last_seq_when_polling(jobs_model):
    jobs_model.create_job(_make_job_doc("job1"))
    jobs_model.append_event("job1", "stage_complete", {"stage": "validate"})
    jobs_model.append_event("job1", "stage_complete", {"stage": "identify"})
    jobs_model.append_event("job1", "stage_complete", {"stage": "scoring"})
    new_events = jobs_model.events_since("job1", last_seq=1)
    assert [e["seq"] for e in new_events] == [2, 3]


def test_should_return_none_when_appending_to_missing_job(jobs_model):
    assert jobs_model.append_event("nope", "complete", {}) is None


def test_should_apply_set_fields_atomically_with_event(jobs_model):
    jobs_model.create_job(_make_job_doc("job1"))
    jobs_model.append_event(
        "job1",
        "complete",
        {"success": True, "total_scores": 7},
        set_fields={"status": "complete", "progress": 100},
    )
    doc = jobs_model.get("job1")
    # Terminal status and its terminal event are visible in the same document
    assert doc["status"] == "complete"
    assert doc["progress"] == 100
    assert doc["events"][-1]["event_type"] == "complete"


# =============================================================================
# Scalar updates
# =============================================================================

def test_should_update_fields_and_stamp_updated_at_when_set_fields(jobs_model):
    jobs_model.create_job(_make_job_doc("job1"))
    before = jobs_model.get("job1")["updated_at"]
    modified = jobs_model.set_fields("job1", progress=42, stage="scoring")
    assert modified == 1
    doc = jobs_model.get("job1")
    assert doc["progress"] == 42
    assert doc["stage"] == "scoring"
    assert doc["updated_at"] >= before


def test_should_return_zero_when_set_fields_called_with_no_fields(jobs_model):
    jobs_model.create_job(_make_job_doc("job1"))
    assert jobs_model.set_fields("job1") == 0


# =============================================================================
# Concurrency cap support
# =============================================================================

def test_should_count_active_jobs_per_user(jobs_model):
    jobs_model.create_job(_make_job_doc("a1", user_id="alice", status="scoring"))
    jobs_model.create_job(_make_job_doc("a2", user_id="alice", status="complete"))
    jobs_model.create_job(_make_job_doc("b1", user_id="bob", status="pending"))
    assert jobs_model.count_active("alice") == 1
    assert jobs_model.count_active("bob") == 1
    assert jobs_model.count_active() == 2  # global: a1 + b1 (a2 is terminal)


# =============================================================================
# Indexes & validation
# =============================================================================

def test_should_create_unique_job_id_index(jobs_model):
    info = jobs_model._mongo_database.index_information()
    assert "unique_job_id" in info
    assert info["unique_job_id"].get("unique") is True


def test_should_raise_on_duplicate_job_id_with_unique_index(jobs_model):
    jobs_model.create_job(_make_job_doc("dup"))
    with pytest.raises(DuplicateKeyError):
        jobs_model.create_job(_make_job_doc("dup"))


def test_should_reject_invalid_status_in_validation(jobs_model):
    doc = _make_job_doc("job1", status="not-a-status")
    with pytest.raises(InvalidDocumentFormatError):
        jobs_model.create_job(doc)


def test_should_reject_out_of_range_progress(jobs_model):
    doc = _make_job_doc("job1", progress=150)
    with pytest.raises(InvalidDocumentFormatError):
        jobs_model.create_job(doc)


def test_should_reject_missing_job_id(jobs_model):
    doc = _make_job_doc("job1")
    del doc["job_id"]
    with pytest.raises(InvalidDocumentFormatError):
        jobs_model.create_job(doc)
