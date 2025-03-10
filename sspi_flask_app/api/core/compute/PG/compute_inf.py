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
from sspi_flask_app.api.datasource.sdg import (
    extract_sdg_pivot_data_to_nested_dictionary,
    flatten_nested_dictionary_intrnt,
)


@compute_bp.route("/INTRNT", methods=['GET'])
@login_required
def compute_intrnt():
    if not sspi_raw_api_data.raw_data_available("INTRNT"):
        return redirect(url_for("collect_bp.INTRNT"))
    # worldbank #
    wb_raw = sspi_raw_api_data.fetch_raw_data(
        "INTRNT", IntermediateCode="AVINTR")
    wb_clean = clean_wb_data(wb_raw, "INTRNT", unit="Percent")
    # sdg #
    sdg_raw = sspi_raw_api_data.fetch_raw_data(
        "INTRNT", IntermediateCode="QLMBPS")
    sdg_clean = extract_sdg_pivot_data_to_nested_dictionary(sdg_raw)
    sdg_clean = flatten_nested_dictionary_intrnt(sdg_clean)
    combined_list = wb_clean + sdg_clean
    cleaned_list = zip_intermediates(combined_list, "INTRNT",
                                     ScoreFunction=lambda AVINTR, QUINTR: 0.5 * AVINTR + 0.5 * QUINTR,
                                     ScoreBy="Score")
    filtered_list, incomplete_observations = filter_incomplete_data(
        cleaned_list)
    sspi_clean_api_data.insert_many(filtered_list)
    print(incomplete_observations)
    return parse_json(filtered_list)
