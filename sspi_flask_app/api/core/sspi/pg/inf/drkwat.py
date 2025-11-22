from sspi_flask_app.api.core.sspi import compute_bp
from flask import current_app as app, Response
from sspi_flask_app.models.database import (
    sspi_clean_api_data,
    sspi_indicator_data,
    sspi_metadata
)
from sspi_flask_app.api.resources.utilities import (
    parse_json,
    score_indicator,
    goalpost
)
from flask_login import login_required, current_user


# @collect_bp.route("/DRKWAT", methods=['GET']
from sspi_flask_app.auth.decorators import admin_required
# @admin_required
# def drkwat():
#     def collect_iterator(**kwargs):
#         yield from collect_wb_data("SH.H2O.SMDW.ZS", "DRKWAT", **kwargs)
#     return Response(collect_iterator(Username=current_user.username), mimetype='text/event-stream')


@compute_bp.route("/DRKWAT", methods=["POST"])
@admin_required
def compute_drkwat():
    app.logger.info("Running /api/v1/compute/DRKWAT")
    sspi_indicator_data.delete_many({"IndicatorCode": "DRKWAT"})
    drkwat_clean = sspi_clean_api_data.find({"DatasetCode": "WB_DRKWAT"})
    lg, ug = sspi_metadata.get_goalposts("DRKWAT")
    scored_list, _ = score_indicator(
        drkwat_clean, "DRKWAT",
        score_function=lambda WB_DRKWAT: goalpost(WB_DRKWAT, lg, ug),
        unit="%"
    )
    sspi_indicator_data.insert_many(scored_list)
    return parse_json(scored_list)
