import json
from flask import Blueprint, request, jsonify
from flask_login import login_required

from sspi_flask_app.models.database import sspi_bulk_data, sspi_metadata, sspi_main_data_v3

load_bp = Blueprint("load_bp", __name__,
                    template_folder="templates", 
                    static_folder="static")

@load_bp.route("/load/<IndicatorCode>", methods=["POST"])
@login_required
def load(IndicatorCode):
    """
    Utility function that handles loading data from the API into the database
    """
    observations_list = json.loads(request.get_json())
    count = sspi_bulk_data.insert_many(observations_list)
    return f"Inserted {count} observations into database for Indicator {IndicatorCode}."

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

