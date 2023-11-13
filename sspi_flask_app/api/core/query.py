import re
from flask import Blueprint, jsonify, request
from ..resources.errors import InvalidQueryError
from ..resources.validators import validate_query_logic, validate_query_safety
from ..resources.utilities import parse_json, lookup_database
from ..resources.metadata import indicator_codes, country_codes, indicator_group, indicator_groups, country_group, country_groups, indicator_details
from ... import sspi_clean_api_data, sspi_main_data_v3, sspi_metadata, sspi_raw_api_data

query_bp = Blueprint("query_bp", __name__,
                     template_folder="templates", 
                     static_folder="static", 
                     url_prefix="/query")

@query_bp.route("/<database_string>")
def query_full_database(database_string):
    try:
        query_params = get_query_params(request)
        print(query_params)
    except InvalidQueryError as e:
        return f"{e}"
    database = lookup_database(database_string)
    if database is None:
        return "database {} not found".format(database)
    if database.name == "sspi_raw_api_data" and query_params.get("IndicatorCode"):
        query_params = {"collection-info.IndicatorCode": query_params["IndicatorCode"]}
    return jsonify(parse_json(database.find(query_params, {"_id": 0})))


def get_query_params(request, requires_database=False):
    """
    Implements the logic of query parameters and raises an 
    InvalidQueryError for invalid queries.

    In Flask, request.args is a MultiDict object of query parameters, but
    I wanted the function to work for simple dictionaries as well so we can
    use it easily internally
    
    Sanitizes User Input and returns a MongoDB query dictionary.

    Should always be implemented inside of a try except block
    with an except that returns a 404 error with the error message.

    requires_database determines whether the query 
    """
    raw_query_input = {
        "IndicatorCode": request.args.getlist("IndicatorCode"),
        "IndicatorGroup": request.args.get("IndicatorGroup"),
        "CountryCode": request.args.getlist("CountryCode"),
        "CountryGroup": request.args.get("CountryGroup"),
        "Year": request.args.getlist("Year"),
        "YearRangeStart": request.args.get("YearRangeStart"),
        "YearRangeEnd": request.args.get("YearRangeEnd")
    }
    if requires_database:
        raw_query_input["Database"] = request.args.get("database"),
    raw_query_input = validate_query_safety(raw_query_input)
    raw_query_input = validate_query_logic(raw_query_input, requires_database)
    return build_mongo_query(raw_query_input, requires_database)


def build_mongo_query(raw_query_input, requires_database):
    """
    Given a safe and logically valid query input, build a mongo query
    """
    mongo_query = {}
    if raw_query_input["IndicatorCode"]: 
        mongo_query["IndicatorCode"] = {"$in": raw_query_input["IndicatorCode"]}
    if raw_query_input["IndicatorGroup"]:
        mongo_query["IndicatorGroup"] = {"$in": indicator_group(raw_query_input["IndicatorGroup"])}
    if raw_query_input["CountryCode"]:
        mongo_query["CountryCode"] = {"$in": raw_query_input["CountryCode"]}
    if raw_query_input["CountryGroup"]:
        mongo_query["CountryCode"] = {"$in": country_group(raw_query_input["CountryGroup"])}
    if raw_query_input["Year"]:
        mongo_query["YEAR"] = {"$in": raw_query_input["Year"]}
    return mongo_query




@query_bp.route("/indicator/<IndicatorCode>")
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
    try:
        query_params = get_query_params(request, requires_database=True)
    except InvalidQueryError as e:
        return f"{e}"
    if query_params["Database"].name == "sspi_raw_api_data":
        indicator_data = database.find({"collection-info.IndicatorCode": IndicatorCode})
    else:  
        indicator_data = database.find({"IndicatorCode": IndicatorCode}.update(query_params), {"_id": 0})
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
def query_country_groups():
    return country_groups()

@query_bp.route("/metadata/country_groups/<country_group>", methods=["GET"])
def query_country_group(country_group):
    return country_groups(country_group)

@query_bp.route("/metadata/indicator_codes", methods=["GET"])
def query_indicator_codes():
    return indicator_codes()

@query_bp.route("/metadata/indicator_groups", methods=["GET"])
def query_indicator_groups():
    return indicator_groups()

@query_bp.route("/metadata/indicator_groups/<indicator_group>", methods=["GET"])
def query_indicator_group(indicator_group):
    return indicator_codes(indicator_group)

@query_bp.route("/metadata/indicator_details")
def query_indicator_details():
    return indicator_details()