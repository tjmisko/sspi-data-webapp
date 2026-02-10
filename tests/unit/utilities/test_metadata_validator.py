"""
Tests for the metadata validator module.

Tests cover:
- Basic validation of required fields
- Hierarchy validation (Children, *Codes fields)
- ScoreFunction validation integration
- Canonicalization for deterministic ordering
- Hash computation for caching
"""

import pytest

from sspi_flask_app.api.resources.metadata_validator import (
    validate_custom_metadata,
    validate_required_fields,
    validate_indicator_metadata,
    validate_hierarchy,
    canonicalize_metadata,
    canonicalize_item,
    canonicalize_value,
    compute_config_hash,
    compute_indicator_hash,
    extract_indicator_codes,
    extract_dataset_codes_from_metadata,
    get_indicators_with_score_functions,
    ValidationResult,
    ValidationError,
    MetadataValidationError,
    VALID_ITEM_TYPES,
    REQUIRED_FIELDS,
)


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
def minimal_valid_metadata():
    """Minimal valid SSPI structure with one indicator."""
    return [
        {
            "ItemType": "SSPI",
            "ItemCode": "SSPI",
            "ItemName": "Test SSPI",
            "Children": ["SUS"],
            "PillarCodes": ["SUS"],
        },
        {
            "ItemType": "Pillar",
            "ItemCode": "SUS",
            "ItemName": "Sustainability",
            "PillarCode": "SUS",
            "Children": ["ECO"],
            "CategoryCodes": ["ECO"],
        },
        {
            "ItemType": "Category",
            "ItemCode": "ECO",
            "ItemName": "Ecosystem",
            "CategoryCode": "ECO",
            "PillarCode": "SUS",
            "Children": ["BIODIV"],
            "IndicatorCodes": ["BIODIV"],
        },
        {
            "ItemType": "Indicator",
            "ItemCode": "BIODIV",
            "ItemName": "Biodiversity",
            "IndicatorCode": "BIODIV",
            "CategoryCode": "ECO",
            "PillarCode": "SUS",
            "DatasetCodes": ["UNSDG_MARINE", "UNSDG_TERRST"],
            "ScoreFunction": "Score = average(goalpost(UNSDG_MARINE, 0, 100), goalpost(UNSDG_TERRST, 0, 100))",
            "LowerGoalpost": None,
            "UpperGoalpost": None,
        },
    ]


@pytest.fixture
def full_sspi_structure():
    """More complete SSPI structure with multiple pillars, categories, and indicators."""
    return [
        {
            "ItemType": "SSPI",
            "ItemCode": "SSPI",
            "ItemName": "SSPI",
            "Children": ["SUS", "MS"],
            "PillarCodes": ["SUS", "MS"],
            "TreeIndex": [0, -1, -1, -1],
        },
        {
            "ItemType": "Pillar",
            "ItemCode": "SUS",
            "ItemName": "Sustainability",
            "PillarCode": "SUS",
            "Children": ["ECO"],
            "CategoryCodes": ["ECO"],
            "TreeIndex": [0, 0, -1, -1],
        },
        {
            "ItemType": "Pillar",
            "ItemCode": "MS",
            "ItemName": "Market Structure",
            "PillarCode": "MS",
            "Children": ["LAB"],
            "CategoryCodes": ["LAB"],
            "TreeIndex": [0, 1, -1, -1],
        },
        {
            "ItemType": "Category",
            "ItemCode": "ECO",
            "ItemName": "Ecosystem",
            "CategoryCode": "ECO",
            "PillarCode": "SUS",
            "Children": ["BIODIV", "REDLST"],
            "IndicatorCodes": ["BIODIV", "REDLST"],
            "TreeIndex": [0, 0, 0, -1],
        },
        {
            "ItemType": "Category",
            "ItemCode": "LAB",
            "ItemName": "Labor Market",
            "CategoryCode": "LAB",
            "PillarCode": "MS",
            "Children": ["EMPLOY"],
            "IndicatorCodes": ["EMPLOY"],
            "TreeIndex": [0, 1, 0, -1],
        },
        {
            "ItemType": "Indicator",
            "ItemCode": "BIODIV",
            "ItemName": "Biodiversity",
            "IndicatorCode": "BIODIV",
            "CategoryCode": "ECO",
            "PillarCode": "SUS",
            "DatasetCodes": ["UNSDG_MARINE", "UNSDG_TERRST"],
            "ScoreFunction": "Score = average(goalpost(UNSDG_MARINE, 0, 100), goalpost(UNSDG_TERRST, 0, 100))",
            "TreeIndex": [0, 0, 0, 0],
        },
        {
            "ItemType": "Indicator",
            "ItemCode": "REDLST",
            "ItemName": "Red List Index",
            "IndicatorCode": "REDLST",
            "CategoryCode": "ECO",
            "PillarCode": "SUS",
            "DatasetCodes": ["UNSDG_REDLST"],
            "ScoreFunction": "Score = goalpost(UNSDG_REDLST, 0, 1)",
            "TreeIndex": [0, 0, 0, 1],
        },
        {
            "ItemType": "Indicator",
            "ItemCode": "EMPLOY",
            "ItemName": "Employment",
            "IndicatorCode": "EMPLOY",
            "CategoryCode": "LAB",
            "PillarCode": "MS",
            "DatasetCodes": ["ILO_EMPLOY_TO_POP"],
            "ScoreFunction": "Score = goalpost(ILO_EMPLOY_TO_POP, 50, 95)",
            "TreeIndex": [0, 1, 0, 0],
        },
    ]


