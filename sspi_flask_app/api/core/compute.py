from flask import Blueprint
from ..api import indicator_data_available
from ... import sspi_clean_api_data, sspi_raw_api_data, parse_json
from ..datasource.sdg import flatten_nested_dictionary_biodiv, extract_sdg_pivot_data_to_nested_dictionary, flatten_nested_dictionary_redlst
from .dashboard import fetch_raw_data

compute_bp = Blueprint("compute_bp", __name__,
                       template_folder="templates", 
                       static_folder="static", 
                       url_prefix="/compute")

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
    # implement a computation function as an argument which can be adapted to different contexts
    final_data_list = flatten_nested_dictionary_biodiv(intermediate_obs_dict)
    # store the cleaned data in the database
    sspi_clean_api_data.insert_many(final_data_list)
    return parse_json(final_data_list)

@compute_bp.route("/REDLST", methods = ['GET'])
def compute_rdlst():
    if not indicator_data_available("REDLST"):
        return "Data unavailable. Try running collect."
    raw_data = fetch_raw_data("REDLST")
    intermediate_obs_dict = extract_sdg_pivot_data_to_nested_dictionary(raw_data)
    final_list = flatten_nested_dictionary_redlst(intermediate_obs_dict)
    sspi_clean_api_data.insert_many(final_list)
    return parse_json(final_list)

@compute_bp.route("/ALTNRG", methods=['GET'])
def compute_altnrg():
    if not indicator_data_available("ALTNRG"):
        return "Data unavailable. Try running collect."
    raw_data = fetch_raw_data("ALTNRG")
    lst = []
    for row in raw_data:
        lst.append(row["observation"])
    return parse_json(lst)