import requests
from sspi_flask_app.models.database import sspi_raw_api_data
import json
from flask import jsonify
import re

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
 #   print(type(data[0]['Raw']))
    data_decoded = str(data[0]['Raw'])
    # print(data_raw)
    print(len(data_decoded))
    # loaded_json = json.loads(data_decoded[44500:45000])
    substring = data_decoded[40000:50000]
    structures = re.findall(pattern = "structures", string = data_decoded)
    # metadata = str(data0]['Raw']["structures"]
    str(structures)
    return data_decoded

