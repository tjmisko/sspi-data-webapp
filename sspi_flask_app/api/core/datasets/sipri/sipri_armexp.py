###############################################################
# Documentation: datasets/sipri/sipri_armexp/documentation.md #
###############################################################
import logging
import math
import pycountry
import requests
from sspi_flask_app.api.core.datasets import dataset_collector, dataset_cleaner
from sspi_flask_app.models.database import sspi_raw_api_data, sspi_clean_api_data, sspi_metadata
import pandas as pd
from io import StringIO
from sspi_flask_app.api.resources.utilities import get_country_code

@dataset_collector("SIPRI_ARMEXP")
def collect_sipri_armexp(**kwargs):
    log = logging.getLogger(__name__)
    url = "https://atbackend.sipri.org/api/p/trades/import-export-csv-str/"
    source_info = sspi_metadata.get_source_info("SIPRI_ARMEXP")
    log.info(f"Requesting ARMEXP data from URL: {url}")
    headers = {
        "Content-Type": "application/json",
        "Origin": "https://armstransfers.sipri.org",
        "Referer": "https://armstransfers.sipri.org",
    }
    query_payload = {
        "filters": [
            {
                "field": "Year range 1",
                "oldField": "",
                "condition": "contains",
                "value1": 1990,
                "value2": 2025,
                "listData": []
            },
            {
                "field": "orderbyseller",
                "oldField": "",
                "condition": "",
                "value1": "",
                "value2": "",
                "listData": []
            },
            {
                "field": "DeliveryType",
                "oldField": "",
                "condition": "",
                "value1": "delivered",
                "value2": "",
                "listData": []
            },
            {
                "field": "Status",
                "oldField": "",
                "condition": "",
                "value1": "0",
                "value2": "",
                "listData": []
            }
        ],
        "logic": "AND"
    }
    response = requests.post(url, headers=headers, json=query_payload)
    sspi_raw_api_data.raw_insert_one(response.json(), source_info, **kwargs)
    yield "Collected ARMEXP data"


SIPRI_ARMEXP_DATASET_CODE = "SIPRI_ARMEXP"
SIPRI_ARMEXP_UNIT = "Millions SIPRI TIV"
SIPRI_ARMEXP_DESCRIPTION = (
    "Arms transfers: the supply of military weapons through sales, aid, "
    "gifts, and those made through manufacturing licenses."
)
SIPRI_ARMEXP_ZERO_NOTE = "No recorded transfers (0 TIV)"
SIPRI_ARMEXP_HEADER_PREFIX = "Exports by,"
SIPRI_ARMEXP_EXPORTER_COLUMN = "Exports by"
SIPRI_ARMEXP_WORLD_TOTAL_LABEL = "total world export"
SIPRI_ARMEXP_FIRST_YEAR = 1990
SIPRI_ARMEXP_LAST_YEAR = 2025

# SIPRI exporter labels that are not ISO names. get_country_code returns an
# unknown label unchanged, so a three-letter label like "UAE" would otherwise
# pass as a country code. Keys are lowercased, stripped labels.
SIPRI_EXPORTER_CODE_OVERRIDES = {
    "uae": "ARE",
    "united arab emirates": "ARE",
    "brunei": "BRN",
    "bosnia-herzegovina": "BIH",
    "south korea": "KOR",
    "north korea": "PRK",
    "dr congo": "COD",
    "turkiye": "TUR",
    "russia": "RUS",
}

# Labels for exporters that are not current states (dissolved states,
# non-state actors, the EU, unknown suppliers) and the table's summary rows.
SIPRI_NON_STATE_EXPORTER_LABELS = {
    "soviet union",
    "yugoslavia",
    "czechoslovakia",
    "east germany (gdr)",
    "unknown supplier(s)",
    "european union**",
    "fmln (el salvador)*",
    "mujahedin (afghanistan)*",
    "hor (libya)*",
    SIPRI_ARMEXP_WORLD_TOTAL_LABEL,
    "sum total years",
}


def sipri_exporter_country_code(exporter_label) -> str | None:
    """
    ISO 3166 alpha-3 code for a SIPRI exporter label, or None when the label
    is a non-state exporter, a summary row, or cannot be resolved to a real
    ISO code.
    """
    if not isinstance(exporter_label, str):
        return None
    normalized_label = exporter_label.strip().lower()
    if not normalized_label or normalized_label in SIPRI_NON_STATE_EXPORTER_LABELS:
        return None
    if normalized_label in SIPRI_EXPORTER_CODE_OVERRIDES:
        return SIPRI_EXPORTER_CODE_OVERRIDES[normalized_label]
    country_code = get_country_code(exporter_label.strip())
    if not isinstance(country_code, str) or len(country_code) != 3:
        return None
    if pycountry.countries.get(alpha_3=country_code.upper()) is None:
        return None
    return country_code.upper()


def parse_sipri_tiv_cell(cell) -> tuple[float, bool]:
    """
    (Value, is_blank) for one SIPRI TIV cell. SIPRI prints "0" for deliveries
    between 0 and 0.5 million TIV and leaves the cell empty when no delivery
    was identified; by owner ruling (2026-09-13) an empty cell is 0 TIV.
    Raises ValueError for text that is neither blank nor numeric.
    """
    if cell is None:
        return 0.0, True
    if isinstance(cell, float) and math.isnan(cell):
        return 0.0, True
    cell_text = str(cell).strip()
    if cell_text == "":
        return 0.0, True
    return float(cell_text), False


