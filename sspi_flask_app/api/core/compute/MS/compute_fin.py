from flask import redirect, url_for
from flask_login import login_required
from sspi_flask_app.api.core.compute import compute_bp
from sspi_flask_app.models.database import (
    sspi_raw_api_data,
    sspi_clean_api_data
)
from sspi_flask_app.api.resources.utilities import (
    parse_json,
    zip_intermediates,
    filter_incomplete_data,
    score_single_indicator
)
from sspi_flask_app.api.datasource.worldbank import (
    clean_wb_data
)


@compute_bp.route("/FDEPTH", methods=['GET'])
@login_required
def compute_fdepth():
    if not sspi_raw_api_data.raw_data_available("FDEPTH"):
        return redirect(url_for("collect_bp.FDEPTH"))
    credit_raw = sspi_raw_api_data.fetch_raw_data(
        "FDEPTH", IntermediateCode="CREDIT")
    credit_clean = clean_wb_data(credit_raw, "FDEPTH", unit="Percent")
    deposit_raw = sspi_raw_api_data.fetch_raw_data(
        "FDEPTH", IntermediateCode="DPOSIT")
    deposit_clean = clean_wb_data(deposit_raw, "FDEPTH", unit="Percent")
    combined_list = credit_clean + deposit_clean
    cleaned_list = zip_intermediates(combined_list, "FDEPTH",
                                     ScoreFunction=lambda CREDIT, DPOSIT: 0.5 * CREDIT + 0.5 * DPOSIT,
                                     ScoreBy="Score")
    filtered_list, incomplete_data = filter_incomplete_data(cleaned_list)
    sspi_clean_api_data.insert_many(filtered_list)
    print(incomplete_data)
    return parse_json(filtered_list)


@compute_bp.route("/PUBACC", methods=['GET'])
@login_required
def compute_pubacc():
    if not sspi_raw_api_data.raw_data_available("PUBACC"):
        return redirect(url_for("collect_bp.PUBACC"))
    pubacc_raw = sspi_raw_api_data.fetch_raw_data("PUBACC")
    pubacc_clean = clean_wb_data(pubacc_raw, "PUBACC", unit="Percent")
    pubacc_clean = score_single_indicator(pubacc_clean, "PUBACC")
    sspi_clean_api_data.insert_many(pubacc_clean)
    return parse_json(pubacc_clean)
