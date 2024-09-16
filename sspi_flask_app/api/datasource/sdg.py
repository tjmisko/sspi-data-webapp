from pycountry import countries
from ... import sspi_raw_api_data
from ..resources.utilities import format_m49_as_string, string_to_float, parse_json, zip_intermediates
import json
import time
import math
import requests


# Implement API Collection for https://unstats.un.org/sdgapi/v1/sdg/Indicator/PivotData?indicator=14.5.1

def collectSDGIndicatorData(SDGIndicatorCode, IndicatorCode, **kwargs):
    url_source = f"https://unstats.un.org/sdgapi/v1/sdg/Indicator/PivotData?indicator={SDGIndicatorCode}" 
    response = requests.get(url_source)
    nPages = response.json().get('totalPages')
    yield "Iterating through {0} pages of source data for SDG {1}\n".format(nPages, SDGIndicatorCode)
    for p in range(1, nPages + 1):
        new_url = f"{url_source}&page={p}"
        yield "Fetching data for page {0} of {1}\n".format(p, nPages)
        response = requests.get(new_url)
        data_list = response.json().get('data')
        count = sspi_raw_api_data.raw_insert_many(data_list, IndicatorCode, **kwargs)
        yield f"Inserted {count} new observations into SSPI Raw Data\n"
        time.sleep(1)
    yield f"Collection complete for SDG {SDGIndicatorCode}"

def extract_sdg_pivot_data_to_nested_dictionary(raw_sdg_pivot_data):
    """
    Takes in a list of observations from the sdg_pivot_data_api and returns a nested dictionary 
    with only the relevant information extracted
    """
    intermediate_obs_dict = {}
    for country in raw_sdg_pivot_data:
        geoAreaCode = format_m49_as_string(country["Raw"]["geoAreaCode"])
        country_data = countries.get(numeric=geoAreaCode)
        # make sure that the data corresponds to a valid country (gets rid of regional aggregates)
        if not country_data:
            continue
        series = country["Raw"]["series"]
        annual_data_list = json.loads(country["Raw"]["years"])
        COU = country_data.alpha_3
        # add the country to the dictionary if it's not there already
        if COU not in intermediate_obs_dict.keys():
            intermediate_obs_dict[COU] = {}
        # iterate through each of the annual observations and add the appropriate entry
        for obs in annual_data_list:
            year = int(obs["year"][1:5])
            if obs["value"] == '':
                continue
            if year not in intermediate_obs_dict[COU].keys():
                intermediate_obs_dict[COU][year] = {}
            intermediate_obs_dict[COU][year][series] = obs["value"]
    return intermediate_obs_dict
    
def flatten_nested_dictionary_biodiv(intermediate_obs_dict):
    final_data_list = []
    for cou in intermediate_obs_dict.keys():
        for year in intermediate_obs_dict[cou].keys():
            for intermediate in intermediate_obs_dict[cou][year]:
                sdg_sspi_inter_dict = {"ER_MRN_MPA": ["MARINE", "Percent", "Percentage of important sites covered by protected areas, marine"],
                                       "ER_PTD_TERR": ["TERRST", "Percent", "Percentage of important sites covered by protected areas, terrestrial"],
                                       "ER_PTD_FRHWTR": ["FRSHWT", "Percent", "Percentage of important sites covered by protected areas, freshwater"]
                                       }
                if intermediate_obs_dict[cou][year][intermediate] == "N":
                    continue
                observation = {
                    "CountryCode": cou,
                    "IndicatorCode": "BIODIV",
                    "Unit": sdg_sspi_inter_dict[intermediate][1],
                    "Description": sdg_sspi_inter_dict[intermediate][2],
                    "Year": year,
                    "Value": string_to_float(intermediate_obs_dict[cou][year][intermediate]),
                    "IntermediateCode": sdg_sspi_inter_dict[intermediate][0],
                }
                final_data_list.append(observation)
    return final_data_list

