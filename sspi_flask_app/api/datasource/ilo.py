from ... import sspi_raw_api_data
# import pandas as pd
# import json
import requests
from datetime import datetime

def collectILOData(ILOIndicatorCode, RawDataDestination, QueryParams="...."):
    yield "Sending Data Request to ILO API\n"
    response_obj = requests.get(f"https://www.ilo.org/sdmx/rest/data/ILO,{ILOIndicatorCode}/{QueryParams}")
    print(str(response_obj.content))
    observation = str(response_obj.content)
    yield "Data Received from ILO API.  Storing Data in SSPI Raw Data\n"
    sspi_raw_api_data.insert_one({
        "collection-info": {
            "RawDataDestination": RawDataDestination,
            "Source": "ILO",
            "CollectedAt": datetime.now()
        },
        "observation": observation
    })