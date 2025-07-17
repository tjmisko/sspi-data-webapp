from sspi_flask_app.api.core.sspi import collect_bp
from sspi_flask_app.api.core.sspi import compute_bp
from sspi_flask_app.api.core.sspi import impute_bp
from flask_login import login_required, current_user
from flask import Response, current_app as app
from sspi_flask_app.api.datasource.sdg import collectSDGIndicatorData
from sspi_flask_app.models.database import (
    sspi_raw_api_data,
    sspi_clean_api_data,
    sspi_incomplete_api_data,
    sspi_imputed_data
)
from sspi_flask_app.api.resources.utilities import (
    parse_json,
    zip_intermediates,
    extrapolate_backward,
    extrapolate_forward,
    slice_intermediate,
    filter_imputations,
    impute_global_average
)
from sspi_flask_app.api.datasource.sdg import extract_sdg, filter_sdg


# @collect_bp.route("/WATMAN", methods=["GET"])
# @login_required
# def watman():
#     def collect_iterator(**kwargs):
#         yield from collectSDGIndicatorData(
#             "6.4.1", "WATMAN", IntermediateCode="CWUEFF", **kwargs
#         )
#         yield from collectSDGIndicatorData(
#             "6.4.2", "WATMAN", IntermediateCode="WTSTRS", **kwargs
#         )
#     return Response(
#         collect_iterator(Username=current_user.username), mimetype="text/event-stream"
#     )


@compute_bp.route("/WATMAN", methods=['GET'])
@login_required
def compute_watman():
    """
    metadata_map = {
        "ER_H2O_WUEYST": "CWUEFF",
        "ER_H2O_STRESS": "WTSTRS"
    }
    """
    app.logger.info("Running /api/v1/compute/WATMAN")
    sspi_clean_api_data.delete_many({"IndicatorCode": "WATMAN"})
    sspi_incomplete_api_data.delete_many({"IndicatorCode": "WATMAN"})
    raw_data = sspi_raw_api_data.fetch_raw_data("WATMAN")
    watman_data = extract_sdg(raw_data)
    intermediate_map = {
        "ER_H2O_WUEYST": "CWUEFF",
        "ER_H2O_STRESS": "WTSTRS"
    }
    intermediate_list = filter_sdg(
        watman_data, intermediate_map, activity="TOTAL"
    )
    clean_list, incomplete_list = zip_intermediates(
        intermediate_list, "WATMAN",
        ScoreFunction=lambda CWUEFF, WTSTRS: (CWUEFF + WTSTRS) / 2,
        ScoreBy="Score"
    )
    sspi_clean_api_data.insert_many(clean_list)
    sspi_incomplete_api_data.insert_many(incomplete_list)
    return parse_json(clean_list)

@impute_bp.route("/WATMAN", methods=["POST"])
def impute_watman():
    mongo_query = {"IndicatorCode": "WATMAN"}
    sspi_imputed_data.delete_many(mongo_query)
    clean_list = sspi_clean_api_data.find(mongo_query)
    incomplete_list = sspi_incomplete_api_data.find(mongo_query)
    # Extract clean CWUEFF Data and Extrapolate Backwards
    clean_cwueff = slice_intermediate(clean_list, "CWUEFF") + \
        slice_intermediate(incomplete_list, "CWUEFF")
    imputed_cwueff = extrapolate_backward(
        clean_cwueff, 2000, series_id=["CountryCode", "IntermediateCode"]
    )
    imputed_cwueff = extrapolate_forward(
        imputed_cwueff, 2023, series_id=["CountryCode", "IntermediateCode"]
    )
    # Impute CWUEFF Data for SGP
    sgp_cwueff = impute_global_average("SGP", 2000, 2023, "Intermediate", "CWUEFF", clean_cwueff)
    # Extract matched WTSTRS Data
    clean_wtstrs = slice_intermediate(clean_list, "WTSTRS") + \
        slice_intermediate(incomplete_list, "WTSTRS")
    imputed_wtstrs = extrapolate_backward(
        clean_wtstrs, 2000, series_id=["CountryCode", "IntermediateCode"]
    )
    imputed_wtstrs = extrapolate_forward(
        imputed_wtstrs, 2023, series_id=["CountryCode", "IntermediateCode"]
    )
    overall_watman, missing_imputations = zip_intermediates(
        imputed_wtstrs + imputed_cwueff + sgp_cwueff, "WATMAN",
        ScoreFunction=lambda CWUEFF, WTSTRS: (CWUEFF + WTSTRS) / 2,
        ScoreBy="Score"
    )
    imputed_watman = filter_imputations(overall_watman)
    sspi_imputed_data.insert_many(imputed_watman)
    return parse_json(imputed_watman)

