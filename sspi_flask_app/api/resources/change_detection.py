"""
Change Detection for Custom SSPI Configurations

This module identifies which indicators have been modified from the default
SSPI configuration, enabling efficient scoring by only recomputing changed
indicators and reusing cached scores for unchanged ones.

Key Functions:
- identify_modified_indicators: Compare custom config to defaults
- compute_indicator_scoring_signature: Hash of everything that changes an
  indicator's OWN score (see SCORE_AFFECTING_FIELDS)
- get_default_indicator_hashes: Cache hash of default indicator configs

What counts as "changed" for an indicator
-----------------------------------------
An indicator is CHANGED when any of these differ from the default SSPI:
ScoreFunction (whitespace-normalized), DatasetCodes (order-sensitive, because
the vectorized goalpost path reads the first listed dataset), LowerGoalpost,
UpperGoalpost. A brand-new indicator code is CHANGED. If the default metadata
cannot be loaded, every indicator is CHANGED (fail safe).

Everything else leaves the indicator's own score untouched and therefore does
NOT make it changed: Weight (applied during aggregation), the parent category
or pillar (aggregation handles moves), names, descriptions and other display
fields.
"""

import hashlib
import json
import logging
from typing import NamedTuple
from sspi_flask_app.models.database import sspi_metadata
from sspi_flask_app.api.resources.metadata_validator import (
    compute_indicator_hash,
    canonicalize_value,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Data Classes
# =============================================================================

class ChangeDetectionResult(NamedTuple):
    """Result of change detection analysis."""
    modified_indicators: set[str]    # Indicators needing recomputation
    unchanged_indicators: set[str]   # Indicators with same scoring config as default
    new_indicators: set[str]         # Indicators not in default SSPI
    removed_indicators: set[str]     # Default indicators not in custom config
    default_available: bool = True   # False if defaults could not be loaded


# =============================================================================
# Default Configuration Cache
# =============================================================================

_default_indicator_hashes: dict[str, str] | None = None
_default_indicator_details: dict[str, dict] | None = None
_default_indicator_signatures: dict[str, str] | None = None

# Indicator fields that change the indicator's own score. Weight is
# deliberately absent: it only matters during aggregation.
SCORE_AFFECTING_FIELDS = (
    "DatasetCodes",
    "ScoreFunction",
    "LowerGoalpost",
    "UpperGoalpost",
)


def compute_indicator_scoring_signature(indicator: dict) -> str:
    """
    Hash the fields that determine an indicator's own score.

    Missing fields and None are equivalent. Strings are whitespace-normalized
    and numbers canonicalized (1 == 1.0) via canonicalize_value. DatasetCodes
    keep their order (the vectorized goalpost path scores the first dataset).
    """
    data = {}
    for field_name in SCORE_AFFECTING_FIELDS:
        value = indicator.get(field_name, None)
        if field_name == "DatasetCodes" and isinstance(value, list):
            value = [
                " ".join(v.split()) if isinstance(v, str) else v
                for v in value
            ]
        else:
            value = canonicalize_value(value)
        data[field_name] = value
    json_str = json.dumps(
        data, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    )
    return hashlib.sha256(json_str.encode("utf-8")).hexdigest()[:16]


GOALPOST_FIELDS = ("LowerGoalpost", "UpperGoalpost")


def _inherit_unset_goalposts(indicator: dict, default: dict) -> dict:
    """Copy of `indicator` with None/missing goalposts taken from `default`."""
    if all(indicator.get(field) is not None for field in GOALPOST_FIELDS):
        return indicator
    merged = dict(indicator)
    for field in GOALPOST_FIELDS:
        if merged.get(field) is None:
            merged[field] = default.get(field)
    return merged


def get_default_indicator_signatures() -> dict[str, str]:
    """
    Scoring signature of each default indicator, keyed by indicator code.

    An empty result (defaults unavailable) is never cached so a later call
    can recover once the database is reachable.
    """
    global _default_indicator_signatures
    if _default_indicator_signatures is not None:
        return _default_indicator_signatures
    signatures = {
        code: compute_indicator_scoring_signature(details)
        for code, details in _load_default_indicators().items()
    }
    if signatures:
        _default_indicator_signatures = signatures
    return signatures


def _load_default_indicators() -> dict[str, dict]:
    """
    Load default indicator details from database.

    Returns:
        Dictionary mapping IndicatorCode -> indicator metadata
    """
    global _default_indicator_details

    if _default_indicator_details is not None:
        return _default_indicator_details

    try:

        indicator_details = sspi_metadata.indicator_details()
        _default_indicator_details = {
            ind.get("IndicatorCode"): ind
            for ind in indicator_details
            if ind.get("IndicatorCode")
        }

        logger.info(f"Loaded {len(_default_indicator_details)} default indicators")
        return _default_indicator_details

    except Exception as e:
        logger.warning(f"Could not load default indicators from database: {e}")
        return {}


def get_default_indicator_hashes() -> dict[str, str]:
    """
    Get hash of each default indicator's scoring configuration.

    Uses caching to avoid repeated database queries and hash computations.

    Returns:
        Dictionary mapping IndicatorCode -> hash string (16 chars)
    """
    global _default_indicator_hashes

    if _default_indicator_hashes is not None:
        return _default_indicator_hashes

    default_indicators = _load_default_indicators()

    _default_indicator_hashes = {
        code: compute_indicator_hash(details)
        for code, details in default_indicators.items()
    }

    logger.info(f"Computed hashes for {len(_default_indicator_hashes)} default indicators")
    return _default_indicator_hashes


def clear_default_caches():
    """Clear cached default indicator data. Useful for testing or reloading."""
    global _default_indicator_hashes, _default_indicator_details
    global _default_indicator_signatures
    _default_indicator_hashes = None
    _default_indicator_details = None
    _default_indicator_signatures = None
    logger.info("Cleared default indicator caches")


def get_default_indicator_detail(indicator_code: str) -> dict | None:
    """Get the default details for a specific indicator."""
    defaults = _load_default_indicators()
    return defaults.get(indicator_code)


# =============================================================================
# Change Detection Functions
# =============================================================================

def identify_modified_indicators(
    custom_metadata: list[dict],
    actions: list[dict] | None = None
) -> ChangeDetectionResult:
    """
    Identify which indicators need recomputation.

    Compares each indicator's scoring signature (ScoreFunction, goalposts,
    DatasetCodes; see SCORE_AFFECTING_FIELDS) against the default SSPI.
    Weight and category/pillar placement do not count as changes.
    If the default metadata is unavailable, every indicator is reported as
    modified and default_available is False.

    Args:
        custom_metadata: User's custom configuration metadata
        actions: Optional action history from the configuration editor

    Returns:
        ChangeDetectionResult with sets of modified, unchanged, new, and removed codes

    Example:
        >>> result = identify_modified_indicators(custom_metadata)
        >>> print(f"Modified: {result.modified_indicators}")
        >>> print(f"Unchanged: {result.unchanged_indicators}")
    """
    default_hashes = get_default_indicator_signatures()
    default_codes = set(default_hashes.keys())
    default_available = bool(default_codes)

    # Extract indicators from custom metadata
    custom_indicators = {
        item.get("ItemCode"): item
        for item in custom_metadata
        if item.get("ItemType") == "Indicator" and item.get("ItemCode")
    }
    custom_codes = set(custom_indicators.keys())
    # Categorize indicators
    modified_indicators = set()
    unchanged_indicators = set()
    new_indicators = set()
    removed_indicators = set()
    if not default_available:
        logger.warning(
            "Default SSPI indicators unavailable; treating every indicator "
            "as modified"
        )
        return ChangeDetectionResult(
            modified_indicators=custom_codes,
            unchanged_indicators=set(),
            new_indicators=set(),
            removed_indicators=set(),
            default_available=False,
        )
    # Check each custom indicator
    for code, indicator in custom_indicators.items():
        if code not in default_codes:
            # This indicator doesn't exist in default SSPI
            new_indicators.add(code)
            modified_indicators.add(code)  # New = needs computation
            continue
        # Compare hash of scoring config. The builder stores goalposts inside
        # the ScoreFunction and saves LowerGoalpost/UpperGoalpost as None, so
        # an unset goalpost inherits the default rather than counting as an
        # edit (the scorer falls back to the ScoreFunction when they're None).
        custom_hash = compute_indicator_scoring_signature(
            _inherit_unset_goalposts(indicator, _load_default_indicators().get(code, {}))
        )
        default_hash = default_hashes[code]

        if custom_hash == default_hash:
            unchanged_indicators.add(code)
        else:
            modified_indicators.add(code)

    # Identify removed indicators (in default but not in custom)
    removed_indicators = default_codes - custom_codes
    # Cross-validate with actions if provided
    if actions:
        _validate_against_actions(
            actions,
            modified_indicators,
            unchanged_indicators,
            new_indicators
        )
    logger.info(
        f"Change detection: {len(modified_indicators)} modified, "
        f"{len(unchanged_indicators)} unchanged, "
        f"{len(new_indicators)} new, "
        f"{len(removed_indicators)} removed"
    )

    return ChangeDetectionResult(
        modified_indicators=modified_indicators,
        unchanged_indicators=unchanged_indicators,
        new_indicators=new_indicators,
        removed_indicators=removed_indicators
    )


def changed_indicator_codes(custom_metadata: list[dict]) -> set[str] | None:
    """
    Codes of indicators whose own score must be (re)computed and validated.

    Returns None if change detection fails for any reason, which callers
    pass straight through as "validate/compute everything".
    """
    try:
        items = [i for i in custom_metadata if isinstance(i, dict)]
        return identify_modified_indicators(items).modified_indicators
    except Exception as e:
        logger.warning(f"Change detection failed ({e}); treating all as changed")
        return None


def _validate_against_actions(
    actions: list[dict],
    modified: set[str],
    unchanged: set[str],
    new: set[str]
) -> None:
    """
    Cross-validate detected changes against action history.
    Logs warnings if there are inconsistencies between the detected changes
    and what the action history suggests.
    Args:
        actions: List of action dictionaries from config editor
        modified: Set of detected modified indicator codes
        unchanged: Set of detected unchanged indicator codes
        new: Set of detected new indicator codes
    """
    # Extract indicator codes mentioned in actions
    action_modified = set()
    action_new = set()

    for action in actions:
        action_type = action.get("type", "")
        item_code = action.get("itemCode") or action.get("indicatorCode")
        if not item_code:
            continue
        if action_type in ("modify_scorefunction", "modify_goalpost", "modify_datasets"):
            action_modified.add(item_code)
        elif action_type in ("add_indicator", "create_indicator"):
            action_new.add(item_code)
    # Check for inconsistencies
    # Modified by action but detected as unchanged
    inconsistent_unchanged = action_modified & unchanged
    if inconsistent_unchanged:
        logger.warning(
            f"Indicators modified in actions but detected unchanged: {inconsistent_unchanged}. "
            "This may indicate the changes were reverted."
        )
    # New by action but not detected as new
    inconsistent_not_new = action_new - new - modified
    if inconsistent_not_new:
        logger.warning(
            f"Indicators added in actions but not detected as new or modified: {inconsistent_not_new}. "
            "This may indicate the additions were removed."
        )


def get_indicator_change_summary(
    indicator_code: str,
    custom_indicator: dict
) -> dict:
    """
    Get a summary of what changed for a specific indicator.

    Args:
        indicator_code: Code of the indicator to check
        custom_indicator: Custom indicator metadata

    Returns:
        Dictionary describing the changes
    """
    default = get_default_indicator_detail(indicator_code)

    if default is None:
        return {
            "indicator_code": indicator_code,
            "status": "new",
            "changes": ["New indicator not in default SSPI"]
        }

    changes = []

    # Compare ItemCode (indicator code)
    default_code = default.get("ItemCode")
    custom_code = custom_indicator.get("ItemCode")
    if default_code != custom_code:
        changes.append(f"ItemCode: {default_code} → {custom_code}")

    # Compare ScoreFunction (normalize whitespace for comparison)
    default_sf = " ".join((default.get("ScoreFunction") or "").split())
    custom_sf = " ".join((custom_indicator.get("ScoreFunction") or "").split())
    if default_sf != custom_sf:
        changes.append("ScoreFunction changed")

    # Compare datasets
    default_ds = set(default.get("DatasetCodes") or [])
    custom_ds = set(custom_indicator.get("DatasetCodes") or [])
    if default_ds != custom_ds:
        added = custom_ds - default_ds
        removed = default_ds - custom_ds
        if added:
            changes.append(f"Datasets added: {added}")
        if removed:
            changes.append(f"Datasets removed: {removed}")

    return {
        "indicator_code": indicator_code,
        "status": "modified" if changes else "unchanged",
        "changes": changes if changes else ["No scoring-relevant changes"]
    }


# =============================================================================
# Utility Functions
# =============================================================================

def get_modified_indicator_details(
    custom_metadata: list[dict],
    modified_codes: set[str]
) -> list[dict]:
    """
    Get full metadata for modified indicators.
    Args:
        custom_metadata: User's custom configuration
        modified_codes: Set of modified indicator codes
    Returns:
        List of indicator metadata dicts for modified indicators
    """
    return [
        item for item in custom_metadata
        if item.get("ItemType") == "Indicator"
        and item.get("ItemCode") in modified_codes
    ]


def check_scoring_equivalence(indicator1: dict, indicator2: dict) -> bool:
    """
    Check if two indicators have equivalent scoring configurations.

    Args:
        indicator1: First indicator metadata
        indicator2: Second indicator metadata

    Returns:
        True if scoring configurations are equivalent
    """
    return compute_indicator_hash(indicator1) == compute_indicator_hash(indicator2)
