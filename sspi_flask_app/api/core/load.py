import json
from flask import Blueprint, request
from flask_login import login_required

from ..resources.utilities import parse_json
from ... import sspi_bulk_data
from ..resources.validators import validate_observation_list

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
    print(type(observations_list))
    ### Check that observations match the expected format and declared IndicatorCode
    validate_observation_list(observations_list, "sspi_bulk_data", IndicatorCode)
    ### If format valid, insert
    count = sspi_bulk_data.insert_many(observations_list)
    return f"Inserted {count} observations into database."

@dashboard_bp.route("/local/upload", methods=['GET'])
@login_required
def upload_local_data():
    local_path = os.path.join(app.instance_path, "local")
    indicator_details = pd.read_csv(os.path.join(local_path, "IndicatorDetails.csv"))
    intermediate_details = pd.read_csv(os.path.join(local_path, "IntermediateDetails.csv"))
    sspi_main_data_v3 = pd.read_csv(os.path.join(local_path, "SSPIMainDataV3.csv"))
    sspi_main_data_v3 = build_main_data(
    return app.instance_path
