from flask import Blueprint, current_app as app
from sspi_flask_app.models.database import (
    sspi_clean_api_data,
    sspi_incomplete_api_data,
    sspi_main_data_v3,
    sspi_metadata,
    sspi_raw_api_data,
    sspi_imputed_data
)
from sspi_flask_app.api.resources.utilities import (
    parse_json,
    extrapolate_backward,
    extrapolate_forward,
    interpolate_linear
)


impute_bp = Blueprint(
    "impute_bp", __name__,
    template_folder="templates",
    static_folder="static",
    url_prefix="/impute"
)


@impute_bp.route("/BIODIV", methods=["GET"])
def impute_biodiv():
    sspi_imputed_data.delete_many({"IndicatorCode": "SENIOR"})
    clean_list = sspi_clean_api_data.find({"IndicatorCode": "BIODIV"})
    incomplete_list = sspi_imputed_data.find({"IndicatorCode": "BIODIV"})
    # Do imputation logic here
    documents = []
    count = sspi_imputed_data.insert_many(documents)
    return parse_json(documents)


@impute_bp.route("/SENIOR", methods=["GET"])
def impute_senior(IndicatorCode):
    sspi_imputed_data.delete_many({"IndicatorCode": "SENIOR"})
    clean_data = sspi_clean_api_data.find({"IndicatorCode": "SENIOR"})
    incomplete_list = sspi_imputed_data.find({"IndicatorCode": "SENIOR"})
    # Do imputation logic here
    count = sspi_imputed_data.insert_many([])
    return f"{count} documents inserted into sspi_imputed_data."
