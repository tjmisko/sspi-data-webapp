import json
import time
import requests
import math
# import pandasdmx as sdmx
import pandas as pd
import xml.etree.ElementTree as ET
import bs4 as bs
from ... import sspi_raw_api_data
from flask_login import current_user
from datetime import datetime
from pycountry import countries
from ..api import format_m49_as_string
from ..api import string_to_float, string_to_int
from ..api import fetch_raw_data
from ..api import missing_countries, added_countries

def collectOECDIndicator(OECDIndicatorCode, RawDataDestination):
    SDMX_URL_OECD = f"https://stats.oecd.org/restsdmx/sdmx.ashx/GetData/{OECDIndicatorCode}"
    yield "Sending Data Request to OECD SDMX API\n"
    response_obj = requests.get(SDMX_URL_OECD)
    observation = str(response_obj.content) 
    yield "Data Received from OECD SDMX API.  Storing Data in SSPI Raw Data\n"
    sspi_raw_api_data.insert_one({
        "collection-info": {
            "RawDataDestination": RawDataDestination,
            "Source": "OECD",
            "CollectedAt": datetime.now()
        },
        "observation": observation
    })
    yield "Data Stored in SSPI Raw Data.  Collection Complete\n"

# ghg (total), ghg (index1990), ghg (ghg cap), co2 (total)

def processOECDdata(oecd_XML):
    xml_soup = bs.BeautifulSoup(oecd_XML, "lxml")
    series_list = xml_soup.find_all("series")
    return series_list
    
def organizeOECDdata(series_list):
    listofdicts = []
    for series in series_list:
        SeriesKeys = series.findall(".//{http://www.SDMX.org/resources/SDMXML/schemas/v2_0/generic}SeriesKey/{http://www.SDMX.org/resources/SDMXML/schemas/v2_0/generic}Value")
        Attributes = series.findall(".//{http://www.SDMX.org/resources/SDMXML/schemas/v2_0/generic}Attributes/{http://www.SDMX.org/resources/SDMXML/schemas/v2_0/generic}Value")
        Observation_time = series.findall(".//{http://www.SDMX.org/resources/SDMXML/schemas/v2_0/generic}Obs/{http://www.SDMX.org/resources/SDMXML/schemas/v2_0/generic}Time")
        Observation_value = series.findall(".//{http://www.SDMX.org/resources/SDMXML/schemas/v2_0/generic}Obs/{http://www.SDMX.org/resources/SDMXML/schemas/v2_0/generic}ObsValue")
        relevant_attribute = [True for x in Attributes if x.attrib["value"] == "T_CO2_EQVT"]
        relevant_key = [True for y in SeriesKeys if y.attrib["value"] == "CO2"]
        if relevant_attribute and relevant_key:
            year_lst = [year.text for year in Observation_time]
            obs_lst = [obs.attrib["value"] for obs in Observation_value]
            for value in SeriesKeys:
                if value.attrib["concept"] == "COU":
                    cou = value.attrib["value"]   
                    i = 0
                    while i <= (len(year_lst)- 1):
                        new_observation = {
                            "CountryCode": cou,
                            "IndicatorCode": "GTRANS",
                            "Source": "OECD",
                            "YEAR": string_to_int(year_lst[i]),
                            "RAW": string_to_float(obs_lst[i])
                        }
                        listofdicts.append(new_observation)
                        i += 1
    return listofdicts

def OECD_country_list(series_list):
    country_lst = []
    for series in series_list:
        SeriesKeys = series.findall(".//{http://www.SDMX.org/resources/SDMXML/schemas/v2_0/generic}SeriesKey/{http://www.SDMX.org/resources/SDMXML/schemas/v2_0/generic}Value")
        Attributes = series.findall(".//{http://www.SDMX.org/resources/SDMXML/schemas/v2_0/generic}Attributes/{http://www.SDMX.org/resources/SDMXML/schemas/v2_0/generic}Value")
        relevant_attribute = [True for x in Attributes if x.attrib["value"] == "T_CO2_EQVT"]
        relevant_key = [True for y in SeriesKeys if y.attrib["value"] == "CO2"]
        if relevant_attribute and relevant_key:
            for value in SeriesKeys:
                if value.attrib["concept"] == "COU":
                    cou = value.attrib["value"]
                    country_lst.append(cou)
    print("this is the oecd country list:" + str(country_lst))
    return country_lst
    
        