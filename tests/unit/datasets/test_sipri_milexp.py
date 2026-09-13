"""
Unit tests for the SIPRI_MILEXP cleaner.

The fixture mirrors the "Share of GDP" section of the raw document stored by
collect_sipri_milexp (SIPRI Milex excel-export preview, 1990-2024 request):
title rows, a header of "Country", "Notes", "1990.0" ... "2024.0", one-cell
region rows, footnote markers in the Notes column, ". ." rendered as "...",
"xxx" for years before independence, and shares stored as fractions of GDP.
Every database call is monkeypatched.
"""
import pytest

import sspi_flask_app.api.core.datasets.sipri.sipri_milexp as milexp
from sspi_flask_app.api.core.datasets import dataset_cleaner_registry


FIXTURE_YEARS = list(range(1990, 2025))


def make_header_row(years=FIXTURE_YEARS):
    return ["Country", "Notes"] + [f"{year}.0" for year in years]


def make_country_row(country_name, notes, values_by_year, years=FIXTURE_YEARS, filler="..."):
    return [country_name, notes] + [values_by_year.get(year, filler) for year in years]


def make_share_of_gdp_rows():
    return [
        ["Military expenditure by country as percentage of gross domestic product, 1990-2024     © SIPRI 2024"],
        ["Countries are grouped by region and subregion"],
        ["Figures in blue are SIPRI estimates. Figures in red indicate highly uncertain data."],
        ["\". .\" = data unavailable. \"xxx\" = country did not exist or was not independent during all or part of the year in question."],
        [""],
        make_header_row(),
        ["Africa"],
        ["North Africa"],
        make_country_row("Algeria", "§", {1990: "0.014610705859434187", 2024: "0.08"}),
        make_country_row("Congo, DR", "", {1990: "0.02", 2000: "0.01"}),
        make_country_row("Cote d'Ivoire", "", {2020: "0.009631194706426356"}),
        make_country_row("South Sudan", "", {2011: "0.05"}, filler="xxx"),
        ["North America"],
        make_country_row("United States of America", "", {
            1990: "0.0512",
            2000: "0.0295",
            2012: "0.044617099699335",
            2013: "0.0399",
            2023: "0.033044416375979976",
            2024: "0.03419216532280439",
        }),
        ["East Asia"],
        make_country_row("Korea, North", "", {}),
        make_country_row("Korea, South", "", {2023: "0.02576425603950086"}),
        ["Eastern Europe"],
        make_country_row("German Democratic Republic", "†¶", {1990: "0.07"}, filler="xxx"),
        make_country_row("USSR", "", {1990: "0.12"}, filler="xxx"),
        make_country_row("Ukraine", "‖", {
            2014: "0.0303",
            2023: "0.3652817250772237",
            2024: "0.3448152977018923",
        }),
        ["Middle East"],
        make_country_row("Kuwait", "", {
            1990: "0.48517267267267267",
            1991: "1.173498232086904",
            1992: "0.3178602444709137",
            2002: "0.07399194070290187",
        }),
        make_country_row("European Union", "", {2022: "0.013"}),
    ]


def make_raw(rows=None):
    return {
        "Data": [
            {"DataType": "Front page", "Rows": [["SIPRI Military Expenditure Database"]]},
            {"DataType": "Local currency calendar years", "Rows": [make_header_row(), make_country_row("Kuwait", "", {1991: "5000"})]},
            {"DataType": "Share of GDP", "Rows": make_share_of_gdp_rows() if rows is None else rows},
            {"DataType": "Footnotes", "Rows": [["†", "Figures for these countries do not include military pensions"]]},
        ]
    }


def index_by_country_year(observations):
    return {(obs["CountryCode"], obs["Year"]): obs["Value"] for obs in observations}


def test_should_place_usa_2023_share_on_2023_when_sheet_starts_in_1990_with_notes_column():
    observations = milexp.parse_sipri_milexp_share_of_gdp(make_raw())
    values = index_by_country_year(observations)
    assert values[("USA", 2023)] == pytest.approx(3.3044416375979976)
    assert values[("USA", 2012)] == pytest.approx(4.4617099699335)
    assert values[("USA", 2024)] == pytest.approx(3.419216532280439)
    assert values[("USA", 1990)] == pytest.approx(5.12)


