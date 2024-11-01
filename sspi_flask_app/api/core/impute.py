from flask import Blueprint, request
from sspi_flask_app.models.database import (
    sspi_clean_api_data,
    sspi_main_data_v3,
    sspi_metadata,
    sspi_raw_api_data,
    sspi_imputed_data
)
from ..resources.utilities import parse_json


impute_bp = Blueprint("impute_bp", __name__,
                      template_folder="templates",
                      static_folder="static",
                      url_prefix="/impute")

@impute_bp.route("/IndicatorCode", methods=["POST"])
def impute(IndicatorCode):
    data = parse_json(request.get_json())
    sspi_imputed_data.insert_many(data)
    return f"Inserted {len(data)} documents into the database"