def flatten_nested_dictionary_redlst(intermediate_obs_dict):
    final_data_lst = []
    for country in intermediate_obs_dict:
        for year in intermediate_obs_dict[country]:
            value = [x for x in intermediate_obs_dict[country][year].values()][0]
            if value == "N":
                continue
            new_observation = {
                "CountryCode": country,
                "IndicatorCode": "REDLST",
                "Unit": "Index",
                "Description": "Red List Index",
                "Year": year,
                "Value": string_to_float(value),
            }
            final_data_lst.append(new_observation)
    return final_data_lst

def flatten_nested_dictionary_intrnt(intermediate_obs_dict):
    final_data_lst = []
    for country in intermediate_obs_dict:
        for year in intermediate_obs_dict[country]:
            value = [x for x in intermediate_obs_dict[country][year].values()][0]
            if value == "N":
                continue
            new_observation = {
                "CountryCode": country,
                "IndicatorCode": "INTRNT",
                "Unit": "PER_100_POP",
                "Description": "Fixed broadband subscriptions per 100 inhabitants, by speed (per 100 inhabitants)",
                "Year": year,
                "Value": string_to_float(value),
                "IntermediateCode": "QUINTR"
            }
            final_data_lst.append(new_observation)
    return final_data_lst

def flatten_nested_dictionary_watman(intermediate_obs_dict):
    final_data_list = []
    for country in intermediate_obs_dict:
        for year in intermediate_obs_dict[country]:
            for intermediate in intermediate_obs_dict[country][year]:
                sdg_sspi_inter_dict = {"ER_H2O_WUEYST": ["CWUEFF", "USD/m3", "Water Use Efficiency (United States dollars per cubic meter)"] ,
                                       "ER_H2O_STRESS": ["WTSTRS", "Percent", "Freshwater withdrawal as a proportion of available freshwater resources"]}
                inter_value = string_to_float(intermediate_obs_dict[country][year][intermediate])
                log_scaled_value = (lambda intermediate: math.log(inter_value) if intermediate == "ER_H2O_WUEYST" 
                              and isinstance(inter_value, float) else inter_value)
                if inter_value == "NaN":
                    continue
                observation = {
                    "CountryCode": country,
                    "IndicatorCode": "WATMAN",
                    "Unit": sdg_sspi_inter_dict[intermediate][1],
                    "Description": sdg_sspi_inter_dict[intermediate][2],
                    "Year": year,
                    "Value": inter_value,
                    "IntermediateCode": sdg_sspi_inter_dict[intermediate][0],
                }
                final_data_list.append(observation)
    return final_data_list

def find_intermediate_watman(inter):
    if inter == "ER_H2O_WUEYST":
        return "CWUEFF"
    if inter == "ER_H2O_STRESS":
        return "WTSTRS"

def find_unit_watman(inter):
    if inter == "ER_H2O_WUEYST":
        return "United States dollars per cubic meter"
    if inter == "ER_H2O_STRESS":
        return "Freshwater withdrawal as a proportion of available freshwater resources"

def flatten_nested_dictionary_airpol(intermediate_obs_dict):
    final_data_lst = []
    for country in intermediate_obs_dict:
        for year in intermediate_obs_dict[country]:
            value = [x for x in intermediate_obs_dict[country][year].values()][0]
            new_observation = {
                "CountryCode": country,
                "IntermediateCode": "AIRPOL",
                "Year": int(year),
                "Value": string_to_float(value),
                "Unit": "mgr/m^3"
            }
            final_data_lst.append(new_observation)
    return final_data_lst

def flatten_nested_dictionary_stkhlm(intermediate_obs_dict):
    final_data_lst = []
    for country in intermediate_obs_dict:
        for year in intermediate_obs_dict[country]:
            value = [x for x in intermediate_obs_dict[country][year].values()][0]
            if value == "N":
                continue
            new_observation = {
                "CountryCode": country,
                "IndicatorCode": "STKHLM",
                "Unit": "Percent",
                "Description": "Parties meeting their commitments and obligations in transmitting information as required by Stockholm Convention on hazardous waste, and other chemicals (%)",
                "Year": year,
                "Value": string_to_float(value),
            }
            final_data_lst.append(new_observation)
    return final_data_lst

