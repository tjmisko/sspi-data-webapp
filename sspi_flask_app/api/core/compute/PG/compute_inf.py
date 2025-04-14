from flask import current_app as app
from flask_login import login_required
from sspi_flask_app.api.core.compute import compute_bp
from sspi_flask_app.models.database import (
    sspi_raw_api_data,
    sspi_clean_api_data
)
from sspi_flask_app.api.resources.utilities import (
    parse_json,
    zip_intermediates,
    score_single_indicator
)


from sspi_flask_app.api.datasource.worldbank import (
    clean_wb_data
)
from sspi_flask_app.api.datasource.sdg import (
    extract_sdg,
    filter_sdg
)


@compute_bp.route("/INTRNT", methods=['GET'])
@login_required
def compute_intrnt():
    app.logger.info("Running /api/v1/compute/INTRNT")
    sspi_clean_api_data.delete_many({"IndicatorCode": "INTRNT"})
    # AVINTR (WorldBank)
    wb_raw = sspi_raw_api_data.fetch_raw_data(
        "INTRNT", IntermediateCode="AVINTR"
    )
    clean_avintr = clean_wb_data(wb_raw, "INTRNT", unit="Percent")
    # QUINTR (SDG)
    sdg_raw = sspi_raw_api_data.fetch_raw_data(
        "INTRNT", IntermediateCode="QUINTR"
    )
    extracted_quintr = extract_sdg(sdg_raw)
    idcode_map = {"IT_NET_BBND": "QUINTR"}
    filtered_quintr = filter_sdg(
        extracted_quintr, idcode_map,
        type_of_speed="10MBPS"
    )
    for obs in filtered_quintr:
        obs["IntermediateCode"] = "QUINTR"
    clean_list, incomplete_list = zip_intermediates(
        clean_avintr + filtered_quintr, "INTRNT",
        ScoreFunction=lambda AVINTR, QUINTR: (AVINTR + QUINTR) / 2,
        ScoreBy="Score"
    )
    sspi_clean_api_data.insert_many(clean_list)
    print(incomplete_list)
    return parse_json(clean_list)


@compute_bp.route("/DRKWAT")
@login_required
def compute_drkwat():
    app.logger.info("Running /api/v1/compute/DRKWAT")
    sspi_clean_api_data.delete_many({"IndicatorCode": "DRKWAT"})
    raw_data = sspi_raw_api_data.fetch_raw_data("DRKWAT")
    cleaned = clean_wb_data(raw_data, "DRKWAT", "Percent")
    scored_list = score_single_indicator(cleaned, "DRKWAT")
    sspi_clean_api_data.insert_many(scored_list)
    return parse_json(scored_list)


@compute_bp.route("/SANSRV")
@login_required
def compute_sansrv():
    app.logger.info("Running /api/v1/compute/SANSRV")
    sspi_clean_api_data.delete_many({"IndicatorCode": "SANSRV"})
    raw_data = sspi_raw_api_data.fetch_raw_data("SANSRV")
    cleaned = clean_wb_data(raw_data, "SANSRV", "Percent")
    scored_list = score_single_indicator(cleaned, "SANSRV")
    sspi_clean_api_data.insert_many(scored_list)
    return parse_json(scored_list)
