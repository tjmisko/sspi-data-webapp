###############################################################
# Documentation: datasets/sipri/sipri_milexp/documentation.md #
###############################################################
import logging
import math
import statistics
import requests
from sspi_flask_app.api.core.datasets import dataset_collector, dataset_cleaner
from sspi_flask_app.models.database import sspi_raw_api_data, sspi_clean_api_data, sspi_metadata
from sspi_flask_app.api.resources.utilities import get_country_code

@dataset_collector("SIPRI_MILEXP")
def collect_sipri_milexp(**kwargs):
    source_info = sspi_metadata.get_source_info("SIPRI_MILEXP")
    log = logging.getLogger(__name__)
    url = "https://backend.sipri.org/api/p/excel-export/preview"
    msg = f"Requesting MILEXP data from URL: {url}\n"
    yield msg
    log.info(msg)
    headers = {
        "Content-Type": "application/json",
        "Origin": "https://milex.sipri.org",
        "Referer": "https://milex.sipri.org/",
    }
    query_payload = {
        "regionalTotals": False,
        "currencyFY": False,
        "currencyCY": True,
        "constantUSD": False,
        "currentUSD": False,
        "shareOfGDP": True,
        "perCapita": False,
        "shareGovt": False,
        "regionDataDetails": False,
        "getLiveData": False,
        "yearFrom": None,
        "yearTo": None,
        "yearList": [1990, 2024],
        "countryList": []
    }
    raw = requests.post(
        url, headers=headers, json=query_payload, verify=False
    ).json()
    sspi_raw_api_data.raw_insert_one(
        raw, source_info, **kwargs
    )
    yield "Successfully collected MILEXP data"


SIPRI_MILEXP_DESCRIPTION = (
    "Military expenditure (local currency at current prices) according to "
    "the calendar year as a percentage of GDP."
)

# SIPRI labels that pycountry cannot resolve, or that get_country_code
# resolves to the wrong country.
SIPRI_COUNTRY_CODE_OVERRIDES = {
    "Brunei": "BRN",
    "Congo, Republic": "COG",
    "Cote d'Ivoire": "CIV",
    "Gambia, The": "GMB",
    "Korea, North": "PRK",
    "Korea, South": "KOR",
}

# Historical states and aggregates: none has a current ISO alpha-3 code, and
# get_country_code maps "German Democratic Republic" to COD, which would
# overwrite the DR Congo series.
SIPRI_NON_COUNTRY_ROWS = {
    "Czechoslovakia",
    "European Union",
    "German Democratic Republic",
    "USSR",
    "Yemen, North",
    "Yugoslavia",
}

SIPRI_MISSING_VALUE_MARKERS = {"", "...", ". .", "..", "xxx", "n/a", "N/A"}

# The Share of GDP sheet stores shares as fractions (USA 2023 = 0.033). A
# median above this means the export switched to percentages, and scaling by
# 100 again would inflate every value a hundredfold.
SIPRI_FRACTION_MEDIAN_CEILING = 0.5


def parse_sipri_year_label(label) -> int | None:
    """
    Returns the year for a header label such as "1990.0", "1990" or 1990.
    Returns None for non-year columns ("Country", "Notes", blanks).
    """
    if isinstance(label, bool) or label is None:
        return None
    try:
        year_float = float(str(label).strip())
    except ValueError:
        return None
    if math.isnan(year_float) or not year_float.is_integer():
        return None
    year = int(year_float)
    if year < 1900 or year > 2100:
        return None
    return year


def parse_sipri_share_value(raw_value) -> float | None:
    """
    Returns the share as a float fraction, or None when the cell is missing:
    ". ." / "..." (unavailable), "xxx" (country did not exist), blanks, and
    anything unparseable such as a value carrying a footnote marker.
    """
    if raw_value is None or isinstance(raw_value, bool):
        return None
    if isinstance(raw_value, str) and raw_value.strip() in SIPRI_MISSING_VALUE_MARKERS:
        return None
    try:
        value = float(str(raw_value).strip())
    except ValueError:
        return None
    if math.isnan(value) or math.isinf(value):
        return None
    return value


