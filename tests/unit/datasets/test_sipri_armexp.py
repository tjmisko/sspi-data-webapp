"""
Unit tests for the SIPRI_ARMEXP cleaner. The raw, clean and metadata
collections are monkeypatched so nothing reads or writes the database.
"""
import pytest

import sspi_flask_app.api.core.datasets.sipri.sipri_armexp as sipri_armexp
from sspi_flask_app.api.core.datasets.sipri.sipri_armexp import (
    SIPRI_ARMEXP_ZERO_NOTE,
    parse_sipri_armexp_csv,
    parse_sipri_tiv_cell,
    sipri_armexp_reported_years,
    read_sipri_armexp_table,
    sipri_exporter_country_code,
    zero_fill_absent_exporters,
)

# Mirrors the SIPRI Trade Register export: a preamble, then the exporter table
# with year columns, summary columns, a blank unpublished year (2025) and a
# "Total world export" row. Cells use SIPRI conventions: "0 " for a delivery
# below 0.5 million TIV, an empty cell for no identified delivery.
SIPRI_PREAMBLE = (
    "Volume of transfers of major arms\n"
    "Figures are in millions of SIPRI trend-indicator values (TIVs).\n"
    "A '0' indicates that the volume of deliveries is between 0 and 0.5 million SIPRI TIV. "
    "An empty field indicates that no deliveries have been identified.\n"
    "\n"
    "Source: SIPRI Arms Transfers Database (c) SIPRI.\n"
)
SIPRI_HEADER = "Exports by,2021,2022,2023,2024,2025,2021-2025,Percentage,Sum total years,Percentage of total\n"
SIPRI_ROWS = (
    "United States,9000,15351,11102,13512,,48965,40%,48965,40%\n"
    "UAE,58,18,,117,,193,0.2%,193,0.2%\n"
    "South Korea,1000,,0 ,500,,1500,1%,1500,1%\n"
    "North Korea,,,,1,,1,0.0%,1,0.0%\n"
    "Brunei,,24,,,,24,0.0%,24,0.0%\n"
    "Bosnia-Herzegovina,,,2,7,,9,0.0%,9,0.0%\n"
    "Soviet Union,,,,,,0,0.0%,0,0.0%\n"
    "European Union**,,,0 ,,,0 ,0.0%,0 ,0.0%\n"
    "Total world export,26263,33871,29683,28938,,118755,100%,118755,\n"
)
SIPRI_CSV = SIPRI_PREAMBLE + SIPRI_HEADER + SIPRI_ROWS
REPORTED_YEARS = [2021, 2022, 2023, 2024]


def values_by_cell(docs):
    return {(doc["CountryCode"], doc["Year"]): doc["Value"] for doc in docs}


def docs_for(docs, country_code):
    return sorted(
        (doc for doc in docs if doc["CountryCode"] == country_code),
        key=lambda doc: doc["Year"],
    )


@pytest.mark.parametrize(
    "label, expected_code",
    [
        ("UAE", "ARE"),
        (" UAE ", "ARE"),
        ("uae", "ARE"),
        ("United Arab Emirates", "ARE"),
        ("Brunei", "BRN"),
        ("Bosnia-Herzegovina", "BIH"),
        ("South Korea", "KOR"),
        ("North Korea", "PRK"),
        ("DR Congo", "COD"),
        ("Turkiye", "TUR"),
        ("Russia", "RUS"),
        ("United States", "USA"),
        ("Viet Nam", "VNM"),
    ],
)
def test_should_map_sipri_label_to_iso3_when_label_is_known(label, expected_code):
    assert sipri_exporter_country_code(label) == expected_code


@pytest.mark.parametrize(
    "label",
    [
        "Soviet Union",
        "Total world export",
        "European Union**",
        "unknown supplier(s)",
        "Mujahedin (Afghanistan)*",
        "Atlantis",
        "XYZ",
        "",
        "   ",
        None,
        float("nan"),
    ],
)
def test_should_return_none_when_label_is_not_an_iso_country(label):
    assert sipri_exporter_country_code(label) is None


@pytest.mark.parametrize(
    "cell, expected",
    [
        ("", (0.0, True)),
        ("   ", (0.0, True)),
        (None, (0.0, True)),
        (float("nan"), (0.0, True)),
        ("0 ", (0.0, False)),
        ("0", (0.0, False)),
        ("117", (117.0, False)),
        (" 12.5 ", (12.5, False)),
    ],
)
def test_should_read_blank_as_zero_and_keep_numbers_when_parsing_tiv_cell(cell, expected):
    assert parse_sipri_tiv_cell(cell) == expected


