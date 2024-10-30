import requests
from ... import sspi_raw_api_data

def collectILOData(ILOIndicatorCode, IndicatorCode, **kwargs):
    yield "Sending Data Request to ILO API\n"
    response_obj = requests.get(f"https://www.sdmx.ilo.org/rest/data/ILO,{ILOIndicatorCode}?format=csv")
    print(str(response_obj.content))
    observation = str(response_obj.content)
    yield "Data Received from ILO API.  Storing Data in SSPI Raw Data\n"
    count = sspi_raw_api_data.raw_insert_one(observation, IndicatorCode, **kwargs)
    yield f"Inserted {count} observations into the database."
