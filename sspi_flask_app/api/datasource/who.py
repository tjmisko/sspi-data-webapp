import requests
import json
from sspi_flask_app.models.database import sspi_raw_api_data
from ..resources.utilities import parse_json


def collectWHOdata(WHOIndicatorCode, IndicatorCode, **kwargs):
    response = requests.get(
        f"https://ghoapi.azureedge.net/api/{WHOIndicatorCode}")
    observation = json.loads(response.text)
    yield "Data Received from WHO API.  Storing Data in SSPI Raw Data\n"
    count = sspi_raw_api_data.raw_insert_one(
        observation, IndicatorCode, **kwargs)
    yield f"Inserted {count} observations into the database."


def cleanWHOdata(raw_data, IndicatorCode, Unit, Description):
    cleaned_data_list = []
    for entry in raw_data[0]["Raw"]["value"]:
        if IndicatorCode == "DPTCOV":
            if entry["SpatialDimType"] != "COUNTRY":
                continue
            if entry["Dim1Type"] != "DHSMICSGEOREGION":
                continue
            if entry["Value"] == "No data":
                continue
            observation = {
                "CountryCode": entry["SpatialDim"],
                "IndicatorCode": IndicatorCode,
                "Description": Description,
                "Unit": Unit,
                "Year": entry["TimeDim"],
                "Value": entry["Value"].split(" ")[0]
            }
        else:
            if entry["SpatialDimType"] != "COUNTRY":
                continue
            observation = {
                "CountryCode": entry["SpatialDim"],
                "IndicatorCode": IndicatorCode,
                "Description": Description,
                "Unit": Unit,
                "Year": entry["TimeDim"],
                "Value": entry["Value"]
            }
        cleaned_data_list.append(observation)
    return parse_json(cleaned_data_list)


def collectCSTUNTData(**kwargs):
    yield "Collecting data from WHO API\n"
    base_url = "https://apps.who.int/gho/athena/data/GHO/"
    stub = "NUTSTUNTINGPREV,NUTRITION_ANT_HAZ_NE2.json?filter=COUNTRY:*&ead="
    yield "Fetching from {}\n".format(base_url + stub)
    raw = requests.get(base_url + stub).json()
    sspi_raw_api_data.raw_insert_one(raw, "CSTUNT", **kwargs)
    yield "Succesfully stored raw CSTUNT data in sspi_raw_api_database!\n"
