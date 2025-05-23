from datetime import datetime
import json
import os
from flask import Response, current_app as app
from flask import Blueprint
from flask_login import login_required
from sspi_flask_app.api.resources.utilities import lookup_database
from sspi_flask_app.models.database import sspidb, sspi_raw_api_data
import logging

log = logging.getLogger(__name__)

save_bp = Blueprint(
    "save_bp",
    __name__,
    template_folder="templates",
    static_folder="static"
)


@save_bp.route("/save/<database_name>", methods=["GET"])
@login_required
def save_database(database_name):
    """
    Creates a local snapshot of a SSPI database
    """
    snapshot_dir = os.environ.get("SSPI_SNAPSHOT_DIR", "")
    if not snapshot_dir:
        snapshot_dir = os.path.join(
            os.path.dirname(app.instance_path), "snapshots"
        )
    return save_database_image(database_name, snapshot_dir)


@save_bp.route("/save", methods=["GET"])
@login_required
def save_all():
    """
    Creates a local snapshot of all SSPI databases
    """
    snapshot_directory = os.path.join(
        os.path.dirname(app.instance_path), "snapshots"
    )

    def save_iterator(snapshot_directory):
        for i, database_name in enumerate(sspidb.list_collection_names()):
            yield f"Saving {database_name} ( {i + 1} / {len(sspidb.list_collection_names())} )\n"
            yield from save_database_image(database_name, snapshot_directory)
    return Response(save_iterator(snapshot_directory), mimetype="text/event-stream")


def save_database_image(database_name, snapshot_directory):
    """
    Saves a snapshot off all databases in the snapshot folder
    """
    database = lookup_database(database_name)
    database_contents = database.find({})
    datetime_str = datetime.now().strftime("%Y-%m-%d")
    snap_time_dir = os.path.join(snapshot_directory, datetime_str)
    if not os.path.exists(snap_time_dir):
        os.makedirs(snap_time_dir, exist_ok=True)
    file = f"{snap_time_dir}/{datetime_str} - {database_name}.json"
    with open(file, "w+") as f:
        json.dump(database_contents, f)
    msg = (
        f"Dumped {len(database_contents)} records "
        f"from {database_name} to {file}\n"
    )
    log.info(msg)
    yield msg
    return
