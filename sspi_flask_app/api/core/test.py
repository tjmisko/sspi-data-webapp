import json
from flask import Blueprint, request
from flask_login import login_required

from sspi_flask_app.models.database import SSPIRawAPIData

from ..resources.utilities import parse_json
from ... import sspi_bulk_data
from ..resources.validators import validate_observation_list

test_bp = Blueprint("test_bp", __name__,
                    template_folder="templates", 
                    static_folder="static")
                   

@test_bp.route("/load/<IndicatorCode>", methods=["POST"])
@login_required
def draw_three(IndicatorCode):
    """
    Testing utility function that pulls three random observations from SSPIRawAPIData
    """
    return SSPIRawAPIData.sample(3)