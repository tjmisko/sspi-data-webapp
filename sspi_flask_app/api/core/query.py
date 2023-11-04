from flask import Blueprint, request
from ... import sspi_clean_api_data, sspi_main_data_v3, sspi_metadata, sspi_raw_api_data
from ..api import parse_json, lookup_database


query_bp = Blueprint("query_bp", __name__,
                     template_folder="templates", 
                     static_folder="static", 
                     url_prefix="/query")

@query_bp.route("/")
def query_full_database():
    database_string = request.args.get('database', default = "sspi_main_data_v3", type = str)
    database = lookup_database(database_string)
    if database is None:
        return "database {} not found".format(database)
    return parse_json(database.find())

@query_bp.route("/indicator/<IndicatorCode>")
def query_indicator(IndicatorCode):
    """
    Take an indicator code and return the data
    Update with query parameters for country group
    """
    country_group = request.args.get('country_group', default = "all", type = str)
    if country_group != "all":
        query_parameters = {"CountryGroup": country_group}
    database = request.args.get('database', default = "sspi_main_data_v3", type = str)
    if database == "sspi_raw_api_data":
        indicator_data = sspi_raw_api_data.find({"collection-info.IndicatorCode": IndicatorCode})
    elif database == "sspi_clean_api_data":
        indicator_data = sspi_clean_api_data.find({"IndicatorCode": IndicatorCode}, {"_id": 0, "Intermediates": 0})
    else:  
        indicator_data = sspi_main_data_v3.find({"IndicatorCode": IndicatorCode})
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