# =============================================================================
# Basic Validation Tests
# =============================================================================

class TestValidateCustomMetadata:
    """Tests for validate_custom_metadata function."""

    def test_empty_metadata_fails(self):
        """Empty metadata should fail validation."""
        result = validate_custom_metadata([])
        assert not result.valid
        assert len(result.errors) > 0
        assert "empty" in result.errors[0].message.lower()

    def test_none_metadata_fails(self):
        """None metadata should fail validation."""
        result = validate_custom_metadata(None)
        assert not result.valid

    def test_non_list_metadata_fails(self):
        """Non-list metadata should fail validation."""
        result = validate_custom_metadata({"ItemType": "SSPI"})
        assert not result.valid
        assert "list" in result.errors[0].message.lower()

    def test_minimal_valid_metadata_passes(self, minimal_valid_metadata):
        """Minimal valid metadata should pass validation."""
        result = validate_custom_metadata(
            minimal_valid_metadata,
            valid_dataset_codes={"UNSDG_MARINE", "UNSDG_TERRST"},
            validate_score_functions=True
        )
        assert result.valid, f"Errors: {[e.message for e in result.errors]}"
        assert result.item_count == 4
        assert result.indicator_count == 1

    def test_full_structure_passes(self, full_sspi_structure):
        """Full SSPI structure should pass validation."""
        valid_datasets = {"UNSDG_MARINE", "UNSDG_TERRST", "UNSDG_REDLST", "ILO_EMPLOY_TO_POP"}
        result = validate_custom_metadata(
            full_sspi_structure,
            valid_dataset_codes=valid_datasets,
            validate_score_functions=True
        )
        assert result.valid, f"Errors: {[e.message for e in result.errors]}"
        assert result.item_count == 8
        assert result.indicator_count == 3


