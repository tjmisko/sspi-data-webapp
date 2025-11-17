import json
from flask import Blueprint, Response, request, current_app as app
from sspi_flask_app.api.resources.utilities import lookup_database
from flask_login import login_required
from sspi_flask_app.models.database import (
    sspi_metadata,
    sspi_static_data_2018)

from sspi_flask_app.auth.decorators import admin_required

load_bp = Blueprint(
    "load_bp", __name__,
    template_folder="templates",
    static_folder="static",
    url_prefix="/load"
)


@load_bp.route("/<database_name>", methods=["POST"])
@admin_required
def load(database_name):
    """
    Utility function that handles loading data from the API into the database
    """
    database = lookup_database(database_name)
    observations_list = json.loads(request.get_json())
    count = database.insert_many(observations_list)
    message = f"Inserted {count} documents into {database_name}"
    app.logger.info(message)
    return Response(message, status=200, mimetype="text/plain")


@load_bp.route("/sspi_static_data_2018", methods=['GET'])
@admin_required
def load_maindata():
    count = sspi_static_data_2018.load()
    return f"Inserted {count} main data documents into database."


@load_bp.route("/sspi_metadata", methods=['GET'])
@admin_required
def load_metadata():
    count = sspi_metadata.load()
    return f"Inserted {count} metadata documents into database."
