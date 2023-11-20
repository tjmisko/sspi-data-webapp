from flask import Blueprint, request
from flask_login import login_required
from ... import sspi_bulk_data
from ..resources.errors import InvalidObservationFormatError, InvalidDatabaseError
from ..resources.validators import validate_observation_list

load_bp = Blueprint("load", __name__,
                    template_folder="templates", 
                    static_folder="static", 
                    url_prefix="/load")

@load_bp.route("/load/<IndicatorCode>", methods=["POST"])
@login_required
def load(IndicatorCode):
    """
    Utility function that handles loading data from the API into the database
    """
    observations_list = request.get_json()
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