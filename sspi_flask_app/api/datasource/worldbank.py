from flask_login import current_user
import requests
import json
import time
from datetime import datetime
from ... import sspi_raw_api_data
from ..api import parse_json

def collectWorldBankdata(IndicatorCode, RawDataDestination):
    collection_time = datetime.now()
    url_source = "https://api.worldbank.org/v2/country/all/indicator/" + IndicatorCode + "?format=json"
    print(url_source)
    response = requests.get(url_source).json()
    print(response)
    total_pages = response[0]['pages']
    for p in range(1, total_pages+1):
        new_url = url_source + f"&page={p}"
        print(p)
        response = requests.get(new_url).json()
        for r in response[1]:
            sspi_raw_api_data.insert_one(
                {"collection_info": {"RawDataDestination": RawDataDestination,
                                     "CollectedAt": collection_time},
                "observation": r                    
                })
        time.sleep(0.5)
    return response

