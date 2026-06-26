import json
from flask import Blueprint, Response, request, current_app as app
from sspi_flask_app.api.resources.utilities import lookup_database
from flask_login import login_required
from sspi_flask_app.models.database import (
    sspi_metadata,
    sspi_static_data_2018)
from sspi_flask_app import csrf

from sspi_flask_app.auth.decorators import admin_required

load_bp = Blueprint(
    "load_bp", __name__,
    template_folder="templates",
    static_folder="static",
    url_prefix="/load"
)


@load_bp.route("/<database_name>", methods=["POST"])
@csrf.exempt  # API endpoint accessed programmatically (CLI/scripts), not browser forms
@admin_required
def load(database_name):
    """
    Utility function that handles loading data from the API into the database.
    This is a programmatic API endpoint accessed via CLI/scripts, not browser forms.
    CSRF exemption is appropriate here since it uses admin authentication and
    is not subject to browser-based CSRF attacks.
    """
    database = lookup_database(database_name)
    observations_list = request.get_json()
    # Back-compat: older/external connectors double-encode the body
    # (json=json.dumps(obs_lst)), so get_json() yields a JSON string rather
    # than the list. Decode once more in that case. Current connectors send
    # the list directly. This shim can be removed once all clients are
    # confirmed migrated to single-encoding.
    if isinstance(observations_list, str):
        observations_list = json.loads(observations_list)
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
