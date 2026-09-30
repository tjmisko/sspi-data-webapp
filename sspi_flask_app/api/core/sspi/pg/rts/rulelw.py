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
    extrapolate_forward)

from sspi_flask_app.auth.decorators import admin_required

RULELW_PANEL_END_YEAR = 2023


@compute_bp.route("/RULELW", methods=['POST'])
@admin_required
def compute_rulelw():
    app.logger.info("Running /api/v1/compute/RULELW")
    sspi_indicator_data.delete_many({"IndicatorCode": "RULELW"})
    rulelw_clean = sspi_clean_api_data.find({"DatasetCode": "VDEM_RULELW"})
    lg, ug = sspi_metadata.get_goalposts("RULELW")
    scored_list, _ = score_indicator(
        rulelw_clean, "RULELW",
        score_function=lambda VDEM_RULELW: goalpost(VDEM_RULELW, lg, ug),
        unit="Index"
    )
    sspi_indicator_data.insert_many(scored_list)
    return parse_json(scored_list)


@impute_bp.route("/RULELW", methods=['POST'])
@admin_required
def impute_rulelw():
    """
    Forward-extrapolate VDEM_RULELW to RULELW_PANEL_END_YEAR and store only the
    carried years in sspi_imputed_data, flagged Imputed with ImputationMethod
    "Forward Extrapolation" and ImputationDistance (no distance cap, owner
    ruling 2026-09-13). Observed rows in sspi_indicator_data are never read
    or written here, and the route replaces its own imputed rows on each run.
    """
    app.logger.info("Running /api/v1/impute/RULELW")
    sspi_imputed_data.delete_many({"IndicatorCode": "RULELW"})
    rulelw_clean = sspi_clean_api_data.find({"DatasetCode": "VDEM_RULELW"})
    rulelw_carried = extrapolate_forward(
        rulelw_clean, RULELW_PANEL_END_YEAR,
        series_id=["CountryCode", "DatasetCode"], impute_only=True
    )
    lg, ug = sspi_metadata.get_goalposts("RULELW")
    imputed_rulelw, _ = score_indicator(
        rulelw_carried, "RULELW",
        score_function=lambda VDEM_RULELW: goalpost(VDEM_RULELW, lg, ug),
        unit="Index"
    )
    app.logger.info(f"RULELW: {len(imputed_rulelw)} forward extrapolations imputed")
    if imputed_rulelw:
        sspi_imputed_data.insert_many(imputed_rulelw)
    return parse_json(imputed_rulelw)
