"""
Tests for the ARMEXP compute and impute routes after the SIPRI_ARMEXP
cleaner started recording blank cells and absent SSPI exporters as observed
0 TIV (owner ruling 2026-09-13). Collections are in-memory fakes running the
real document validators; handlers are called through __wrapped__ (below
@admin_required) inside a bare Flask app context.
"""
from copy import deepcopy

import pytest
from flask import Flask

import sspi_flask_app.api.core.sspi.pg.glb.armexp as armexp_module
from sspi_flask_app.api.core.datasets.sipri.sipri_armexp import sipri_armexp_doc
from sspi_flask_app.api.core.sspi.pg.glb.armexp import (
    build_armexp_imputations,
    missing_armexp_cells,
)
from sspi_flask_app.models.database import sspi_imputed_data, sspi_indicator_data

ZERO_NOTE = "No recorded transfers (0 TIV)"


class FakeCollection:
    def __init__(self, documents=None, validator=None):
        self.documents = deepcopy(documents or [])
        self.validator = validator
        self.insert_calls = 0

    @staticmethod
    def matches(document, query):
        return all(document.get(key) == value for key, value in query.items())

    def find(self, query, options=None):
        return [deepcopy(doc) for doc in self.documents if self.matches(doc, query)]

    def delete_many(self, query):
        kept = [doc for doc in self.documents if not self.matches(doc, query)]
        deleted_count = len(self.documents) - len(kept)
        self.documents = kept
        return deleted_count

    def insert_many(self, documents):
        if self.validator is not None:
            self.validator(documents)
        self.insert_calls += 1
        self.documents.extend(deepcopy(documents))
        return len(documents)


class FakeMetadata:
    def __init__(self, country_codes):
        self.country_codes = country_codes

    def get_goalposts(self, indicator_code):
        assert indicator_code == "ARMEXP"
        return 500, 0

    def country_group(self, group_name):
        assert group_name == "SSPI67"
        return self.country_codes


def dense_clean_panel(first_year=1990, last_year=2024):
    """USA sells every year; KWT has one 1998 sale; BGD is a zero-filled absentee."""
    docs = []
    for year in range(first_year, last_year + 1):
        docs.append(sipri_armexp_doc("USA", year, 10000.0, False))
        kwt_value = 117.0 if year == 1998 else 0.0
        docs.append(sipri_armexp_doc("KWT", year, kwt_value, year != 1998))
        docs.append(sipri_armexp_doc("BGD", year, 0.0, True))
    return docs


@pytest.fixture
def install_fakes(monkeypatch):
    def install(clean_docs, country_codes, observed_docs=(), imputed_docs=()):
        fakes = {
            "clean": FakeCollection(clean_docs),
            "indicator": FakeCollection(list(observed_docs), sspi_indicator_data.validate_documents_format),
            "imputed": FakeCollection(list(imputed_docs), sspi_imputed_data.validate_documents_format),
        }
        monkeypatch.setattr(armexp_module, "sspi_clean_api_data", fakes["clean"])
        monkeypatch.setattr(armexp_module, "sspi_indicator_data", fakes["indicator"])
        monkeypatch.setattr(armexp_module, "sspi_imputed_data", fakes["imputed"])
        monkeypatch.setattr(armexp_module, "sspi_metadata", FakeMetadata(country_codes))
        return fakes
    return install


def run_route(handler_name):
    with Flask(__name__).app_context():
        return getattr(armexp_module, handler_name).__wrapped__()


def score_by_cell(docs):
    return {(doc["CountryCode"], doc["Year"]): doc["Score"] for doc in docs}


def test_should_build_no_imputations_when_clean_panel_is_dense_over_window():
    assert build_armexp_imputations(dense_clean_panel()) == []


def test_should_not_carry_old_sale_forward_when_later_years_are_observed_zero():
    imputations = build_armexp_imputations(dense_clean_panel())
    assert not [doc for doc in imputations if doc["CountryCode"] == "KWT"]


def test_should_carry_only_to_2023_with_distance_when_table_ends_early():
    imputations = build_armexp_imputations(dense_clean_panel(last_year=2021))
    cells = sorted((doc["CountryCode"], doc["Year"], doc["ImputationDistance"]) for doc in imputations)
    assert cells == [
        ("BGD", 2022, 1), ("BGD", 2023, 2),
        ("KWT", 2022, 1), ("KWT", 2023, 2),
        ("USA", 2022, 1), ("USA", 2023, 2),
    ]
    assert all(doc["Imputed"] is True for doc in imputations)
    assert all(doc["ImputationMethod"] == "Forward Extrapolation" for doc in imputations)


