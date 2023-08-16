from flask_login import current_user
import requests
import json
import time
from datetime import datetime
from ... import sspi_raw_api_data

def store_raw_observation(response, IndicatorCode):
    """
    Store the response from an API call in the database
    """
    collection_time = datetime.now()
    try:
        for r in response:
            print(r)
            sspi_raw_api_data.insert_one(
                {"collection-info": {"CollectedBy": current_user.username,
                                    "RawDataDestination": IndicatorCode,
                                    "CollectedAt": collection_time}, 
                "observation": r}) 
        return response
    except Exception as e:
        print("Error storing API data:", e)
        return "Error storing API data"

def collectWorldBankdata(indicator_code):
    url_source = "https://api.worldbank.org/v2/country/all/indicator/" + indicator_code + "?format=JSON" 
    """make API request"""
    data = requests.get(url_source).json()
    npage=data[0]['pages']
    biglist=data[1] 
    for p in range(2,npage+1):
        new_url=url_source+ "&page=" + str(p)
        response=requests.get(new_url).json()
        store_raw_observation(response, "GTRANS")
        time.sleep(1)
        print(new_url)
    return "Complete"