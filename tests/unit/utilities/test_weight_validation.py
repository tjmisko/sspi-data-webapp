"""
Unit tests for per-parent weight semantic validation (F3).

validate_custom_metadata is pure (no Mongo when valid_dataset_codes/data
checks are off), so these run offline. They cover the all-or-none rule, the
sum-to-1.0 rule (within tolerance), and the [0, 1] range rule at all three
parent levels: SSPI->Pillars, Pillar->Categories, Category->Indicators.
"""
import pytest

from sspi_flask_app.api.resources.metadata_validator import (
    validate_custom_metadata,
    validate_sibling_weights,
    ValidationResult,
    WEIGHT_SUM_TOLERANCE,
)


def _base(weights=None):
    """Fully-valid 2 pillars x 2 categories x 2 indicators tree.

    ``weights`` maps ItemCode -> Weight; only those codes get a Weight key.
    """
    weights = weights or {}

    def w(item):
        if item["ItemCode"] in weights:
            item = dict(item, Weight=weights[item["ItemCode"]])
        return item

    items = [
        {"ItemType": "SSPI", "ItemCode": "SSPI", "ItemName": "SSPI",
         "Children": ["PILLR1", "PILLR2"], "PillarCodes": ["PILLR1", "PILLR2"]},
    ]
    for p in ("PILLR1", "PILLR2"):
        cats = [f"{p}CATG1", f"{p}CATG2"]
        items.append(w({
            "ItemType": "Pillar", "ItemCode": p, "ItemName": p,
            "PillarCode": p, "Children": cats, "CategoryCodes": cats}))
        for c in cats:
            inds = [f"{c}I1", f"{c}I2"]
            items.append(w({
                "ItemType": "Category", "ItemCode": c, "ItemName": c,
                "CategoryCode": c, "PillarCode": p,
                "Children": inds, "IndicatorCodes": inds}))
            for ind in inds:
                items.append(w({
                    "ItemType": "Indicator", "ItemCode": ind, "ItemName": ind,
                    "IndicatorCode": ind, "Children": []}))
    return items


def _validate(weights=None):
    return validate_custom_metadata(_base(weights), validate_score_functions=False)


def _weight_errors(result):
    return [e for e in result.errors if e.field == "Weight"]


# =============================================================================
# Sanity: the weightless base is valid
# =============================================================================

def test_no_weights_is_valid():
    result = _validate()
    assert result.valid, result.to_dict()["errors"]
    assert _weight_errors(result) == []


# =============================================================================
# Indicator level (Category -> Indicators)
# =============================================================================

def test_indicator_weights_sum_one_valid():
    result = _validate({"PILLR1CATG1I1": 0.75, "PILLR1CATG1I2": 0.25})
    assert _weight_errors(result) == []
    assert result.valid


def test_indicator_weights_sum_not_one_error():
    result = _validate({"PILLR1CATG1I1": 0.5, "PILLR1CATG1I2": 0.4})
    assert any(e.field == "Weight" for e in result.errors)
    assert not result.valid


def test_indicator_weights_mixed_error():
    # Only one of the two indicators in the category is weighted.
    result = _validate({"PILLR1CATG1I1": 1.0})
    assert any(e.field == "Weight" for e in result.errors)
    assert not result.valid


def test_indicator_weight_out_of_range_error():
    result = _validate({"PILLR1CATG1I1": 1.5, "PILLR1CATG1I2": -0.5})
    assert any(e.field == "Weight" for e in result.errors)
    assert not result.valid


# =============================================================================
# Category level (Pillar -> Categories)
# =============================================================================

def test_category_weights_sum_one_valid():
    result = _validate({"PILLR1CATG1": 0.3, "PILLR1CATG2": 0.7})
    assert _weight_errors(result) == []
    assert result.valid


def test_category_weights_sum_not_one_error():
    result = _validate({"PILLR1CATG1": 0.3, "PILLR1CATG2": 0.5})
    assert any(e.field == "Weight" for e in result.errors)
    assert not result.valid


def test_category_weights_mixed_error():
    result = _validate({"PILLR1CATG1": 1.0})
    assert any(e.field == "Weight" for e in result.errors)


# =============================================================================
# Pillar level (SSPI -> Pillars)
# =============================================================================

def test_pillar_weights_sum_one_valid():
    result = _validate({"PILLR1": 0.5, "PILLR2": 0.5})
    assert _weight_errors(result) == []
    assert result.valid


def test_pillar_weights_sum_not_one_error():
    result = _validate({"PILLR1": 0.8, "PILLR2": 0.8})
    assert any(e.field == "Weight" for e in result.errors)
    assert not result.valid


def test_pillar_weights_mixed_error():
    result = _validate({"PILLR1": 1.0})
    assert any(e.field == "Weight" for e in result.errors)


# =============================================================================
# Tolerance + direct helper
# =============================================================================

def test_sum_within_tolerance_is_accepted():
    # 0.3333 + 0.3333 + 0.3334 = 1.0 exactly here, but verify display-rounding
    # drift just under the tolerance passes.
    half = 0.5 + WEIGHT_SUM_TOLERANCE / 4
    result = _validate({"PILLR1CATG1I1": half, "PILLR1CATG1I2": half})
    assert _weight_errors(result) == []


def test_validate_sibling_weights_helper_directly():
    items = {
        "A": {"ItemCode": "A", "Weight": 0.6},
        "B": {"ItemCode": "B", "Weight": 0.4},
    }
    result = ValidationResult(valid=True)
    validate_sibling_weights("PARENT", ["A", "B"], items, result)
    assert result.valid
    assert result.errors == []

    bad = {"ItemCode": "A", "Weight": 0.6}
    items2 = {"A": bad, "B": {"ItemCode": "B"}}  # mixed
    result2 = ValidationResult(valid=True)
    validate_sibling_weights("PARENT", ["A", "B"], items2, result2)
    assert not result2.valid
