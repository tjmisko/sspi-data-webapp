from flask import Blueprint, jsonify, request
from pymongo.errors import OperationFailure

from sspi_flask_app.api.resources.utilities import lookup_database, parse_json
from sspi_flask_app.api.resources.query_builder import get_query_params
from sspi_flask_app.models.database import sspi_metadata
from sspi_flask_app.models.errors import InvalidDatabaseError, InvalidQueryError

query_bp = Blueprint(
    "query_bp",
    __name__,
    template_folder="templates",
    static_folder="static",
    url_prefix="/query",
)


@query_bp.route("/<database_string>")
def query_database(database_string):
    try:
        database = lookup_database(database_string)
        query_params = get_query_params(request, database)
        limit = request.args.get("limit", type=int)
        return jsonify(
            parse_json(database.find(query_params, options={"_id": 0}, limit=limit))
        )
    except InvalidDatabaseError as e:
        return jsonify({"error": "Invalid Database Provided: " + str(e)}), 400
    except InvalidQueryError as e:
        return jsonify({"error": str(e)}), 400
    except OperationFailure as e:
        return jsonify({"error": "Database Operation Failed: " + str(e)}), 400


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


@query_bp.route("/metadata/dataset_details")
def query_dataset_details():
    return parse_json(sspi_metadata.dataset_details())


@query_bp.route("/metadata/dataset_codes", methods=["GET"])
def query_dataset_codes():
    return parse_json(sspi_metadata.dataset_codes())


@query_bp.route("/metadata/dataset_detail/<dataset_code>", methods=["GET"])
def query_dataset_detail(dataset_code):
    return parse_json(sspi_metadata.get_dataset_detail(dataset_code))


@query_bp.route("/metadata/category_details")
def query_category_details():
    return parse_json(sspi_metadata.category_details())


@query_bp.route("/metadata/category_codes", methods=["GET"])
def query_category_codes():
    return parse_json(sspi_metadata.category_codes())


@query_bp.route("/metadata/category_detail/<dataset_code>", methods=["GET"])
def query_category_detail(dataset_code):
    return parse_json(sspi_metadata.get_category_detail(dataset_code))


@query_bp.route("/metadata/pillar_details")
def query_pillar_details():
    return parse_json(sspi_metadata.pillar_details())


@query_bp.route("/metadata/pillar_codes", methods=["GET"])
def query_pillar_codes():
    return parse_json(sspi_metadata.pillar_codes())


@query_bp.route("/metadata/pillar_detail/<pillar_code>", methods=["GET"])
def query_pillar_detail(pillar_code):
    return parse_json(sspi_metadata.get_pillar_detail(pillar_code))


@query_bp.route("/metadata/item_details")
def query_item_details():
    return jsonify(sspi_metadata.item_details())


@query_bp.route("/metadata/item_detail/<item_code>", methods=["GET"])
def query_item_detail(item_code):
    return parse_json(sspi_metadata.get_item_detail(item_code))

@query_bp.route("/metadata/country_detail/<country_code>", methods=["GET"])
def query_country_detail(country_code):
    return jsonify(sspi_metadata.get_country_detail(country_code))

@query_bp.route("/metadata/series_detail/<series_code>", methods=["GET"])
def query_series_detail(series_code):
    series_type = sspi_metadata.get_series_type(series_code)
    if not series_type:
        return parse_json({})
    if series_type == "Dataset":
        return parse_json(sspi_metadata.get_dataset_detail(series_code))
    elif series_type == "Item":
        return parse_json(sspi_metadata.get_item_detail(series_code))
    else:
        return parse_json({})
