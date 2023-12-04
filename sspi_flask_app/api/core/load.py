import json
from flask import Blueprint, request
from flask_login import login_required

from ... import sspi_bulk_data

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
    ### If format valid, insert
    count = sspi_bulk_data.insert_many(observations_list)
    return f"Inserted {count} observations into database."
