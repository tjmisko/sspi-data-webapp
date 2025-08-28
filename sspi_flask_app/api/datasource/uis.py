from sspi_flask_app.models.database import sspi_raw_api_data
import requests
import time
from pycountry import countries
from ..resources.utilities import string_to_float


def collect_uis_data(uis_indicator_code, **kwargs):
    yield f"Collecting data for UNESCO Institute for Statistics Indicator {uis_indicator_code}\n"
    url_source = f"https://api.uis.unesco.org/api/public/data/indicators?indicator={uis_indicator_code}"
    count = 0
    source_info = {
        "OrganizationName": "UNESCO Institute for Statistics",
        "OrganizationCode": "UIS",
        "OrganizationSeriesCode": uis_indicator_code,
        "QueryCode": uis_indicator_code,
        "URL": url_source
    }
    response = requests.get(url_source)
    if response.status_code != 200:
        yield f"Error fetching data from UIS API: {response.status_code}\n"
        return
    json = response.json()
    count = sspi_raw_api_data.raw_insert_many(json["records"], source_info, **kwargs)
    yield f"Inserted {count} raw documents\n"
    yield f"Collection complete for UNESCO Institute for Statistics Indicator {uis_indicator_code}"


def clean_uis_data(raw_data, dataset_code, unit, description):
    clean_data_list = []
    for obs in raw_data:
        country = obs["Raw"]["geoUnit"]
        country_data = countries.get(alpha_3 = country)
        if not country_data:
            continue
        year = int(obs["Raw"]["year"])
        value = obs["Raw"]["value"]
        if value == "NaN" or value is None or not value:
            continue
        clean_obs = {
            "CountryCode": country,
            "DatasetCode": dataset_code,
            "Description": description,
            "Year": year,
            "Unit": unit,
            "Value": string_to_float(value)
        }
        clean_data_list.append(clean_obs)
    return clean_data_list
