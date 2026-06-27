"""
Regression tests for the all-NaN indicator drop in score_custom_configuration_fast.

An indicator whose score function needs a dataset that is entirely absent scores
NaN across the whole panel. identify_empty_datasets() only drops an indicator
when ALL of its datasets are empty, so such an indicator can survive that check
and still score all-NaN. Left in the aggregation, one all-NaN indicator poisons
the matrix multiply and nulls EVERY category/pillar/SSPI score, so nothing above
the indicator level gets stored. The engine must drop these post-scoring and
renormalize over the indicators that actually scored.

These tests mock the Mongo-touching seams so no live database is needed.
"""
import numpy as np
import pytest
from unittest.mock import patch

from sspi_flask_app.api.resources import fast_custom_scoring as fcs
from sspi_flask_app.api.resources.custom_scoring import (
    rebuild_metadata_without_indicators,
)


def _chain_metadata():
    """SSPI -> one pillar -> one category -> two indicators (GOOD + DEAD)."""
    return [
        {"ItemType": "SSPI", "ItemCode": "SSPI", "ItemName": "SSPI",
         "PillarCodes": ["PIL"], "Children": ["PIL"]},
        {"ItemType": "Pillar", "ItemCode": "PIL", "ItemName": "Pillar",
         "CategoryCodes": ["CAT"], "Children": ["CAT"]},
        {"ItemType": "Category", "ItemCode": "CAT", "ItemName": "Category",
         "IndicatorCodes": ["GOOD", "DEAD"], "Children": ["GOOD", "DEAD"]},
        {"ItemType": "Indicator", "ItemCode": "GOOD", "ItemName": "Good",
         "DatasetCodes": ["DS_GOOD"], "ScoreFunction": "Score = DS_GOOD"},
        {"ItemType": "Indicator", "ItemCode": "DEAD", "ItemName": "Dead",
         "DatasetCodes": ["DS_DEAD"], "ScoreFunction": "Score = DS_DEAD"},
    ]


def _run_with_dead_indicator(good_scores, dead_scores):
    """Run score_custom_configuration_fast with score_indicators_vectorized and
    the Mongo seams mocked. good_scores/dead_scores are (n_countries, n_years)."""
    countries = ["AAA", "BBB"]
    good = np.asarray(good_scores, dtype=float)
    dead = np.asarray(dead_scores, dtype=float)
    indicator_scores = np.stack([good, dead])  # (2 indicators, 2 countries, 2 years)

    with patch.object(fcs, "fetch_all_datasets_aggregated",
                      return_value={"DS_GOOD": np.zeros((2, 2)), "DS_DEAD": np.zeros((2, 2))}), \
         patch.object(fcs, "impute_dataset_vectorized",
                      side_effect=lambda arr, mask, neutral_fill=0.5: (arr, np.zeros_like(arr, dtype=bool))), \
         patch.object(fcs, "score_indicators_vectorized", return_value=indicator_scores), \
         patch.object(fcs.sspi_metadata, "country_group", return_value=countries):
        return fcs.score_custom_configuration_fast(
            _chain_metadata(),
            country_codes=countries,
            start_year=2000,
            end_year=2001,
        )


def test_drops_all_nan_indicator_and_still_aggregates():
    """A single all-NaN indicator is dropped so SSPI/pillar/category aggregate."""
    good = [[0.5, 0.6], [0.7, 0.8]]            # GOOD scores for AAA, BBB over 2000-2001
    dead = [[np.nan, np.nan], [np.nan, np.nan]]  # DEAD scores NaN everywhere

    result = _run_with_dead_indicator(good, dead)

    # The dead indicator contributes no documents...
    assert not result.get("DEAD"), "all-NaN indicator should produce no score docs"
    # ...but every aggregate level still has data (the bug nulled all of these).
    for code in ("CAT", "PIL", "SSPI"):
        assert result.get(code), f"{code} should have aggregated scores after the drop"
    assert len(result["SSPI"]) == 4, "2 countries x 2 years of SSPI scores expected"


def test_aggregate_equals_surviving_indicator():
    """With one indicator dropped, the category/SSPI score equals the survivor
    (weights renormalize over the single remaining indicator -> *100 scale)."""
    good = [[0.5, 0.6], [0.7, 0.8]]
    dead = [[np.nan, np.nan], [np.nan, np.nan]]

    result = _run_with_dead_indicator(good, dead)

    sspi_by_cy = {(d["country_code"], d["year"]): d["score"] for d in result["SSPI"]}
    assert sspi_by_cy[("AAA", 2000)] == pytest.approx(50.0)
    assert sspi_by_cy[("AAA", 2001)] == pytest.approx(60.0)
    assert sspi_by_cy[("BBB", 2000)] == pytest.approx(70.0)
    assert sspi_by_cy[("BBB", 2001)] == pytest.approx(80.0)


def test_no_drop_when_all_indicators_score():
    """When every indicator scores, nothing is dropped and both appear."""
    good = [[0.5, 0.6], [0.7, 0.8]]
    other = [[0.3, 0.4], [0.1, 0.2]]

    result = _run_with_dead_indicator(good, other)

    assert result.get("GOOD"), "GOOD should be present"
    assert result.get("DEAD"), "the non-NaN second indicator should be kept"
    assert result.get("SSPI"), "SSPI should aggregate both"


def test_rebuild_metadata_renormalizes_category_children():
    """The shared helper removes the indicator and updates parent references."""
    rebuilt = rebuild_metadata_without_indicators(_chain_metadata(), {"DEAD"})
    codes = {m["ItemCode"] for m in rebuilt}
    assert "DEAD" not in codes
    cat = next(m for m in rebuilt if m["ItemCode"] == "CAT")
    assert cat["IndicatorCodes"] == ["GOOD"]
    assert cat["Children"] == ["GOOD"]