def flatten_nested_dictionary_airpol(intermediate_obs_dict):
    final_data_lst = []
    for country in intermediate_obs_dict:
        for year in intermediate_obs_dict[country]:
            value = [x for x in intermediate_obs_dict[country][year].values()][0]
            if value == "NaN":
                continue
            new_observation = {
                "CountryCode": country,
                "IndicatorCode": "AIRPOL",
                "Year": int(year),
                "Value": string_to_float(value),
                "Description": "Annual mean levels of fine particulate matter (PM2.5 and PM10) in cities (population weighted) measured in micrograms per cubic meter of air",
                "Unit": "μg/m^3"
            }
            final_data_lst.append(new_observation)
    return final_data_lst

def flatten_nested_dictionary_nrgint(intermediate_obs_dict):
    final_data_lst = []
    for country in intermediate_obs_dict:
        for year in intermediate_obs_dict[country]:
            value = [x for x in intermediate_obs_dict[country][year].values()][0]
            if value == "NaN":
                continue
            new_observation = {
                "CountryCode": country,
                "IndicatorCode": "NRGINT",
                "Unit": "MJ_PER_GDP_CON_PPP_USD",
                "Description": "Energy intensity level of primary energy (megajoules per constant 2017 purchasing power parity GDP)",
                "Year": year,
                "Value": string_to_float(value),
            }
            final_data_lst.append(new_observation)
    return final_data_lst

def flatten_nested_dictionary_fampln(intermediate_obs_dict):
    final_data_lst = []
    for country in intermediate_obs_dict:
        for year in intermediate_obs_dict[country]:
            value = [x for x in intermediate_obs_dict[country][year].values()][0]
            if value == "NaN":
                continue
            new_observation = {
                "CountryCode": country,
                "IndicatorCode": "FAMPLN",
                "Unit": "Percent",
                "Description": "Proportion of women of reproductive age (aged 15-49 years) who have their need for family planning satisfied with modern methods",
                "Year": year,
                "Value": 100 - string_to_float(value),
            }
            final_data_lst.append(new_observation)
    return final_data_lst

def flatten_nested_dictionary_drkwat(intermediate_obs_dict):
    final_data_lst = []
    for country in intermediate_obs_dict:
        for year in intermediate_obs_dict[country]:
            value = [x for x in intermediate_obs_dict[country][year].values()][0]
            if value == "NaN":
                continue
            new_observation = {
                "CountryCode": country,
                "IndicatorCode": "DRKWAT",
                "Unit": "Percent",
                "Description": "Percentage of population using safely managed drinking water services",
                "Year": year,
                "Value": string_to_float(value),
            }
            final_data_lst.append(new_observation)
    return final_data_lst

def flatten_nested_dictionary_sansrv(intermediate_obs_dict):
    intermediates = {"SH_SAN_HNDWSH": "Proportion of population with basic handwashing facilities on premises, by urban/rural (%)",
                     "SH_SAN_SAFE": "Proportion of population using safely managed sanitation services, by urban/rural (%)"}
    final_data_lst = []
    for country in intermediate_obs_dict:
        for year in intermediate_obs_dict[country]:
            if "SH_SAN_SAFE" not in intermediate_obs_dict[country][year].keys():
                continue
            value = intermediate_obs_dict[country][year]["SH_SAN_SAFE"]
            if value == "NaN":
                continue
            new_observation = {
                "CountryCode": country,
                "IndicatorCode": "SANSRV",
                "Unit": "Percent",
                "Description": "Proportion of population using safely managed sanitation services, by urban/rural (%)",
                "Year": year,
                "Value": string_to_float(value),
            }
            final_data_lst.append(new_observation)
    return final_data_lst
