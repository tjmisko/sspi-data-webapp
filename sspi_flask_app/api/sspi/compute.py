from flask import Blueprint, request, render_template
from ... import sspi_clean_api_data, sspi_raw_api_data

compute_bp = Blueprint("compute_bp", __name__,
                       template_folder="templates", 
                       static_folder="static", 
                       url_prefix="/compute")

def indicator_data_available(IndicatorCode):
    """
    Check if indicator is in database
    """
    return bool(sspi_raw_api_data.find_one({"RawDataDestination": IndicatorCode}))

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
        return render_template("missingdata.html", IndicatorCode="BIODIV")
    # Should I do my aggregation operations in MongoDB or in Python?
    raw_data = sspi_raw_api_data.find({"RawDataDestination": "BIODIV"})

    
