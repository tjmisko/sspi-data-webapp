"""
impute_dataset_vectorized must fill gaps like utilities.impute_dataset, the
official dataset-level imputation: the reference class average is the mean of
each reference country's own mean, not the pooled mean over all cells.
"""
from unittest.mock import patch

import numpy as np
import pytest

import sspi_flask_app.api.resources.utilities as util
from sspi_flask_app.api.resources.fast_custom_scoring import (
    impute_dataset_vectorized,
)

NAN = np.nan


def test_should_average_country_means_when_filling_a_country_with_no_data():
    # AAA has 3 observed years (mean 0.2), BBB 1 observed year (0.8).
    # Pooled mean would be 0.35; mean of country means is 0.5.
    data = np.array([
        [0.2, 0.2, 0.2],
        [NAN, 0.8, NAN],
        [NAN, NAN, NAN],
    ])
    imputed, flags = impute_dataset_vectorized(
        data, np.array([True, True, False]))
    assert np.allclose(imputed[2], 0.5)
    assert flags[2].all()
    assert not flags[0].any()


def test_should_extrapolate_and_interpolate_when_a_country_has_partial_data():
    data = np.array([[NAN, 0.2, NAN, 0.6, NAN]])
    imputed, _ = impute_dataset_vectorized(data, np.array([True]))
    assert imputed[0] == pytest.approx([0.2, 0.2, 0.4, 0.6, 0.6])


def test_should_fill_neutral_when_the_whole_dataset_is_empty():
    imputed, flags = impute_dataset_vectorized(
        np.full((2, 3), NAN), np.array([True, True]))
    assert np.allclose(imputed, 0.5)
    assert flags.all()


def test_should_match_official_impute_dataset_when_same_panel_is_filled():
    countries = ["AAA", "BBB", "CCC"]
    years = [2000, 2001, 2002, 2003]
    panel = np.array([
        [0.1, NAN, 0.5, NAN],
        [NAN, 0.9, NAN, NAN],
        [NAN, NAN, NAN, NAN],
    ])
    clean_docs = [
        {"DatasetCode": "DS", "CountryCode": c, "Year": y,
         "Value": float(panel[i, j]), "Unit": "Index"}
        for i, c in enumerate(countries) for j, y in enumerate(years)
        if not np.isnan(panel[i, j])
    ]
    with patch.object(util.sspi_clean_api_data, "find",
                      return_value=clean_docs), \
         patch.object(util.sspi_metadata, "country_group",
                      return_value=countries):
        official = util.impute_dataset("DS", countries, 2000, 2003)
    vectorized, _ = impute_dataset_vectorized(panel, np.array([True] * 3))
    for i, c in enumerate(countries):
        for j, y in enumerate(years):
            assert vectorized[i, j] == pytest.approx(official[(c, y)]["Value"])
