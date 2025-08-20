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
    goalpost,
    extrapolate_backward,
    extrapolate_forward,
    slice_dataset,
    filter_imputations,
    impute_reference_class_average
)


@compute_bp.route("/WATMAN", methods=['POST'])
@login_required
def compute_watman():
    def score_watman(UNSDG_CWUEFF, UNSDG_WTSTRS) -> float:
        """
        Score WATMAN using CWUEFF and WTSTRS.
        """
        return (goalpost(UNSDG_CWUEFF, -20, 50) + goalpost(UNSDG_WTSTRS, 100, 0)) / 2

    app.logger.info("Running /api/v1/compute/WATMAN")
    sspi_indicator_data.delete_many({"IndicatorCode": "WATMAN"})
    sspi_incomplete_indicator_data.delete_many({"IndicatorCode": "WATMAN"})
    wuseff_clean = sspi_clean_api_data.find({"DatasetCode": "UNSDG_WUSEFF"})
    cwueff_clean = sspi_clean_api_data.find({"DatasetCode": "UNSDG_CWUEFF"})
    wtstrs_clean = sspi_clean_api_data.find({"DatasetCode": "UNSDG_WTSTRS"})
    combined_list = cwueff_clean + wtstrs_clean
    clean_list, incomplete_list = score_indicator(
        combined_list, "WATMAN",
        score_function=score_watman,
        unit="Index",
    )
    sspi_indicator_data.insert_many(clean_list)
    sspi_incomplete_indicator_data.insert_many(incomplete_list)
    return parse_json(clean_list)

@impute_bp.route("/WATMAN", methods=["POST"])
@login_required
def impute_watman():
    def score_watman(UNSDG_CWUEFF, UNSDG_WTSTRS) -> float:
        """
        Score WATMAN using CWUEFF and WTSTRS.
        """
        return (goalpost(UNSDG_CWUEFF, -20, 50) + goalpost(UNSDG_WTSTRS, 100, 0)) / 2
    mongo_query = {"IndicatorCode": "WATMAN"}
    sspi_imputed_data.delete_many(mongo_query)
    clean_list = sspi_indicator_data.find(mongo_query)
    incomplete_list = sspi_incomplete_indicator_data.find(mongo_query)
    # Extract clean CWUEFF Data and Extrapolate Backwards
    clean_cwueff = slice_dataset(clean_list, "UNSDG_CWUEFF") + \
        slice_dataset(incomplete_list, "UNSDG_CWUEFF")
    imputed_cwueff = extrapolate_backward(
        clean_cwueff, 2000, series_id=["CountryCode", "DatasetCode"]
    )
    imputed_cwueff = extrapolate_forward(
        imputed_cwueff, 2023, series_id=["CountryCode", "DatasetCode"]
    )
    # Impute CWUEFF Data for SGP
    sgp_cwueff = impute_reference_class_average("SGP", 2000, 2023, "Dataset", "UNSDG_CWUEFF", clean_cwueff)
    # Extract matched WTSTRS Data
    clean_wtstrs = slice_dataset(clean_list, "UNSDG_WTSTRS") + \
        slice_dataset(incomplete_list, "UNSDG_WTSTRS")
    imputed_wtstrs = extrapolate_backward(
        clean_wtstrs, 2000, series_id=["CountryCode", "DatasetCode"]
    )
    imputed_wtstrs = extrapolate_forward(
        imputed_wtstrs, 2023, series_id=["CountryCode", "DatasetCode"]
    )
    overall_watman, missing_imputations = score_indicator(
        imputed_wtstrs + imputed_cwueff + sgp_cwueff, "WATMAN",
        score_function=score_watman,
        unit="Index",
    )
    imputed_watman = filter_imputations(overall_watman)
    sspi_imputed_data.insert_many(imputed_watman)
    return parse_json(imputed_watman)

