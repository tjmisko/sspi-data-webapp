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
    filter_incomplete_data,
    score_single_indicator
)

from sspi_flask_app.api.datasource.sdg import (
    extract_sdg_pivot_data_to_nested_dictionary,
    flatten_nested_dictionary_biodiv,
    flatten_nested_dictionary_redlst,
)


@compute_bp.route("/BIODIV", methods=['GET'])
@login_required
def compute_biodiv():
    app.logger.info("Running /api/v1/compute/BIODIV")
    sspi_clean_api_data.delete_many({"IndicatorCode": "BIODIV"})
    raw_data = sspi_raw_api_data.fetch_raw_data("BIODIV")
    intermediate_obs_dict = extract_sdg_pivot_data_to_nested_dictionary(
        raw_data)
    final_data_list = flatten_nested_dictionary_biodiv(intermediate_obs_dict)
    zipped_document_list = zip_intermediates(final_data_list, "BIODIV",
                                             ScoreFunction=lambda MARINE, TERRST, FRSHWT: 0.33 *
                                             MARINE + 0.33 * TERRST + 0.33 * FRSHWT,
                                             ScoreBy="Score")
    clean_observations, incomplete_observations = filter_incomplete_data(
        zipped_document_list)
    sspi_clean_api_data.insert_many(clean_observations)
    print(incomplete_observations)
    return parse_json(clean_observations)


@compute_bp.route("/REDLST", methods=['GET'])
@login_required
def compute_rdlst():
    app.logger.info("Running /api/v1/compute/REDLST")
    sspi_clean_api_data.delete_many({"IndicatorCode": "REDLST"})
    raw_data = sspi_raw_api_data.fetch_raw_data("REDLST")
    intermediate_obs_dict = extract_sdg_pivot_data_to_nested_dictionary(
        raw_data)
    final_list = flatten_nested_dictionary_redlst(intermediate_obs_dict)
    meta_data_added = score_single_indicator(final_list, "REDLST")
    clean_document_list, incomplete_observations = filter_incomplete_data(
        meta_data_added)
    sspi_clean_api_data.insert_many(clean_document_list)
    print(incomplete_observations)
    return parse_json(clean_document_list)
