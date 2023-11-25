from datetime import datetime
import json
import os
from flask import Response, current_app as app
from flask import Blueprint, request
from flask_login import login_required

from sspi_flask_app.models.database import SSPIRawAPIData

from ..resources.utilities import lookup_database, parse_json
from ... import sspidb
from ..resources.validators import validate_observation_list

save_bp = Blueprint("save_bp", __name__,
                    template_folder="templates", 
                    static_folder="static")
                   

@save_bp.route("/save/<database_name>", methods=["GET"])
@login_required
def save_database(database_name):
    """
    Saves a snapshot off all databases
    """
    database = lookup_database(database_name)
    database_contents = parse_json(database.find({}))
    datetime_str = datetime.now().strftime("%Y-%m-%d")
    snapshots_path = os.path.join(os.path.dirname(app.instance_path), f"snapshots/{datetime_str}")
    if not os.path.exists(snapshots_path):
        os.mkdir(snapshots_path)
    with open(f"{snapshots_path}/{datetime_str} - {database_name}.json", "w+") as f:
        json.dump(database_contents, f)
    return database_contents

@save_bp.route("/save", methods=["GET"])
def save_all():
    """
    Creates a local snapshot of all SSPI databases
    """
    def save_iterator():
        for i, database_name in enumerate(sspidb.list_collection_names()):
            yield f"Saving {database_name} to local ({i}/{len(sspidb.list_collection_names())})"
            save_database(database_name)
    return Response(save_iterator(), mimetype="text/event-stream")