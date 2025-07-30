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


# def compute_biodiv_old():
#     app.logger.info("Running /api/v1/compute/BIODIV")
#     sspi_clean_api_data.delete_many({"IndicatorCode": "BIODIV"})
#     sspi_incomplete_indicator_data.delete_many({"IndicatorCode": "BIODIV"})
#     raw_data = sspi_raw_api_data.fetch_raw_data("BIODIV")
#     extracted_biodiv = extract_sdg(raw_data)
#     idcode_map = {
#         "ER_MRN_MPA": "MARINE",
#         "ER_PTD_TERR": "TERRST",
#         "ER_PTD_FRHWTR": "FRSHWT",
#     }
#     rename_map = {"units": "Unit", "seriesDescription": "Description"}
#     drop_list = [
#         "goal",
#         "indicator",
#         "series",
#         "seriesCount",
#         "target",
#         "geoAreaCode",
#         "geoAreaName",
#     ]
#     intermediate_list = filter_sdg(
#         extracted_biodiv,
#         idcode_map,
#         rename_map,
#         drop_list,
#     )

@compute_bp.route("/BIODIV", methods=["POST"])
@login_required
def compute_biodiv():
    def score_biodiv(UNSDG_MARINE, UNSDG_TERRST, UNSDG_FRSHWT):
        return (UNSDG_MARINE + UNSDG_TERRST + UNSDG_FRSHWT) / 3

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
def impute_biodiv():
    sspi_imputed_data.delete_many({"IndicatorCode": "BIODIV"})
    clean_list = sspi_clean_api_data.find({"IndicatorCode": "BIODIV"})
    incomplete_list = sspi_incomplete_indicator_data.find({"IndicatorCode": "BIODIV"})
    # Do imputation logic here
    documents = []
    count = sspi_imputed_data.insert_many(documents)
    return parse_json(documents)