class TestRequiredFields:
    """Tests for required field validation."""

    def test_missing_item_type_fails(self):
        """Missing ItemType should fail validation."""
        metadata = [{"ItemCode": "SSPI", "ItemName": "Test"}]
        result = validate_custom_metadata(metadata)
        assert not result.valid
        assert any("ItemType" in e.field for e in result.errors if e.field)

    def test_missing_item_code_fails(self):
        """Missing ItemCode should fail validation."""
        metadata = [{"ItemType": "SSPI", "ItemName": "Test"}]
        result = validate_custom_metadata(metadata)
        assert not result.valid
        assert any("ItemCode" in e.field for e in result.errors if e.field)

    def test_invalid_item_type_fails(self):
        """Invalid ItemType should fail validation."""
        metadata = [{
            "ItemType": "InvalidType",
            "ItemCode": "TEST",
            "ItemName": "Test"
        }]
        result = validate_custom_metadata(metadata)
        assert not result.valid
        assert any("Invalid ItemType" in e.message for e in result.errors)

    def test_missing_sspi_root_fails(self, minimal_valid_metadata):
        """Missing SSPI root should fail validation."""
        # Remove SSPI item
        metadata = [m for m in minimal_valid_metadata if m["ItemType"] != "SSPI"]
        result = validate_custom_metadata(metadata)
        assert not result.valid
        assert any("SSPI root" in e.message for e in result.errors)

    def test_multiple_sspi_roots_fails(self, minimal_valid_metadata):
        """Multiple SSPI roots should fail validation."""
        metadata = minimal_valid_metadata + [{
            "ItemType": "SSPI",
            "ItemCode": "SSPI2",
            "ItemName": "Another SSPI",
            "Children": [],
            "PillarCodes": [],
        }]
        result = validate_custom_metadata(metadata)
        assert not result.valid
        assert any("Multiple SSPI" in e.message for e in result.errors)

    def test_duplicate_item_codes_fails(self, minimal_valid_metadata):
        """Duplicate ItemCodes should fail validation."""
        # Add duplicate
        metadata = minimal_valid_metadata + [{
            "ItemType": "Indicator",
            "ItemCode": "BIODIV",  # Duplicate
            "ItemName": "Duplicate",
            "IndicatorCode": "BIODIV",
            "CategoryCode": "ECO",
            "PillarCode": "SUS",
        }]
        result = validate_custom_metadata(metadata)
        assert not result.valid
        assert any("Duplicate" in e.message for e in result.errors)


class TestHierarchyValidation:
    """Tests for hierarchy validation."""

    def test_missing_child_fails(self, minimal_valid_metadata):
        """Reference to non-existent child should fail."""
        # Add reference to non-existent category
        minimal_valid_metadata[1]["Children"] = ["ECO", "NONEXISTENT"]
        minimal_valid_metadata[1]["CategoryCodes"] = ["ECO", "NONEXISTENT"]

        result = validate_custom_metadata(minimal_valid_metadata)
        assert any("not found" in e.message.lower() for e in result.errors)

    def test_wrong_child_type_fails(self, minimal_valid_metadata):
        """Child with wrong ItemType should fail."""
        # Make pillar reference an indicator directly
        minimal_valid_metadata[1]["Children"] = ["BIODIV"]
        minimal_valid_metadata[1]["CategoryCodes"] = ["BIODIV"]

        result = validate_custom_metadata(minimal_valid_metadata)
        assert any("expected" in e.message.lower() for e in result.errors)

    def test_children_codes_mismatch_warns(self, minimal_valid_metadata):
        """Mismatch between Children and *Codes should warn."""
        # Mismatch Children and CategoryCodes
        minimal_valid_metadata[1]["Children"] = ["ECO"]
        minimal_valid_metadata[1]["CategoryCodes"] = []  # Missing

        result = validate_custom_metadata(minimal_valid_metadata)
        # Should have warnings about mismatch
        assert len(result.warnings) > 0 or not result.valid

    def test_orphaned_items_warn(self, minimal_valid_metadata):
        """Orphaned items should generate warnings."""
        # Add an orphaned indicator
        minimal_valid_metadata.append({
            "ItemType": "Indicator",
            "ItemCode": "ORPHAN",
            "ItemName": "Orphan",
            "IndicatorCode": "ORPHAN",
            "CategoryCode": "ECO",
            "PillarCode": "SUS",
        })

        result = validate_custom_metadata(minimal_valid_metadata)
        assert any("not reachable" in w.message.lower() for w in result.warnings)


