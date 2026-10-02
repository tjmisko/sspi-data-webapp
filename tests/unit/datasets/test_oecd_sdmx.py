"""
Unit tests for the generic OECD SDMX helpers in
``sspi_flask_app.api.datasource.oecdstat`` and the OECD_TOTDON / OECD_TONREC
dataset modules built on them. requests.get and the raw-data insert are
monkeypatched so nothing touches the network or the database.
"""
import frontmatter
import os
import pytest
import requests

import sspi_flask_app.api.datasource.oecdstat as oecdstat
from sspi_flask_app.api.datasource.oecdstat import (
    OECD_SDMX_CSV_LABELS_ACCEPT_HEADER,
    OECD_SDMX_DEFAULT_QUERY_PARAMETERS,
    OECD_SDMX_REQUEST_TIMEOUT_SECONDS,
    build_oecd_sdmx_data_url,
    clean_oecd_sdmx_observations,
    collect_oecd_sdmx_csv,
    oecd_sdmx_unit_from_row,
    parse_oecd_sdmx_csv,
)
from sspi_flask_app.api.core.datasets.oecd import oecd_totdon, oecd_tonrec


REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))

CLEAN_OBSERVATION_KEYS = {"CountryCode", "DatasetCode", "Description", "Year", "Unit", "Value"}

# Header and rows exactly as sdmx.oecd.org returns them for
# Accept: application/vnd.sdmx.data+csv;version=2.0.0;labels=name
DAC1_HEADER = (
    "STRUCTURE,STRUCTURE_ID,STRUCTURE_NAME,ACTION,DONOR,Donor,SECTOR,Sector,MEASURE,Measure,"
    "TYING_STATUS,Tying status,FLOW_TYPE,Flow type,UNIT_MEASURE,Unit of measure,PRICE_BASE,"
    "Price base,TIME_PERIOD,Time period,OBS_VALUE,Observation value,BASE_PER,Base period,"
    "OBS_STATUS,Observation status,UNIT_MULT,Unit multiplier,DECIMALS,Decimals"
)
DAC1_STRUCTURE = (
    "DATAFLOW,OECD.DCD.FSD:DSD_DAC1@DF_DAC1(1.7),DAC1: Flows by provider (ODA+OOF+Private),I"
)


def dac1_row(donor, donor_label, year, value, measure="1010", flow_type="1140",
             unit_measure="USD", price_base="V", unit_mult="6"):
    return (
        f"{DAC1_STRUCTURE},{donor},{donor_label},_Z,Not applicable,{measure},"
        f"Official Development Assistance (ODA),_Z,Not applicable,{flow_type},"
        f"\"Disbursements, net\",{unit_measure},US dollar,{price_base},Current prices,"
        f"{year},,{value},,,,A,Normal value,{unit_mult},Millions,,"
    )


DAC1_FIXTURE_CSV = "\ufeff" + "\n".join([
    DAC1_HEADER,
    dac1_row("DAC", "DAC countries", 2015, "131585.51"),
    dac1_row("4EU001", "EU Institutions", 2015, "13849.7"),
    dac1_row("USA", "United States", 2015, "30985.54"),
    dac1_row("DEU", "Germany", 2020, "29320.38"),
    dac1_row("USA", "United States", 2020, "35396.41", price_base="Q"),
    dac1_row("FRA", "France", 2020, ""),
    dac1_row("FRA", "France", "2020-Q1", "100"),
    "",
    "",
])

DAC2A_HEADER = (
    "STRUCTURE,STRUCTURE_ID,STRUCTURE_NAME,ACTION,DONOR,Donor,RECIPIENT,Recipient,MEASURE,"
    "Measure,UNIT_MEASURE,Unit of measure,PRICE_BASE,Price base,TIME_PERIOD,Time period,"
    "OBS_VALUE,Observation value,BASE_PER,Base period,UNIT_MULT,Unit multiplier,FLOW_TYPE,"
    "Flow type,OBS_STATUS,Observation status"
)
DAC2A_STRUCTURE = (
    "DATAFLOW,OECD.DCD.FSD:DSD_DAC2@DF_DAC2A(1.6),"
    "DAC2A: Aid (ODA) disbursements to countries and regions,I"
)


