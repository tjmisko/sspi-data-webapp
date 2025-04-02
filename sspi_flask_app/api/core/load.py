import json
from flask import Blueprint, Response, request
from sspi_flask_app.api.resources.utilities import lookup_database
from flask_login import login_required
from sspi_flask_app.models.database import (
    sspi_metadata,
    sspi_main_data_v3
)

load_bp = Blueprint(
    "load_bp", __name__,
    template_folder="templates",
    static_folder="static"
)


@load_bp.route("/load/<database_name>/<IndicatorCode>", methods=["POST"])
@login_required
def load(database_name, IndicatorCode):
    """
    Utility function that handles loading data from the API into the database
    """
    database = lookup_database(database_name)
    observations_list = json.loads(request.get_json())
    count = database.insert_many(observations_list)
    message = (
        f"Inserted {count} documents into {database_name} for "
        f"IndicatorCode {IndicatorCode}"
    )
    return Response(message, status=200, mimetype="text/plain")


@load_bp.route("/load/sspi_main_data_v3", methods=['GET'])
@login_required
def load_maindata():
    count = sspi_main_data_v3.load()
    return f"Inserted {count} main data documents into database."


@load_bp.route("/load/sspi_metadata", methods=['GET'])
@login_required
def load_metadata():
    count = sspi_metadata.load()
    return f"Inserted {count} metadata documents into database."
