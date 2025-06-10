from flask import Blueprint, jsonify, request
from sspi_flask_app.models.errors import InvalidQueryError
from sspi_flask_app.api.resources.validators import validate_data_query
from sspi_flask_app.api.resources.utilities import parse_json, lookup_database
from sspi_flask_app.models.database import sspi_metadata

query_bp = Blueprint("query_bp", __name__,
                     template_folder="templates",
                     static_folder="static",
                     url_prefix="/query")


@query_bp.route("/<database_string>")
def query_database(database_string):
    query_params = get_query_params(request)
    database = lookup_database(database_string)
    print(query_params)
    return jsonify(parse_json(database.find(query_params, options={"_id": 0})))


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
        "CountryCode": request.args.getlist("CountryCode"),
        "CountryGroup": request.args.get("CountryGroup"),
        "Year": request.args.getlist("Year"),
        "YearRangeStart": request.args.get("YearRangeStart"),
        "YearRangeEnd": request.args.get("YearRangeEnd"),
    }
    if requires_database:
        raw_query_input["Database"] = request.args.get("database"),
    validated_query_input = validate_data_query(raw_query_input)
    return build_mongo_query(validated_query_input)


def build_mongo_query(raw_query_input):
    """
    Given a safe and logically valid query input, build a mongo query
    """
    mongo_query = {}
    if raw_query_input["IndicatorCode"]:
        mongo_query["IndicatorCode"] = {
            "$in": raw_query_input["IndicatorCode"]
        }
    country_codes = set()
    if raw_query_input["CountryGroup"]:
        country_codes.update(
            sspi_metadata.country_group(raw_query_input["CountryGroup"])
        )
    if raw_query_input["CountryCode"]:
        country_codes.update(raw_query_input["CountryCode"])
    if country_codes:
        mongo_query["CountryCode"] = {"$in": list(country_codes)}
    years = set()
    if raw_query_input["Year"]:
        years.update([int(y) for y in raw_query_input["Year"]])
    if raw_query_input["YearRangeStart"] and raw_query_input["YearRangeEnd"]:
        start_year = int(raw_query_input["YearRangeStart"])
        end_year = int(raw_query_input["YearRangeEnd"])
        years.update(range(start_year, end_year + 1))
    if years:
        mongo_query["Year"] = {"$in": list(years)}
    return mongo_query


@query_bp.route("/metadata/country_groups", methods=["GET"])
def query_country_groups(tree=False):
    if request.args.get("tree") == "true" or tree:
        tree = True
        return jsonify(sspi_metadata.country_groups_tree())
    return sspi_metadata.country_groups()


@query_bp.route("/metadata/country_group/<country_group>", methods=["GET"])
def get_country_group(country_group):
    return sspi_metadata.country_group(country_group)


@query_bp.route("/metadata/indicator_codes", methods=["GET"])
def query_indicator_codes():
    return jsonify(sspi_metadata.indicator_codes())


@query_bp.route("/metadata/indicator_details")
def query_indicator_details():
    return jsonify(sspi_metadata.indicator_details())


@query_bp.route("/metadata/indicator_detail/<indicator_code>", methods=["GET"])
def query_indicator_detail(indicator_code):
    return jsonify(sspi_metadata.get_indicator_detail(indicator_code))


@query_bp.route("/metadata/intermediate_details")
def query_intermediate_details():
    return parse_json(sspi_metadata.intermediate_details())


@query_bp.route("/metadata/intermediate_codes", methods=["GET"])
def query_intermediate_codes():
    return parse_json(sspi_metadata.intermediate_codes())


@query_bp.route("/metadata/intermediate_detail/<intermediate_code>", methods=["GET"])
def query_intermediate_detail(intermediate_code):
    return parse_json(sspi_metadata.get_intermediate_detail(intermediate_code))


@query_bp.route("/metadata/category_details")
def query_category_details():
    return parse_json(sspi_metadata.category_details())


@query_bp.route("/metadata/category_codes", methods=["GET"])
def query_category_codes():
    return parse_json(sspi_metadata.category_codes())


@query_bp.route("/metadata/category_detail/<intermediate_code>", methods=["GET"])
def query_category_detail(intermediate_code):
    return parse_json(sspi_metadata.get_category_detail(intermediate_code))


@query_bp.route("/metadata/pillar_details")
def query_pillar_details():
    return parse_json(sspi_metadata.pillar_details())


@query_bp.route("/metadata/pillar_codes", methods=["GET"])
def query_pillar_codes():
    return parse_json(sspi_metadata.pillar_codes())


@query_bp.route("/metadata/pillar_detail/<intermediate_code>", methods=["GET"])
def query_pillar_detail(intermediate_code):
    return parse_json(sspi_metadata.get_pillar_detail(intermediate_code))


@query_bp.route("/metadata/item_detail/<item_code>", methods=["GET"])
def query_item_detail(item_code):
    return parse_json(sspi_metadata.get_item_detail(item_code))
