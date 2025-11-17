from sspi_flask_app.api.core.sspi import compute_bp, impute_bp
from flask import current_app as app
from flask_login import login_required
from sspi_flask_app.models.database import (
    sspi_clean_api_data,
    sspi_indicator_data,
    sspi_imputed_data,
    sspi_metadata)

from sspi_flask_app.auth.decorators import admin_required
from sspi_flask_app.api.resources.utilities import (
    parse_json,
    score_indicator,
    goalpost,
    extrapolate_forward,
    extrapolate_backward,
    impute_reference_class_average
)


@compute_bp.route("/RECYCL", methods=["POST"])
@admin_required
def compute_recycl():
    app.logger.info("Running /api/v1/compute/RECYCL")
    sspi_indicator_data.delete_many({"IndicatorCode": "RECYCL"})
    
    # Fetch clean dataset
    recycl_clean = sspi_clean_api_data.find({"DatasetCode": "WB_RECYCL"})
    lg, ug = sspi_metadata.get_goalposts("RECYCL")
    
    scored_list, _ = score_indicator(
        recycl_clean, "RECYCL",
        score_function=lambda WB_RECYCL: goalpost(WB_RECYCL, lg, ug),
        unit="Index"
    )
    sspi_indicator_data.insert_many(scored_list)
    return parse_json(scored_list)


@impute_bp.route("/RECYCL", methods=["POST"])
@admin_required
def impute_recycl():
    mongo_query = {"IndicatorCode": "RECYCL"}
    sspi_imputed_data.delete_many(mongo_query)
    
    # Get complete indicator data
    clean_list = sspi_indicator_data.find(mongo_query)
    
    # Extrapolate indicator scores backward to 2000 and forward to 2023
    imputed_backward = extrapolate_backward(
        clean_list, 2000, series_id=["CountryCode", "IndicatorCode"], impute_only=True
    )
    imputed_forward = extrapolate_forward(
        clean_list, 2023, series_id=["CountryCode", "IndicatorCode"], impute_only=True
    )
    imputed_recycl = imputed_backward + imputed_forward
    
    # Handle countries with no data using reference class average
    sspi67_countries = sspi_metadata.country_group("SSPI67")
    countries_with_data = {d["CountryCode"] for d in clean_list}
    countries_no_data = [c for c in sspi67_countries if c not in countries_with_data]
    
    if countries_no_data:
        ref_data = [d for d in clean_list if d["CountryCode"] not in countries_no_data]
        
        for country in countries_no_data:
            if ref_data:
                country_imputed = impute_reference_class_average(
                    country, 2000, 2023, "Indicator", "RECYCL", ref_data
                )
                imputed_recycl.extend(country_imputed)
    
    # Insert into database
    if imputed_recycl:
        sspi_imputed_data.insert_many(imputed_recycl)
    
    return parse_json(imputed_recycl)
