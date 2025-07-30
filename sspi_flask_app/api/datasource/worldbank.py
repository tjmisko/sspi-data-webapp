from sspi_flask_app.models.database import sspi_raw_api_data
import requests
import time
from pycountry import countries
from ..resources.utilities import string_to_float


def collect_world_bank_data(world_bank_indicator_code, IndicatorCode, **kwargs):
    yield f"Collecting data for World Bank Indicator {world_bank_indicator_code}\n"
    base_url = f"https://api.worldbank.org/v2/country/all/indicator/{world_bank_indicator_code}"
    url_w_options = base_url + "?per_page=1000&format=json"
    response = requests.get(url_w_options).json()
    total_pages = response[0]['pages']
    for p in range(1, total_pages+1):
        new_url = f"{url_w_options}&page={p}"
        yield f"Sending Request for page {p} of {total_pages}\n"
        response = requests.get(new_url).json()
        document_list = response[1]
        source_info = {
            "OrganizationName": "World Bank",
            "OrganizationCode": "WB",
            "OrganizationSeriesCode": world_bank_indicator_code,
            "URL": new_url,
            "BaseURL": base_url
        }
        count = sspi_raw_api_data.raw_insert_many(document_list, source_info, **kwargs)
        yield f"Inserted {count} new observations into sspi_raw_api_data\n"
        time.sleep(0.5)
    yield f"Collection complete for World Bank Indicator {world_bank_indicator_code}"


def clean_wb_data(raw_data, IndicatorCode, unit) -> list[dict]:
    clean_data_list = []
    for entry in raw_data:
        iso3 = entry["Raw"]["countryiso3code"]
        country_data = countries.get(alpha_3=iso3)
        if not country_data:
            continue
        value = entry["Raw"]["value"]
        if value == "NaN" or value is None or not value:
            continue
        clean_obs = {
            "CountryCode": iso3,
            "IndicatorCode": IndicatorCode,
            "Description": entry["Raw"]["indicator"]["value"],
            "Year": int(str(entry["Raw"]["date"])),
            "Unit": unit,
            "Value": string_to_float(value)
        }
        if "IntermediateCode" in entry.keys():
            clean_obs["IntermediateCode"] = entry["IntermediateCode"]
        clean_data_list.append(clean_obs)
    return clean_data_list
