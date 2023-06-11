import re
from flask import Blueprint, request, render_template
from ... import sspi_clean_api_data, sspi_raw_api_data
import json
from bson import json_util

def parse_json(data):
    return json.loads(json_util.dumps(data))
def print_json(data):
    print(json.dumps(data, indent=4, sort_keys=True))

compute_bp = Blueprint("compute_bp", __name__,
                       template_folder="templates", 
                       static_folder="static", 
                       url_prefix="/compute")

def indicator_data_available(IndicatorCode):
    """
    Check if indicator is in database
    """
    return bool(sspi_raw_api_data.find_one({"collection-info.RawDataDestination": IndicatorCode}))

@compute_bp.route("/BIODIV", methods=['GET'])
def compute_biodiv():
    """
    If indicator is not in database, return a page with a button to collect the data
    - If no collection route is implemented, return a page with a message
    - If collection route is implemented, return a page with a button to collect the data
    If indicator is in database, compute the indicator from the raw data
    - Indicator computation: average of the three scores for percentage of biodiversity in
    marine, freshwater, and terrestrial ecosystems
    """
    if indicator_data_available("BIODIV"):
        # retrieve our raw data from the database
        mongoQuery = {"collection-info.RawDataDestination": "BIODIV"}
        raw_data = parse_json(sspi_raw_api_data.find(mongoQuery))
        # parse the observation into a clean format
        clean_obs_dict = {}
        for country in raw_data:
            geoAreaCode = country["observation"]["geoAreaCode"]
            if not geoAreaCode in clean_obs_dict.keys():
                clean_obs_dict[geoAreaCode] = {"CountryName": country["observation"]["geoAreaName"]}
            series = country["observation"]["series"]
            years_list = json.loads(country["observation"]["years"])
            for year in years_list:
                year_int = int(year["year"][1:5])
                if year["value"] is '':
                    pass
                elif year_int not in clean_obs_dict[geoAreaCode].keys():
                    clean_obs_dict[geoAreaCode][year_int] = {series: year["value"]}
                else:   
                    clean_obs_dict[geoAreaCode][year_int][series] = year["value"]
            for year in years_list:
                if not year in clean_obs_dict[geoAreaCode].keys():
                    pass
                elif 'N' in clean_obs_dict[geoAreaCode][year].values():
                    clean_obs_dict[geoAreaCode][year]["RAW"] = 'N'
                else:
                    clean_obs_dict[geoAreaCode][year]["RAW"] == sum(clean_obs_dict[geoAreaCode][year])/len(clean_obs_dict[geoAreaCode][year])

        # check the coverage
        coverage = {}
        for r in raw_data:
            if r["observation"]["series"] in coverage.keys():
                coverage[r["observation"]["series"]].append(r["observation"]["geoAreaName"])
            else:
                coverage[r["observation"]["series"]] = [r["observation"]["geoAreaName"]]
        print("# of Observations = ", len(raw_data))
        print("Series: ", coverage.keys())
        print(len(raw_data))
        print(clean_obs_dict)
        # store the cleaned data in the database
        return str(clean_obs_dict)
    return "failure"
