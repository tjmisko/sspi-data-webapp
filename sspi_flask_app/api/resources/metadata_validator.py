"""
Metadata Validator for Custom SSPI Configurations

This module provides validation and hashing functions for custom SSPI metadata structures.
Used for validating user-provided configurations and computing deterministic hashes for caching.

Key Functions:
- validate_custom_metadata: Full validation of a custom configuration
- canonicalize_metadata: Sort metadata into canonical order for hashing
- compute_config_hash: Compute deterministic hash for cache lookups
"""

import hashlib
import json
import logging
from dataclasses import dataclass, field
from typing import Any

from sspi_flask_app.api.resources.score_function_validator import (
    validate_score_function,
    ScoreFunctionValidationError,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Constants
# =============================================================================

VALID_ITEM_TYPES = frozenset({"SSPI", "Pillar", "Category", "Indicator"})

# Required fields per ItemType
# NOTE: These must match the actual metadata schema from `sspi metadata item:*`
# Indicators do NOT have CategoryCode or PillarCode in canonical metadata
REQUIRED_FIELDS = {
    "SSPI": {"ItemType", "ItemCode", "ItemName", "Children", "PillarCodes"},
    "Pillar": {"ItemType", "ItemCode", "ItemName", "Children", "CategoryCodes", "PillarCode"},
    "Category": {"ItemType", "ItemCode", "ItemName", "Children", "IndicatorCodes", "CategoryCode", "PillarCode"},
    "Indicator": {"ItemType", "ItemCode", "ItemName", "IndicatorCode"},
}

# Fields that affect scoring (used for change detection)
# Only ScoreFunction, ItemCode (indicator code), and DatasetCodes trigger recomputation
# Goalposts are embedded in the ScoreFunction itself, not tracked separately
SCORING_RELEVANT_FIELDS = frozenset({
    "ItemCode",
    "DatasetCodes",
    "ScoreFunction",
})

# Fields that matter for config hash computation (structure + scoring)
# These fields determine whether two configs are functionally equivalent
# Excludes display-only fields like Description, Footnote, Policy, etc.
CONFIG_HASH_FIELDS = frozenset({
    # Structure fields (all item types)
    "ItemType",
    "ItemCode",
    "ItemName",
    "Children",
    "TreeIndex",
    "ItemOrder",
    # Hierarchy references
    "PillarCodes",
    "CategoryCodes",
    "IndicatorCodes",
    "PillarCode",
    "CategoryCode",
    # Scoring fields (indicators)
    "DatasetCodes",
    "ScoreFunction",
})


# =============================================================================
# Validation Result Classes
# =============================================================================

@dataclass
class ValidationError:
    """A single validation error."""
    item_code: str | None
    field: str | None
    message: str
    severity: str = "error"  # "error" or "warning"


@dataclass
class ValidationResult:
    """Result of metadata validation."""
    valid: bool
    errors: list[ValidationError] = field(default_factory=list)
    warnings: list[ValidationError] = field(default_factory=list)
    item_count: int = 0
    indicator_count: int = 0
    dropped_indicators: list[dict] = field(default_factory=list)

    def add_error(self, item_code: str | None, field: str | None, message: str):
        self.errors.append(ValidationError(item_code, field, message, "error"))
        self.valid = False

    def add_warning(self, item_code: str | None, field: str | None, message: str):
        self.warnings.append(ValidationError(item_code, field, message, "warning"))

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "valid": self.valid,
            "errors": [
                {"item_code": e.item_code, "field": e.field, "message": e.message}
                for e in self.errors
            ],
            "warnings": [
                {"item_code": w.item_code, "field": w.field, "message": w.message}
                for w in self.warnings
            ],
            "item_count": self.item_count,
            "indicator_count": self.indicator_count,
            "dropped_indicators": self.dropped_indicators,
        }


class MetadataValidationError(Exception):
    """Raised when metadata validation fails critically."""

    def __init__(self, message: str, validation_result: ValidationResult | None = None):
        self.validation_result = validation_result
        super().__init__(message)


