import logging
from flask import Response, current_app as app
from flask_login import login_required, current_user
from sspi_flask_app.api.core.sspi import compute_bp, impute_bp
from sspi_flask_app.api.resources.utilities import (
    parse_json,
    score_indicator,
    goalpost,
    extrapolate_forward,
    extrapolate_backward,
    interpolate_linear,
    impute_reference_class_average
)
from sspi_flask_app.models.database import (
    sspi_raw_api_data,
    sspi_clean_api_data,
    sspi_metadata,
    sspi_indicator_data,
    sspi_imputed_data
)

log = logging.getLogger(__name__)

@compute_bp.route("/STCONS", methods=['POST'])
@login_required
def compute_stcons():
    lg, ug = sspi_metadata.get_goalposts("STCONS")
    def stcons_score_function(WID_CARBON_TOT_P90P100, WID_CARBON_TOT_P0P100, FPI_ECOFPT_PER_CAP):
        return goalpost(FPI_ECOFPT_PER_CAP*WID_CARBON_TOT_P90P100 / WID_CARBON_TOT_P0P100, lg, ug)
    sspi_indicator_data.delete_many({"IndicatorCode": "STCONS"})
    dataset_list = sspi_clean_api_data.find(
        {"DatasetCode": {"$in": [
            "WID_CARBON_TOT_P0P100", "WID_CARBON_TOT_P90P100", "FPI_ECOFPT_PER_CAP"]
    }})
    scored_data, _ = score_indicator(
        dataset_list, "STCONS",
        score_function=stcons_score_function,
        unit="Index"
    )
    sspi_indicator_data.insert_many(scored_data)
    return parse_json(scored_data)


@impute_bp.route("/STCONS", methods=["POST"])
@login_required
def impute_stcons():
    mongo_query = {"IndicatorCode": "STCONS"}
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
    
    # Combine for interpolation
    all_data = clean_list + imputed_backward + imputed_forward
    interpolated = interpolate_linear(
        all_data, series_id=["CountryCode", "IndicatorCode"], impute_only=True
    )
    
    imputed_stcons = imputed_backward + imputed_forward + interpolated
    
    # Handle countries with no data using reference class average
    sspi67_countries = sspi_metadata.country_group("SSPI67")
    countries_with_data = {d["CountryCode"] for d in clean_list}
    countries_no_data = [c for c in sspi67_countries if c not in countries_with_data]
    
    if countries_no_data:
        ref_data = [d for d in clean_list if d["CountryCode"] not in countries_no_data]
        
        for country in countries_no_data:
            if ref_data:
                country_imputed = impute_reference_class_average(
                    country, 2000, 2023, "Indicator", "STCONS", ref_data
                )
                imputed_stcons.extend(country_imputed)
    
    # Insert into database
    if imputed_stcons:
        sspi_imputed_data.insert_many(imputed_stcons)
    
    return parse_json(imputed_stcons)