from sspi_flask_app.api.core.sspi import compute_bp, impute_bp
from flask import current_app as app
from flask_login import login_required
from sspi_flask_app.models.database import (
    sspi_clean_api_data,
    sspi_indicator_data,
    sspi_metadata,
    sspi_imputed_data
)
from sspi_flask_app.api.resources.utilities import (
    parse_json,
    score_indicator,
    goalpost,
    extrapolate_backward,
    extrapolate_forward,
    interpolate_linear
)


@compute_bp.route("/EMPLOY", methods=['POST'])
@login_required
def compute_employ():
    app.logger.info("Running /api/v1/compute/EMPLOY")
    sspi_indicator_data.delete_many({"IndicatorCode": "EMPLOY"})
    # Fetch clean dataset
    employ_clean = sspi_clean_api_data.find({"DatasetCode": "ILO_EMPLOY_TO_POP"})
    lg, ug = sspi_metadata.get_goalposts("EMPLOY")
    scored_list, _ = score_indicator(
        employ_clean, "EMPLOY",
        score_function=lambda ILO_EMPLOY_TO_POP: goalpost(ILO_EMPLOY_TO_POP, lg, ug),
        unit="Percentage"
    )
    sspi_indicator_data.insert_many(scored_list)
    return parse_json(scored_list)

@impute_bp.route("/EMPLOY", methods=['POST'])
def impute_employ():
    app.logger.info("Running /api/v1/compute/EMPLOY")
    sspi_imputed_data.delete_many({"IndicatorCode": "EMPLOY"})
    clean_employ = sspi_clean_api_data.find({"DatasetCode": "ILO_EMPLOY_TO_POP"})
    backward = extrapolate_backward(clean_employ, 2000, ["CountryCode", "DatasetCode"], impute_only=True)
    forward = extrapolate_forward(clean_employ, 2023, ["CountryCode", "DatasetCode"], impute_only=True)
    interpolated = interpolate_linear(clean_employ, ["CountryCode", "DatasetCode"], impute_only=True)
    lg, ug = sspi_metadata.get_goalposts("EMPLOY")
    imputed_employ, _ = score_indicator(
        forward + backward + interpolated, "EMPLOY",
        score_function=lambda ILO_EMPLOY_TO_POP: goalpost(ILO_EMPLOY_TO_POP, lg, ug),
        unit="Tax Rate"
    )
    sspi_imputed_data.insert_many(imputed_employ) 
    return parse_json(imputed_employ)
