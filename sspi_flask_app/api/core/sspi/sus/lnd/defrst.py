from sspi_flask_app.api.core.sspi import compute_bp, impute_bp
from flask_login import login_required
from flask import current_app as app
from sspi_flask_app.models.database import (
    sspi_clean_api_data,
    sspi_indicator_data,
    sspi_incomplete_indicator_data,
    sspi_imputed_data,
    sspi_metadata)

from sspi_flask_app.auth.decorators import admin_required
from sspi_flask_app.api.resources.utilities import (
    parse_json,
    goalpost,
    score_indicator,
    extrapolate_forward,
    slice_dataset,
    filter_imputations,
    impute_reference_class_average
)


@compute_bp.route("/DEFRST", methods=['POST'])
@admin_required
def compute_defrst():
    lg, ug = sspi_metadata.get_goalposts("DEFRST")
    def score_defrst(UNFAO_FRSTLV, UNFAO_FRSTAV) -> float: 
        if UNFAO_FRSTAV == 0:
            return 0
        return goalpost((UNFAO_FRSTLV - UNFAO_FRSTAV) / UNFAO_FRSTAV * 100, lg, ug)

    app.logger.info("Running /api/v1/compute/DEFRST")
    sspi_indicator_data.delete_many({"IndicatorCode": "DEFRST"})
    sspi_incomplete_indicator_data.delete_many({"IndicatorCode": "DEFRST"})
    frstlv_clean = sspi_clean_api_data.find({"DatasetCode": "UNFAO_FRSTLV"})
    frstav_clean = sspi_clean_api_data.find({"DatasetCode": "UNFAO_FRSTAV"})
    combined_list = frstlv_clean + frstav_clean
    
    # Filter to post-2000 data for FRSTLV
    filtered_combined = []
    for obs in combined_list:
        if obs.get("DatasetCode") == "UNFAO_FRSTLV" and obs.get("Year", 0) >= 2000:
            filtered_combined.append(obs)
        elif obs.get("DatasetCode") == "UNFAO_FRSTAV":
            filtered_combined.append(obs)
    
    
    clean_list, incomplete_list = score_indicator(
        filtered_combined,
        "DEFRST",
        score_function=score_defrst,
        unit="Index",
    )
    sspi_indicator_data.insert_many(clean_list)
    sspi_incomplete_indicator_data.insert_many(incomplete_list)
    return parse_json(clean_list)


@impute_bp.route("/DEFRST", methods=["POST"])
@admin_required
def impute_defrst():
    mongo_query = {"IndicatorCode": "DEFRST"}
    sspi_imputed_data.delete_many(mongo_query)
    
    # Get complete indicator data
    clean_list = sspi_indicator_data.find(mongo_query)
    
    # Extrapolate indicator scores forward to 2023
    imputed_defrst = extrapolate_forward(
        clean_list, 2023, series_id=["CountryCode", "IndicatorCode"], impute_only=True
    )
    
    # Handle countries with no data using reference class average
    countries_no_data = ["BEL", "ARE", "LUX"]
    ref_data = [d for d in clean_list if d["CountryCode"] not in countries_no_data]
    
    for country in countries_no_data:
        if ref_data:
            country_imputed = impute_reference_class_average(
                country, 2000, 2023, "Indicator", "DEFRST", ref_data
            )
            imputed_defrst.extend(country_imputed)
    
    # Insert into database
    if imputed_defrst:
        sspi_imputed_data.insert_many(imputed_defrst)
    
    return parse_json(imputed_defrst)