def test_should_raise_when_tiv_cell_is_non_numeric_text():
    with pytest.raises(ValueError):
        parse_sipri_tiv_cell("n/a")


def test_should_emit_are_rows_and_no_uae_rows_when_table_labels_uae():
    docs = parse_sipri_armexp_csv(SIPRI_CSV)
    assert not [doc for doc in docs if doc["CountryCode"] == "UAE"]
    are_values = {doc["Year"]: doc["Value"] for doc in docs_for(docs, "ARE")}
    assert are_values == {2021: 58.0, 2022: 18.0, 2023: 0.0, 2024: 117.0}


def test_should_store_blank_cell_as_observed_zero_with_note_when_no_delivery_identified():
    docs = parse_sipri_armexp_csv(SIPRI_CSV)
    are_2023 = next(doc for doc in docs_for(docs, "ARE") if doc["Year"] == 2023)
    assert are_2023["Value"] == 0.0
    assert are_2023["Note"] == SIPRI_ARMEXP_ZERO_NOTE
    assert "Imputed" not in are_2023
    assert are_2023["Unit"] == "Millions SIPRI TIV"


def test_should_keep_sipri_zero_without_note_when_cell_reads_zero_space():
    docs = parse_sipri_armexp_csv(SIPRI_CSV)
    kor_2023 = next(doc for doc in docs_for(docs, "KOR") if doc["Year"] == 2023)
    assert kor_2023["Value"] == 0.0
    assert "Note" not in kor_2023


def test_should_not_zero_fill_unpublished_year_when_world_total_is_blank():
    table = read_sipri_armexp_table(SIPRI_CSV)
    assert sipri_armexp_reported_years(table) == REPORTED_YEARS
    docs = parse_sipri_armexp_csv(SIPRI_CSV)
    assert {doc["Year"] for doc in docs} == set(REPORTED_YEARS)


def test_should_emit_one_row_per_exporter_year_when_table_is_parsed():
    docs = parse_sipri_armexp_csv(SIPRI_CSV)
    country_codes = {doc["CountryCode"] for doc in docs}
    assert country_codes == {"USA", "ARE", "KOR", "PRK", "BRN", "BIH"}
    assert len(docs) == len(country_codes) * len(REPORTED_YEARS)
    assert len(values_by_cell(docs)) == len(docs)


def test_should_drop_non_state_and_summary_rows_when_parsing():
    docs = parse_sipri_armexp_csv(SIPRI_CSV)
    assert all(len(doc["CountryCode"]) == 3 for doc in docs)
    assert all(doc["CountryCode"].isupper() for doc in docs)


def test_should_return_empty_list_when_header_row_is_missing():
    assert parse_sipri_armexp_csv(SIPRI_PREAMBLE) == []
    assert parse_sipri_armexp_csv("") == []


def test_should_log_and_drop_row_when_label_is_unmappable(caplog):
    csv_string = SIPRI_HEADER + "Atlantis,5,,,,,5,0%,5,0%\n" + SIPRI_ROWS
    with caplog.at_level("WARNING", logger=sipri_armexp.__name__):
        docs = parse_sipri_armexp_csv(csv_string)
    assert "Atlantis" in caplog.text
    assert "Soviet Union" not in caplog.text
    assert {doc["CountryCode"] for doc in docs} == {"USA", "ARE", "KOR", "PRK", "BRN", "BIH"}


def test_should_keep_first_row_when_two_labels_map_to_same_country(caplog):
    csv_string = SIPRI_HEADER + SIPRI_ROWS + "United Arab Emirates,1,1,1,1,,4,0%,4,0%\n"
    with caplog.at_level("WARNING", logger=sipri_armexp.__name__):
        docs = parse_sipri_armexp_csv(csv_string)
    assert len(docs_for(docs, "ARE")) == len(REPORTED_YEARS)
    assert docs_for(docs, "ARE")[0]["Value"] == 58.0
    assert "duplicate exporter row for ARE" in caplog.text


def test_should_drop_only_the_bad_cell_when_a_cell_is_non_numeric():
    csv_string = SIPRI_HEADER + "France,1,n/a,3,4,,8,1%,8,1%\n" + SIPRI_ROWS
    docs = parse_sipri_armexp_csv(csv_string)
    assert {doc["Year"] for doc in docs_for(docs, "FRA")} == {2021, 2023, 2024}


