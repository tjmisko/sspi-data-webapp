from flask import Blueprint, flash, redirect, request, url_for
from flask_login import current_user, login_required
from .. import sspi_raw_api_data, sspi_clean_api_data, sspi_main_data_v3, sspi_metadata, sspi_dynamic_data, sspi_imputed_data, sspi_bulk_data
from bson import json_util
import json
import math
from datetime import datetime

api_bp = Blueprint(
    'api_bp', __name__,
    template_folder='templates',
    static_folder='static',
    url_prefix='/api/v1'
)

# some common utility functions used across the api core functionality



def lookup_database(database_name):
    """
    Utility function used for safe database lookup
    Returns nothing if the database name is incorrect
    """
    if database_name == "sspi_main_data_v3":
        return sspi_main_data_v3
    elif database_name == "sspi_raw_api_data":
        return sspi_raw_api_data
    elif database_name == "sspi_clean_api_data":
        return sspi_clean_api_data
    elif database_name == "sspi_imputed_data":
        return sspi_imputed_data
    elif database_name == "sspi_metadata":
        return sspi_metadata
    elif database_name == "sspi_dynamic_data":
        return sspi_dynamic_data

@api_bp.route("/finalize/<indicator_code>")
@login_required
def finalize(indicator_code):
    api_data = parse_json(sspi_clean_api_data.find({"IndicatorCode": indicator_code}, {"_id": 0}))
    imputed_data = parse_json(sspi_imputed_data.find({"IndicatorCode": indicator_code}, {"_id": 0}))
    print(api_data)
    print(imputed_data)
    final_data = api_data + imputed_data
    print(type(final_data))
    count = len(final_data)
    sspi_dynamic_data.insert_many(final_data)
    flash(f"Inserted {count} documents into SSPI Dynamic Data Database for {indicator_code}")
    return redirect(url_for("api_bp.api_dashboard"))

    
def check_observation_list_format(observations_list, database_name, IndicatorCode):
    ### Check that ID vars are present
    database = lookup_database(database_name)
    if database is None:
        raise InvalidDatabaseError(database_name)
    for i, obs in enumerate(observations_list):
        CountryCode = obs.get("CountryCode")
        Year = obs.get("Year")
        IndicatorCodeFromData = obs.get("IndicatorCode")
        if CountryCode is None or Year is None or IndicatorCodeFromData is None:
            raise InvalidObservationFormatError(f"Observation missing required ID variable for observation {i+1}")
        if IndicatorCodeFromData not in indicator_codes 