from ... import sspi_raw_api_data
import requests
import time
from pycountry import countries
from ..resources.utilities import string_to_float

def collectWorldBankdata(WorldBankIndicatorCode, IndicatorCode, **kwargs):
    yield f"Collecting data for World Bank Indicator {WorldBankIndicatorCode}\n"
    url_source = f"https://api.worldbank.org/v2/country/all/indicator/{WorldBankIndicatorCode}?format=json"
    response = requests.get(url_source).json()
    total_pages = response[0]['pages']
    for p in range(1, total_pages+1):
        new_url = f"{url_source}&page={p}"
        yield f"Sending Request for page {p} of {total_pages}\n"
        response = requests.get(new_url).json()
        document_list = response[1]
        count = sspi_raw_api_data.raw_insert_many(document_list, IndicatorCode, **kwargs)
        yield f"Inserted {count} new observations into sspi_raw_api_data\n"
        time.sleep(0.5)
    yield f"Collection complete for World Bank Indicator {WorldBankIndicatorCode}"

def cleanedWorldBankData(RawData, IndName):
    """
    Takes in list of collected raw data and our 6 letter indicator code 
    and returns a list of dictionaries with only relevant data from wanted countries
    """
    clean_data_list = []
    for entry in RawData:
        iso3 = entry["Raw"]["countryiso3code"]
        country_data = countries.get(alpha_3=iso3)
        if not country_data:
            continue
        clean_obs = {
            "CountryCode": iso3,
            "CountryName": entry["Raw"]["country"]["value"],
            "IndicatorCode": IndName,
            "Source": "WORLDBANK",
            "YEAR": entry["Raw"]["date"],
            "RAW": entry["Raw"]["value"]
        }
        clean_data_list.append(clean_obs)
    return clean_data_list

def cleaned_wb_current(RawData, IndName, unit):
    """
    Takes in list of collected raw data and our 6 letter indicator code 
    and returns a list of dictionaries with only relevant data from wanted countries
    """
    clean_data_list = []
    for entry in RawData:
        iso3 = entry["Raw"]["countryiso3code"]
        country_data = countries.get(alpha_3=iso3)
        if not country_data:
            continue
        if entry["Raw"]["value"] is None:
            continue
        clean_obs = {
            "CountryCode": iso3,
            "IndicatorCode": IndName,
            "IntermediateCode": entry["IntermediateCode"],
            "Description": entry["Raw"]["indicator"]["value"],
            "Year": entry["Raw"]["date"],
            "Unit": unit,
            "Value": string_to_float(entry["Raw"]["value"])
        }
        clean_data_list.append(clean_obs)
    return clean_data_list