def test_should_treat_any_value_as_reported_year_when_world_total_row_is_absent():
    csv_string = SIPRI_HEADER + "France,1,,,,,1,1%,1,1%\nUAE,,,3,,,3,0%,3,0%\n"
    docs = parse_sipri_armexp_csv(csv_string)
    assert {doc["Year"] for doc in docs} == {2021, 2023}
    assert values_by_cell(docs)[("FRA", 2023)] == 0.0


def test_should_add_zero_series_for_every_reported_year_when_sspi_country_is_absent():
    docs = parse_sipri_armexp_csv(SIPRI_CSV)
    filled = zero_fill_absent_exporters(docs, ["USA", "ARE", "BGD", "IRQ"])
    for country_code in ("BGD", "IRQ"):
        series = docs_for(filled, country_code)
        assert [doc["Year"] for doc in series] == REPORTED_YEARS
        assert all(doc["Value"] == 0.0 for doc in series)
        assert all(doc["Note"] == SIPRI_ARMEXP_ZERO_NOTE for doc in series)
        assert all(doc["DatasetCode"] == "SIPRI_ARMEXP" for doc in series)
    assert len(filled) == len(docs) + 2 * len(REPORTED_YEARS)


def test_should_not_duplicate_rows_when_sspi_country_is_already_in_table():
    docs = parse_sipri_armexp_csv(SIPRI_CSV)
    filled = zero_fill_absent_exporters(docs, ["USA", "ARE", "KOR"])
    assert filled == docs


def test_should_add_nothing_when_table_has_no_reported_years():
    assert zero_fill_absent_exporters([], ["BGD"]) == []


def test_should_replace_own_dataset_with_zero_filled_panel_when_cleaner_runs(monkeypatch):
    calls = {"delete": [], "insert": [], "range": []}

    class FakeCleanCollection:
        def delete_many(self, query):
            calls["delete"].append(query)

        def insert_many(self, docs):
            calls["insert"].append(list(docs))

    class FakeRawCollection:
        def fetch_raw_data(self, source_info):
            return [{"Raw": {"result": SIPRI_CSV}}]

    class FakeMetadata:
        def get_source_info(self, dataset_code):
            return {"OrganizationCode": "SIPRI", "QueryCode": "armstransfers"}

        def country_group(self, group_name):
            assert group_name == "SSPI67"
            return ["USA", "ARE", "KOR", "BGD", "IRQ"]

        def record_dataset_range(self, cleaned, dataset_code):
            calls["range"].append((len(cleaned), dataset_code))

    real_clean_collection = sipri_armexp.sspi_clean_api_data
    monkeypatch.setattr(sipri_armexp, "sspi_clean_api_data", FakeCleanCollection())
    monkeypatch.setattr(sipri_armexp, "sspi_raw_api_data", FakeRawCollection())
    monkeypatch.setattr(sipri_armexp, "sspi_metadata", FakeMetadata())

    result = sipri_armexp.clean_sipri_armexp()

    assert calls["delete"] == [{"DatasetCode": "SIPRI_ARMEXP"}]
    assert len(calls["insert"]) == 1
    inserted = calls["insert"][0]
    real_clean_collection.validate_documents_format(inserted)
    expected_rows = (6 + 2) * len(REPORTED_YEARS)
    assert len(inserted) == expected_rows
    assert calls["range"] == [(expected_rows, "SIPRI_ARMEXP")]
    assert result == inserted
    cells = values_by_cell(inserted)
    for year in REPORTED_YEARS:
        assert cells[("BGD", year)] == 0.0
        assert cells[("IRQ", year)] == 0.0
    assert ("UAE", 2021) not in cells


def test_should_insert_nothing_when_raw_data_is_missing(monkeypatch):
    calls = {"insert": 0}

    class FakeCleanCollection:
        def delete_many(self, query):
            pass

        def insert_many(self, docs):
            calls["insert"] += 1

    class FakeRawCollection:
        def fetch_raw_data(self, source_info):
            return []

    class FakeMetadata:
        def get_source_info(self, dataset_code):
            return {}

    monkeypatch.setattr(sipri_armexp, "sspi_clean_api_data", FakeCleanCollection())
    monkeypatch.setattr(sipri_armexp, "sspi_raw_api_data", FakeRawCollection())
    monkeypatch.setattr(sipri_armexp, "sspi_metadata", FakeMetadata())

    assert sipri_armexp.clean_sipri_armexp() == []
    assert calls["insert"] == 0