def dac2a_row(recipient, recipient_label, year, value, donor="ALLD", donor_label="Official donors",
              measure="206"):
    return (
        f"{DAC2A_STRUCTURE},{donor},{donor_label},{recipient},{recipient_label},{measure},"
        f"\"Official development assistance (ODA), disbursements\",USD,US dollar,V,Current prices,"
        f"{year},,{value},,,,6,Millions,D,Disbursements,A,Normal value"
    )


DAC2A_FIXTURE_CSV = "\n".join([
    DAC2A_HEADER,
    dac2a_row("IND", "India", 2015, "3174.348367"),
    dac2a_row("CHN", "China (People's Republic of)", 2020, "-570.617053"),
    dac2a_row("DPGC", "Developing countries", 2015, "150000"),
    dac2a_row("LDC", "Least developed countries", 2015, "40000"),
    dac2a_row("XKV", "Kosovo", 2015, "500"),
    dac2a_row("ETH", "Ethiopia", 2015, "1854.467825", donor="DAC", donor_label="DAC countries"),
])


def _load_doc_source(org_folder, dataset_folder):
    doc_path = os.path.join(REPO_ROOT, "datasets", org_folder, dataset_folder, "documentation.md")
    return frontmatter.load(doc_path).metadata["Source"]


class _FakeResponse:
    def __init__(self, status_code, text):
        self.status_code = status_code
        self.text = text

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"{self.status_code} error")


def _install_fakes(monkeypatch, status_code=200, text=DAC1_FIXTURE_CSV):
    captured = {"requests": [], "inserts": []}

    def _fake_get(url, *args, **kwargs):
        captured["requests"].append({"url": url, **kwargs})
        return _FakeResponse(status_code, text)

    def _fake_raw_insert_one(document, source_info, **kwargs):
        captured["inserts"].append({"document": document, "source_info": source_info, **kwargs})
        return 1

    monkeypatch.setattr(oecdstat.requests, "get", _fake_get)
    monkeypatch.setattr(oecdstat.sspi_raw_api_data, "raw_insert_one", _fake_raw_insert_one)
    return captured


# --------------------------------------------------------------------------
# build_oecd_sdmx_data_url
# --------------------------------------------------------------------------

def test_should_join_dataflow_key_and_params_when_building_url():
    url = build_oecd_sdmx_data_url(
        "OECD.DCD.FSD,DSD_DAC1@DF_DAC1", "._Z.1010._Z.1140.USD.V", "startPeriod=2000"
    )
    assert url == (
        "https://sdmx.oecd.org/public/rest/data/"
        "OECD.DCD.FSD,DSD_DAC1@DF_DAC1/._Z.1010._Z.1140.USD.V?startPeriod=2000"
    )


def test_should_omit_question_mark_when_no_query_parameters():
    url = build_oecd_sdmx_data_url("A,B", "X.Y", "")
    assert url == "https://sdmx.oecd.org/public/rest/data/A,B/X.Y"


# --------------------------------------------------------------------------
# collect_oecd_sdmx_csv
# --------------------------------------------------------------------------

def test_should_request_labelled_sdmx_csv_with_timeout_when_collecting(monkeypatch):
    captured = _install_fakes(monkeypatch)
    list(collect_oecd_sdmx_csv(
        "OECD.DCD.FSD,DSD_DAC1@DF_DAC1", "._Z.1010._Z.1140.USD.V",
        "startPeriod=2000&dimensionAtObservation=AllDimensions", "QC", username="tester",
    ))
    assert len(captured["requests"]) == 1
    request = captured["requests"][0]
    assert request["url"] == (
        "https://sdmx.oecd.org/public/rest/data/OECD.DCD.FSD,DSD_DAC1@DF_DAC1/"
        "._Z.1010._Z.1140.USD.V?startPeriod=2000&dimensionAtObservation=AllDimensions"
    )
    assert request["headers"] == {"Accept": OECD_SDMX_CSV_LABELS_ACCEPT_HEADER}
    assert request["headers"]["Accept"] == "application/vnd.sdmx.data+csv;version=2.0.0;labels=name"
    assert request["timeout"] == OECD_SDMX_REQUEST_TIMEOUT_SECONDS


def test_should_store_csv_text_verbatim_as_one_raw_document_when_collecting(monkeypatch):
    captured = _install_fakes(monkeypatch)
    list(collect_oecd_sdmx_csv("A,B", "X.Y", "startPeriod=2000", "QC", username="tester"))
    assert len(captured["inserts"]) == 1
    insert = captured["inserts"][0]
    assert insert["document"] == DAC1_FIXTURE_CSV
    assert isinstance(insert["document"], str)
    assert insert["username"] == "tester"


