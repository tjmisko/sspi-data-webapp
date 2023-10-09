from flask_login import current_user
from ..api import raw_insert_many
import requests
import json
import time
from datetime import datetime
from ... import sspi_raw_api_data
from ..api import parse_json
from pycountry import countries

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
                {"collection-info": {"RawDataDestination": RawDataDestination,
                                     "Source": "WORLDBANK",
                                     "CollectedAt": collection_time},
                
                "observation": r                    
                })
        time.sleep(0.5)
    return response

def cleanedWorldBankData(RawData, IndName):
    """
    Takes in list of collected raw data and our 6 letter indicator code 
    and returns a list of dictionaries with only relevant data from wanted countries
    """
    clean_data_list = []
    for entry in RawData:
        iso3 = entry["observation"]["countryiso3code"]
        country_data = countries.get(alpha_3=iso3)
        if not country_data:
            continue
        clean_obs = {
            "CountryCode": iso3,
            "CountryName": entry["observation"]["country"]["value"],
            "IndicatorCode": IndName,
            "Source": "WORLDBANK",
            "YEAR": entry["observation"]["date"],
            "RAW": entry["observation"]["value"]
        }
        clean_data_list.append(clean_obs)
    return clean_data_list