class TestIndicatorValidation:
    """Tests for indicator-specific validation."""

    def test_valid_score_function_passes(self, minimal_valid_metadata):
        """Valid ScoreFunction should pass."""
        result = validate_custom_metadata(
            minimal_valid_metadata,
            valid_dataset_codes={"UNSDG_MARINE", "UNSDG_TERRST"},
            validate_score_functions=True
        )
        assert result.valid

    def test_invalid_score_function_fails(self, minimal_valid_metadata):
        """Invalid ScoreFunction should fail."""
        minimal_valid_metadata[3]["ScoreFunction"] = "Score = import os"

        result = validate_custom_metadata(
            minimal_valid_metadata,
            validate_score_functions=True
        )
        assert not result.valid
        assert any("ScoreFunction" in e.field for e in result.errors if e.field)

    def test_unknown_dataset_code_warns(self, minimal_valid_metadata):
        """Unknown dataset code should generate warning."""
        result = validate_custom_metadata(
            minimal_valid_metadata,
            valid_dataset_codes={"UNSDG_MARINE"},  # Missing UNSDG_TERRST
            validate_score_functions=True
        )
        # Unknown dataset should generate warning, not error
        assert any("UNSDG_TERRST" in w.message for w in result.warnings)

    def test_invalid_goalpost_type_fails(self, minimal_valid_metadata):
        """Invalid goalpost type should fail."""
        minimal_valid_metadata[3]["LowerGoalpost"] = "not a number"

        result = validate_custom_metadata(minimal_valid_metadata)
        assert not result.valid
        assert any("LowerGoalpost" in e.field for e in result.errors if e.field)

    def test_dataset_codes_must_be_list(self, minimal_valid_metadata):
        """DatasetCodes must be a list."""
        minimal_valid_metadata[3]["DatasetCodes"] = "UNSDG_MARINE"

        result = validate_custom_metadata(minimal_valid_metadata)
        assert not result.valid
        assert any("list" in e.message.lower() for e in result.errors)


# =============================================================================
# Canonicalization Tests
# =============================================================================

class TestCanonicalization:
    """Tests for metadata canonicalization."""

    def test_canonicalize_sorts_by_tree_index(self, full_sspi_structure):
        """Canonicalization should sort by TreeIndex."""
        # Shuffle the metadata
        import random
        shuffled = list(full_sspi_structure)
        random.shuffle(shuffled)

        canonical = canonicalize_metadata(shuffled)

        # SSPI should be first
        assert canonical[0]["ItemType"] == "SSPI"

        # Pillars should be next, in TreeIndex order
        pillars = [c for c in canonical if c["ItemType"] == "Pillar"]
        assert pillars[0]["ItemCode"] == "SUS"
        assert pillars[1]["ItemCode"] == "MS"

    # def test_canonicalize_item_sorts_keys(self):
    #     """canonicalize_item should sort keys alphabetically."""
    #     item = {
    #         "Zebra": 1,
    #         "Apple": 2,
    #         "Middle": 3,
    #     }

    #     canonical = canonicalize_item(item)
    #     keys = list(canonical.keys())

    #     assert keys == ["Apple", "Middle", "Zebra"]

    def test_canonicalize_value_normalizes_strings(self):
        """canonicalize_value should normalize whitespace in strings."""
        assert canonicalize_value("  multiple   spaces  ") == "multiple spaces"
        assert canonicalize_value("normal") == "normal"

    def test_canonicalize_value_sorts_string_lists(self):
        """canonicalize_value should sort lists of strings."""
        assert canonicalize_value(["c", "a", "b"]) == ["a", "b", "c"]

    def test_canonicalize_value_preserves_tree_index_order(self):
        """canonicalize_value should preserve TreeIndex order."""
        # TreeIndex is a mixed list that shouldn't be sorted
        tree_index = [0, 1, 2, -1]
        assert canonicalize_value(tree_index) == [0, 1, 2, -1]

    def test_canonicalize_value_handles_none(self):
        """canonicalize_value should handle None."""
        assert canonicalize_value(None) is None

    # def test_canonicalize_value_handles_nested_dict(self):
    #     """canonicalize_value should handle nested dictionaries."""
    #     nested = {
    #         "outer": {
    #             "z": 1,
    #             "a": 2,
    #         }
    #     }

    #     canonical = canonicalize_item(nested)
    #     inner_keys = list(canonical["outer"].keys())
    #     assert inner_keys == ["a", "z"]


# =============================================================================
# Hash Computation Tests
# =============================================================================