# =============================================================================
# Main Validation Functions
# =============================================================================

def validate_custom_metadata(
    metadata: list[dict],
    valid_dataset_codes: set[str] | None = None,
    validate_score_functions: bool = True,
    check_data_availability: bool = False
) -> ValidationResult:
    """
    Validate complete custom SSPI metadata structure.

    Validates:
    - Required fields per ItemType
    - Hierarchy consistency (Children match *Codes fields)
    - ScoreFunction validity for Indicators
    - DatasetCodes exist (if valid_dataset_codes provided)
    - Data availability (if check_data_availability=True)

    Args:
        metadata: List of metadata item dictionaries
        valid_dataset_codes: Optional set of valid dataset codes for validation
        validate_score_functions: Whether to validate ScoreFunction strings
        check_data_availability: Whether to check if datasets have actual data

    Returns:
        ValidationResult with errors, warnings, and dropped_indicators
    """
    result = ValidationResult(valid=True)

    if not metadata:
        result.add_error(None, None, "Metadata list cannot be empty")
        return result

    if not isinstance(metadata, list):
        result.add_error(None, None, "Metadata must be a list")
        return result

    # Build lookup for hierarchy validation
    items_by_code: dict[str, dict] = {}
    item_type_counts = {"SSPI": 0, "Pillar": 0, "Category": 0, "Indicator": 0}

    # First pass: validate structure and build lookup
    for i, item in enumerate(metadata):
        if not isinstance(item, dict):
            result.add_error(None, None, f"Item at index {i} is not a dictionary")
            continue

        item_type = item.get("ItemType")
        item_code = item.get("ItemCode")

        # Validate ItemType
        if not item_type:
            result.add_error(item_code, "ItemType", f"Missing ItemType (index {i})")
            continue

        if item_type not in VALID_ITEM_TYPES:
            result.add_error(
                item_code, "ItemType",
                f"Invalid ItemType '{item_type}'. Must be one of: {', '.join(sorted(VALID_ITEM_TYPES))}"
            )
            continue

        item_type_counts[item_type] += 1

        # Validate ItemCode
        if not item_code:
            result.add_error(None, "ItemCode", f"Missing ItemCode for {item_type} at index {i}")
            continue

        if not isinstance(item_code, str):
            result.add_error(item_code, "ItemCode", f"ItemCode must be a string")
            continue

        # Check for duplicate codes
        if item_code in items_by_code:
            result.add_error(item_code, "ItemCode", f"Duplicate ItemCode: {item_code}")
            continue

        items_by_code[item_code] = item

        # Validate required fields for ItemType
        validate_required_fields(item, item_type, result)

        # Validate indicator-specific fields
        if item_type == "Indicator":
            validate_indicator_metadata(
                item,
                valid_dataset_codes,
                validate_score_functions,
                result
            )

    # Validate hierarchy structure
    result.item_count = len(items_by_code)
    result.indicator_count = item_type_counts["Indicator"]

    # Must have exactly one SSPI root
    if item_type_counts["SSPI"] == 0:
        result.add_error(None, None, "Missing SSPI root item")
    elif item_type_counts["SSPI"] > 1:
        result.add_error(None, None, f"Multiple SSPI root items found ({item_type_counts['SSPI']})")

    # Validate hierarchy relationships
    validate_hierarchy(items_by_code, result)

    # Check for empty datasets if requested
    if check_data_availability:
        from sspi_flask_app.api.resources.custom_scoring import identify_empty_datasets
        empty_result = identify_empty_datasets(metadata)

        for dropped in empty_result.dropped_indicators:
            result.add_warning(
                dropped["code"],
                "DatasetCodes",
                f"Indicator will be dropped: {dropped['reason']}"
            )
            result.dropped_indicators.append(dropped)

    return result


