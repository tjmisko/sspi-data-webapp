from pycountry import countries
from sspi_flask_app.models.database import sspi_raw_api_data
from sspi_flask_app.api.resources.utilities import (
    format_m49_as_string,
    string_to_float,
)
import json
import time
import math
import requests


# Implement API Collection for
# https://unstats.un.org/sdgapi/v1/sdg/Indicator/PivotData?indicator=14.5.1
def collectSDGIndicatorData(SDGIndicatorCode, IndicatorCode, **kwargs):
    url_params = f"indicator={SDGIndicatorCode}"
    url_source = "https://unstats.un.org/SDGAPI/v1/sdg/Indicator/PivotData?"
    base_url = url_source + url_params
    response = requests.get(url_source + url_params)
    nPages = response.json().get('totalPages')
    yield f"Iterating through {nPages} pages of source data for SDG {SDGIndicatorCode}\n"
    for p in range(1, nPages + 1):
        new_url = f"{base_url}&page={p}"
        yield "Fetching data for page {0} of {1}\n".format(p, nPages)
        response = requests.get(new_url)
        data_list = response.json().get('data')
        count = sspi_raw_api_data.raw_insert_many(
            data_list, IndicatorCode, **kwargs
        )
        yield f"Inserted {count} new observations into SSPI Raw Data\n"
        time.sleep(1)
    yield f"Collection complete for SDG {SDGIndicatorCode}"


def extract_sdg(raw_sdg_pivot_data):
    """
    Takes in a list of observations from the sdg_pivot_data_api and returns a
    nested dictionary with only the relevant information extracted
    """
    observations_list = []
    for country_obs in raw_sdg_pivot_data:
        geoAreaCode = format_m49_as_string(country_obs["Raw"]["geoAreaCode"])
        series_identifiers = {}
        for field, value in country_obs["Raw"].items():
            if not value:
                continue
            if isinstance(value, str) and len(value) > 500:
                continue
            valid_identifier = any([
                isinstance(value, str),
                isinstance(value, float),
                isinstance(value, int),
            ])
            if valid_identifier:
                series_identifiers[field] = value
        country_data = countries.get(numeric=geoAreaCode)
        if not country_data:
            continue
        sdg_series = country_obs["Raw"]["series"]
        sdg_indicator = country_obs["Raw"]["indicator"]
        annual_data_list = json.loads(country_obs["Raw"]["years"])
        CountryCode = country_data.alpha_3
        for year_obs in annual_data_list:
            value = string_to_float(year_obs["value"])
            if not isinstance(value, float):
                continue
            extracted_obs = {
                "CountryCode": CountryCode,
                "Year": int(year_obs["year"][1:5]),
                "Value": value,
                "SDGIndicator": sdg_indicator,
                "SDGSeriesCode": sdg_series,
            }
            extracted_obs.update(series_identifiers)
            observations_list.append(extracted_obs)
    return observations_list


def filter_sdg(observations: list[dict], idcode_map: dict, rename_map: dict, drop_keys: list[str], **kwargs):
    """
    observations - the list of observations returned by extract_sdg

    Arguments are used in this order:
    idcode_map - a dictionary specifying how to map an SDGSeriesCode to an IntermediateCode
    kwargs - Use keyword arguments to filter based on fields
        - Pass a string, float, or int to retain only observations with the field
        - Pass a list of strings, floats, or ints
    rename_map - a dictionary how to rename fields in the data
    drop_keys - a list specifying keys/fields to drop from the final data
    """
    filtered_list = []
    for obs in observations:
        if obs["SDGSeriesCode"] not in idcode_map.keys():
            continue
        if len(idcode_map.keys()) > 1:
            obs["IntermediateCode"] = idcode_map[obs["SDGSeriesCode"]]
        keep_obs = True
        for k, v in kwargs.items():
            if k in obs.keys() and obs[k] != v:
                keep_obs = False
        if not keep_obs:
            continue
        for k, v in rename_map.items():
            if k in obs.keys():
                obs[v] = obs[k]
                del obs[k]
        for k in drop_keys:
            if k in obs.keys():
                del obs[k]
        filtered_list.append(obs)
    return filtered_list


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
                sdg_sspi_inter_dict = {
                    "ER_H2O_WUEYST": [
                        "CWUEFF",
                        "USD/m3",
                        "Water Use Efficiency (United States dollars per cubic meter)"
                    ],
                    "ER_H2O_STRESS": [
                        "WTSTRS",
                        "Percent",
                        "Freshwater withdrawal as a proportion of available freshwater resources"
                    ]
                }
                inter_value = string_to_float(
                    intermediate_obs_dict[country][year][intermediate])
                if not isinstance(inter_value, float) or not isinstance(inter_value, int):
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


def flatten_nested_dictionary_physpc(intermediate_obs_dict):
    final_data_lst = []
    for country in intermediate_obs_dict:
        for year in intermediate_obs_dict[country]:
            value = [x for x in intermediate_obs_dict[country][year].values()][0]
            if value == "0.0" or value == 0 or value == 0.0 or value == "NaN":
                continue
            new_observation = {
                "CountryCode": country,
                "IndicatorCode": "PHYSPC",
                "Unit": "Index",
                "Description": "Physicians per 10,000.",
                "Year": year,
                "Value": string_to_float(value),
            }
            final_data_lst.append(new_observation)
    return final_data_lst
