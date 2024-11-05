import requests
from sspi_flask_app.models.database import sspi_raw_api_data
import json
from flask import jsonify
import re
import ujson

# def collectILOData(ILOIndicatorCode, IndicatorCode, QueryParams="....", **kwargs):
#     yield "Sending Data Request to ILO API\n"
#     response_obj = requests.get(f"https://www.ilo.org/sdmx/rest/data/ILO,{ILOIndicatorCode}/{QueryParams}")
#     print(str(response_obj.content))
#     observation = str(response_obj.content)
#     yield "Data Received from ILO API.  Storing Data in SSPI Raw Data\n"
#     count = sspi_raw_api_data.raw_insert_one(observation, IndicatorCode, **kwargs)
#     yield f"Inserted {count} observations into the database."


def collectILOData(ILOIndicatorCode, IndicatorCode, QueryParams="....", **kwargs):
    yield "Sending Data Request to ILO API\n"
    response_obj = requests.get(f"https://sdmx.ilo.org/rest/data/ILO,{ILOIndicatorCode}/?format=jsondata&{QueryParams}")
    print(str(response_obj.content))
    observation = str(response_obj.content)
    yield "Data Received from ILO API.  Storing Data in SSPI Raw Data\n"
    count = sspi_raw_api_data.raw_insert_one(observation, IndicatorCode, **kwargs)
    yield f"Inserted {count} observations into the database."


def cleanILOData(IndicatorCode):
    data = sspi_raw_api_data.fetch_raw_data(IndicatorCode)
    # print(type(data[0]['Raw']))
    data = str(data[0]['Raw'][2:-1]).encode("ascii", "ignore")
    # fixed_string = re.sub("<a.*</a>.}", "\"", data_decoded)
    # print(data_decoded[43000:45000])
    # print("============================")
    # json_string = data.replace('\\\"', '\"') # fixing escape characters for 45780
    # json_string = json_string.replace('"T\\xc3\\xbcrkiye\"', '"Turkey"') # fixing turkey encoding
    # json_string = re.sub(r"\\'", "'", json_string)  # Replace escaped single quotes
    # json_string = re.sub(r'\\xc3\\xad', 'í', json_string)  # Decode UTF-8 sequences
    # json_string = re.sub(r'\\xc3\\xb3', 'ó', json_string)  # Example for 'ó' if needed
    # subset = json_string[61000:63000]
    loaded_json = json.loads(data)
    # print(json_string[61700:61800])
    return "done"