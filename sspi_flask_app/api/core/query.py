import re
from flask import Blueprint, request
from ... import sspi_clean_api_data, sspi_main_data_v3, sspi_metadata, sspi_raw_api_data
from ..api import parse_json, lookup_database


query_bp = Blueprint("query_bp", __name__,
                     template_folder="templates", 
                     static_folder="static", 
                     url_prefix="/query")

@query_bp.route("/<database>")
def query_full_database(database_string):
    query_params = get_query_params(request)
    database = lookup_database(database_string)
    if database is None:
        return "database {} not found".format(database)
    return parse_json(database.find())

def get_query_params(request):
    """
    Implements the logic of query parameters and raises an 
    InvalidQueryError for invalid queries.
    
    Sanitizes User Input and returns a MongoDB query dictionary.

    Should always be implemented inside of a try except block
    with an except that returns a 404 error with the error message.
    """
    # Harvest parameters from query
    raw_query_input = {
        "Database": request.args.get("Database"),
        "IndicatorCode": request.args.getlist("IndicatorCode"),
        "IndicatorGroup": request.args.get("IndicatorGroup"),
        "CountryCode": request.args.getlist("CountryCode"),
        "CountryGroup": request.args.get("CountryGroup"),
        "Year": request.args.getlist("Year"),
        "YearRangeStart": request.args.get("YearRangeStart"),
        "YearRangeEnd": request.args.get("YearRangeEnd")
    }
    # Check that user input is safe
    # for key, value in enumerate(raw_query_input):
    #     if type(value) is str and :
            
    

def is_safe(query_string):
    """
    Returns True if the query_string meets the sanitization criteria.

    Fairly restrictive sanitization that allows only alphanumeric characters, ampersands, and underscores
    """
    safe_pattern = r"^[\w\d&]*$"
    return bool(re.match(safe_pattern, query_string))



@query_bp.route("/<database>/<IndicatorCode>")
def query_indicator(database, IndicatorCode):
    """
    Take an indicator code and return the data
    
    Query Parameters:
        Database
        CountryCode
        CountryGroup
        Year
        YearRangeStart
        YearRangeEnd
    """
    country_group = request.args.get('country_group', default = "all", type = str)
    if country_group != "all":
        query_parameters = {"CountryGroup": country_group}
    database_string = request.args.get('database', default = "sspi_main_data_v3", type = str)
    database = lookup_database(database_string)
    if database.name == "sspi_raw_api_data":
        indicator_data = sspi_raw_api_data.find({"collection-info.IndicatorCode": IndicatorCode})
    else:  
        indicator_data = database.find({"IndicatorCode": IndicatorCode}, {"_id": 0})
    return parse_json(indicator_data)

@query_bp.route("/country/<CountryCode>")
def query_country(CountryCode):
    """
    Take a country code and return the data
    """
    country_data = sspi_main_data_v3.find({"CountryCode": CountryCode})
    return parse_json(country_data)

####################
# METADATA QUERIES #
####################

@query_bp.route("/metadata/country_groups", methods=["GET"])
def country_groups():
    """
    Return a list of all country groups in the database
    """
    try:
        query_result = parse_json(sspi_metadata.find_one({"country_groups": {"$exists": True}}))["country_groups"]
    except TypeError:
        return ["Metadata not Loaded"]
    return parse_json(query_result.keys())

@query_bp.route("/metadata/country_groups/<country_group>", methods=["GET"])
def country_group(country_group):
    """
    Return a list of all countries in a given country group
    """
    try:
        query_result = parse_json(sspi_metadata.find_one({"country_groups": {"$exists": True}}))["country_groups"][country_group]
    except TypeError:
        return ["Metadata not Loaded"]
    return query_result

@query_bp.route("/metadata/indicator_codes", methods=["GET"])
def indicator_codes():
    """
    Return a list of all indicator codes in the database
    """
    try:
        query_result = parse_json(sspi_metadata.find_one({"indicator_codes": {"$exists": True}}))["indicator_codes"]
    except TypeError:
        return ["Metadata not loaded"]
    return query_result

@query_bp.route("/metadata/indicator_details")
def indicator_details():
    indicator_details = parse_json(sspi_metadata.find_one({"indicator_details": {"$exists": True}}))["indicator_details"].values()
    return parse_json(indicator_details)