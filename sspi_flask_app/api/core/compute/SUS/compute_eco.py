from flask import current_app as app
from flask_login import login_required
from sspi_flask_app.api.core.compute import compute_bp
from sspi_flask_app.models.database import (
    sspi_raw_api_data,
    sspi_clean_api_data,
    sspi_incomplete_api_data
)
from sspi_flask_app.api.resources.utilities import (
    parse_json,
    zip_intermediates,
    score_single_indicator
)

from sspi_flask_app.api.datasource.sdg import (
    extract_sdg,
    filter_sdg,
)


@compute_bp.route("/BIODIV", methods=['GET'])
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
        "ER_PTD_FRHWTR": "FRSHWT"
    }
    rename_map = {
        "units": "Unit",
        "seriesDescription": "Description"
    }
    drop_list = [
        "goal", "indicator", "series", "seriesCount", "target",
        "geoAreaCode", "geoAreaName"
    ]
    intermediate_list = filter_sdg(
        extracted_biodiv,
        idcode_map,
        rename_map,
        drop_list,
    )
    clean_list, incomplete_list = zip_intermediates(
        intermediate_list, "BIODIV",
        ScoreFunction=lambda MARINE, TERRST, FRSHWT: (MARINE + TERRST + FRSHWT) / 3,
        ScoreBy="Score"
    )
    sspi_clean_api_data.insert_many(clean_list)
    sspi_incomplete_api_data.insert_many(incomplete_list)
    return parse_json(clean_list)


@compute_bp.route("/REDLST", methods=['GET'])
@login_required
def compute_rdlst():
    app.logger.info("Running /api/v1/compute/REDLST")
    sspi_clean_api_data.delete_many({"IndicatorCode": "REDLST"})
    raw_data = sspi_raw_api_data.fetch_raw_data("REDLST")
    extracted_redlst = extract_sdg(raw_data)
    idcode_map = {
        "ER_RSK_LST": "REDLST",
    }
    filtered_redlst = filter_sdg(
        extracted_redlst,
        idcode_map,
    )
    scored_data = score_single_indicator(filtered_redlst, "REDLST")
    sspi_clean_api_data.insert_many(scored_data)
    return parse_json(scored_data)