def validate_required_fields(
    item: dict,
    item_type: str,
    result: ValidationResult
) -> None:
    """Validate that all required fields are present for the given ItemType."""
    item_code = item.get("ItemCode", "<unknown>")
    required = REQUIRED_FIELDS.get(item_type, set())

    for field_name in required:
        if field_name not in item:
            result.add_error(item_code, field_name, f"Missing required field: {field_name}")
        elif item[field_name] is None and field_name not in {"LowerGoalpost", "UpperGoalpost"}:
            # Allow None for goalposts, but not for other required fields
            result.add_error(item_code, field_name, f"Required field {field_name} cannot be None")


def validate_indicator_metadata(
    indicator: dict,
    valid_dataset_codes: set[str] | None,
    validate_score_fn: bool,
    result: ValidationResult
) -> None:
    """
    Validate a single indicator's metadata.

    Args:
        indicator: Indicator metadata dictionary
        valid_dataset_codes: Optional set of valid dataset codes
        validate_score_fn: Whether to validate ScoreFunction
        result: ValidationResult to append errors/warnings to
    """
    item_code = indicator.get("ItemCode", "<unknown>")

    # Validate DatasetCodes
    dataset_codes = indicator.get("DatasetCodes")
    if dataset_codes is not None:
        if not isinstance(dataset_codes, list):
            result.add_error(item_code, "DatasetCodes", "DatasetCodes must be a list")
        elif valid_dataset_codes is not None:
            for dc in dataset_codes:
                if not isinstance(dc, str):
                    result.add_error(item_code, "DatasetCodes", f"Dataset code must be a string, got {type(dc).__name__}")
                elif dc not in valid_dataset_codes:
                    result.add_warning(item_code, "DatasetCodes", f"Unknown dataset code: {dc}")

    # Validate goalposts
    lower_gp = indicator.get("LowerGoalpost")
    upper_gp = indicator.get("UpperGoalpost")

    if lower_gp is not None and not isinstance(lower_gp, (int, float)):
        result.add_error(item_code, "LowerGoalpost", "LowerGoalpost must be a number")

    if upper_gp is not None and not isinstance(upper_gp, (int, float)):
        result.add_error(item_code, "UpperGoalpost", "UpperGoalpost must be a number")

    # Validate ScoreFunction if present
    score_function = indicator.get("ScoreFunction")
    if validate_score_fn and score_function:
        if not isinstance(score_function, str):
            result.add_error(item_code, "ScoreFunction", "ScoreFunction must be a string")
        else:
            try:
                # Collect dataset codes referenced in the score function
                indicator_dataset_codes = set(dataset_codes) if dataset_codes else None
                validate_score_function(score_function, indicator_dataset_codes)
            except ScoreFunctionValidationError as e:
                result.add_error(item_code, "ScoreFunction", f"Invalid ScoreFunction for Indicator {indicator.get("IndicatorCode")} : {e}")