def test_should_stamp_dataflow_and_query_code_in_source_info_when_collecting(monkeypatch):
    captured = _install_fakes(monkeypatch)
    list(collect_oecd_sdmx_csv(
        "OECD.DCD.FSD,DSD_DAC1@DF_DAC1", "._Z.1010._Z.1140.USD.V", "startPeriod=2000",
        "DSD_DAC1@DF_DAC1(._Z.1010._Z.1140.USD.V)", username="tester",
    ))
    source_info = captured["inserts"][0]["source_info"]
    assert source_info == {
        "OrganizationName": "Organisation for Economic Co-operation and Development",
        "OrganizationCode": "OECD",
        "OrganizationSeriesCode": "OECD.DCD.FSD,DSD_DAC1@DF_DAC1",
        "QueryCode": "DSD_DAC1@DF_DAC1(._Z.1010._Z.1140.USD.V)",
        "URL": captured["requests"][0]["url"],
    }
    assert all(value is not None for value in source_info.values())


def test_should_use_default_query_parameters_when_given_empty_string(monkeypatch):
    captured = _install_fakes(monkeypatch)
    list(collect_oecd_sdmx_csv("A,B", "X.Y", "", "QC", username="tester"))
    assert captured["requests"][0]["url"].endswith(f"?{OECD_SDMX_DEFAULT_QUERY_PARAMETERS}")


def test_should_honour_custom_accept_header_when_given(monkeypatch):
    captured = _install_fakes(monkeypatch)
    list(collect_oecd_sdmx_csv(
        "A,B", "X.Y", "startPeriod=2000", "QC",
        accept_header="application/vnd.sdmx.data+csv;version=1.0.0", username="tester",
    ))
    assert captured["requests"][0]["headers"] == {
        "Accept": "application/vnd.sdmx.data+csv;version=1.0.0"
    }


def test_should_insert_nothing_and_yield_message_when_api_returns_404(monkeypatch):
    captured = _install_fakes(monkeypatch, status_code=404, text="NoResultsFound")
    messages = list(collect_oecd_sdmx_csv(
        "OECD.DCD.FSD,DSD_DAC1@DF_DAC1", "USA.1000.1010._T.1140.USD.V", "startPeriod=2000",
        "QC", username="tester",
    ))
    assert captured["inserts"] == []
    assert any("404" in message and "USA.1000.1010._T.1140.USD.V" in message for message in messages)


def test_should_raise_and_insert_nothing_when_api_returns_server_error(monkeypatch):
    captured = _install_fakes(monkeypatch, status_code=500, text="<html>error</html>")
    with pytest.raises(requests.HTTPError):
        list(collect_oecd_sdmx_csv("A,B", "X.Y", "startPeriod=2000", "QC", username="tester"))
    assert captured["inserts"] == []


# --------------------------------------------------------------------------
# parse_oecd_sdmx_csv
# --------------------------------------------------------------------------

def test_should_return_one_dict_per_row_with_csv_columns_when_parsing():
    rows = parse_oecd_sdmx_csv(DAC1_FIXTURE_CSV)
    assert len(rows) == 7
    first = rows[0]
    assert first["STRUCTURE"] == "DATAFLOW", "BOM must not be glued onto the first header"
    assert first["DONOR"] == "DAC"
    assert first["Donor"] == "DAC countries"
    assert first["MEASURE"] == "1010"
    assert first["Measure"] == "Official Development Assistance (ODA)"
    assert first["Flow type"] == "Disbursements, net", "quoted comma label must survive"
    assert first["TIME_PERIOD"] == "2015"
    assert first["OBS_VALUE"] == "131585.51"
    assert first["UNIT_MULT"] == "6"
    assert first["Unit multiplier"] == "Millions"
    assert set(first) == set(DAC1_HEADER.split(","))


def test_should_skip_trailing_blank_lines_when_parsing():
    rows = parse_oecd_sdmx_csv(DAC1_HEADER + "\n" + dac1_row("USA", "United States", 2015, "1") + "\n\n\n")
    assert len(rows) == 1


