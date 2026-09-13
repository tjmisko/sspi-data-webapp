"""
Route tests for /impute/RULELW and /impute/EDEMOC. The clean, observed and
imputed collections are in-memory fakes that run the real document
validators, so nothing reads or writes MongoDB. The handlers are called
through __wrapped__ (below @admin_required) inside a bare Flask app context.
"""
from copy import deepcopy

import pytest
from flask import Flask

import sspi_flask_app.api.core.sspi.pg.rts.edemoc as edemoc_module
import sspi_flask_app.api.core.sspi.pg.rts.rulelw as rulelw_module
from sspi_flask_app.models.database import sspi_imputed_data, sspi_indicator_data


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
    def get_goalposts(self, indicator_code):
        return 0, 1


ROUTES = [
    pytest.param(rulelw_module, "RULELW", "impute_rulelw", id="RULELW"),
    pytest.param(edemoc_module, "EDEMOC", "impute_edemoc", id="EDEMOC"),
]


def vdem_doc(dataset_code, country_code, year, value):
    return {
        "DatasetCode": dataset_code,
        "CountryCode": country_code,
        "Year": year,
        "Value": value,
        "Unit": "Index",
    }


def observed_indicator_doc(indicator_code, dataset_code, country_code, year, value):
    return {
        "IndicatorCode": indicator_code,
        "CountryCode": country_code,
        "Year": year,
        "Score": value,
        "Unit": "Index",
        "Datasets": [vdem_doc(dataset_code, country_code, year, value)],
    }


@pytest.fixture
def install_fakes(monkeypatch):
    def install(module, indicator_code, clean_docs, observed_docs, imputed_docs=()):
        fakes = {
            "clean": FakeCollection(clean_docs),
            "indicator": FakeCollection(observed_docs, sspi_indicator_data.validate_documents_format),
            "imputed": FakeCollection(list(imputed_docs), sspi_imputed_data.validate_documents_format),
        }
        monkeypatch.setattr(module, "sspi_clean_api_data", fakes["clean"])
        monkeypatch.setattr(module, "sspi_indicator_data", fakes["indicator"])
        monkeypatch.setattr(module, "sspi_imputed_data", fakes["imputed"])
        monkeypatch.setattr(module, "sspi_metadata", FakeMetadata())
        return fakes
    return install


def run_route(module, handler_name):
    with Flask(__name__).app_context():
        return getattr(module, handler_name).__wrapped__()


def panel(indicator_code):
    """AAA observed through 2021, BBB through 2023, CCC through 2025."""
    dataset_code = f"VDEM_{indicator_code}"
    last_years = {"AAA": 2021, "BBB": 2023, "CCC": 2025}
    clean_docs, observed_docs = [], []
    for country_code, last_year in last_years.items():
        for year in range(2019, last_year + 1):
            value = round(0.1 * (year - 2018), 2)
            clean_docs.append(vdem_doc(dataset_code, country_code, year, value))
            observed_docs.append(
                observed_indicator_doc(indicator_code, dataset_code, country_code, year, value)
            )
    return clean_docs, observed_docs


@pytest.mark.parametrize("module, indicator_code, handler_name", ROUTES)
def test_should_write_carried_years_to_imputed_collection_when_series_ends_before_2023(
    install_fakes, module, indicator_code, handler_name
):
    clean_docs, observed_docs = panel(indicator_code)
    fakes = install_fakes(module, indicator_code, clean_docs, observed_docs)
    run_route(module, handler_name)
    imputed = fakes["imputed"].documents
    assert sorted((doc["CountryCode"], doc["Year"]) for doc in imputed) == [
        ("AAA", 2022), ("AAA", 2023)
    ]
    for doc in imputed:
        assert doc["IndicatorCode"] == indicator_code
        dataset = doc["Datasets"][0]
        assert dataset["Imputed"] is True
        assert dataset["ImputationMethod"] == "Forward Extrapolation"
        assert dataset["ImputationDistance"] == doc["Year"] - 2021
        assert doc["Score"] == pytest.approx(0.3)


@pytest.mark.parametrize("module, indicator_code, handler_name", ROUTES)
def test_should_leave_observed_collection_untouched_when_imputing(
    install_fakes, module, indicator_code, handler_name
):
    clean_docs, observed_docs = panel(indicator_code)
    fakes = install_fakes(module, indicator_code, clean_docs, observed_docs)
    before = deepcopy(fakes["indicator"].documents)
    run_route(module, handler_name)
    run_route(module, handler_name)
    assert fakes["indicator"].documents == before
    assert fakes["indicator"].insert_calls == 0


@pytest.mark.parametrize("module, indicator_code, handler_name", ROUTES)
def test_should_keep_same_imputed_row_count_when_route_runs_twice(
    install_fakes, module, indicator_code, handler_name
):
    clean_docs, observed_docs = panel(indicator_code)
    fakes = install_fakes(module, indicator_code, clean_docs, observed_docs)
    first = run_route(module, handler_name)
    first_rows = deepcopy(fakes["imputed"].documents)
    second = run_route(module, handler_name)
    assert len(fakes["imputed"].documents) == len(first_rows) == 2
    assert fakes["imputed"].documents == first_rows
    assert len(first) == len(second) == 2


@pytest.mark.parametrize("module, indicator_code, handler_name", ROUTES)
def test_should_replace_stale_rows_of_own_indicator_only_when_rerun(
    install_fakes, module, indicator_code, handler_name
):
    clean_docs, observed_docs = panel(indicator_code)
    stale_own = observed_indicator_doc(indicator_code, f"VDEM_{indicator_code}", "ZZZ", 2023, 0.5)
    other_indicator = observed_indicator_doc("GENDEQ", "VDEM_GENDEQ", "ZZZ", 2023, 0.5)
    fakes = install_fakes(
        module, indicator_code, clean_docs, observed_docs, [stale_own, other_indicator]
    )
    run_route(module, handler_name)
    remaining = {(doc["IndicatorCode"], doc["CountryCode"]) for doc in fakes["imputed"].documents}
    assert (indicator_code, "ZZZ") not in remaining
    assert ("GENDEQ", "ZZZ") in remaining


@pytest.mark.parametrize("module, indicator_code, handler_name", ROUTES)
def test_should_insert_nothing_and_clear_old_rows_when_every_series_reaches_2023(
    install_fakes, module, indicator_code, handler_name
):
    clean_docs, observed_docs = panel(indicator_code)
    clean_docs = [doc for doc in clean_docs if doc["CountryCode"] != "AAA"]
    stale_own = observed_indicator_doc(indicator_code, f"VDEM_{indicator_code}", "BBB", 2023, 0.5)
    fakes = install_fakes(module, indicator_code, clean_docs, observed_docs, [stale_own])
    assert run_route(module, handler_name) == []
    assert fakes["imputed"].documents == []
    assert fakes["imputed"].insert_calls == 0


@pytest.mark.parametrize("module, indicator_code, handler_name", ROUTES)
def test_should_insert_nothing_when_clean_dataset_is_empty(
    install_fakes, module, indicator_code, handler_name
):
    fakes = install_fakes(module, indicator_code, [], [])
    assert run_route(module, handler_name) == []
    assert fakes["imputed"].insert_calls == 0

