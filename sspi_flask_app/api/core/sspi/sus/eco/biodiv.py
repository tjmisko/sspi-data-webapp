import logging
from flask import Response
from flask import current_app as app
from flask_login import current_user, login_required
from sspi_flask_app.api.core.sspi import compute_bp, impute_bp
from sspi_flask_app.api.datasource.unsdg import (
    collect_sdg_indicator_data,
    extract_sdg,
    filter_sdg,
)
from sspi_flask_app.api.resources.utilities import parse_json, score_indicator
from sspi_flask_app.models.database import (
    sspi_clean_api_data,
    sspi_indicator_data,
    sspi_incomplete_indicator_data,
    sspi_imputed_data,
)

log = logging.getLogger(__name__)


@compute_bp.route("/BIODIV", methods=["POST"])
@login_required
def compute_biodiv():
    def score_biodiv(UNSDG_MARINE, UNSDG_TERRST, UNSDG_FRSHWT):
        return (UNSDG_MARINE + UNSDG_TERRST + UNSDG_FRSHWT) / 3 / 100

    sspi_indicator_data.delete_many({"IndicatorCode": "BIODIV"})
    sspi_incomplete_indicator_data.delete_many({"IndicatorCode": "BIODIV"})
    dataset_list = sspi_clean_api_data.find(
        {"DatasetCode": {"$in": ["UNSDG_MARINE", "UNSDG_TERRST", "UNSDG_FRSHWT"]}}
    )
    clean_list, incomplete_list = score_indicator(
        dataset_list,
        "BIODIV",
        score_function=score_biodiv,
        unit="Index",
    )
    sspi_indicator_data.insert_many(clean_list)
    sspi_incomplete_indicator_data.insert_many(incomplete_list)
    return parse_json(clean_list)


@impute_bp.route("/BIODIV", methods=["POST"])
@login_required
def impute_biodiv():
    sspi_imputed_data.delete_many({"IndicatorCode": "BIODIV"})
    clean_list = sspi_clean_api_data.find({"IndicatorCode": "BIODIV"})
    incomplete_list = sspi_incomplete_indicator_data.find({"IndicatorCode": "BIODIV"})
    # Do imputation logic here
    documents = []
    count = sspi_imputed_data.insert_many(documents)
    return parse_json(documents)
