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
        mongoQuery = {"collection-info.RawDataDestination": "BIODIV"}
        raw_data = parse_json(sspi_raw_api_data.find(mongoQuery))
        clean_obs_dict = {}
        for country in raw_data:
            if not country["observation"]["geoAreaCode"] in clean_obs_dict.keys():
                clean_obs_dict[country["observation"]["geoAreaCode"]] = {"CountryName": country["observation"]["geoAreaName"]}
            years_list = json.loads(country["observation"]["years"])
            print(type(years_list))
            #for year in years_list:
                #clean_obs_dict[country["observation"]["geoAreaCode"]][year["year"]] = year["value"]
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
        return str(raw_data[788])
    return "failure"