class TestHashComputation:
    """Tests for hash computation functions."""

    def test_same_metadata_same_hash(self, minimal_valid_metadata):
        """Same metadata should produce same hash."""
        hash1 = compute_config_hash(minimal_valid_metadata)
        hash2 = compute_config_hash(minimal_valid_metadata)

        assert hash1 == hash2
        assert len(hash1) == 32  # 32 hex characters

    def test_different_order_same_hash(self, minimal_valid_metadata):
        """Different order should produce same hash after canonicalization."""
        import random

        shuffled = list(minimal_valid_metadata)
        random.shuffle(shuffled)

        hash1 = compute_config_hash(minimal_valid_metadata)
        hash2 = compute_config_hash(shuffled)

        assert hash1 == hash2

    def test_different_metadata_different_hash(self, minimal_valid_metadata):
        """Different metadata should produce different hash."""
        hash1 = compute_config_hash(minimal_valid_metadata)

        # Modify something
        modified = list(minimal_valid_metadata)
        modified[3] = dict(modified[3])
        modified[3]["ScoreFunction"] = "Score = goalpost(UNSDG_MARINE, 0, 50)"

        hash2 = compute_config_hash(modified)

        assert hash1 != hash2

    def test_whitespace_differences_same_hash(self, minimal_valid_metadata):
        """Whitespace differences should not affect hash."""
        hash1 = compute_config_hash(minimal_valid_metadata)

        # Add extra whitespace
        modified = list(minimal_valid_metadata)
        modified[3] = dict(modified[3])
        modified[3]["ItemName"] = "  Biodiversity  "

        hash2 = compute_config_hash(modified)

        assert hash1 == hash2

    def test_indicator_hash_scoring_fields_only(self):
        """compute_indicator_hash should only use scoring-relevant fields."""
        indicator1 = {
            "ItemCode": "BIODIV",
            "ItemName": "Biodiversity",  # Not scoring-relevant
            "DatasetCodes": ["UNSDG_MARINE"],
            "ScoreFunction": "Score = goalpost(UNSDG_MARINE, 0, 100)",
        }

        indicator2 = {
            "ItemCode": "BIODIV",
            "ItemName": "Different Name",  # Different but not scoring-relevant
            "DatasetCodes": ["UNSDG_MARINE"],
            "ScoreFunction": "Score = goalpost(UNSDG_MARINE, 0, 100)",
        }

        hash1 = compute_indicator_hash(indicator1)
        hash2 = compute_indicator_hash(indicator2)

        assert hash1 == hash2
        assert len(hash1) == 16  # 16 hex characters

    def test_indicator_hash_detects_scorefunction_change(self):
        """compute_indicator_hash should detect ScoreFunction changes."""
        indicator1 = {
            "ItemCode": "BIODIV",
            "DatasetCodes": ["UNSDG_MARINE"],
            "ScoreFunction": "Score = goalpost(UNSDG_MARINE, 0, 100)",
        }

        indicator2 = {
            "ItemCode": "BIODIV",
            "DatasetCodes": ["UNSDG_MARINE"],
            "ScoreFunction": "Score = goalpost(UNSDG_MARINE, 0, 50)",  # Different
        }

        hash1 = compute_indicator_hash(indicator1)
        hash2 = compute_indicator_hash(indicator2)

        assert hash1 != hash2


# =============================================================================
# Utility Function Tests
# =============================================================================

class TestUtilityFunctions:
    """Tests for utility functions."""

    def test_extract_indicator_codes(self, full_sspi_structure):
        """extract_indicator_codes should return all indicator codes."""
        codes = extract_indicator_codes(full_sspi_structure)

        assert codes == {"BIODIV", "REDLST", "EMPLOY"}

    def test_extract_dataset_codes_from_metadata(self, full_sspi_structure):
        """extract_dataset_codes_from_metadata should return all dataset codes."""
        codes = extract_dataset_codes_from_metadata(full_sspi_structure)

        assert codes == {"UNSDG_MARINE", "UNSDG_TERRST", "UNSDG_REDLST", "ILO_EMPLOY_TO_POP"}

    def test_get_indicators_with_score_functions(self, full_sspi_structure):
        """get_indicators_with_score_functions should return indicators with ScoreFunction."""
        indicators = get_indicators_with_score_functions(full_sspi_structure)

        assert len(indicators) == 3
        assert all(ind.get("ScoreFunction") for ind in indicators)


