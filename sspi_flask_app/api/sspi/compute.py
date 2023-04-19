from flask import Blueprint, request, render_template
from ... import sspi_clean_api_data, sspi_raw_api_data
import json
from bson import json_util

def parse_json(data):
    return json.loads(json_util.dumps(data))

compute_bp = Blueprint("compute_bp", __name__,
                       template_folder="templates", 
                       static_folder="static", 
                       url_prefix="/compute")

def indicator_data_available(IndicatorCode):
    """
    Check if indicator is in database
    """
    if not bool(sspi_raw_api_data.find_one({"RawDataDestination": IndicatorCode})):
        return render_template("missingdata.html", IndicatorCode=IndicatorCode)
    else:
        return True

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
        raw_data = sspi_raw_api_data.find({"collection-info": {"RawDataDestination": "BIODIV"}})
        raw_data_test = sspi_raw_api_data.find_one()
        print(parse_json(raw_data_test))
        print(raw_data)
        print(parse_json(raw_data))
        return "success"
    return "failure"

    
