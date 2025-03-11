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
from sspi_flask_app.api.datasource.prisonstudies import (
    scrape_stored_pages_for_data
)


@compute_bp.route("/PRISON", methods=['GET'])
@login_required
def compute_prison():
    # clean_data_list, missing_data_list = scrape_stored_pages_for_data()
    # final_list, incomplete_observations = compute_prison_rate(clean_data_list)
    # print(f"Missing from World Prison Brief: {missing_data_list}")
    # print(f"Missing from UN population: {incomplete_observations}")
    return final_list


@compute_bp.route("/DRKWAT")
@login_required
def compute_drkwat():
    if not sspi_raw_api_data.raw_data_available("DRKWAT"):
        return redirect(url_for("api_bp.collect_bp.DRKWAT"))
    raw_data = sspi_raw_api_data.fetch_raw_data("DRKWAT")
    cleaned = clean_wb_data(raw_data, "DRKWAT", "Percent")
    scored = score_single_indicator(cleaned, "DRKWAT")
    filtered_list, incomplete_observations = filter_incomplete_data(scored)
    sspi_clean_api_data.insert_many(filtered_list)
    print(incomplete_observations)
    return parse_json(filtered_list)


@compute_bp.route("/SANSRV")
@login_required
def compute_sansrv():
    if not sspi_raw_api_data.raw_data_available("SANSRV"):
        return redirect(url_for("api_bp.collect_bp.SANSRV"))
    raw_data = sspi_raw_api_data.fetch_raw_data("SANSRV")
    cleaned = clean_wb_data(raw_data, "SANSRV", "Percent")
    scored = score_single_indicator(cleaned, "SANSRV")
    filtered_list, incomplete_observations = filter_incomplete_data(scored)
    sspi_clean_api_data.insert_many(filtered_list)
    print(incomplete_observations)
    return parse_json(filtered_list)