def test_should_return_empty_list_when_csv_is_empty():
    assert parse_oecd_sdmx_csv("") == []
    assert parse_oecd_sdmx_csv(DAC1_HEADER + "\n") == []


# --------------------------------------------------------------------------
# clean_oecd_sdmx_observations
# --------------------------------------------------------------------------

def test_should_compose_unit_from_label_columns_when_present():
    row = {"Unit of measure": "US dollar", "Unit multiplier": "Millions", "Price base": "Current prices"}
    assert oecd_sdmx_unit_from_row(row) == "US dollar, Millions, Current prices"


def test_should_skip_missing_labels_when_composing_unit():
    assert oecd_sdmx_unit_from_row({"Unit of measure": "Tonnes", "Unit multiplier": ""}) == "Tonnes"


def test_should_keep_only_iso3_country_rows_with_int_year_and_float_value_when_cleaning_totdon():
    rows = parse_oecd_sdmx_csv(DAC1_FIXTURE_CSV)
    cleaned, drop_report = clean_oecd_sdmx_observations(
        rows, "OECD_TOTDON", oecd_totdon.OECD_TOTDON_COUNTRY_CODE_COLUMN,
        oecd_totdon.describe_oecd_totdon_row, row_filters=oecd_totdon.OECD_TOTDON_ROW_FILTERS,
    )
    by_country_year = {(obs["CountryCode"], obs["Year"]): obs for obs in cleaned}
    assert set(by_country_year) == {("USA", 2015), ("DEU", 2020)}
    assert by_country_year[("USA", 2015)]["Value"] == 30985.54
    assert by_country_year[("DEU", 2020)]["Value"] == 29320.38
    for obs in cleaned:
        assert set(obs) == CLEAN_OBSERVATION_KEYS
        assert isinstance(obs["Year"], int)
        assert isinstance(obs["Value"], float)
        assert obs["DatasetCode"] == "OECD_TOTDON"
        assert obs["Unit"] == "US dollar, Millions, Current prices"
        assert obs["Description"] == (
            "Official Development Assistance (ODA): Disbursements, net from donor "
            "(DAC1: Flows by provider (ODA+OOF+Private))"
        )


def test_should_count_every_dropped_row_when_cleaning_totdon():
    rows = parse_oecd_sdmx_csv(DAC1_FIXTURE_CSV)
    cleaned, drop_report = clean_oecd_sdmx_observations(
        rows, "OECD_TOTDON", "DONOR", oecd_totdon.describe_oecd_totdon_row,
        row_filters=oecd_totdon.OECD_TOTDON_ROW_FILTERS,
    )
    assert drop_report["NonCountryCodes"] == {"DAC": 1, "4EU001": 1}
    assert drop_report["FilteredRows"]["PRICE_BASE"] == 1
    assert drop_report["MissingValueRows"] == 1
    assert drop_report["NonAnnualPeriodRows"] == 1
    total_dropped = (
        sum(drop_report["FilteredRows"].values())
        + sum(drop_report["NonCountryCodes"].values())
        + drop_report["MissingValueRows"]
        + drop_report["NonAnnualPeriodRows"]
    )
    assert len(cleaned) + total_dropped == len(rows)


def test_should_keep_negative_net_oda_and_drop_aggregates_when_cleaning_tonrec():
    rows = parse_oecd_sdmx_csv(DAC2A_FIXTURE_CSV)
    cleaned, drop_report = clean_oecd_sdmx_observations(
        rows, "OECD_TONREC", oecd_tonrec.OECD_TONREC_COUNTRY_CODE_COLUMN,
        oecd_tonrec.describe_oecd_tonrec_row, row_filters=oecd_tonrec.OECD_TONREC_ROW_FILTERS,
    )
    by_country = {obs["CountryCode"]: obs for obs in cleaned}
    assert set(by_country) == {"IND", "CHN"}
    assert by_country["CHN"]["Value"] == -570.617053
    assert by_country["CHN"]["Year"] == 2020
    assert by_country["IND"]["Value"] == 3174.348367
    assert drop_report["NonCountryCodes"] == {"DPGC": 1, "LDC": 1, "XKV": 1}
    # the DAC-only donor row for ETH must not leak into the ALLD series
    assert drop_report["FilteredRows"]["DONOR"] == 1
    for obs in cleaned:
        assert set(obs) == CLEAN_OBSERVATION_KEYS
        assert obs["Unit"] == "US dollar, Millions, Current prices"
        assert obs["Description"] == (
            "Official development assistance (ODA), disbursements: Disbursements from "
            "Official donors to recipient (DAC2A: Aid (ODA) disbursements to countries and regions)"
        )


