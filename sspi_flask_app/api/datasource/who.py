import requests
import json
from ... import sspi_raw_api_data
from ..resources.utilities import parse_json


def collectWHOdata(WHOIndicatorCode, IndicatorCode, **kwargs):
    response = requests.get(f"https://ghoapi.azureedge.net/api/{WHOIndicatorCode}")
    observation = json.loads(response.text)
    yield "Data Received from WHO API.  Storing Data in SSPI Raw Data\n"
    count = sspi_raw_api_data.raw_insert_one(observation, IndicatorCode, **kwargs)
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