def sipri_armexp_doc(country_code: str, year: int, value: float, no_recorded_transfers: bool) -> dict:
    document = {
        "CountryCode": country_code,
        "Year": year,
        "Value": value,
        "Unit": SIPRI_ARMEXP_UNIT,
        "DatasetCode": SIPRI_ARMEXP_DATASET_CODE,
        "Description": SIPRI_ARMEXP_DESCRIPTION,
    }
    if no_recorded_transfers:
        document["Note"] = SIPRI_ARMEXP_ZERO_NOTE
    return document


def read_sipri_armexp_table(csv_string: str) -> pd.DataFrame | None:
    """The exporter table below SIPRI's preamble, every cell read as text."""
    lines = csv_string.strip().split("\n")
    header_index = next(
        (i for i, line in enumerate(lines) if line.startswith(SIPRI_ARMEXP_HEADER_PREFIX)),
        None,
    )
    if header_index is None:
        return None
    table = pd.read_csv(
        StringIO("\n".join(lines[header_index:])), dtype=str, keep_default_na=False
    )
    table.columns = [str(column).strip() for column in table.columns]
    return table


def sipri_armexp_reported_years(table: pd.DataFrame) -> list[int]:
    """
    Year columns SIPRI has published: those with a value on the "Total world
    export" row. A year with no world total (e.g. the current, unpublished
    year) is not zero-filled. Without a world total row, a year counts as
    reported when any exporter has a value in it.
    """
    year_columns = [
        column for column in table.columns
        if column.isdigit()
        and SIPRI_ARMEXP_FIRST_YEAR <= int(column) <= SIPRI_ARMEXP_LAST_YEAR
    ]
    exporter_labels = table[SIPRI_ARMEXP_EXPORTER_COLUMN].str.strip().str.lower()
    world_total_rows = table[exporter_labels == SIPRI_ARMEXP_WORLD_TOTAL_LABEL]
    reference_rows = world_total_rows if not world_total_rows.empty else table
    reported_years = []
    for column in year_columns:
        if any(parse_sipri_tiv_cell(cell)[1] is False for cell in reference_rows[column]):
            reported_years.append(int(column))
    return sorted(reported_years)


def parse_sipri_armexp_csv(csv_string: str) -> list[dict]:
    """
    Clean SIPRI_ARMEXP documents for every exporter row that maps to an ISO
    country and every reported year. Blank cells become 0 TIV with the
    "No recorded transfers (0 TIV)" note; they are observations, not
    imputations. Unmappable labels are logged and dropped.
    """
    log = logging.getLogger(__name__)
    table = read_sipri_armexp_table(csv_string)
    if table is None:
        log.warning("SIPRI_ARMEXP: no 'Exports by' header found in raw CSV")
        return []
    reported_years = sipri_armexp_reported_years(table)
    cleaned_data = []
    seen_country_codes = set()
    for _, row in table.iterrows():
        exporter_label = row[SIPRI_ARMEXP_EXPORTER_COLUMN]
        country_code = sipri_exporter_country_code(exporter_label)
        if country_code is None:
            normalized_label = str(exporter_label).strip().lower()
            if normalized_label and normalized_label not in SIPRI_NON_STATE_EXPORTER_LABELS:
                log.warning(f"SIPRI_ARMEXP: unmapped exporter label {exporter_label!r} dropped")
            continue
        if country_code in seen_country_codes:
            log.warning(
                f"SIPRI_ARMEXP: duplicate exporter row for {country_code} "
                f"({exporter_label!r}) dropped"
            )
            continue
        seen_country_codes.add(country_code)
        for year in reported_years:
            try:
                value, is_blank = parse_sipri_tiv_cell(row[str(year)])
            except ValueError:
                log.warning(
                    f"SIPRI_ARMEXP: non-numeric cell {row[str(year)]!r} for "
                    f"{country_code} {year} dropped"
                )
                continue
            cleaned_data.append(sipri_armexp_doc(country_code, year, value, is_blank))
    return cleaned_data


def zero_fill_absent_exporters(cleaned_data: list[dict], country_codes: list[str]) -> list[dict]:
    """
    Countries in `country_codes` with no row in the exporter table have no
    recorded transfers: add a 0 TIV series for every year the table reports.
    """
    reported_years = sorted({doc["Year"] for doc in cleaned_data})
    present_country_codes = {doc["CountryCode"] for doc in cleaned_data}
    zero_filled = []
    for country_code in country_codes:
        if country_code in present_country_codes:
            continue
        for year in reported_years:
            zero_filled.append(sipri_armexp_doc(country_code, year, 0.0, True))
    return cleaned_data + zero_filled


@dataset_cleaner("SIPRI_ARMEXP")
def clean_sipri_armexp():
    sspi_clean_api_data.delete_many({"DatasetCode": SIPRI_ARMEXP_DATASET_CODE})
    source_info = sspi_metadata.get_source_info(SIPRI_ARMEXP_DATASET_CODE)
    raw_data = sspi_raw_api_data.fetch_raw_data(source_info)
    if not raw_data:
        return []
    cleaned_data = parse_sipri_armexp_csv(raw_data[0]["Raw"]["result"])
    if not cleaned_data:
        return []
    cleaned_data = zero_fill_absent_exporters(
        cleaned_data, sspi_metadata.country_group("SSPI67")
    )
    sspi_clean_api_data.insert_many(cleaned_data)
    sspi_metadata.record_dataset_range(cleaned_data, SIPRI_ARMEXP_DATASET_CODE)
    return cleaned_data