def validate_hierarchy(
    items_by_code: dict[str, dict],
    result: ValidationResult
) -> None:
    """
    Validate the SSPI hierarchy relationships.

    Checks:
    - Children codes reference existing items
    - Children match *Codes fields (PillarCodes, CategoryCodes, etc.)
    - No circular references
    - All non-root items are reachable from SSPI root
    """
    # Find SSPI root
    sspi_items = [item for item in items_by_code.values() if item.get("ItemType") == "SSPI"]
    if not sspi_items:
        return  # Already reported as error

    sspi_root = sspi_items[0]
    reachable_codes = set()

    def validate_children(parent: dict, expected_type: str, codes_field: str):
        """Recursively validate children of a parent item."""
        parent_code = parent.get("ItemCode")
        children = parent.get("Children", [])
        codes_list = parent.get(codes_field, [])

        if not isinstance(children, list):
            result.add_error(parent_code, "Children", "Children must be a list")
            return

        if not isinstance(codes_list, list):
            result.add_error(parent_code, codes_field, f"{codes_field} must be a list")
            return

        # Children should match *Codes field
        children_set = set(children)
        codes_set = set(codes_list)

        if children_set != codes_set:
            missing_in_children = codes_set - children_set
            missing_in_codes = children_set - codes_set

            if missing_in_children:
                result.add_warning(
                    parent_code, "Children",
                    f"Codes in {codes_field} not in Children: {missing_in_children}"
                )
            if missing_in_codes:
                result.add_warning(
                    parent_code, codes_field,
                    f"Children not in {codes_field}: {missing_in_codes}"
                )

        # Validate each child
        for child_code in children:
            if not isinstance(child_code, str):
                result.add_error(parent_code, "Children", f"Child code must be a string")
                continue

            if child_code in reachable_codes:
                result.add_error(parent_code, "Children", f"Circular reference detected: {child_code}")
                continue

            if child_code not in items_by_code:
                result.add_error(
                    parent_code, "Children",
                    f"Child '{child_code}' not found in metadata"
                )
                continue

            child = items_by_code[child_code]
            child_type = child.get("ItemType")

            if child_type != expected_type:
                result.add_error(
                    parent_code, "Children",
                    f"Child '{child_code}' has type '{child_type}', expected '{expected_type}'"
                )
                continue

            reachable_codes.add(child_code)

            # Recursively validate grandchildren
            if child_type == "Pillar":
                validate_children(child, "Category", "CategoryCodes")
            elif child_type == "Category":
                validate_children(child, "Indicator", "IndicatorCodes")

    # Start validation from SSPI root
    reachable_codes.add(sspi_root.get("ItemCode"))
    validate_children(sspi_root, "Pillar", "PillarCodes")

    # Check for orphaned items
    all_codes = set(items_by_code.keys())
    orphaned = all_codes - reachable_codes

    for orphan_code in orphaned:
        orphan = items_by_code[orphan_code]
        result.add_warning(
            orphan_code, None,
            f"Item '{orphan_code}' ({orphan.get('ItemType')}) is not reachable from SSPI root"
        )


# =============================================================================
# Canonicalization and Hashing
# =============================================================================

def canonicalize_metadata(metadata: list[dict]) -> list[dict]:
    """
    Sort metadata into canonical order for deterministic hashing.

    Order: SSPI → Pillars (by TreeIndex) → Categories → Indicators
    Within each item: sort keys alphabetically, normalize values

    Args:
        metadata: List of metadata item dictionaries

    Returns:
        List of canonicalized metadata dictionaries
    """
    # Build lookup and categorize by type
    by_type: dict[str, list[dict]] = {
        "SSPI": [],
        "Pillar": [],
        "Category": [],
        "Indicator": [],
    }

    for item in metadata:
        item_type = item.get("ItemType")
        if item_type in by_type:
            by_type[item_type].append(item)

    # Sort each category
    # SSPI: should be only one
    # Pillars, Categories, Indicators: sort by TreeIndex then ItemCode
    def sort_key(item: dict) -> tuple:
        tree_index = item.get("TreeIndex", [])
        if isinstance(tree_index, list):
            # Pad with -1 for consistent sorting
            padded = tree_index + [-1] * (4 - len(tree_index))
        else:
            padded = [-1, -1, -1, -1]
        item_code = item.get("ItemCode", "")
        return (tuple(padded), item_code)

    for item_type in ["Pillar", "Category", "Indicator"]:
        by_type[item_type].sort(key=sort_key)

    # Combine in canonical order
    canonical = (
        by_type["SSPI"] +
        by_type["Pillar"] +
        by_type["Category"] +
        by_type["Indicator"]
    )

    # Normalize each item (sort keys, normalize values)
    return [canonicalize_item(item) for item in canonical]


def canonicalize_item(item: dict, filter_fields: bool = True) -> dict:
    """
    Normalize a single metadata item for consistent hashing.

    - Sort keys alphabetically
    - Sort list values
    - Convert numbers to consistent format
    - Optionally filter to only CONFIG_HASH_FIELDS

    Args:
        item: Metadata item dictionary
        filter_fields: If True, only include fields in CONFIG_HASH_FIELDS
    """
    canonical = {}

    for key in sorted(item.keys()):
        # Skip fields that don't affect config hash (like Description, Footnote, etc.)
        if filter_fields and key not in CONFIG_HASH_FIELDS:
            continue
        value = item[key]
        canonical[key] = canonicalize_value(value)

    return canonical


