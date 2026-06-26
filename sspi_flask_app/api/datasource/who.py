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


def clean_who_data(raw_data, dataset_code, unit, description,
                   dimension_values=None):
    """Clean WHO GHO API data into SSPI observation documents.

    dimension_values: optional {field: value} filter used to collapse a
    disaggregated indicator down to a single series. For example,
    {"Dim1": "SEX_BTSX"} keeps only the both-sexes total for an indicator
    that GHO otherwise splits by SEX. Entries that do not match every given
    filter are skipped. Defaults to no filtering, so undisaggregated
    indicators are unaffected.
    """
    cleaned_data_list = []
    for entry in raw_data[0]["Raw"]["value"]:
        if entry["SpatialDimType"] != "COUNTRY":
            continue
        if entry["Value"] == "No data":
            continue
        if dimension_values and any(
            entry.get(field) != value
            for field, value in dimension_values.items()
        ):
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
