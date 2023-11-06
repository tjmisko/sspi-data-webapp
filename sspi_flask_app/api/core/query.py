import re
from flask import Blueprint, jsonify, request
from ... import sspi_clean_api_data, sspi_main_data_v3, sspi_metadata, sspi_raw_api_data
from ..api import parse_json, lookup_database


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

class InvalidQueryError(Exception):
    """
    Raised when a query is invalid
    """
    pass

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
    if type(request) is dict:
        raw_query_input = {
            "IndicatorCode": request.get("IndicatorCode", None),
            "IndicatorGroup": request.get("IndicatorGroup", None),
            "CountryCode": request.get("CountryCode", None),
            "CountryGroup": request.get("CountryGroup", None),
            "Year": request.get("Year", None),
            "YearRangeStart": request.get("YearRangeStart", None),
            "YearRangeEnd": request.get("YearRangeEnd", None)
        }
    else:
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
    raw_query_input = check_input_safety(raw_query_input)
    raw_query_input = check_query_logic(raw_query_input, requires_database)
    return build_mongo_query(raw_query_input, requires_database)


def check_input_safety(raw_query_input):
    """
    Uses is_safe to check that the query parameters are safe
    """ 
    if len(raw_query_input.keys()) > 200:
        raise InvalidQueryError(f"Invalid Query: Too many parameters passed")
    for key, value in enumerate(raw_query_input):
        if type(value) is str and not is_safe(value):
            raise InvalidQueryError(f"Invalid Query: Unsafe Parameters Passed for {key}: {value}")
        elif type(value) is list and any([not is_safe(item) for item in value]):
            raise InvalidQueryError(f"Invalid Query: Unsafe Parameters Passed for list {key}")
    return raw_query_input

def check_query_logic(raw_query_input, requires_database=False):
    """
    Checks that the query parameters are logically valid
    """
    if raw_query_input["IndicatorCode"] and raw_query_input["IndicatorGroup"] is not None:
        raise InvalidQueryError("Invalid Query: Cannot query both IndicatorCode and IndicatorGroup")
    if raw_query_input["CountryCode"] and raw_query_input["CountryGroup"] is not None:
        raise InvalidQueryError("Invalid Query: Cannot query both CountryCode and CountryGroup")
    if raw_query_input["YearRangeStart"] is not None and raw_query_input["YearRangeEnd"] is None:
        raise InvalidQueryError("Invalid Query: Must specify both YearRangeStart and YearRangeEnd to use a Year Range")
    if raw_query_input["YearRangeStart"] is None and raw_query_input["YearRangeEnd"] is not None:
        raise InvalidQueryError("Invalid Query: Must specify both YearRangeStart and YearRangeEnd to use a Year Range")
    if raw_query_input["Year"] and (raw_query_input["YearRangeStart"] is not None or raw_query_input["YearRangeEnd"] is not None):
        raise InvalidQueryError("Invalid Query: Cannot query both Year and Year Range")
    if raw_query_input["Year"]:
        try:
            raw_query_input["Year"] = [int(year) for year in raw_query_input["Year"]]
        except ValueError:
            raise InvalidQueryError("Invalid Query: Year must be integers")
    if raw_query_input["YearRangeStart"] is not None and raw_query_input["YearRangeEnd"] is not None:
        try:
            year_list = list(range(int(raw_query_input["YearRangeStart"]), int(raw_query_input["YearRangeEnd"])+1))
        except ValueError:
            raise InvalidQueryError("Invalid Query: Year Range must be integers")
        if len(year_list) == 0:
            raise InvalidQueryError("Invalid Query: YearRangeStart must be greater than YearRangeEnd")
        raw_query_input["Year"] = year_list
    if requires_database:
        if raw_query_input["Database"] is None:
            raise InvalidQueryError("Invalid Query: Must specify a database")
        database = lookup_database(raw_query_input["Database"])
        if database is None:
            raise InvalidQueryError("Invalid Query: Database not found")
        raw_query_input["Database"] = database
    return raw_query_input

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

def is_safe(query_string):
    """
    Returns True if the query_string meets the sanitization criteria.

    Fairly restrictive sanitization that allows only alphanumeric characters, ampersands, and underscores
    """
    if query_string is None:
        return True
    safe_pattern = r"^[\w\d&]*$"
    return bool(re.match(safe_pattern, query_string))



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

def indicator_group(indicator_group):
    """
    Return a list of all indicators in a given indicator group
    """
    try:
        query_result = parse_json(sspi_metadata.find_one({"indicator_groups": {"$exists": True}}))["indicator_groups"][indicator_group]
    except TypeError:
        return ["Metadata not loaded"]
    return query_result

@query_bp.route("/metadata/indicator_details")
def indicator_details():
    indicator_details = parse_json(sspi_metadata.find_one({"indicator_details": {"$exists": True}}))["indicator_details"].values()
    return parse_json(indicator_details)