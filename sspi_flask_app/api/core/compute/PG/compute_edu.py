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
from sspi_flask_app.api.datasource.uis import (
    cleanUISdata
)
from sspi_flask_app.api.datasource.worldbank import (
    clean_wb_data
)


@compute_bp.route("/ENRPRI", methods=['GET'])
@login_required
def compute_enrpri():
    if not sspi_raw_api_data.raw_data_available("ENRPRI"):
        return redirect(url_for("api_bp.collect_bp.ENRPRI"))
    raw_data = sspi_raw_api_data.fetch_raw_data("ENRPRI")
    cleaned_list = cleanUISdata(raw_data, "ENRPRI", "Percent", "Net enrollment in primary school (%)")
    scored_list = score_single_indicator(cleaned_list, "ENRPRI")
    clean_document_list, incomplete_observations = filter_incomplete_data(scored_list)
    sspi_clean_api_data.insert_many(clean_document_list)
    return parse_json(clean_document_list)

@compute_bp.route("/ENRSEC", methods=['GET'])
@login_required
def compute_enrsec():
    if not sspi_raw_api_data.raw_data_available("ENRSEC"):
        return redirect(url_for("api_bp.collect_bp.ENRSEC"))
    raw_data = sspi_raw_api_data.fetch_raw_data("ENRSEC")
    cleaned_list = cleanUISdata(raw_data, "ENRSEC", "Percent", "Net enrollment in lower secondary school (%)")
    scored_list = score_single_indicator(cleaned_list, "ENRSEC")
    clean_document_list, incomplete_observations = filter_incomplete_data(scored_list)
    sspi_clean_api_data.insert_many(clean_document_list)
    return parse_json(clean_document_list)


@compute_bp.route("/PUPTCH", methods=['GET'])
@login_required
def compute_puptch():
    if not sspi_raw_api_data.raw_data_available("PUPTCH"):
        return redirect(url_for("api_bp.collect_bp.PUPTCH"))
    raw_data = sspi_raw_api_data.fetch_raw_data("PUPTCH")
    cleaned_list = clean_wb_data(raw_data, "PUPTCH", "Average")
    scored_list = score_single_indicator(cleaned_list, "PUPTCH")
    clean_document_list, incomplete_observations = filter_incomplete_data(scored_list)
    sspi_clean_api_data.insert_many(clean_document_list)
    return parse_json(clean_document_list)
