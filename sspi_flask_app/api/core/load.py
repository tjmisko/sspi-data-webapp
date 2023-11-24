import json
from flask import Blueprint, request
from flask_login import login_required

from ... import sspi_bulk_data
from ...models.errors import InvalidObservationFormatError, InvalidDatabaseError
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
    try:
        validate_observation_list(observations_list, "sspi_bulk_data", IndicatorCode)
    except InvalidObservationFormatError as e:
        return f"Error: Data Not Loaded!\n{e}", 400
    except InvalidDatabaseError as e:
        return f"Error: Data Not Loaded!\n{e}", 400
    ### If format valid, insert
    count = sspi_bulk_data.insert_many(observations_list)
    return f"Inserted {count} observations into database."