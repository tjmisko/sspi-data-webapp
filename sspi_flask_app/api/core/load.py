import os
import json
import pandas as pd
from flask import Blueprint, request, current_app as app
from flask_login import login_required

from ... import sspi_bulk_data, sspi_metadata

load_bp = Blueprint("load_bp", __name__,
                    template_folder="templates", 
                    static_folder="static")
                   

@load_bp.route("/load/<IndicatorCode>", methods=["POST"])
@login_required
def load():
    """
    Utility function that handles loading data from the API into the database
    """
    observations_list = json.loads(request.get_json())
    count = sspi_bulk_data.insert_many(observations_list)
    return f"Inserted {count} observations into database."

@load_bp.route("/load/sspi_metadata", methods=['GET'])
@login_required
def load_metadata():
    count = sspi_metadata.load()
    return f"Inserted {count} metadata documents into database."

@load_bp.route("/load/sspi_main_data_v3", methods=['POST'])
@login_required
def load_maindata():
    local_path = os.path.join(app.instance_path, "local")
    sspi_main_data_v3 = pd.read_csv(os.path.join(local_path, "SSPIMainDataV3.csv"))
    sspi_main_data_v3 = build_main_data(sspi_main_data_v3)
    return "success!"

def build_main_data(sspi_main_data_v3:pd.DataFrame):
    """
    Utility function that builds the main data JSON list from the SSPIMainDataV3.csv file
    """
    sspi_main_data_v3 = sspi_main_data_v3.drop(columns=["Unnamed: 0"])
    return sspi_main_data_v3.to_json(orient="records")

