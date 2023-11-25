from datetime import datetime
import json
import os
from flask import current_app as app
from flask import Blueprint, request
from flask_login import login_required

from sspi_flask_app.models.database import SSPIRawAPIData

from ..resources.utilities import lookup_database, parse_json
from ... import sspi_bulk_data
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
    database_contents = json.loads(database.find({}))
    datetime_str = datetime.now().strftime("%Y-%m-%d - (%H.%M)")
    print(datetime_str)
    print(os.path.dirname(app.instance_path))
    # os.mkdir(f"snapshots/{datetime_str}")
    # with open(f"snapshots/ {datetime_str}.json", "w") as f:
        # json.dump(database_contents, f)
    return "Database Saved"