def test_should_load_2014_through_2024_when_header_runs_to_2024():
    values = index_by_country_year(milexp.parse_sipri_milexp_share_of_gdp(make_raw()))
    assert values[("UKR", 2014)] == pytest.approx(3.03)
    assert values[("UKR", 2023)] == pytest.approx(36.52817250772237)
    assert values[("UKR", 2024)] == pytest.approx(34.48152977018923)
    assert values[("DZA", 2024)] == pytest.approx(8.0)


def test_should_scale_shares_above_one_when_value_exceeds_one_hundred_percent():
    values = index_by_country_year(milexp.parse_sipri_milexp_share_of_gdp(make_raw()))
    assert values[("KWT", 1991)] == pytest.approx(117.3498232086904)
    assert values[("KWT", 1990)] == pytest.approx(48.517267267267267)
    assert values[("KWT", 2002)] == pytest.approx(7.399194070290187)


def test_should_not_emit_a_value_for_notes_column_when_notes_cell_is_blank_or_marked():
    observations = milexp.parse_sipri_milexp_share_of_gdp(make_raw())
    values = index_by_country_year(observations)
    assert ("USA", 2000) in values
    assert values[("USA", 2000)] == pytest.approx(2.95)
    assert ("DZA", 2000) not in values
    assert {obs["Year"] for obs in observations} <= set(FIXTURE_YEARS)


def test_should_skip_missing_markers_when_cells_are_ellipsis_xxx_or_blank():
    values = index_by_country_year(milexp.parse_sipri_milexp_share_of_gdp(make_raw()))
    assert [key for key in values if key[0] == "SSD"] == [("SSD", 2011)]
    assert [key for key in values if key[0] == "PRK"] == []
    assert [key for key in values if key[0] == "KOR"] == [("KOR", 2023)]


def test_should_drop_historical_states_and_aggregates_when_rows_have_no_current_iso_code():
    observations = milexp.parse_sipri_milexp_share_of_gdp(make_raw())
    values = index_by_country_year(observations)
    # get_country_code maps "German Democratic Republic" to COD; the DR Congo
    # 1990 value must come from the Congo, DR row alone.
    assert values[("COD", 1990)] == pytest.approx(2.0)
    assert len([obs for obs in observations if obs["CountryCode"] == "COD"]) == 2
    country_codes = {obs["CountryCode"] for obs in observations}
    assert country_codes == {"DZA", "COD", "CIV", "SSD", "USA", "KOR", "UKR", "KWT"}


def test_should_attach_unit_and_dataset_code_when_emitting_observations():
    observations = milexp.parse_sipri_milexp_share_of_gdp(make_raw())
    assert observations
    for obs in observations:
        assert obs["DatasetCode"] == "SIPRI_MILEXP"
        assert obs["Unit"] == "Percent of GDP"
        assert isinstance(obs["Year"], int)
        assert isinstance(obs["Value"], float)


def test_should_map_years_by_label_when_header_starts_later_and_has_extra_non_year_columns():
    header = ["Country", "Notes", "2021", "Footnote", 2022.0, "2023.0 "]
    row = ["United States of America", "", "0.03", "†", "0.031", "0.033"]
    raw = make_raw(rows=[["title"], header, ["North America"], row])
    values = index_by_country_year(milexp.parse_sipri_milexp_share_of_gdp(raw))
    assert values == {
        ("USA", 2021): pytest.approx(3.0),
        ("USA", 2022): pytest.approx(3.1),
        ("USA", 2023): pytest.approx(3.3),
    }


@pytest.mark.parametrize("raw_value", [
    None, "", "   ", "...", ". .", "..", "xxx", "n/a", "0.03[a]", "0.03†",
    "nan", "inf", True, float("nan"),
])
def test_should_treat_cell_as_missing_when_value_is_marker_footnoted_or_not_finite(raw_value):
    assert milexp.parse_sipri_share_value(raw_value) is None


@pytest.mark.parametrize("raw_value,expected", [
    ("0.033", 0.033), (" 0.033 ", 0.033), (0.033, 0.033), (1, 1.0), ("0", 0.0),
])
def test_should_parse_share_when_value_is_numeric_string_or_number(raw_value, expected):
    assert milexp.parse_sipri_share_value(raw_value) == pytest.approx(expected)


