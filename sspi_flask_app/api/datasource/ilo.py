# import pandas as pd
# import json
import requests
from datetime import datetime
from ..api import raw_insert_one

def collectILOData(ILOIndicatorCode, IndicatorCode, QueryParams="....", IntermediateCode="NA"):
    yield "Sending Data Request to ILO API\n"
    response_obj = requests.get(f"https://www.ilo.org/sdmx/rest/data/ILO,{ILOIndicatorCode}/{QueryParams}")
    print(str(response_obj.content))
    observation = str(response_obj.content)
    yield "Data Received from ILO API.  Storing Data in SSPI Raw Data\n"
    count = raw_insert_one(observation, IndicatorCode, IntermediateCode)
    yield f"Inserted {count} observations into the database."
    # sspi_raw_api_data.insert_one({
        # "collection-info": {
    #         "IndicatorCode": IndicatorCode,
    #         "CollectedAt": datetime.now()
    #     },
    #     "observation": observation
    # })