def resolve_sipri_country_code(country_name: str) -> str | None:
    if country_name in SIPRI_NON_COUNTRY_ROWS:
        return None
    if country_name in SIPRI_COUNTRY_CODE_OVERRIDES:
        return SIPRI_COUNTRY_CODE_OVERRIDES[country_name]
    country_code = get_country_code(country_name)
    if not isinstance(country_code, str) or len(country_code) != 3 or not country_code.isupper():
        return None
    return country_code


def find_sipri_share_of_gdp_section(milexp_raw: dict) -> dict:
    for section in milexp_raw.get("Data", []):
        if section.get("DataType") == "Share of GDP":
            return section
    raise ValueError("SIPRI_MILEXP raw document has no 'Share of GDP' section")


def find_sipri_header(rows: list) -> tuple[int, dict[int, int]]:
    """
    Returns the index of the header row (first cell "Country") and a map from
    column index to year, built from the header labels. Non-year columns
    such as "Notes" are left out of the map.
    """
    for row_index, row in enumerate(rows):
        if not row or str(row[0]).strip() != "Country":
            continue
        year_by_column = {}
        for column_index, label in enumerate(row):
            if column_index == 0:
                continue
            year = parse_sipri_year_label(label)
            if year is None:
                continue
            year_by_column[column_index] = year
        if not year_by_column:
            raise ValueError("SIPRI_MILEXP header row has no year columns")
        return row_index, year_by_column
    raise ValueError("SIPRI_MILEXP 'Share of GDP' section has no header row")


def parse_sipri_milexp_share_of_gdp(milexp_raw: dict) -> list[dict]:
    """
    Converts the SIPRI Milex 'Share of GDP' sheet into clean observations in
    percent of GDP. Years come from the header labels, so the Notes column
    and the sheet's start year never shift values.
    """
    log = logging.getLogger(__name__)
    rows = find_sipri_share_of_gdp_section(milexp_raw).get("Rows", [])
    header_index, year_by_column = find_sipri_header(rows)
    observations = []
    seen_country_years = set()
    for row in rows[header_index + 1:]:
        if not row or len(row) < 2:
            continue
        country_name = str(row[0]).strip()
        if not country_name:
            continue
        country_code = resolve_sipri_country_code(country_name)
        if country_code is None:
            if country_name not in SIPRI_NON_COUNTRY_ROWS:
                log.warning("SIPRI_MILEXP: skipping unmapped row %r", country_name)
            continue
        for column_index, year in year_by_column.items():
            if column_index >= len(row):
                continue
            share_fraction = parse_sipri_share_value(row[column_index])
            if share_fraction is None:
                continue
            if (country_code, year) in seen_country_years:
                log.error(
                    "SIPRI_MILEXP: duplicate %s %s from row %r; keeping the first",
                    country_code, year, country_name
                )
                continue
            seen_country_years.add((country_code, year))
            observations.append({
                "CountryCode": country_code,
                "Year": year,
                "Value": share_fraction,
                "Unit": "Percent of GDP",
                "DatasetCode": "SIPRI_MILEXP",
                "Description": SIPRI_MILEXP_DESCRIPTION,
            })
    if not observations:
        return observations
    median_share = statistics.median(obs["Value"] for obs in observations)
    if median_share > SIPRI_FRACTION_MEDIAN_CEILING:
        raise ValueError(
            f"SIPRI_MILEXP shares look like percentages (median {median_share}); "
            "expected fractions of GDP"
        )
    for obs in observations:
        obs["Value"] = obs["Value"] * 100
    return observations


@dataset_cleaner("SIPRI_MILEXP")
def clean_sipri_milexp():
    source_info = sspi_metadata.get_source_info("SIPRI_MILEXP")
    raw_data = sspi_raw_api_data.fetch_raw_data(source_info)
    cleaned_data = parse_sipri_milexp_share_of_gdp(raw_data[0]["Raw"])
    if not cleaned_data:
        raise ValueError("SIPRI_MILEXP raw document produced no observations")
    sspi_clean_api_data.delete_many({"DatasetCode": "SIPRI_MILEXP"})
    sspi_clean_api_data.insert_many(cleaned_data)
    return cleaned_data