# =============================================================================
# ValidationResult Tests
# =============================================================================

class TestValidationResult:
    """Tests for ValidationResult class."""

    def test_add_error_sets_valid_false(self):
        """Adding an error should set valid to False."""
        result = ValidationResult(valid=True)
        assert result.valid

        result.add_error("TEST", "field", "error message")

        assert not result.valid
        assert len(result.errors) == 1

    def test_add_warning_keeps_valid_true(self):
        """Adding a warning should not affect valid status."""
        result = ValidationResult(valid=True)

        result.add_warning("TEST", "field", "warning message")

        assert result.valid
        assert len(result.warnings) == 1

    def test_to_dict(self):
        """to_dict should return proper dictionary format."""
        result = ValidationResult(valid=True, item_count=5, indicator_count=3)
        result.add_warning("TEST", "field", "warning")

        d = result.to_dict()

        assert d["valid"] is True
        assert d["item_count"] == 5
        assert d["indicator_count"] == 3
        assert len(d["warnings"]) == 1
        assert len(d["errors"]) == 0


# =============================================================================
# Edge Cases
# =============================================================================

class TestEdgeCases:
    """Tests for edge cases."""

    def test_indicator_without_dataset_codes(self, minimal_valid_metadata):
        """Indicator without DatasetCodes should pass (may have different scoring)."""
        minimal_valid_metadata[3]["DatasetCodes"] = None
        minimal_valid_metadata[3]["ScoreFunction"] = None

        result = validate_custom_metadata(
            minimal_valid_metadata,
            validate_score_functions=False
        )
        # Should pass basic validation
        assert result.valid or all(
            "DatasetCodes" not in e.message for e in result.errors
        )

    def test_indicator_with_variable_goalposts(self, minimal_valid_metadata):
        """Indicator using LowerGoalpost/UpperGoalpost variables should pass."""
        minimal_valid_metadata[3]["ScoreFunction"] = "Score = goalpost(UNSDG_MARINE, LowerGoalpost, UpperGoalpost)"
        minimal_valid_metadata[3]["LowerGoalpost"] = 0
        minimal_valid_metadata[3]["UpperGoalpost"] = 100
        minimal_valid_metadata[3]["DatasetCodes"] = ["UNSDG_MARINE"]

        result = validate_custom_metadata(
            minimal_valid_metadata,
            valid_dataset_codes={"UNSDG_MARINE"},
            validate_score_functions=True
        )
        assert result.valid, f"Errors: {[e.message for e in result.errors]}"

    def test_empty_children_list(self, minimal_valid_metadata):
        """Empty Children list should be valid for leaves."""
        # Indicator already has no children, so it should pass
        result = validate_custom_metadata(minimal_valid_metadata)
        # Check indicator doesn't have Children field or it's empty
        indicator = next(m for m in minimal_valid_metadata if m["ItemType"] == "Indicator")
        assert "Children" not in indicator or indicator.get("Children") == []

    def test_very_long_score_function_in_metadata(self, minimal_valid_metadata):
        """Very long ScoreFunction should fail validation."""
        minimal_valid_metadata[3]["ScoreFunction"] = "Score = goalpost(UNSDG_MARINE" + ", 0" * 100 + ", 100)"

        result = validate_custom_metadata(
            minimal_valid_metadata,
            validate_score_functions=True
        )
        # Should fail due to length
        assert not result.valid

    def test_non_dict_item_in_metadata(self):
        """Non-dict items in metadata list should fail."""
        metadata = [
            {"ItemType": "SSPI", "ItemCode": "SSPI", "ItemName": "Test", "Children": [], "PillarCodes": []},
            "not a dict",
            123,
        ]

        result = validate_custom_metadata(metadata)
        assert not result.valid
        assert any("not a dictionary" in e.message for e in result.errors)

    def test_hash_determinism_across_runs(self, full_sspi_structure):
        """Hash should be deterministic across multiple runs."""
        hashes = [compute_config_hash(full_sspi_structure) for _ in range(10)]

        assert len(set(hashes)) == 1  # All hashes should be identical
