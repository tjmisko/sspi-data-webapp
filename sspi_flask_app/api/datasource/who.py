import requests
from ... import sspi_raw_api_data

def collectWHOdata(WHOIndicatorCode, IndicatorCode, **kwargs):
    raw = requests.get(f"https://ghoapi.azureedge.net/api/{WHOIndicatorCode}")
    observation = str(raw.content)
    yield "Data Received from WHO API.  Storing Data in SSPI Raw Data\n"
    count = sspi_raw_api_data.raw_insert_one(observation, IndicatorCode, **kwargs)
    yield f"Inserted {count} observations into the database."

def cleanWHOdata(raw_data, IndicatorCode, Unit):
    cleaned_data_list = []
    for entry in raw_data:
        return entry["Raw"]["value"]


