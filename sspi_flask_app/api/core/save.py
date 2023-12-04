from datetime import datetime
import json
import os
from flask import Response, current_app as app
from flask import Blueprint, request
from flask_login import login_required

from sspi_flask_app.models.database import SSPIRawAPIData

from ..resources.utilities import lookup_database, parse_json
from ... import sspidb

save_bp = Blueprint("save_bp", __name__,
                    template_folder="templates", 
                    static_folder="static")
                   

@save_bp.route("/save/<database_name>", methods=["GET"])
@login_required
def save_database_protected_route(database_name):
    """
    Creates a local snapshot of a SSPI database
    """
    return save_database(database_name, os.path.join(os.path.dirname(app.instance_path), "snapshots"))

@save_bp.route("/save", methods=["GET"])
@login_required
def save_all():
    """
    Creates a local snapshot of all SSPI databases
    """
    snapshot_directory = os.path.join(os.path.dirname(app.instance_path), "snapshots")
    def save_iterator(snapshot_directory):
        for i, database_name in enumerate(sspidb.list_collection_names()):
            yield f"Saving {database_name} to local ({i+1}/{len(sspidb.list_collection_names())})\n"
            save_database(database_name, snapshot_directory)
    return Response(save_iterator(snapshot_directory), mimetype="text/event-stream")

def save_database(database_name, snapshot_directory):
    """
    Saves a snapshot off all databases in the snapshot folder
    """
    database = lookup_database(database_name)
    database_contents = parse_json(database.find({}))
    datetime_str = datetime.now().strftime("%Y-%m-%d")
    snapshots_new_dir = os.path.join(snapshot_directory, datetime_str)
    if not os.path.exists(snapshots_new_dir):
        os.mkdir(snapshots_new_dir)
    with open(f"{snapshots_new_dir}/{datetime_str} - {database_name}.json", "w+") as f:
        json.dump(database_contents, f)
    return database_contents
