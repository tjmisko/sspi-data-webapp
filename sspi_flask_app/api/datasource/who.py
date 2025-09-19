import requests
import json
from sspi_flask_app.models.database import sspi_raw_api_data
from sspi_flask_app.api.resources.utilities import parse_json


def collect_who_data(who_indicator_code, **kwargs):
    url = f"https://ghoapi.azureedge.net/api/{who_indicator_code}"
    response = requests.get(url)
    source_info = {
        "OrganizationName": "World Health Organization",
        "OrganizationCode": "WHO",
        "OrganizationSeriesCode": who_indicator_code,
        "QueryCode": who_indicator_code,
        "URL": url,
    }
    obs_list = json.loads(response.text)
    yield "Data Received from WHO API.  Storing Data in SSPI Raw Data\n"
    count = sspi_raw_api_data.raw_insert_one(obs_list, source_info, **kwargs)
    yield f"Inserted {count} observations into the database."


def clean_who_data(raw_data, dataset_code, unit, description):
    cleaned_data_list = []
    for entry in raw_data[0]["Raw"]["value"]:
        if entry["SpatialDimType"] != "COUNTRY":
            continue
        if entry["Value"] == "No data":
            continue
        observation = {
            "CountryCode": entry["SpatialDim"],
            "DatasetCode": dataset_code,
            "Description": description,
            "Unit": unit,
            "Year": int(entry["TimeDim"]),
            "Value": float(entry["NumericValue"]),
            "Datasource": entry["DataSourceDim"],
        }
        cleaned_data_list.append(observation)
    return parse_json(cleaned_data_list)


def collect_gho_cstunt_data(**kwargs):
    yield "Collecting data from WHO API\n"
    base_url = "https://apps.who.int/gho/athena/data/GHO/"
    stub = "NUTSTUNTINGPREV,NUTRITION_ANT_HAZ_NE2.json?filter=COUNTRY:*&ead="
    yield f"Fetching from {base_url + stub}\n"
    raw = requests.get(base_url + stub).json()
    source_info = {
        "OrganizationName": "Global Health Observatory",
        "OrganizationCode": "GHO",
        "OrganizationSeriesCode": "NUTSTUNTINGPREV,NUTRITION_ANT_HAZ_NE2",
        "QueryCode": "NUTSTUNTINGPREV;NUTRITION_ANT_HAZ_NE2",
        "URL": base_url + stub,
        "BaseURL": base_url,
    }
    sspi_raw_api_data.raw_insert_one(raw, source_info, **kwargs)
    yield "Succesfully stored raw CSTUNT data in sspi_raw_api_database!\n"
