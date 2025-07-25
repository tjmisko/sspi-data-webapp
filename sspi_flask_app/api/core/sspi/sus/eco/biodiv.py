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
from sspi_flask_app.api.resources.utilities import parse_json, zip_intermediates
from sspi_flask_app.models.database import (
    sspi_clean_api_data,
    sspi_imputed_data,
    sspi_incomplete_api_data,
    sspi_raw_api_data,
)

log = logging.getLogger(__name__)


# @collect_bp.route("/BIODIV", methods=["GET"])
# @login_required
# def biodiv():
#     # return Response(
#     #     collect_iterator(Username=current_user.username), mimetype="text/event-stream"
#     # )
#     return "Not implemented"


@compute_bp.route("/BIODIV", methods=["GET"])
@login_required
def compute_biodiv():
    app.logger.info("Running /api/v1/compute/BIODIV")
    sspi_clean_api_data.delete_many({"IndicatorCode": "BIODIV"})
    sspi_incomplete_api_data.delete_many({"IndicatorCode": "BIODIV"})
    raw_data = sspi_raw_api_data.fetch_raw_data("BIODIV")
    extracted_biodiv = extract_sdg(raw_data)
    idcode_map = {
        "ER_MRN_MPA": "MARINE",
        "ER_PTD_TERR": "TERRST",
        "ER_PTD_FRHWTR": "FRSHWT",
    }
    rename_map = {"units": "Unit", "seriesDescription": "Description"}
    drop_list = [
        "goal",
        "indicator",
        "series",
        "seriesCount",
        "target",
        "geoAreaCode",
        "geoAreaName",
    ]
    intermediate_list = filter_sdg(
        extracted_biodiv,
        idcode_map,
        rename_map,
        drop_list,
    )
    clean_list, incomplete_list = zip_intermediates(
        intermediate_list,
        "BIODIV",
        ScoreFunction=lambda MARINE, TERRST, FRSHWT: (MARINE + TERRST + FRSHWT) / 3,
        ScoreBy="Score",
    )
    sspi_clean_api_data.insert_many(clean_list)
    sspi_incomplete_api_data.insert_many(incomplete_list)
    return parse_json(clean_list)


@impute_bp.route("/BIODIV", methods=["POST"])
def impute_biodiv():
    sspi_imputed_data.delete_many({"IndicatorCode": "BIODIV"})
    clean_list = sspi_clean_api_data.find({"IndicatorCode": "BIODIV"})
    incomplete_list = sspi_incomplete_api_data.find({"IndicatorCode": "BIODIV"})
    # Do imputation logic here
    documents = []
    count = sspi_imputed_data.insert_many(documents)
    return parse_json(documents)
