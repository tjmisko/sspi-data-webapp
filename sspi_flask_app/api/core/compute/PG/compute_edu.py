from flask import current_app as app
from flask_login import login_required
from sspi_flask_app.api.core.compute import compute_bp
from sspi_flask_app.models.database import (
    sspi_raw_api_data,
    sspi_clean_api_data
)
from sspi_flask_app.api.resources.utilities import (
    parse_json,
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
    app.logger.info("Running /api/v1/compute/ENRPRI")
    sspi_clean_api_data.delete_many({"IndicatorCode": "ENRPRI"})
    raw_data = sspi_raw_api_data.fetch_raw_data("ENRPRI")
    description = "Net enrollment in primary school (%)"
    cleaned_list = cleanUISdata(raw_data, "ENRPRI", "Percent", description)
    scored_list = score_single_indicator(cleaned_list, "ENRPRI")
    clean_document_list, incomplete_observations = filter_incomplete_data(
        scored_list)
    sspi_clean_api_data.insert_many(clean_document_list)
    return parse_json(clean_document_list)


@compute_bp.route("/ENRSEC", methods=['GET'])
@login_required
def compute_enrsec():
    app.logger.info("Running /api/v1/compute/ENRSEC")
    sspi_clean_api_data.delete_many({"IndicatorCode": "ENRSEC"})
    raw_data = sspi_raw_api_data.fetch_raw_data("ENRSEC")
    description = "Net enrollment in lower secondary school (%)"
    cleaned_list = cleanUISdata(raw_data, "ENRSEC", "Percent", description)
    scored_list = score_single_indicator(cleaned_list, "ENRSEC")
    clean_document_list, incomplete_observations = filter_incomplete_data(
        scored_list)
    sspi_clean_api_data.insert_many(clean_document_list)
    return parse_json(clean_document_list)


@compute_bp.route("/PUPTCH", methods=['GET'])
@login_required
def compute_puptch():
    app.logger.info("Running /api/v1/compute/PUPTCH")
    sspi_clean_api_data.delete_many({"IndicatorCode": "PUPTCH"})
    raw_data = sspi_raw_api_data.fetch_raw_data("PUPTCH")
    cleaned_list = clean_wb_data(raw_data, "PUPTCH", "Average")
    scored_list = score_single_indicator(cleaned_list, "PUPTCH")
    clean_document_list, incomplete_observations = filter_incomplete_data(
        scored_list)
    sspi_clean_api_data.insert_many(clean_document_list)
    return parse_json(clean_document_list)
