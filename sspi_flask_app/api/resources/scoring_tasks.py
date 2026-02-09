"""
Background Task Management for Custom SSPI Scoring

This module manages background scoring jobs with progress tracking for SSE streaming.

Key Components:
- ScoringJob: Data class for job state and progress
- scoring_jobs: In-memory job registry
- start_scoring_job: Launch background scoring
- run_scoring_pipeline: Main pipeline executed in background thread
"""

import json
import logging
import re
import secrets
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from queue import Queue, Empty
from threading import Thread
from typing import Callable

from sspi_flask_app.api.resources.metadata_validator import (
    validate_custom_metadata,
    compute_config_hash,
    ValidationResult,
)
from sspi_flask_app.api.resources.change_detection import (
    identify_modified_indicators,
    ChangeDetectionResult,
)
from sspi_flask_app.api.resources.custom_scoring import (
    flatten_scores_for_storage,
    identify_empty_datasets,
    transform_scores_to_line_format,
    build_custom_tree,
)
from sspi_flask_app.api.resources.fast_custom_scoring import (
    score_custom_configuration_fast,
)
from sspi_flask_app.models.database import (
    sspi_custom_panel_data,
    sspi_custom_item_data,
    sspi_custom_user_structure,
    sspi_item_data,
    sspi_metadata,
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


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class ProgressEvent:
    """A single progress update for SSE streaming."""
    event_type: str  # "progress", "indicator_start", "indicator_complete", "complete", "error"
    data: dict
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class ScoringJob:
    """State and progress tracking for a scoring job."""
    job_id: str
    config_id: str
    config_hash: str | None
    user_id: str
    status: JobStatus
    progress: int  # 0-100
    message: str
    result: dict | None = None
    error: str | None = None
    progress_queue: Queue = field(default_factory=Queue)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    completed_at: str | None = None

    def emit_progress(self, percent: int, message: str, event_type: str = "progress"):
        """Emit a progress event to the queue."""
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
        self.progress_queue.put(event)

    def emit_stage_complete(self, stage: str, message: str, data: dict = {}):
        """
        Emit stage completion event.

        Args:
            stage: Stage identifier (validate, identify, scoring, aggregate, ranking, visualizations)
            message: Completion message to display
            data: Optional additional data
        """
        event = ProgressEvent(
            event_type="stage_complete",
            data={
                "stage": stage,
                "message": message,
                **(data or {})
            }
        )
        self.progress_queue.put(event)

    def emit_stage_progress(self, stage: str, current: int, total: int):
        """
        Emit progress within a stage (for stages with progress bars).

        Args:
            stage: Stage identifier
            current: Current item number
            total: Total items to process
        """
        event = ProgressEvent(
            event_type="stage_progress",
            data={
                "stage": stage,
                "current": current,
                "total": total,
            }
        )
        self.progress_queue.put(event)

    def emit_indicator_start(self, code: str, name: str, index: int, total: int):
        """Emit indicator scoring start event."""
        event = ProgressEvent(
            event_type="indicator_start",
            data={
                "code": code,
                "name": name,
                "index": index,
                "total": total,
            }
        )
        self.progress_queue.put(event)

    def emit_indicator_complete(self, code: str, countries: int, duration_ms: int):
        """Emit indicator scoring complete event."""
        event = ProgressEvent(
            event_type="indicator_complete",
            data={
                "code": code,
                "countries": countries,
                "duration_ms": duration_ms,
            }
        )
        self.progress_queue.put(event)

    def emit_complete(self, total_scores: int, duration_ms: int, cached: bool = False):
        """Emit job completion event."""
        self.status = JobStatus.COMPLETE
        self.completed_at = datetime.now(timezone.utc).isoformat()
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
        self.progress_queue.put(event)

    def emit_error(self, message: str, code: str = "SCORING_ERROR"):
        """Emit error event."""
        self.status = JobStatus.ERROR
        self.error = message
        self.completed_at = datetime.now(timezone.utc).isoformat()
        event = ProgressEvent(
            event_type="error",
            data={
                "message": message,
                "code": code,
            }
        )
        self.progress_queue.put(event)


# =============================================================================
# Job Registry (In-Memory)
# =============================================================================

# In-memory job tracking (for MVP - could move to Redis later)
scoring_jobs: dict[str, ScoringJob] = {}

# Job cleanup threshold (jobs older than this are removed)
JOB_TTL_SECONDS = 3600  # 1 hour


def _cleanup_old_jobs():
    """Remove jobs older than TTL."""
    now = datetime.now(timezone.utc)
    to_remove = []

    for job_id, job in scoring_jobs.items():
        created = datetime.fromisoformat(job.created_at.replace('Z', '+00:00'))
        age = (now - created).total_seconds()

        if age > JOB_TTL_SECONDS:
            to_remove.append(job_id)

    for job_id in to_remove:
        del scoring_jobs[job_id]

    if to_remove:
        logger.info(f"Cleaned up {len(to_remove)} old scoring jobs")


def get_job(job_id: str) -> ScoringJob | None:
    """Get a job by ID."""
    return scoring_jobs.get(job_id)


def get_user_jobs(user_id: str) -> list[ScoringJob]:
    """Get all jobs for a user."""
    return [job for job in scoring_jobs.values() if job.user_id == user_id]


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

    Args:
        config_id: Configuration identifier
        metadata: Custom SSPI metadata
        actions: Action history from editor
        user_id: User who initiated the job

    Returns:
        job_id for tracking via SSE
    """
    # Cleanup old jobs first
    _cleanup_old_jobs()
    # Generate job ID
    job_id = secrets.token_hex(16)
    # Create job entry
    job = ScoringJob(
        job_id=job_id,
        config_id=config_id,
        config_hash=None,  # Will be computed during validation
        user_id=user_id,
        status=JobStatus.PENDING,
        progress=0,
        message="Starting...",
    )
    scoring_jobs[job_id] = job
    # Start background thread
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
    Cancel a running job.

    Args:
        job_id: Job to cancel

    Returns:
        True if job was found and cancelled
    """
    job = scoring_jobs.get(job_id)
    if not job:
        return False

    if job.status in (JobStatus.COMPLETE, JobStatus.ERROR, JobStatus.CANCELLED):
        return False

    job.status = JobStatus.CANCELLED
    job.message = "Cancelled by user"
    job.completed_at = datetime.now(timezone.utc).isoformat()

    logger.info(f"Cancelled job {job_id}")
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
    2. identify - Identify modified indicators
    3. scoring - Score modified indicators (with progress bar)
    4. aggregate - Aggregate hierarchy
    5. ranking - Compute ranks
    6. visualizations - Build visualizations (save results)
    """
    start_time = time.time()
    try:
        job.status = JobStatus.VALIDATING

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
        job.config_hash = config_hash

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
                    job.result = {"cached": True, "results": cached_results}
                    job.emit_complete(len(cached_results), duration_ms, cached=True)

                    logger.info(f"Cache hit for job {job.job_id}, returning {len(cached_results)} cached results")
                    return
        except Exception as e:
            logger.warning(f"Cache check failed: {e}, proceeding with scoring")

        # =====================================================================
        # Stage 2: Identify Modified Indicators
        # =====================================================================
        change_result = identify_modified_indicators(metadata, actions)
        modified_count = len(change_result.modified_indicators)
        unchanged_count = len(change_result.unchanged_indicators)

        job.emit_stage_complete(
            "identify",
            f"Identified {modified_count} Modified Indicators",
            {"modified": modified_count, "unchanged": unchanged_count}
        )

        logger.info(
            f"Job {job.job_id}: {modified_count} modified, {unchanged_count} unchanged"
        )

        # =====================================================================
        # Stage 3: Score Modified Indicators
        # =====================================================================
        job.status = JobStatus.SCORING

        # Get default scores for unchanged indicators from sspi_item_data
        default_scores = None
        if change_result.unchanged_indicators:
            try:
                country_codes = sspi_metadata.country_group("SSPI67") or []
                default_scores = {}
                for indicator_code in change_result.unchanged_indicators:
                    # Fetch pre-computed scores from sspi_item_data
                    scores = list(sspi_item_data.find({
                        "ItemCode": indicator_code,
                        "ItemType": "Indicator",
                        "CountryCode": {"$in": country_codes},
                        "Year": {"$gte": 2000, "$lte": 2023}
                    }, {"_id": 0}))
                    # Convert to expected format
                    formatted_scores = []
                    for doc in scores:
                        formatted_scores.append({
                            "item_code": doc.get("ItemCode"),
                            "item_name": doc.get("ItemName", indicator_code),
                            "item_type": "Indicator",
                            "country_code": doc.get("CountryCode"),
                            "year": doc.get("Year"),
                            "score": doc.get("Score", 0) * 100,  # Convert to 0-100 scale
                            "imputed": False,
                            "imputation_method": None,
                        })

                    if formatted_scores:
                        default_scores[indicator_code] = formatted_scores

                logger.info(f"Fetched {len(default_scores)} unchanged indicator scores")

            except Exception as e:
                logger.warning(f"Failed to fetch unchanged indicator scores: {e}")
                default_scores = None

        # Progress callback for scoring - emits stage_progress events
        indicators_to_score = [
            item for item in metadata
            if item.get("ItemType") == "Indicator"
            and item.get("ItemCode") in (change_result.modified_indicators or set())
        ]
        total_to_score = len(indicators_to_score) if change_result.modified_indicators else len([
            item for item in metadata if item.get("ItemType") == "Indicator"
        ])

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
            modified_indicators=change_result.modified_indicators or None,
            default_scores=default_scores,
            progress_callback=progress_callback
        )

        # Count scored indicators
        scored_count = total_to_score
        job.emit_stage_complete(
            "scoring",
            f"Scored {scored_count} Indicators",
            {"count": scored_count}
        )

        # =====================================================================
        # Stage 4: Aggregate Hierarchy
        # =====================================================================
        job.status = JobStatus.AGGREGATING
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
        job.status = JobStatus.SAVING

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
        job.result = {"cached": False, "results": flat_scores}
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

def generate_sse_events(job_id: str, timeout: float = 300.0):
    """
    Generator for SSE events from a scoring job.

    Args:
        job_id: Job ID to stream events for
        timeout: Maximum time to wait for events (seconds)

    Yields:
        SSE-formatted event strings
    """
    job = scoring_jobs.get(job_id)
    if not job:
        yield f"event: error\ndata: {{\"message\": \"Job not found\", \"code\": \"JOB_NOT_FOUND\"}}\n\n"
        return

    # Immediately send current job status on connection
    # This handles the case where job failed/completed before SSE connected
    if job.status == JobStatus.ERROR:
        error_data = {"message": job.error or "Unknown error", "code": "SCORING_ERROR"}
        yield f'event: error\ndata: {json.dumps(error_data)}\n\n'
        return
    elif job.status == JobStatus.COMPLETE:
        results_count = len(job.result.get("results", [])) if job.result else 0
        complete_data = {"success": True, "total_scores": results_count, "duration_ms": 0, "cached": False}
        yield f'event: complete\ndata: {json.dumps(complete_data)}\n\n'
        return
    elif job.status == JobStatus.CANCELLED:
        yield f'event: error\ndata: {json.dumps({"message": "Job was cancelled", "code": "CANCELLED"})}\n\n'
        return

    # Send initial status event so frontend knows connection succeeded and current state
    status_data = {"status": job.status.value, "progress": job.progress, "message": job.message}
    yield f'event: status\ndata: {json.dumps(status_data)}\n\n'

    start_time = time.time()

    while True:
        # Check timeout
        if time.time() - start_time > timeout:
            yield f"event: error\ndata: {{\"message\": \"Stream timeout\", \"code\": \"TIMEOUT\"}}\n\n"
            return

        # Check if job is done
        if job.status in (JobStatus.COMPLETE, JobStatus.ERROR, JobStatus.CANCELLED):
            # Drain remaining events
            while True:
                try:
                    event = job.progress_queue.get_nowait()
                    yield _format_sse_event(event)
                except Empty:
                    break
            return

        # Get next event with timeout
        try:
            event = job.progress_queue.get(timeout=1.0)
            yield _format_sse_event(event)

            # If this was a terminal event, we're done
            if event.event_type in ("complete", "error"):
                return

        except Empty:
            # Send heartbeat to keep connection alive
            yield ": heartbeat\n\n"


def _format_sse_event(event: ProgressEvent) -> str:
    """Format a ProgressEvent as an SSE string."""
    lines = [f"event: {event.event_type}"]
    lines.append(f"data: {json.dumps(event.data)}")
    lines.append("")  # Blank line to end event

    return "\n".join(lines) + "\n"