def test_should_accept_static_description_and_unit_strings_when_cleaning():
    rows = parse_oecd_sdmx_csv(DAC2A_FIXTURE_CSV)
    cleaned, _ = clean_oecd_sdmx_observations(rows, "X_TEST", "RECIPIENT", "desc", unit="u")
    assert cleaned and all(obs["Description"] == "desc" and obs["Unit"] == "u" for obs in cleaned)


def test_should_return_empty_and_zero_counts_when_no_rows():
    cleaned, drop_report = clean_oecd_sdmx_observations([], "X_TEST", "DONOR", "desc")
    assert cleaned == []
    assert drop_report == {
        "FilteredRows": {}, "NonCountryCodes": {}, "MissingValueRows": 0, "NonAnnualPeriodRows": 0,
    }


# --------------------------------------------------------------------------
# Dataset modules: registry, source stamp vs documentation
# --------------------------------------------------------------------------

def test_should_register_collectors_and_cleaners_when_oecd_modules_import():
    from sspi_flask_app.api.core.datasets import dataset_collector_registry, dataset_cleaner_registry
    assert "OECD_TOTDON" in dataset_collector_registry
    assert "OECD_TONREC" in dataset_collector_registry
    assert "OECD_TOTDON" in dataset_cleaner_registry
    assert "OECD_TONREC" in dataset_cleaner_registry


@pytest.mark.parametrize(
    "dataset_folder, collector, dataflow, key, query_code",
    [
        (
            "oecd_totdon", oecd_totdon.collect_oecd_totdon,
            "OECD.DCD.FSD,DSD_DAC1@DF_DAC1", "._Z.1010._Z.1140.USD.V",
            "DSD_DAC1@DF_DAC1(._Z.1010._Z.1140.USD.V)",
        ),
        (
            "oecd_tonrec", oecd_tonrec.collect_oecd_tonrec,
            "OECD.DCD.FSD,DSD_DAC2@DF_DAC2A", "ALLD..206.USD.V",
            "DSD_DAC2@DF_DAC2A(ALLD..206.USD.V)",
        ),
    ],
)
def test_should_stamp_source_info_matching_doc_source_when_collected(
    monkeypatch, dataset_folder, collector, dataflow, key, query_code
):
    """Every key in the doc's Source becomes a Mongo filter against the raw
    document's Source, so the doc Source must be an exact subset of the stamp."""
    captured = _install_fakes(monkeypatch)
    list(collector(username="tester"))
    assert captured["requests"][0]["url"].startswith(
        f"https://sdmx.oecd.org/public/rest/data/{dataflow}/{key}?"
    )
    stamped = captured["inserts"][0]["source_info"]
    assert stamped["OrganizationSeriesCode"] == dataflow
    assert stamped["QueryCode"] == query_code
    doc_source = _load_doc_source("oecd", dataset_folder)
    assert set(doc_source.keys()) == {"OrganizationCode", "QueryCode"}
    for doc_key, doc_value in doc_source.items():
        assert doc_value is not None, f"doc Source.{doc_key} must not be null"
        assert stamped[doc_key] == doc_value, (
            f"doc Source.{doc_key}={doc_value!r} but collector stamps {stamped[doc_key]!r}"
        )


@pytest.mark.parametrize("dataset_folder, dataset_code", [
    ("oecd_totdon", "OECD_TOTDON"), ("oecd_tonrec", "OECD_TONREC"),
])
def test_should_declare_required_frontmatter_when_documenting_dataset(dataset_folder, dataset_code):
    doc_path = os.path.join(REPO_ROOT, "datasets", "oecd", dataset_folder, "documentation.md")
    metadata = frontmatter.load(doc_path).metadata
    assert metadata["DatasetCode"] == dataset_code
    assert metadata["DatasetType"] == "Intermediate"
    assert metadata["DatasetProcessorFile"] == f"sspi_flask_app/api/core/datasets/oecd/{dataset_folder}.py"
    assert metadata["Unit"].strip() == "US dollar, Millions, Current prices"
    for field in ("DatasetName", "Description", "Source"):
        assert metadata[field]
