import json
import time
import requests
import math
# import pandasdmx as sdmx
import pandas as pd
import xml.etree.ElementTree as ET
from ... import sspi_raw_api_data
from flask_login import current_user
from datetime import datetime
from pycountry import countries
from ..api import format_m49_as_string
from ..api import string_to_float, string_to_int
from ..api import fetch_raw_data
from ..api import missing_countries, added_countries

def collectOECDIndicator(SDMX_URL, RawDataDestination):
    response_obj = requests.get(SDMX_URL)
    SDMX_URL = "https://stats.oecd.org/restsdmx/sdmx.ashx/GetData/AIR_GHG/AUS+AUT+BEL+CAN+CHL+COL+CRI+CZE+DNK+EST+FIN+FRA+DEU+GRC+HUN+ISL+IRL+ISR+ITA+JPN+KOR+LVA+LTU+LUX+MEX+NLD+NZL+NOR+POL+PRT+SVK+SVN+ESP+SWE+CHE+TUR+GBR+USA+NMEC+ARG+BGD+BLR+BRA+BGR+CHN+HRV+CYP+IND+IDN+IRN+KAZ+LIE+MLT+MCO+PER+ROU+RUS+SAU+ZAF+UKR+OECDAM+OECDAO.GHG+CO2.TOTAL+ENER+ENER_IND+ENER_MANUF+ENER_TRANS+ENER_OSECT+ENER_OTH+ENER_FU+ENER_CO2+TOTAL_LULU+INTENS+GHG_CAP+GHG_GDP+GHG_CAP_LULU+GHG_GDP_LULU+INDEX+INDEX_2000+INDEX_1990+PERCENT+ENER_P+ENER_IND_P+ENER_MANUF_P+ENER_TRANS_P+ENER_OSECT_P+ENER_OTH_P+ENER_FU_P+ENER_CO2_P+IND_PROC_P+AGR_P+WAS_P+OTH_P/all?startTime=1990&endTime=2021"
    shorterurl = "https://stats.oecd.org/restsdmx/sdmx.ashx/GetData/AIR_GHG/AUS+AUT+BEL+CAN+CHL+COL+CRI+CZE+DNK+EST+FIN+FRA+DEU+GRC+HUN+ISL+IRL+ISR+ITA+JPN+KOR+LVA+LTU+LUX+MEX+NLD+NZL+NOR+POL+PRT+SVK+SVN+ESP+SWE+CHE+TUR+GBR+USA+NMEC+ARG+BGD+BLR+BRA+BGR+CHN+HRV+CYP+IND+IDN+IRN+KAZ+LIE+MLT+MCO+PER+ROU+RUS+SAU+ZAF+UKR+OECDAM+OECDAO.GHG+CO2.TOTAL+ENER+ENER_TRANS+ENER+ENER_CO2+INDEX+INDEX_2000+INDEX_1990+PERCENT+ENER_P+ENER_IND_P+ENER_MANUF_P+ENER_TRANS_P+ENER_OSECT_P+ENER_OTH_P+ENER_FU_P+ENER_CO2_P+IND_PROC_P+AGR_P+WAS_P+OTH_P/all?startTime=1990&endTime=2021"
    # nPages = response_obj.json().get('totalPages')
    print("RawDataDestination: {}".format(RawDataDestination))
    
    # print(response_obj.status_code)
    # print(response_obj.headers)
    # print(response_obj.content)
    sspi_raw_api_data.insert_one({
        "collection-info": {"CollectedBy": current_user.username,
                                        "RawDataDestination": RawDataDestination,
                                        "CollectedAt": datetime.now()}, 
        "observation": str(response_obj.content)
    })
    return "success!"

# ghg (total), ghg (index1990), ghg (ghg cap), co2 (total)

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
    
        