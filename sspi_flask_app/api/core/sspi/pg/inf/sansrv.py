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


# @collect_bp.route("/SANSRV", methods=['GET'])
# @login_required
# def sansrv():
#     def collect_iterator(**kwargs):
#         yield from collect_wb_data("SH.STA.BASS.ZS", "SANSRV", **kwargs)
#     return Response(collect_iterator(Username=current_user.username), mimetype='text/event-stream')


@compute_bp.route("/SANSRV", methods=["POST"])
@login_required
def compute_sansrv():
    app.logger.info("Running /api/v1/compute/SANSRV")
    sspi_indicator_data.delete_many({"IndicatorCode": "SANSRV"})
    sansrv_clean = sspi_clean_api_data.find({"DatasetCode": "WB_SANSRV"})
    lg, ug = sspi_metadata.get_goalposts("SANSRV")
    scored_list, _ = score_indicator(
        sansrv_clean, "SANSRV",
        score_function=lambda WB_SANSRV: goalpost(WB_SANSRV, lg, ug),
        unit="Percent"
    )
    sspi_indicator_data.insert_many(scored_list)
    return parse_json(scored_list)
