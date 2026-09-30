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

EDEMOC_PANEL_END_YEAR = 2023


# @collect_bp.route("/EDEMOC", methods=['POST'])
# @admin_required
# def edemoc():
#     def collect_iterator(**kwargs):
#         yield from collectVDEMData("v2x_polyarchy", "EDEMOC", **kwargs)
#     return Response(collect_iterator(Username=current_user.username), mimetype='text/event-stream')


@compute_bp.route("/EDEMOC", methods=['POST'])
@admin_required
def compute_edemoc():
    app.logger.info("Running /api/v1/compute/EDEMOC")
    sspi_indicator_data.delete_many({"IndicatorCode": "EDEMOC"})
    edemoc_clean = sspi_clean_api_data.find({"DatasetCode": "VDEM_EDEMOC"})
    lg, ug = sspi_metadata.get_goalposts("EDEMOC")
    scored_list, _ = score_indicator(
        edemoc_clean, "EDEMOC",
        score_function=lambda VDEM_EDEMOC: goalpost(VDEM_EDEMOC, lg, ug),
        unit="Index"
    )
    sspi_indicator_data.insert_many(scored_list)
    return parse_json(scored_list)


@impute_bp.route("/EDEMOC", methods=['POST'])
@admin_required
def impute_edemoc():
    """
    Forward-extrapolate VDEM_EDEMOC to EDEMOC_PANEL_END_YEAR and store only the
    carried years in sspi_imputed_data, flagged Imputed with ImputationMethod
    "Forward Extrapolation" and ImputationDistance (no distance cap, owner
    ruling 2026-09-13). Observed rows in sspi_indicator_data are never read
    or written here, and the route replaces its own imputed rows on each run.
    """
    app.logger.info("Running /api/v1/impute/EDEMOC")
    sspi_imputed_data.delete_many({"IndicatorCode": "EDEMOC"})
    edemoc_clean = sspi_clean_api_data.find({"DatasetCode": "VDEM_EDEMOC"})
    edemoc_carried = extrapolate_forward(
        edemoc_clean, EDEMOC_PANEL_END_YEAR,
        series_id=["CountryCode", "DatasetCode"], impute_only=True
    )
    lg, ug = sspi_metadata.get_goalposts("EDEMOC")
    imputed_edemoc, _ = score_indicator(
        edemoc_carried, "EDEMOC",
        score_function=lambda VDEM_EDEMOC: goalpost(VDEM_EDEMOC, lg, ug),
        unit="Index"
    )
    app.logger.info(f"EDEMOC: {len(imputed_edemoc)} forward extrapolations imputed")
    if imputed_edemoc:
        sspi_imputed_data.insert_many(imputed_edemoc)
    return parse_json(imputed_edemoc)
