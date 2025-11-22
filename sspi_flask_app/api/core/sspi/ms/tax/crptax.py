from flask import Response
from flask import current_app as app
from flask_login import current_user, login_required

from sspi_flask_app.api.core.sspi import compute_bp, impute_bp
from sspi_flask_app.api.resources.utilities import (
    extrapolate_backward,
    interpolate_linear,
    parse_json,
    score_indicator,
    goalpost)

from sspi_flask_app.auth.decorators import admin_required
from sspi_flask_app.models.database import (
    sspi_clean_api_data,
    sspi_indicator_data,
    sspi_imputed_data,
    sspi_metadata
)


@compute_bp.route("/CRPTAX", methods=["POST"])
@admin_required
def compute_crptax():
    app.logger.info("Running /api/v1/compute/CRPTAX")
    sspi_indicator_data.delete_many({"IndicatorCode": "CRPTAX"})
    crptax_clean = sspi_clean_api_data.find({"DatasetCode": "TF_CRPTAX"})
    lg, ug = sspi_metadata.get_goalposts("CRPTAX")
    scored_list, _ = score_indicator(
        crptax_clean, "CRPTAX",
        score_function=lambda TF_CRPTAX: goalpost(TF_CRPTAX, lg, ug),
        unit="Tax Rate"
    )
    sspi_indicator_data.insert_many(scored_list)
    return parse_json(scored_list)


@impute_bp.route("/CRPTAX", methods=['POST'])
@admin_required
def impute_crptax():
    app.logger.info("Running /api/v1/impute/CRPTAX")
    sspi_imputed_data.delete_many({"IndicatorCode": "CRPTAX"})
    clean_crptax = sspi_clean_api_data.find({"DatasetCode": "TF_CRPTAX"})
    backward = extrapolate_backward(clean_crptax, 2000, ["CountryCode", "DatasetCode"], impute_only=True)
    interpolated = interpolate_linear(clean_crptax, ["CountryCode", "DatasetCode"], impute_only=True)
    lg, ug = sspi_metadata.get_goalposts("CRPTAX")
    imputed_crptax, _ = score_indicator(
        backward + interpolated, "CRPTAX",
        score_function=lambda TF_CRPTAX: goalpost(TF_CRPTAX, lg, ug),
        unit="Tax Rate"
    )
    sspi_imputed_data.insert_many(imputed_crptax) 
    return parse_json(imputed_crptax)
