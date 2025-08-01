from pycountry import countries
from sspi_flask_app.models.database import sspi_raw_api_data
from sspi_flask_app.api.resources.utilities import (
    format_m49_as_string,
    string_to_float,
)
import json
import time
import requests
import math


# Implement API Collection for
# https://unstats.un.org/sdgapi/v1/sdg/Indicator/PivotData?indicator=14.5.1
def collect_sdg_indicator_data(sdg_indicator_code: str, **kwargs):
    url_params = f"indicator={sdg_indicator_code}"
    url_options = "&pageSize=500"
    url_source = "https://unstats.un.org/SDGAPI/v1/sdg/Indicator/PivotData?"
    sdg_series_url = url_source + url_params # This URL identifies RawDocumentSets for SDG
    sdg_series_url_w_options = sdg_series_url + url_options
    response = requests.get(sdg_series_url_w_options)
    nPages = response.json().get('totalPages')
    yield f"Iterating through {nPages} pages of source data for SDG {sdg_indicator_code}\n"
    for p in range(1, nPages + 1):
        new_url = f"{sdg_series_url_w_options}&page={p}"
        yield "Fetching data for page {0} of {1}\n".format(p, nPages)
        response = requests.get(new_url)
        data_list = response.json().get('data')
        source_info = {
            "OrganizationName": "United Nations Sustainable Development Goals",
            "OrganizationCode": "UNSDG",
            "OrganizationSeriesCode": sdg_indicator_code,
            "BaseURL": sdg_series_url,
            "URL": new_url
        }
        count = sspi_raw_api_data.raw_insert_many(
            data_list, source_info, **kwargs
        )
        yield f"Inserted {count} new observations into SSPI Raw Data\n"
        time.sleep(1)
    yield f"Collection complete for SDG {sdg_indicator_code}\n"


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
            if not isinstance(value, float) or math.isnan(value):
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


def filter_sdg(observations: list[dict], idcode_map: dict, rename_map={}, drop_keys=[], **kwargs):
    """
    observations - the list of observations returned by extract_sdg
    Arguments are used in this order:
    idcode_map - a dictionary specifying how to map an SDGSeriesCode to an DatasetCode
    kwargs - Use keyword arguments to filter based on fields
        - Pass a string, float, or int to retain only observations with the field
        - Pass a list of strings, floats, or ints
    rename_map - a dictionary how to rename fields in the data
    drop_keys - a list specifying keys/fields to drop from the final data
    """
    if not rename_map:  # default rename map
        rename_map = {
            "units": "Unit",
            "seriesDescription": "Description"
        }
    if not drop_keys:  # default drop list
        drop_keys = [
            "goal", "indicator", "series", "seriesCount", "target",
            "geoAreaCode", "geoAreaName"
        ]
    filtered_list = []
    for obs in observations:
        if obs["SDGSeriesCode"] not in idcode_map.keys():
            continue
        obs["DatasetCode"] = idcode_map[obs["SDGSeriesCode"]]
        drop_obs = False
        for k, v in kwargs.items():
            if k not in obs.keys():
                continue
            list_test = type(v) is list and obs[k] not in v
            value_test = type(v) in [str, int, float] and obs[k] != v
            if list_test or value_test:
                drop_obs = True
                break
        if drop_obs:
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

def sdg_indicator_list():
    url = "https://unstats.un.org/SDGAPI/v1/sdg/Indicator/List"
    return requests.get(url).json()