@pytest.mark.parametrize("label,expected", [
    ("1990.0", 1990), ("2024", 2024), (2023, 2023), (2022.0, 2022),
    ("Notes", None), ("Country", None), ("", None), (None, None),
    ("1990.5", None), ("12", None), (True, None),
])
def test_should_parse_year_only_when_header_label_is_an_integral_year(label, expected):
    assert milexp.parse_sipri_year_label(label) == expected


def test_should_keep_short_rows_when_row_ends_before_last_year_column():
    header = make_header_row([2022, 2023, 2024])
    raw = make_raw(rows=[header, ["Kuwait", "", "0.05"]])
    assert index_by_country_year(milexp.parse_sipri_milexp_share_of_gdp(raw)) == {
        ("KWT", 2022): pytest.approx(5.0),
    }


def test_should_keep_first_value_when_two_rows_resolve_to_same_country_year():
    header = make_header_row([2023])
    raw = make_raw(rows=[header, ["Korea, South", "", "0.025"], ["South Korea", "", "0.9"]])
    assert index_by_country_year(milexp.parse_sipri_milexp_share_of_gdp(raw)) == {
        ("KOR", 2023): pytest.approx(2.5),
    }


def test_should_raise_when_share_of_gdp_section_is_absent():
    with pytest.raises(ValueError, match="Share of GDP"):
        milexp.parse_sipri_milexp_share_of_gdp({"Data": [{"DataType": "Footnotes", "Rows": []}]})


def test_should_raise_when_sheet_has_no_header_row():
    raw = make_raw(rows=[["title"], make_country_row("Kuwait", "", {1991: "1.17"})])
    with pytest.raises(ValueError, match="header"):
        milexp.parse_sipri_milexp_share_of_gdp(raw)


def test_should_raise_when_header_row_has_no_year_columns():
    raw = make_raw(rows=[["Country", "Notes", "Region"], ["Kuwait", "", "0.05"]])
    with pytest.raises(ValueError, match="year columns"):
        milexp.parse_sipri_milexp_share_of_gdp(raw)


def test_should_raise_when_shares_already_look_like_percentages():
    header = make_header_row([2022, 2023])
    rows = [header, ["United States of America", "", "3.4", "3.3"], ["Kuwait", "", "4.8", "4.9"]]
    with pytest.raises(ValueError, match="percentages"):
        milexp.parse_sipri_milexp_share_of_gdp(make_raw(rows=rows))


def test_should_return_empty_list_when_every_cell_is_missing():
    header = make_header_row([2022, 2023])
    raw = make_raw(rows=[header, ["Kuwait", "", "...", "xxx"]])
    assert milexp.parse_sipri_milexp_share_of_gdp(raw) == []


def run_cleaner_with_fakes(monkeypatch, raw):
    captured = {"deleted": [], "inserted": None}
    monkeypatch.setattr(milexp.sspi_metadata, "get_source_info", lambda code: {"OrganizationCode": "SIPRI", "QueryCode": "milex"})
    monkeypatch.setattr(milexp.sspi_raw_api_data, "fetch_raw_data", lambda source_info: [{"Raw": raw}])
    monkeypatch.setattr(milexp.sspi_clean_api_data, "delete_many", lambda query: captured["deleted"].append(query))

    def _fake_insert_many(docs):
        captured["inserted"] = list(docs)

    monkeypatch.setattr(milexp.sspi_clean_api_data, "insert_many", _fake_insert_many)
    return captured


def test_should_replace_clean_rows_with_label_mapped_years_when_cleaner_runs(monkeypatch):
    captured = run_cleaner_with_fakes(monkeypatch, make_raw())
    result = dataset_cleaner_registry["SIPRI_MILEXP"]()
    assert captured["deleted"] == [{"DatasetCode": "SIPRI_MILEXP"}]
    assert captured["inserted"] == result
    assert index_by_country_year(result)[("USA", 2023)] == pytest.approx(3.3044416375979976)


def test_should_leave_clean_rows_untouched_when_raw_sheet_yields_nothing(monkeypatch):
    header = make_header_row([2023])
    captured = run_cleaner_with_fakes(monkeypatch, make_raw(rows=[header, ["Kuwait", "", "..."]]))
    with pytest.raises(ValueError, match="no observations"):
        milexp.clean_sipri_milexp()
    assert captured["deleted"] == []
    assert captured["inserted"] is None
