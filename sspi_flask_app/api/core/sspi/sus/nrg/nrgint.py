from flask import current_app as app
from flask_login import login_required

from sspi_flask_app.api.core.sspi import compute_bp, impute_bp
from sspi_flask_app.api.resources.utilities import (
    extrapolate_forward,
    parse_json,
    score_indicator,
    goalpost)

from sspi_flask_app.auth.decorators import admin_required
from sspi_flask_app.models.database import (
    sspi_clean_api_data,
    sspi_imputed_data,
    sspi_indicator_data,
    sspi_metadata
)


@compute_bp.route("/NRGINT", methods=['POST'])
@admin_required
def compute_nrgint():
    app.logger.info("Running /api/v1/compute/NRGINT")
    sspi_indicator_data.delete_many({"IndicatorCode": "NRGINT"})
    # Fetch clean dataset
    nrgint_clean = sspi_clean_api_data.find({"DatasetCode": "UNSDG_NRGINT"})
    lg, ug = sspi_metadata.get_goalposts("NRGINT")
    scored_list, _ = score_indicator(
        nrgint_clean, "NRGINT",
        score_function=lambda UNSDG_NRGINT: goalpost(UNSDG_NRGINT, lg, ug),
        unit="Index"
    )
    sspi_indicator_data.insert_many(scored_list)
    return parse_json(scored_list)


@impute_bp.route("/NRGINT", methods=["POST"])
@admin_required
def impute_nrgint():
    sspi_imputed_data.delete_many({"IndicatorCode": "NRGINT"})
    clean_data = sspi_indicator_data.find({"IndicatorCode": "NRGINT"})
    imputations = extrapolate_forward(clean_data, 2023, impute_only=True)
    sspi_imputed_data.insert_many(imputations)
    return parse_json(imputations)
