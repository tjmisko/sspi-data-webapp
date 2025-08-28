from sspi_flask_app.api.core.sspi import compute_bp, impute_bp
from flask import current_app as app, Response
from sspi_flask_app.models.database import (
    sspi_clean_api_data,
    sspi_indicator_data,
    sspi_metadata,
    sspi_imputed_data,
    sspi_clean_api_data
)
from flask_login import login_required, current_user
from sspi_flask_app.api.resources.utilities import (
    parse_json,
    score_indicator,
    goalpost,
    interpolate_linear,
    extrapolate_backward,
    extrapolate_forward
)


@compute_bp.route("/MURDER", methods=['POST'])
@login_required
def compute_murder():
    app.logger.info("Running /api/v1/compute/MURDER")
    sspi_indicator_data.delete_many({"IndicatorCode": "MURDER"})
    murder_clean = sspi_clean_api_data.find({"DatasetCode": "WB_MURDER"})
    lg, ug = sspi_metadata.get_goalposts("MURDER")
    scored_list, _ = score_indicator(
        murder_clean, "MURDER",
        score_function=lambda WB_MURDER: goalpost(WB_MURDER, lg, ug),
        unit="Index"
    )
    sspi_indicator_data.insert_many(scored_list)
    return parse_json(scored_list)


@impute_bp.route("/MURDER", methods=['POST'])
def impute_murder():
    sspi_imputed_data.delete_many({"IndicatorCode": "MURDER"})
    murder_clean = sspi_clean_api_data.find({"DatasetCode": "WB_MURDER"})
    interpolate = interpolate_linear(murder_clean, series_id=["CountryCode", "DatasetCode"], impute_only=True)
    forward = extrapolate_forward(murder_clean, 2023, series_id=["CountryCode", "DatasetCode"], impute_only=True)
    backward = extrapolate_backward(murder_clean, 2000, series_id=["CountryCode", "DatasetCode"], impute_only=True)
    lg, ug = sspi_metadata.get_goalposts("MURDER")
    imputed_list, _ = score_indicator(
        interpolate + forward + backward, "MURDER",
        score_function=lambda WB_MURDER: goalpost(WB_MURDER, lg, ug),
        unit="Index"
    )
    sspi_imputed_data.insert_many(imputed_list)
    return parse_json(imputed_list)
