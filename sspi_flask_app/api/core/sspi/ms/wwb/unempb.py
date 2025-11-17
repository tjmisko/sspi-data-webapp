from sspi_flask_app.api.core.sspi import compute_bp, impute_bp
from flask_login import login_required, current_user
from flask import current_app as app, Response
from sspi_flask_app.models.database import (
    sspi_clean_api_data,
    sspi_indicator_data,
    sspi_metadata,
    sspi_imputed_data)

from sspi_flask_app.auth.decorators import admin_required
from sspi_flask_app.api.resources.utilities import (
    parse_json,
    score_indicator,
    goalpost,
    extrapolate_backward,
    extrapolate_forward,
    interpolate_linear,
    impute_reference_class_average
)


@compute_bp.route("/UNEMPB", methods=['POST'])
@admin_required
def compute_unempb():
    app.logger.info("Running /api/v1/compute/UNEMPB")
    sspi_indicator_data.delete_many({"IndicatorCode": "UNEMPB"})
    unempb_clean = sspi_clean_api_data.find({"DatasetCode": "UNSDG_BENFTS_UNEMP"})
    lg, ug = sspi_metadata.get_goalposts("UNEMPB")
    scored_data, _ = score_indicator(
        unempb_clean, "UNEMPB",
        score_function=lambda UNSDG_BENFTS_UNEMP: goalpost(UNSDG_BENFTS_UNEMP, lg, ug),
        unit="Benefits Coverage (%)"
    )
    sspi_indicator_data.insert_many(scored_data)
    return parse_json(scored_data)


@impute_bp.route("/UNEMPB", methods=['POST'])
def impute_unempb():
    app.logger.info("Running /api/v1/compute/UNEMPB")
    sspi_imputed_data.delete_many({"IndicatorCode": "UNEMPB"})
    clean_unempb = sspi_clean_api_data.find({"DatasetCode": "UNSDG_BENFTS_UNEMP"})
    backward = extrapolate_backward(clean_unempb, 2000, ["CountryCode", "DatasetCode"], impute_only=True)
    forward = extrapolate_forward(clean_unempb, 2023, ["CountryCode", "DatasetCode"], impute_only=True)
    interpolated = interpolate_linear(clean_unempb, ["CountryCode", "DatasetCode"], impute_only=True)
    lg, ug = sspi_metadata.get_goalposts("UNEMPB")
    isl_imputed = impute_reference_class_average(
        "ISL", 2000, 2023, "Dataset", "UNSDG_BENFTS_UNEMP", clean_unempb
    )
    imputed_unempb, _ = score_indicator(
        forward + backward + interpolated + isl_imputed, "UNEMPB",
        score_function=lambda UNSDG_BENFTS_UNEMP: goalpost(UNSDG_BENFTS_UNEMP, lg, ug),
        unit="Tax Rate"
    )
    sspi_imputed_data.insert_many(imputed_unempb) 
    return parse_json(imputed_unempb)
