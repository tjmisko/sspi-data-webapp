"""
Unit tests for ``clean_wb_data`` in ``sspi_flask_app.api.datasource.worldbank``.

These are pure: they build raw World Bank rows in-memory and never touch the
network or the database. They guard the two data-integrity properties fixed in
issue I-17: zero is a legitimate observation and must be kept, and every
dropped row must be counted and reported in a single log line.
"""
import logging

import pytest

from sspi_flask_app.api.datasource.worldbank import clean_wb_data


DATASET_CODE = "WB_TESTDS"
UNIT = "% of population"
INDICATOR = {"id": "IT.NET.USER.ZS", "value": "Individuals using the Internet (% of population)"}


def make_raw_entry(iso3, country_id, country_name, year, value):
    return {
        "Raw": {
            "indicator": INDICATOR,
            "country": {"id": country_id, "value": country_name},
            "countryiso3code": iso3,
            "date": str(year),
            "value": value,
            "unit": "",
            "obs_status": "",
            "decimal": 1,
        }
    }


@pytest.mark.parametrize("zero_value", [0, 0.0, "0", "0.0"])
def test_should_keep_observation_when_value_is_zero(zero_value):
    raw = [make_raw_entry("USA", "US", "United States", 2001, zero_value)]
    cleaned = clean_wb_data(raw, DATASET_CODE, UNIT)
    assert len(cleaned) == 1
    assert cleaned[0]["CountryCode"] == "USA"
    assert cleaned[0]["Year"] == 2001
    assert cleaned[0]["Value"] == 0.0
    assert isinstance(cleaned[0]["Value"], float)


def test_should_keep_zero_alongside_nonzero_values_when_mixed():
    raw = [
        make_raw_entry("USA", "US", "United States", 2000, 0),
        make_raw_entry("FRA", "FR", "France", 2000, 14.3),
        make_raw_entry("DEU", "DE", "Germany", 2000, 0.0),
    ]
    cleaned = clean_wb_data(raw, DATASET_CODE, UNIT)
    assert sorted(obs["CountryCode"] for obs in cleaned) == ["DEU", "FRA", "USA"]
    assert {obs["CountryCode"]: obs["Value"] for obs in cleaned} == {
        "USA": 0.0, "FRA": 14.3, "DEU": 0.0,
    }


@pytest.mark.parametrize("missing_value", [None, "NaN", ""])
def test_should_drop_observation_when_value_is_missing_sentinel(missing_value):
    raw = [
        make_raw_entry("USA", "US", "United States", 2001, missing_value),
        make_raw_entry("FRA", "FR", "France", 2001, 12.5),
    ]
    cleaned = clean_wb_data(raw, DATASET_CODE, UNIT)
    assert [obs["CountryCode"] for obs in cleaned] == ["FRA"]


def test_should_drop_observation_when_value_is_non_numeric_string():
    raw = [
        make_raw_entry("USA", "US", "United States", 2001, "not-a-number"),
        make_raw_entry("FRA", "FR", "France", 2001, "7.25"),
    ]
    cleaned = clean_wb_data(raw, DATASET_CODE, UNIT)
    assert [obs["CountryCode"] for obs in cleaned] == ["FRA"]
    assert cleaned[0]["Value"] == 7.25


def test_should_drop_aggregate_rows_when_iso3_is_blank_or_not_a_country():
    raw = [
        make_raw_entry("USA", "US", "United States", 2001, 1.0),
        # World Bank aggregates carry a blank iso3 and a WB-internal country id
        make_raw_entry("", "1W", "World", 2001, 2.0),
        make_raw_entry("", "XD", "High income", 2001, 3.0),
        # Some aggregates carry a 3-letter code that is not an ISO alpha-3 country
        make_raw_entry("OED", "OE", "OECD members", 2001, 4.0),
        make_raw_entry("EUU", "EU", "European Union", 2001, 5.0),
    ]
    cleaned = clean_wb_data(raw, DATASET_CODE, UNIT)
    assert [obs["CountryCode"] for obs in cleaned] == ["USA"]


