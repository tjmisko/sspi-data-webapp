from ..api import raw_insert_many, api_bp
from ... import sspi_raw_api_data
from flask_login import current_user
from datetime import datetime
from pycountry import countries
from ..api import format_m49_as_string, string_to_float, raw_insert_many
import json
import time
import requests

# Implement API Collection for https://unstats.un.org/sdgapi/v1/sdg/Indicator/PivotData?indicator=14.5.1
def collectSDGIndicatorData(SDGIndicatorCode, IndicatorCode):
    collection_time = datetime.now()
    url_source = f"https://unstats.un.org/sdgapi/v1/sdg/Indicator/PivotData?indicator={SDGIndicatorCode}" 
    response = requests.get(url_source)
    nPages = response.json().get('totalPages')
    yield "Iterating through {0} pages of source data for SDG {1}\n".format(nPages, SDGIndicatorCode)
    for p in range(1, nPages + 1):
        new_url = f"{url_source}&page={p}"
        yield "Fetching data for page {0} of {1}\n".format(p, nPages)
        response = requests.get(new_url)
        data_list = response.json().get('data')
        count = raw_insert_many(data_list, IndicatorCode)
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
        geoAreaCode = format_m49_as_string(country["observation"]["geoAreaCode"])
        country_data = countries.get(numeric=geoAreaCode)
        # make sure that the data corresponds to a valid country (gets rid of regional aggregates)
        if not country_data:
            continue
        series = country["observation"]["series"]
        annual_data_list = json.loads(country["observation"]["years"])
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
            try:
                mean_across_series = sum([float(x) for x in intermediate_obs_dict[cou][year].values()])/3
            except ValueError:
                mean_across_series = "NaN"
            new_observation = {
                "CountryCode": cou,
                "IndicatorCode": "BIODIV",
                "YEAR": year,
                "RAW": mean_across_series,
                "Intermediates": intermediate_obs_dict[cou][year]
            }
            final_data_list.append(new_observation)
    return final_data_list

def flatten_nested_dictionary_redlst(intermediate_obs_dict):
    final_data_lst = []
    for country in intermediate_obs_dict:
        for year in intermediate_obs_dict[country]:
            value = [x for x in intermediate_obs_dict[country][year].values()][0]
            new_observation = {
                "CountryCode": country,
                "IndicatorCode": "REDLST",
                "YEAR": year,
                "RAW": string_to_float(value)
            }
            final_data_lst.append(new_observation)
    return final_data_lst