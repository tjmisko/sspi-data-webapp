"""
Unit tests for the optional per-child Weight typecheck in
SSPICustomUserStructure.validate_metadata (F1).

validate_metadata is a pure method (no Mongo I/O), so these run without a live
database. Semantic per-parent rules (all-or-none, sibling sum == 1) are F3 and
live in metadata_validator.validate_hierarchy, not here.
"""
import pytest

from sspi_flask_app.models.database import sspi_custom_user_structure
from sspi_flask_app.models.errors import InvalidDocumentFormatError


def _doc(items):
    return {"metadata": items}


def test_absent_weight_is_valid():
    sspi_custom_user_structure.validate_metadata(
        _doc([{"ItemType": "Indicator", "ItemCode": "INDIC1"}])
    )


def test_none_weight_is_valid():
    sspi_custom_user_structure.validate_metadata(
        _doc([{"ItemType": "Indicator", "ItemCode": "INDIC1", "Weight": None}])
    )


@pytest.mark.parametrize("weight", [0, 0.0, 0.25, 0.5, 1, 1.0])
def test_in_range_weight_is_valid(weight):
    sspi_custom_user_structure.validate_metadata(
        _doc([{"ItemType": "Pillar", "Weight": weight}])
    )


@pytest.mark.parametrize("weight", ["0.5", [0.5], {"a": 1}, True, False])
def test_non_numeric_weight_is_rejected(weight):
    with pytest.raises(InvalidDocumentFormatError):
        sspi_custom_user_structure.validate_metadata(
            _doc([{"ItemType": "Indicator", "Weight": weight}])
        )


@pytest.mark.parametrize("weight", [-0.1, 1.5, 2, -1])
def test_out_of_range_weight_is_rejected(weight):
    with pytest.raises(InvalidDocumentFormatError):
        sspi_custom_user_structure.validate_metadata(
            _doc([{"ItemType": "Category", "Weight": weight}])
        )
