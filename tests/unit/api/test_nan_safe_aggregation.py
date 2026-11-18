"""
NaN-safe aggregation in FastCustomSSPI: complete data is the plain weighted
mean (the official aggregation), a missing child's weight is re-normalized over
the siblings that have data, and a parent with no child data stays NaN.
"""
import numpy as np
import pytest

from sspi_flask_app.api.resources.fast_custom_scoring import FastCustomSSPI


def _metadata(weights=None):
    weights = weights or {}

    def ind(code, cat):
        item = {"ItemType": "Indicator", "ItemCode": code, "ItemName": code,
                "CategoryCode": cat}
        if code in weights:
            item["Weight"] = weights[code]
        return item

    return [
        {"ItemType": "SSPI", "ItemCode": "SSPI", "ItemName": "SSPI",
         "PillarCodes": ["PIL1"], "Children": ["PIL1"]},
        {"ItemType": "Pillar", "ItemCode": "PIL1", "ItemName": "P",
         "CategoryCodes": ["CAT1", "CAT2"], "Children": ["CAT1", "CAT2"]},
        {"ItemType": "Category", "ItemCode": "CAT1", "ItemName": "C1",
         "IndicatorCodes": ["AAAAAA", "BBBBBB", "CCCCCC"],
         "Children": ["AAAAAA", "BBBBBB", "CCCCCC"]},
        {"ItemType": "Category", "ItemCode": "CAT2", "ItemName": "C2",
         "IndicatorCodes": ["DDDDDD"], "Children": ["DDDDDD"]},
        ind("AAAAAA", "CAT1"), ind("BBBBBB", "CAT1"), ind("CCCCCC", "CAT1"),
        ind("DDDDDD", "CAT2"),
    ]


def _aggregate(scores, weights=None):
    """scores: (4 indicators, 1 country, 1 year) -> dict code -> value."""
    sspi = FastCustomSSPI(_metadata(weights))
    out = sspi.aggregate(np.array(scores, dtype=float).reshape(4, 1, 1))
    return {code: out[i, 0, 0] for i, code in enumerate(sspi.item_codes)}


def test_should_equal_plain_weighted_mean_when_data_is_complete():
    result = _aggregate([0.2, 0.4, 0.9, 0.5])
    assert result["CAT1"] == pytest.approx((0.2 + 0.4 + 0.9) / 3)
    assert result["CAT2"] == pytest.approx(0.5)
    assert result["PIL1"] == pytest.approx(((0.2 + 0.4 + 0.9) / 3 + 0.5) / 2)
    assert result["SSPI"] == pytest.approx(result["PIL1"])


def test_should_use_configured_weights_when_data_is_complete():
    result = _aggregate([0.2, 0.4, 0.9, 0.5],
                        weights={"AAAAAA": 0.5, "BBBBBB": 0.25, "CCCCCC": 0.25,
                                 "DDDDDD": 1.0})
    assert result["CAT1"] == pytest.approx(0.5 * 0.2 + 0.25 * 0.4 + 0.25 * 0.9)


def test_should_renormalize_over_present_children_when_one_child_is_missing():
    result = _aggregate([0.2, np.nan, 0.8, 0.5])
    assert result["CAT1"] == pytest.approx((0.2 + 0.8) / 2)
    assert result["PIL1"] == pytest.approx(((0.2 + 0.8) / 2 + 0.5) / 2)


def test_should_renormalize_weights_when_a_weighted_child_is_missing():
    result = _aggregate([0.2, np.nan, 0.8, 0.5],
                        weights={"AAAAAA": 0.5, "BBBBBB": 0.25, "CCCCCC": 0.25,
                                 "DDDDDD": 1.0})
    assert result["CAT1"] == pytest.approx((0.5 * 0.2 + 0.25 * 0.8) / 0.75)


def test_should_renormalize_pillar_over_present_categories_when_a_category_is_empty():
    result = _aggregate([np.nan, np.nan, np.nan, 0.6])
    assert np.isnan(result["CAT1"])
    assert result["CAT2"] == pytest.approx(0.6)
    assert result["PIL1"] == pytest.approx(0.6)
    assert result["SSPI"] == pytest.approx(0.6)


def test_should_stay_nan_when_every_child_is_missing():
    result = _aggregate([np.nan] * 4)
    assert all(np.isnan(v) for v in result.values())


def test_should_not_leak_nan_across_country_years_when_one_cell_is_missing():
    sspi = FastCustomSSPI(_metadata())
    scores = np.full((4, 2, 2), 0.5)
    scores[1, 0, 1] = np.nan
    out = sspi.aggregate(scores)
    cat1 = out[sspi.item_codes.index("CAT1")]
    assert np.allclose(cat1, 0.5)
    assert not np.isnan(out).any()
