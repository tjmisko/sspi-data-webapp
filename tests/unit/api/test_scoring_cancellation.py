"""
Unit tests for cooperative cancellation of scoring jobs (D3).

These tests require a live MongoDB and write only to a dedicated, disposable
collection (``test_scoring_jobs_cancel``). The scoring_tasks singleton is
monkeypatched to point at that collection so cancel_job / is_cancel_requested /
_abort_if_cancelled operate against test data, not the real job store.

Run with:
    pytest tests/unit/api/test_scoring_cancellation.py
"""
import pytest
from datetime import datetime, timezone

import sspi_flask_app.api.resources.scoring_tasks as st
from sspi_flask_app.models.database import sspidb
from sspi_flask_app.models.database.sspi_scoring_jobs import SSPIScoringJobs


@pytest.fixture(scope="function")
def patched_store(monkeypatch):
    """Point scoring_tasks at a disposable scoring-jobs collection."""
    collection = sspidb.test_scoring_jobs_cancel
    collection.delete_many({})
    model = SSPIScoringJobs(collection)
    model.create_indexes()
    monkeypatch.setattr(st, "sspi_scoring_jobs", model)
    yield model
    collection.delete_many({})
    sspidb.drop_collection(collection)


def _insert(model, job_id, status="scoring", cancel_requested=False):
    now = datetime.now(timezone.utc)
    model.create_job({
        "job_id": job_id,
        "config_id": f"cfg_{job_id}",
        "config_hash": None,
        "user_id": "alice",
        "status": status,
        "progress": 0,
        "message": "",
        "stage": None,
        "stage_current": None,
        "stage_total": None,
        "result": None,
        "error": None,
        "cancel_requested": cancel_requested,
        "seq": 0,
        "events": [],
        "created_at": now,
        "updated_at": now,
        "completed_at": None,
        "expire_at": now,
        "worker_pid": 0,
    })


def test_should_set_cancel_requested_when_cancelling_running_job(patched_store):
    _insert(patched_store, "running", status="scoring")
    assert st.cancel_job("running") is True
    doc = patched_store.get("running")
    assert doc["cancel_requested"] is True
    # A running job is NOT flipped to terminal here - the pipeline transitions
    # it at its next checkpoint so the owning worker writes the final status.
    assert doc["status"] == "scoring"


def test_should_cancel_pending_job_immediately(patched_store):
    _insert(patched_store, "queued", status="pending")
    assert st.cancel_job("queued") is True
    doc = patched_store.get("queued")
    assert doc["status"] == "cancelled"
    assert doc["cancel_requested"] is True
    assert doc["completed_at"] is not None


def test_should_return_false_when_cancelling_finished_job(patched_store):
    _insert(patched_store, "done", status="complete")
    assert st.cancel_job("done") is False
    assert patched_store.get("done")["status"] == "complete"


def test_should_return_false_when_cancelling_missing_job(patched_store):
    assert st.cancel_job("nope") is False


def test_should_report_cancel_requested_flag(patched_store):
    _insert(patched_store, "flagged", cancel_requested=True)
    _insert(patched_store, "unflagged", cancel_requested=False)
    assert st.is_cancel_requested("flagged") is True
    assert st.is_cancel_requested("unflagged") is False


def test_should_abort_and_emit_cancelled_when_flag_set(patched_store):
    _insert(patched_store, "running", status="scoring", cancel_requested=True)
    job = st.get_job("running")  # read-only snapshot, write-through capable
    assert st._abort_if_cancelled(job) is True
    doc = patched_store.get("running")
    assert doc["status"] == "cancelled"
    assert doc["completed_at"] is not None
    # Terminal event uses the error/CANCELLED wire shape the frontend handles
    assert doc["events"][-1]["event_type"] == "error"
    assert doc["events"][-1]["data"]["code"] == "CANCELLED"


def test_should_not_abort_when_flag_unset(patched_store):
    _insert(patched_store, "running", status="scoring", cancel_requested=False)
    job = st.get_job("running")
    assert st._abort_if_cancelled(job) is False
    assert patched_store.get("running")["status"] == "scoring"
