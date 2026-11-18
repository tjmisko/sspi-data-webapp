"""
Parity guard (synthetic): scoring the default configuration from official
baseline indicator rows must reproduce what the official SSPI model computes
for every category, pillar and the SSPI root, independently of the custom
aggregation code.

Reference: sspi_flask_app.models.sspi.SSPI (the official finalize scorer). The
indicator baseline and country group are mocked; nothing touches the database.
"""
from unittest.mock import patch

import numpy as np
import pytest

import sspi_flask_app.api.resources.fast_custom_scoring as fcs
from sspi_flask_app.models.sspi import SSPI

COUNTRIES = ["AAA", "BBB", "CCC"]
YEARS = [2000, 2001]


def _default_metadata():
    """Two pillars with uneven category and indicator counts, no weights."""
    ind_to_cat = {
        "IND001": "CAT1", "IND002": "CAT1", "IND003": "CAT1",
        "IND004": "CAT2", "IND005": "CAT3", "IND006": "CAT3",
    }
    items = [
        {"ItemType": "SSPI", "ItemCode": "SSPI", "ItemName": "SSPI",
         "PillarCodes": ["PIL1", "PIL2"], "Children": ["PIL1", "PIL2"]},
        {"ItemType": "Pillar", "ItemCode": "PIL1", "ItemName": "P1",
         "CategoryCodes": ["CAT1", "CAT2"], "Children": ["CAT1", "CAT2"]},
        {"ItemType": "Pillar", "ItemCode": "PIL2", "ItemName": "P2",
         "CategoryCodes": ["CAT3"], "Children": ["CAT3"]},
        {"ItemType": "Category", "ItemCode": "CAT1", "ItemName": "C1",
         "IndicatorCodes": ["IND001", "IND002", "IND003"],
         "Children": ["IND001", "IND002", "IND003"]},
        {"ItemType": "Category", "ItemCode": "CAT2", "ItemName": "C2",
         "IndicatorCodes": ["IND004"], "Children": ["IND004"]},
        {"ItemType": "Category", "ItemCode": "CAT3", "ItemName": "C3",
         "IndicatorCodes": ["IND005", "IND006"],
         "Children": ["IND005", "IND006"]},
    ]
    for code, cat in ind_to_cat.items():
        items.append({
            "ItemType": "Indicator", "ItemCode": code, "ItemName": code,
            "CategoryCode": cat, "DatasetCodes": ["DS_" + code],
            "ScoreFunction": f"Score = goalpost(DS_{code}, 0, 1)",
            "LowerGoalpost": 0, "UpperGoalpost": 1,
        })
    return items


def _baseline(codes):
    rng = np.random.default_rng(7)
    return {
        code: rng.random((len(COUNTRIES), len(YEARS))) for code in codes
    }


def _reference_scores(metadata, baseline):
    """Official SSPI model, one country-year at a time."""
    expected = {}
    for ci, country in enumerate(COUNTRIES):
        for yi, year in enumerate(YEARS):
            rows = [
                {"CountryCode": country, "IndicatorCode": code,
                 "Score": float(arr[ci, yi]), "Year": year}
                for code, arr in baseline.items()
            ]
            for doc in SSPI(metadata, rows).to_score_documents(country):
                expected[(doc["ItemCode"], country, year)] = doc["Score"]
    return expected


@pytest.fixture
def custom_result():
    metadata = _default_metadata()
    codes = [m["ItemCode"] for m in metadata if m["ItemType"] == "Indicator"]
    baseline = _baseline(codes)
    with patch.object(fcs.sspi_metadata, "country_group",
                      return_value=COUNTRIES), \
         patch.object(fcs, "fetch_baseline_indicator_scores",
                      return_value=baseline):
        result = fcs.score_custom_configuration_fast(
            metadata, modified_indicators=set(),
            country_codes=COUNTRIES, start_year=YEARS[0], end_year=YEARS[-1],
        )
    return metadata, baseline, result


@pytest.mark.parametrize("level", ["Category", "Pillar", "SSPI"])
def test_should_match_official_scores_when_default_config_is_rescored(
        custom_result, level):
    metadata, baseline, result = custom_result
    expected = _reference_scores(metadata, baseline)
    codes = [m["ItemCode"] for m in metadata if m["ItemType"] == level]
    assert codes
    for code in codes:
        for doc in result[code]:
            want = expected[(code, doc["country_code"], doc["year"])]
            # custom scores are stored at 0-100
            assert doc["score"] / 100 == pytest.approx(want, abs=1e-9)
        assert len(result[code]) == len(COUNTRIES) * len(YEARS)


def test_should_reproduce_baseline_indicator_rows_when_no_indicator_is_modified(
        custom_result):
    _, baseline, result = custom_result
    for code, arr in baseline.items():
        for doc in result[code]:
            ci = COUNTRIES.index(doc["country_code"])
            yi = YEARS.index(doc["year"])
            assert doc["score"] / 100 == pytest.approx(arr[ci, yi], abs=1e-9)