def test_should_fall_back_to_country_id_when_iso3_blank_but_id_is_alpha3():
    raw = [make_raw_entry("", "CAN", "Canada", 2005, 9.0)]
    cleaned = clean_wb_data(raw, DATASET_CODE, UNIT)
    assert len(cleaned) == 1
    assert cleaned[0]["CountryCode"] == "CAN"


def test_should_drop_row_when_iso3_blank_and_country_key_missing():
    entry = make_raw_entry("", "US", "United States", 2005, 9.0)
    del entry["Raw"]["country"]
    cleaned = clean_wb_data([entry], DATASET_CODE, UNIT)
    assert cleaned == []


def test_should_emit_clean_observation_shape_when_row_is_valid():
    raw = [make_raw_entry("USA", "US", "United States", 2010, 71.69)]
    cleaned = clean_wb_data(raw, DATASET_CODE, UNIT)
    assert cleaned == [{
        "CountryCode": "USA",
        "DatasetCode": DATASET_CODE,
        "Description": INDICATOR["value"],
        "Year": 2010,
        "Unit": UNIT,
        "Value": 71.69,
    }]


def test_should_log_one_summary_line_with_drop_counts_when_rows_are_dropped(caplog):
    raw = [
        make_raw_entry("USA", "US", "United States", 2001, 0),
        make_raw_entry("FRA", "FR", "France", 2001, 3.5),
        make_raw_entry("", "1W", "World", 2001, 2.0),
        make_raw_entry("OED", "OE", "OECD members", 2001, 4.0),
        make_raw_entry("DEU", "DE", "Germany", 2001, None),
        make_raw_entry("ITA", "IT", "Italy", 2001, "NaN"),
        make_raw_entry("ESP", "ES", "Spain", 2001, ""),
        make_raw_entry("GBR", "GB", "United Kingdom", 2001, "n/a"),
    ]
    with caplog.at_level(logging.INFO, logger="sspi_flask_app.api.datasource.worldbank"):
        cleaned = clean_wb_data(raw, DATASET_CODE, UNIT)
    assert sorted(obs["CountryCode"] for obs in cleaned) == ["FRA", "USA"]
    summary_records = [
        record for record in caplog.records
        if record.name == "sspi_flask_app.api.datasource.worldbank"
    ]
    assert len(summary_records) == 1
    message = summary_records[0].getMessage()
    assert DATASET_CODE in message
    assert "kept 2 of 8" in message
    assert "2 non-country" in message
    assert "3 missing-value" in message
    assert "1 non-numeric" in message


def test_should_log_zero_drops_when_every_row_is_kept(caplog):
    raw = [
        make_raw_entry("USA", "US", "United States", 2001, 0),
        make_raw_entry("FRA", "FR", "France", 2001, 3.5),
    ]
    with caplog.at_level(logging.INFO, logger="sspi_flask_app.api.datasource.worldbank"):
        cleaned = clean_wb_data(raw, DATASET_CODE, UNIT)
    assert len(cleaned) == 2
    message = caplog.records[-1].getMessage()
    assert "kept 2 of 2" in message
    assert "0 non-country" in message
    assert "0 missing-value" in message
    assert "0 non-numeric" in message


def test_should_return_empty_list_when_raw_data_is_empty():
    assert clean_wb_data([], DATASET_CODE, UNIT) == []


def test_should_accept_iterator_input_when_raw_data_is_not_a_list():
    raw = iter([
        make_raw_entry("USA", "US", "United States", 2001, 0),
        make_raw_entry("FRA", "FR", "France", 2001, 1.5),
    ])
    cleaned = clean_wb_data(raw, DATASET_CODE, UNIT)
    assert [obs["CountryCode"] for obs in cleaned] == ["USA", "FRA"]
