from sspi_flask_app.models.database import sspi_raw_api_data
import logging
import requests
import time
from pycountry import countries

log = logging.getLogger(__name__)

# World Bank JSON marks a missing observation with a null ``value``; the raw
# store may also carry the literal "NaN" string or an empty string from older
# pulls. Zero is a legitimate observation and must never be treated as missing.
WB_MISSING_VALUE_SENTINELS = (None, "NaN", "")


def collect_wb_data(
    world_bank_indicator_code,
    source=None,
    organization_code="WB",
    organization_name="World Bank",
    **kwargs
):
    """
    Collect an indicator distributed through the World Bank API.

    :param source: Optional World Bank source database id (e.g. 3 for the
        Worldwide Governance Indicators). When provided, ``&source=<id>`` is
        appended to every request URL; some indicators are only resolvable
        inside their source database.
    :param organization_code: OrganizationCode stamped on raw documents.
        Defaults to "WB". Override when the World Bank is only the
        distributor and another organization originates the data.
    :param organization_name: OrganizationName stamped on raw documents.
    """
    yield f"Collecting data for World Bank Indicator {world_bank_indicator_code}\n"
    base_url = f"https://api.worldbank.org/v2/country/all/indicator/{world_bank_indicator_code}"
    url_w_options = base_url + "?per_page=1000&format=json"
    if source is not None:
        url_w_options += f"&source={source}"
    response = requests.get(url_w_options).json()
    total_pages = response[0]['pages']
    for p in range(1, total_pages+1):
        new_url = f"{url_w_options}&page={p}"
        yield f"Sending Request for page {p} of {total_pages}\n"
        response = requests.get(new_url).json()
        document_list = response[1]
        source_info = {
            "OrganizationName": organization_name,
            "OrganizationCode": organization_code,
            "OrganizationSeriesCode": world_bank_indicator_code,
            "QueryCode": world_bank_indicator_code,
            "URL": new_url,
            "BaseURL": base_url
        }
        count = sspi_raw_api_data.raw_insert_many(document_list, source_info, **kwargs)
        yield f"Inserted {count} new observations into sspi_raw_api_data\n"
        time.sleep(0.5)
    yield f"Collection complete for World Bank Indicator {world_bank_indicator_code}"


def clean_wb_data(raw_data, dataset_code, unit) -> list[dict]:
    """
    Convert raw World Bank API rows into clean observations.

    Drops (and counts) rows whose country is not an ISO alpha-3 country
    (World Bank aggregates and regions), rows whose value is one of the
    missing-value sentinels (null, "NaN", ""), and rows whose value cannot be
    parsed as a number. Zero values are kept. One summary line is logged per
    call so that no observation is dropped silently.
    """
    clean_data_list = []
    raw_row_count = 0
    dropped_non_country_count = 0
    dropped_missing_value_count = 0
    dropped_non_numeric_count = 0
    for entry in raw_data:
        raw_row_count += 1
        iso3 = entry["Raw"]["countryiso3code"]
        if not iso3:
            iso3 = entry["Raw"].get("country", {}).get("id")
        if not iso3 or not countries.get(alpha_3=iso3):
            dropped_non_country_count += 1
            continue
        value = entry["Raw"]["value"]
        if value in WB_MISSING_VALUE_SENTINELS:
            dropped_missing_value_count += 1
            continue
        try:
            numeric_value = float(value)
        except (TypeError, ValueError):
            dropped_non_numeric_count += 1
            continue
        clean_obs = {
            "CountryCode": iso3,
            "DatasetCode": dataset_code,
            "Description": entry["Raw"]["indicator"]["value"],
            "Year": int(str(entry["Raw"]["date"])),
            "Unit": unit,
            "Value": numeric_value
        }
        clean_data_list.append(clean_obs)
    log.info(
        "clean_wb_data %s: kept %d of %d raw rows; dropped %d non-country "
        "(aggregate/region) rows, %d missing-value rows, %d non-numeric rows",
        dataset_code,
        len(clean_data_list),
        raw_row_count,
        dropped_non_country_count,
        dropped_missing_value_count,
        dropped_non_numeric_count,
    )
    return clean_data_list
