import re
from flask import Blueprint, request, render_template
from ... import sspi_clean_api_data, sspi_raw_api_data
from ...api.source_utilities.sdg import flatten_and_format_nested_sdg_dictionary, extract_sdg_pivot_data_to_nested_dictionary
import json
from bson import json_util
from pycountry import countries
from ..api import fetch_raw_data

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
    if not indicator_data_available("BIODIV"):
        return "Data unavailable. Try running collect."
    raw_data = fetch_raw_data("BIODIV")
    intermediate_obs_dict = extract_sdg_pivot_data_to_nested_dictionary(raw_data)
    final_data_list = flatten_and_format_nested_sdg_dictionary(intermediate_obs_dict)
    # store the cleaned data in the database
    return json_util.dumps(final_data_list)