def test_should_carry_backward_to_2000_when_table_starts_late():
    imputations = build_armexp_imputations(dense_clean_panel(first_year=2002))
    assert sorted({doc["Year"] for doc in imputations}) == [2000, 2001]
    assert {doc["ImputationMethod"] for doc in imputations} == {"Backward Extrapolation"}


def test_should_list_missing_cells_when_country_has_no_rows():
    docs = [{"CountryCode": "USA", "Year": year} for year in range(2000, 2024)]
    missing = missing_armexp_cells(docs, ["USA", "IRQ"])
    assert missing == [("IRQ", year) for year in range(2000, 2024)]


def test_should_list_no_missing_cells_when_panel_is_complete():
    docs = [{"CountryCode": c, "Year": y} for c in ("USA", "IRQ") for y in range(2000, 2024)]
    assert missing_armexp_cells(docs, ["USA", "IRQ"]) == []


def test_should_score_zero_filled_rows_as_observed_with_note_when_computing(install_fakes):
    fakes = install_fakes(dense_clean_panel(), ["USA", "KWT", "BGD"])
    run_route("compute_armexp")
    observed = fakes["indicator"].documents
    scores = score_by_cell(observed)
    assert scores[("BGD", 2020)] == pytest.approx(1.0)
    assert scores[("KWT", 2020)] == pytest.approx(1.0)
    assert scores[("KWT", 1998)] == pytest.approx(1 - 117 / 500)
    assert scores[("USA", 2020)] == pytest.approx(0.0)
    bgd_2020 = next(doc for doc in observed if doc["CountryCode"] == "BGD" and doc["Year"] == 2020)
    dataset = bgd_2020["Datasets"][0]
    assert dataset["Note"] == ZERO_NOTE
    assert "Imputed" not in dataset
    for country_code in ("USA", "KWT", "BGD"):
        for year in range(2000, 2024):
            assert (country_code, year) in scores


def test_should_keep_same_observed_row_count_when_compute_runs_twice(install_fakes):
    fakes = install_fakes(dense_clean_panel(), ["USA", "KWT", "BGD"])
    run_route("compute_armexp")
    first_rows = deepcopy(fakes["indicator"].documents)
    run_route("compute_armexp")
    assert len(fakes["indicator"].documents) == len(first_rows) == 3 * 35


def test_should_impute_nothing_and_clear_stale_fills_when_panel_is_dense(install_fakes):
    stale_world_mean_fill = {
        "IndicatorCode": "ARMEXP", "CountryCode": "BGD", "Year": 2020,
        "Score": 0.0, "Unit": "Expenditure",
        "Datasets": [{"DatasetCode": "SIPRI_ARMEXP", "CountryCode": "BGD", "Year": 2020,
                      "Value": 579.15, "Unit": "Millions SIPRI TIV", "Imputed": True}],
    }
    fakes = install_fakes(dense_clean_panel(), ["USA", "KWT", "BGD"], imputed_docs=[stale_world_mean_fill])
    run_route("compute_armexp")
    assert run_route("impute_armexp") == []
    assert fakes["imputed"].documents == []
    assert fakes["imputed"].insert_calls == 0


def test_should_keep_same_imputed_row_count_when_impute_runs_twice(install_fakes):
    fakes = install_fakes(dense_clean_panel(last_year=2021), ["USA", "KWT", "BGD"])
    run_route("compute_armexp")
    observed_before = deepcopy(fakes["indicator"].documents)
    run_route("impute_armexp")
    first_rows = deepcopy(fakes["imputed"].documents)
    run_route("impute_armexp")
    assert len(fakes["imputed"].documents) == len(first_rows) == 6
    assert fakes["imputed"].documents == first_rows
    assert fakes["indicator"].documents == observed_before


def test_should_warn_when_sspi_country_has_no_armexp_rows_after_impute(install_fakes, caplog):
    install_fakes(dense_clean_panel(), ["USA", "KWT", "BGD", "IRQ"])
    run_route("compute_armexp")
    with caplog.at_level("WARNING"):
        run_route("impute_armexp")
    assert "24 SSPI67 country-years" in caplog.text
    assert "IRQ" in caplog.text
