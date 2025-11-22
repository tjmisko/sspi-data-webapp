from sspi_flask_app.api.core.sspi import compute_bp, impute_bp
from flask import current_app as app, Response
from sspi_flask_app.models.database import (
    sspi_clean_api_data,
    sspi_indicator_data,
    sspi_metadata,
    sspi_imputed_data
)
from flask_login import login_required, current_user
from sspi_flask_app.api.resources.utilities import (
    parse_json,
    score_indicator,
    goalpost,
    extrapolate_forward,
    extrapolate_backward,
    interpolate_linear)

from sspi_flask_app.auth.decorators import admin_required

@compute_bp.route("/PHYSPC", methods=["POST"])
@admin_required
def compute_physpc():
    app.logger.info("Running /api/v1/compute/PHYSPC")
    sspi_indicator_data.delete_many({"IndicatorCode": "PHYSPC"})
    physpc_clean = sspi_clean_api_data.find({"DatasetCode": "WHO_PHYSPC"})
    lg, ug = sspi_metadata.get_goalposts("PHYSPC")
    scored_list, _ = score_indicator(
        physpc_clean, "PHYSPC", 
        score_function=lambda WHO_PHYSPC: goalpost(WHO_PHYSPC, lg, ug),
        unit="Rate"
    )
    sspi_indicator_data.insert_many(scored_list)
    return parse_json(scored_list)

@impute_bp.route("/PHYSPC", methods=["POST"])
@admin_required
def impute_physpc():
    sspi_imputed_data.delete_many({"IndicatorCode": "PHYSPC"})
    physpc_clean = sspi_clean_api_data.find({"DatasetCode": "WHO_PHYSPC"})
    forward = extrapolate_forward(physpc_clean, 2023, ["CountryCode", "DatasetCode"], impute_only=True)
    backward = extrapolate_backward(physpc_clean, 2000, ["CountryCode", "DatasetCode"], impute_only=True)
    interpolated = interpolate_linear(physpc_clean, ["CountryCode", "DatasetCode"], impute_only=True)
    lg, ug = sspi_metadata.get_goalposts("PHYSPC")
    imputed_list, _ = score_indicator(
        forward + backward + interpolated, "PHYSPC", 
        score_function=lambda WHO_PHYSPC: goalpost(WHO_PHYSPC, lg, ug),
        unit="Rate"
    )
    sspi_imputed_data.insert_many(imputed_list)
    return parse_json(imputed_list)