def canonicalize_value(value: Any) -> Any:
    """Recursively canonicalize a value."""
    if value is None:
        return None
    elif isinstance(value, bool):
        return value
    elif isinstance(value, (int, float)):
        # Normalize numbers (float for consistency)
        if isinstance(value, int) or value == int(value):
            return int(value)
        return float(value)
    elif isinstance(value, str):
        # Normalize whitespace in strings
        return " ".join(value.split())
    elif isinstance(value, list):
        # Sort lists of strings (like Children, DatasetCodes, etc.)
        # but preserve order for numeric lists (like TreeIndex)
        if all(isinstance(v, str) for v in value):
            return sorted(value)
        else:
            # Preserve order for numeric and mixed lists (like TreeIndex)
            return [canonicalize_value(v) for v in value]
    elif isinstance(value, dict):
        return canonicalize_item(value)
    else:
        # Fallback: convert to string
        return str(value)


def compute_config_hash(metadata: list[dict]) -> str:
    """
    Compute deterministic SHA-256 hash of canonicalized metadata.

    Used for caching - same config structure = same hash.

    Args:
        metadata: List of metadata item dictionaries

    Returns:
        32-character hexadecimal hash string (first 32 chars of SHA-256)
    """
    canonical = canonicalize_metadata(metadata)

    # Convert to JSON with consistent formatting
    json_str = json.dumps(
        canonical,
        sort_keys=True,
        separators=(',', ':'),
        ensure_ascii=True
    )

    # Compute hash
    hash_bytes = hashlib.sha256(json_str.encode('utf-8')).hexdigest()

    # Return first 32 characters
    return hash_bytes[:32]


def compute_indicator_hash(indicator: dict) -> str:
    """
    Hash the scoring-relevant fields of an indicator.

    Used to detect if an indicator's scoring configuration has changed.

    Args:
        indicator: Indicator metadata dictionary

    Returns:
        16-character hexadecimal hash string
    """
    # Extract only scoring-relevant fields
    # Use None for missing fields to ensure consistency between default
    # indicators (which have explicit None values) and custom indicators
    # (which may be missing these fields entirely)
    scoring_data = {}
    for field_name in SCORING_RELEVANT_FIELDS:
        # Use .get() with None default to treat missing fields same as None
        scoring_data[field_name] = indicator.get(field_name, None)

    # Canonicalize and hash
    canonical = canonicalize_item(scoring_data)
    json_str = json.dumps(
        canonical,
        sort_keys=True,
        separators=(',', ':'),
        ensure_ascii=True
    )

    hash_bytes = hashlib.sha256(json_str.encode('utf-8')).hexdigest()
    return hash_bytes[:16]


# =============================================================================
# Utility Functions
# =============================================================================

def extract_indicator_codes(metadata: list[dict]) -> set[str]:
    """Extract all indicator codes from metadata."""
    return {
        item.get("ItemCode")
        for item in metadata
        if item.get("ItemType") == "Indicator" and item.get("ItemCode")
    }


def extract_dataset_codes_from_metadata(metadata: list[dict]) -> set[str]:
    """Extract all dataset codes referenced by indicators in metadata."""
    dataset_codes = set()
    for item in metadata:
        if item.get("ItemType") == "Indicator":
            codes = item.get("DatasetCodes", [])
            if isinstance(codes, list):
                dataset_codes.update(codes)
    return dataset_codes


def get_indicators_with_score_functions(metadata: list[dict]) -> list[dict]:
    """Get all indicators that have ScoreFunction defined."""
    return [
        item for item in metadata
        if item.get("ItemType") == "Indicator" and item.get("ScoreFunction")
    ]
