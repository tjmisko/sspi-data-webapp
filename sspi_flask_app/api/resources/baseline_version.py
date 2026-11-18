"""
Baseline version for the custom-scoring cache.

Cached custom results embed official indicator scores (sspi_item_data) for
every unchanged indicator, so they go stale whenever the official scores are
regenerated. The config hash only identifies the configuration, so the cache
is keyed on (config_hash, baseline_version) via ``cache_key``.

``compute_baseline_version`` is a cheap deterministic fingerprint of the
official indicator scores: row count plus the sum of Score, one indexed
aggregation. It changes whenever finalize writes different scores (the
finalize step has no stored timestamp to use). A re-finalize that reproduces
identical scores keeps the version, which is correct: nothing is stale.
"""
import hashlib
import logging
import time

from sspi_flask_app.models.database import sspi_item_data

logger = logging.getLogger(__name__)

UNKNOWN_VERSION = "unknown"
_VERSION_TTL_SECONDS = 60.0
_version_cache: tuple[float, str] | None = None


def compute_baseline_version() -> str:
    """
    Fingerprint of the official indicator scores, 12 hex characters.

    Returns UNKNOWN_VERSION when the store cannot be read, so scoring still
    works (with a version-less key) while the database is unavailable.
    """
    try:
        rows = list(sspi_item_data.aggregate([
            {"$match": {"ItemType": "Indicator", "Score": {"$ne": None}}},
            {"$group": {"_id": None, "n": {"$sum": 1},
                        "total": {"$sum": "$Score"}}},
        ]))
    except Exception as e:
        logger.warning(f"Could not compute baseline version: {e}")
        return UNKNOWN_VERSION
    if not rows:
        return UNKNOWN_VERSION
    fingerprint = f"{rows[0]['n']}:{rows[0]['total']:.9f}"
    return hashlib.sha256(fingerprint.encode("utf-8")).hexdigest()[:12]


def get_baseline_version(use_cache: bool = True) -> str:
    """compute_baseline_version, memoized per process for a short TTL."""
    global _version_cache
    now = time.monotonic()
    if use_cache and _version_cache and now - _version_cache[0] < _VERSION_TTL_SECONDS:
        return _version_cache[1]
    version = compute_baseline_version()
    _version_cache = (now, version)
    return version


def clear_baseline_version_cache() -> None:
    global _version_cache
    _version_cache = None


def cache_key(config_hash: str, baseline_version: str | None = None) -> str:
    """
    Key the custom result cache is stored and looked up under.

    32 lowercase hex characters (same shape as config_hash, which the panel
    route validates), derived from config_hash and the baseline version. A
    different baseline version always yields a different key.
    """
    if baseline_version is None:
        baseline_version = get_baseline_version()
    digest = hashlib.sha256(
        f"{config_hash}:{baseline_version}".encode("utf-8")
    ).hexdigest()
    return digest[:32]


def config_scores_are_current(config: dict, has_scores) -> bool:
    """
    True when a saved config's stored results exist and were computed against
    the current official baseline.

    `has_scores` is a callable taking a scored_hash (the custom panel store's
    has_scores). A config scored before the baseline version was recorded, or
    against an older baseline, counts as unscored so the UI asks for a rescore
    instead of showing stale results.
    """
    scored_hash = config.get("scored_hash")
    if not scored_hash:
        return False
    if config.get("scored_baseline_version") != get_baseline_version():
        return False
    return bool(has_scores(scored_hash))
