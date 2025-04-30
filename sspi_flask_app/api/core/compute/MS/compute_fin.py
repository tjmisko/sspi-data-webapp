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
from sspi_flask_app.api.datasource.worldbank import (
    clean_wb_data
)


@compute_bp.route("/FDEPTH", methods=['GET'])
@login_required
def compute_fdepth():
    app.logger.info("Running /api/v1/compute/FDEPTH")
    sspi_clean_api_data.delete_many({"IndicatorCode": "FDEPTH"})
    credit_raw = sspi_raw_api_data.fetch_raw_data(
        "FDEPTH", IntermediateCode="CREDIT")
    credit_clean = clean_wb_data(credit_raw, "FDEPTH", unit="Percent")
    deposit_raw = sspi_raw_api_data.fetch_raw_data(
        "FDEPTH", IntermediateCode="DPOSIT")
    deposit_clean = clean_wb_data(deposit_raw, "FDEPTH", unit="Percent")
    combined_list = credit_clean + deposit_clean
    clean_list, incomplete_list = zip_intermediates(
        combined_list, "FDEPTH",
        ScoreFunction=lambda CREDIT, DPOSIT: (CREDIT + DPOSIT) / 2,
        ScoreBy="Score"
    )
    sspi_clean_api_data.insert_many(clean_list)
    sspi_incomplete_api_data.insert_many(incomplete_list)
    return parse_json(clean_list)


@compute_bp.route("/PUBACC", methods=['GET'])
@login_required
def compute_pubacc():
    app.logger.info("Running /api/v1/compute/PUBACC")
    sspi_clean_api_data.delete_many({"IndicatorCode": "PUBACC"})
    pubacc_raw = sspi_raw_api_data.fetch_raw_data("PUBACC")
    pubacc_clean = clean_wb_data(pubacc_raw, "PUBACC", unit="Percent")
    pubacc_clean = score_single_indicator(pubacc_clean, "PUBACC")
    sspi_clean_api_data.insert_many(pubacc_clean)
    return parse_json(pubacc_clean)
