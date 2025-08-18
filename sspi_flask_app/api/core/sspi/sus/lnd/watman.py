from sspi_flask_app.api.core.sspi import compute_bp
from sspi_flask_app.api.core.sspi import impute_bp
from flask_login import login_required
from flask import current_app as app
from sspi_flask_app.models.database import (
    sspi_clean_api_data,
    sspi_indicator_data,
    sspi_incomplete_indicator_data,
    sspi_imputed_data
)
from sspi_flask_app.api.resources.utilities import (
    parse_json,
    score_indicator,
    extrapolate_backward,
    extrapolate_forward,
    slice_dataset,
    filter_imputations,
    impute_global_average
)


# @collect_bp.route("/WATMAN", methods=["POST"])
# @login_required
# def watman():
#     def collect_iterator(**kwargs):
#         yield from collect_sdg_indicator_data(
#             "6.4.1", "WATMAN", IntermediateCode="CWUEFF", **kwargs
#         )
#         yield from collect_sdg_indicator_data(
#             "6.4.2", "WATMAN", IntermediateCode="WTSTRS", **kwargs
#         )
#     return Response(
#         collect_iterator(Username=current_user.username), mimetype="text/event-stream"
#     )


@compute_bp.route("/WATMAN", methods=['POST'])
@login_required
def compute_watman():
    app.logger.info("Running /api/v1/compute/WATMAN")
    sspi_indicator_data.delete_many({"IndicatorCode": "WATMAN"})
    sspi_incomplete_indicator_data.delete_many({"IndicatorCode": "WATMAN"})
    
    # Fetch clean datasets
    cwueff_clean = sspi_clean_api_data.find({"DatasetCode": "UNSDG_CWUEFF"})
    wtstrs_clean = sspi_clean_api_data.find({"DatasetCode": "UNSDG_WTSTRS"})
    combined_list = cwueff_clean + wtstrs_clean
    
    clean_list, incomplete_list = score_indicator(
        combined_list, "WATMAN",
        score_function=lambda UNSDG_CWUEFF, UNSDG_WTSTRS: (UNSDG_CWUEFF + UNSDG_WTSTRS) / 2,
        unit="Index",
    )
    sspi_indicator_data.insert_many(clean_list)
    sspi_incomplete_indicator_data.insert_many(incomplete_list)
    return parse_json(clean_list)

@impute_bp.route("/WATMAN", methods=["POST"])
@login_required
def impute_watman():
    mongo_query = {"IndicatorCode": "WATMAN"}
    sspi_imputed_data.delete_many(mongo_query)
    clean_list = sspi_clean_api_data.find(mongo_query)
    incomplete_list = sspi_incomplete_indicator_data.find(mongo_query)
    # Extract clean CWUEFF Data and Extrapolate Backwards
    clean_cwueff = slice_dataset(clean_list, "CWUEFF") + \
        slice_dataset(incomplete_list, "CWUEFF")
    imputed_cwueff = extrapolate_backward(
        clean_cwueff, 2000, series_id=["CountryCode", "IntermediateCode"]
    )
    imputed_cwueff = extrapolate_forward(
        imputed_cwueff, 2023, series_id=["CountryCode", "IntermediateCode"]
    )
    # Impute CWUEFF Data for SGP
    sgp_cwueff = impute_global_average("SGP", 2000, 2023, "Intermediate", "CWUEFF", clean_cwueff)
    # Extract matched WTSTRS Data
    clean_wtstrs = slice_dataset(clean_list, "WTSTRS") + \
        slice_dataset(incomplete_list, "WTSTRS")
    imputed_wtstrs = extrapolate_backward(
        clean_wtstrs, 2000, series_id=["CountryCode", "IntermediateCode"]
    )
    imputed_wtstrs = extrapolate_forward(
        imputed_wtstrs, 2023, series_id=["CountryCode", "IntermediateCode"]
    )
    overall_watman, missing_imputations = score_indicator(
        imputed_wtstrs + imputed_cwueff + sgp_cwueff, "WATMAN",
        score_function=lambda CWUEFF, WTSTRS: (CWUEFF + WTSTRS) / 2,
        unit="Index",
    )
    imputed_watman = filter_imputations(overall_watman)
    sspi_imputed_data.insert_many(imputed_watman)
    return parse_json(imputed_watman)

