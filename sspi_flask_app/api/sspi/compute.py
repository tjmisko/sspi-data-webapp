from flask import Blueprint, request, render_template
from ... import sspi_clean_api_data, sspi_raw_api_data

compute_bp = Blueprint("compute_bp", __name__,
                       template_folder="templates", 
                       static_folder="static", 
                       url_prefix="/compute")

def check_indicator(indicatorCode):
    """
    Check if indicator is in database
    """
    return bool(sspi_clean_api_data.find_one({"indicatorCode": indicatorCode}))

@compute_bp.route("/BIODIV", methods=['GET'])
def compute_biodiv():
    """
    If indicator is not in database, return a page with a button to collect the data
    - If no collection route is implemented, return a page with a message
    - If collection route is implemented, return a page with a button to collect the data
    If indicator is in database, compute the indicator from the raw data
    """
    if not check_indicator("BIODIV"):
        return render_template("compute.html", indicatorCode="BIODIV")
    
