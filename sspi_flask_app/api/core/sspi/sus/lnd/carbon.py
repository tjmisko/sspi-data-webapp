from sspi_flask_app.api.core.sspi import compute_bp, impute_bp
from flask import current_app as app
from flask_login import login_required
from sspi_flask_app.models.database import (
    sspi_clean_api_data,
    sspi_indicator_data,
    sspi_incomplete_indicator_data,
    sspi_imputed_data,
    sspi_metadata
)
from sspi_flask_app.api.resources.utilities import (
    parse_json,
    goalpost,
    score_indicator,
    extrapolate_forward,
    impute_reference_class_average
)


@compute_bp.route("/CARBON", methods=['POST'])
@login_required
def compute_carbon():
    lg, ug = sspi_metadata.get_goalposts("CARBON")
    def score_carbon(UNFAO_CRBNLV, UNFAO_CRBNAV) -> float: 
        if UNFAO_CRBNAV == 0:
            return 0
        return goalpost((UNFAO_CRBNLV - UNFAO_CRBNAV) / UNFAO_CRBNAV * 100, lg, ug)

    sspi_indicator_data.delete_many({"IndicatorCode": "CARBON"})
    sspi_incomplete_indicator_data.delete_many({"IndicatorCode": "CARBON"})
    crbnlv_clean = sspi_clean_api_data.find({"DatasetCode": "UNFAO_CRBNLV"})
    crbnav_clean = sspi_clean_api_data.find({"DatasetCode": "UNFAO_CRBNAV"})
    combined_list = crbnlv_clean + crbnav_clean
    filtered_combined = []
    for obs in combined_list:
        if obs.get("DatasetCode") == "UNFAO_CRBNLV" and obs.get("Year", 0) >= 2000:
            filtered_combined.append(obs)
        elif obs.get("DatasetCode") == "UNFAO_CRBNAV":
            filtered_combined.append(obs)
    
    lg, ug = sspi_metadata.get_goalposts("CARBON")
    
    clean_list, incomplete_list = score_indicator(
        filtered_combined,
        "CARBON",
        score_function=score_carbon,
        unit="Index",
    )
    sspi_indicator_data.insert_many(clean_list)
    sspi_incomplete_indicator_data.insert_many(incomplete_list)
    return parse_json(clean_list)


@impute_bp.route("/CARBON", methods=["POST"])
@login_required
def impute_carbon():
    mongo_query = {"IndicatorCode": "CARBON"}
    sspi_imputed_data.delete_many(mongo_query)
    
    # Get complete indicator data
    clean_list = sspi_indicator_data.find(mongo_query)
    
    # Extrapolate indicator scores forward to 2023
    imputed_carbon = extrapolate_forward(
        clean_list, 2023, series_id=["CountryCode", "IndicatorCode"], impute_only=True
    )
    
    # Handle countries with no data using reference class average
    countries_no_data = ["BEL", "ARE", "LUX", "KWT"]
    ref_data = [d for d in clean_list if d["CountryCode"] not in countries_no_data]
    
    for country in countries_no_data:
        if ref_data:
            country_imputed = impute_reference_class_average(
                country, 2000, 2023, "Indicator", "CARBON", ref_data
            )
            imputed_carbon.extend(country_imputed)
    
    # Insert into database
    if imputed_carbon:
        sspi_imputed_data.insert_many(imputed_carbon)
    
    return parse_json(imputed_carbon)
