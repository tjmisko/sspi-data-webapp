from flask_login import current_user
from ..core.collect import raw_insert_many
import requests
import json
import time
from datetime import datetime
from ... import sspi_raw_api_data

def collectWorldBankdata(indicator_code):
    url_source = "https://api.worldbank.org/v2/country/all/indicator/" + indicator_code + "?format=JSON" 
    """make API request"""
    data = requests.get(url_source).json()
    npage=data[0]['pages']
    biglist=data[1] 
    for p in range(2,npage+1):
        new_url=url_source+ "&page=" + str(p)
        response=requests.get(new_url).json()
        raw_insert_many(response, "GTRANS")
        time.sleep(1)
        print(new_url)
    return "Complete"