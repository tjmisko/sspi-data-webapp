import requests
from sspi_flask_app.models.database import sspi_raw_api_data
import json
import re


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
    data_decoded = str(data[0]['Raw'])[2:-1]
    fixed_string = re.sub("<a.*</a>.}", "\"", data_decoded)
    print(data_decoded[43000:45000])
    print("============================")
    print(fixed_string[43000:45000])
    loaded_json = json.loads(fixed_string)
    return fixed_string
