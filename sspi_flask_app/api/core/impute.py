from flask import Blueprint, current_app as app
from sspi_flask_app.models.database import (
    sspi_clean_api_data,
    sspi_incomplete_api_data,
    sspi_main_data_v3,
    sspi_metadata,
    sspi_raw_api_data,
    sspi_imputed_data
)
from sspi_flask_app.api.resources.utilities import (
    parse_json,
    zip_intermediates,
    extrapolate_backward,
    extrapolate_forward,
    interpolate_linear,
    slice_intermediate,
    filter_imputations,
    impute_global_average
)


impute_bp = Blueprint(
    "impute_bp", __name__,
    template_folder="templates",
    static_folder="static",
    url_prefix="/impute"
)


@impute_bp.route("/BIODIV", methods=["POST"])
def impute_biodiv():
    sspi_imputed_data.delete_many({"IndicatorCode": "SENIOR"})
    clean_list = sspi_clean_api_data.find({"IndicatorCode": "BIODIV"})
    incomplete_list = sspi_incomplete_api_data.find({"IndicatorCode": "BIODIV"})
    # Do imputation logic here
    documents = []
    count = sspi_imputed_data.insert_many(documents)
    return parse_json(documents)


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
    sgp_cwueff = impute_global_average("SGP", 2000, 2023, clean_cwueff)
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


@impute_bp.route("/SENIOR", methods=["POST"])
def impute_senior():
    sspi_imputed_data.delete_many({"IndicatorCode": "SENIOR"})
    clean_data = sspi_clean_api_data.find({"IndicatorCode": "SENIOR"})
    incomplete_list = sspi_incomplete_api_data.find(
        {"IndicatorCode": "SENIOR"})
    # Do imputation logic here
    count = sspi_imputed_data.insert_many([])
    return f"{count} documents inserted into sspi_imputed_data."
