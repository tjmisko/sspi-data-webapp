from flask import current_app as app
from flask_login import login_required

from sspi_flask_app.api.core.sspi import compute_bp, impute_bp
from sspi_flask_app.api.resources.utilities import goalpost, parse_json, score_indicator, extrapolate_backward, extrapolate_forward, interpolate_linear
from sspi_flask_app.models.database import (
    sspi_clean_api_data,
    sspi_imputed_data,
    sspi_indicator_data,
    sspi_metadata)

from sspi_flask_app.auth.decorators import admin_required


@compute_bp.route("/COLBAR", methods=["POST"])
@admin_required
def compute_colbar():
    app.logger.info("Running /api/v1/compute/COLBAR")
    sspi_indicator_data.delete_many({"IndicatorCode": "COLBAR"})
    # Fetch clean dataset
    colbar_clean = sspi_clean_api_data.find({"DatasetCode": "ILO_COLBAR"})
    lg, ug = sspi_metadata.get_goalposts("COLBAR")
    scored_list, _ = score_indicator(
        colbar_clean, "COLBAR",
        score_function=lambda ILO_COLBAR: goalpost(ILO_COLBAR, lg, ug),
        unit="%"
    )
    sspi_indicator_data.insert_many(scored_list)
    return parse_json(scored_list)


@impute_bp.route("/COLBAR", methods=['POST'])
def impute_colbar():
    app.logger.info("Running /api/v1/compute/COLBAR")
    sspi_imputed_data.delete_many({"IndicatorCode": "COLBAR"})
    clean_colbar = sspi_clean_api_data.find({"DatasetCode": "ILO_COLBAR"})
    backward = extrapolate_backward(clean_colbar, 2000, ["CountryCode", "DatasetCode"], impute_only=True)
    forward = extrapolate_forward(clean_colbar, 2023, ["CountryCode", "DatasetCode"], impute_only=True)
    interpolated = interpolate_linear(clean_colbar, ["CountryCode", "DatasetCode"], impute_only=True)
    ## Implement Country by Country Calue Imputations Here
    lg, ug = sspi_metadata.get_goalposts("COLBAR")
    imputed_colbar, _ = score_indicator(
        forward + backward + interpolated, "COLBAR",
        score_function=lambda ILO_COLBAR: goalpost(ILO_COLBAR, lg, ug),
        unit="Tax Rate"
    )
    sspi_imputed_data.insert_many(imputed_colbar) 
    return parse_json(imputed_colbar)
