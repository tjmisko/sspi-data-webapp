from sspi_flask_app.api.core.sspi import compute_bp
from flask import current_app as app, Response
from sspi_flask_app.models.database import (
    sspi_raw_api_data,
    sspi_clean_api_data,
)
from sspi_flask_app.api.resources.utilities import (
    parse_json,
    score_single_indicator,
)
from flask_login import login_required, current_user
from sspi_flask_app.api.datasource.worldbank import (
    collect_world_bank_data,
    clean_wb_data
)


# @collect_bp.route("/SANSRV", methods=['GET'])
# @login_required
# def sansrv():
#     def collect_iterator(**kwargs):
#         yield from collect_world_bank_data("SH.STA.BASS.ZS", "SANSRV", **kwargs)
#     return Response(collect_iterator(Username=current_user.username), mimetype='text/event-stream')


@compute_bp.route("/SANSRV")
@login_required
def compute_sansrv():
    app.logger.info("Running /api/v1/compute/SANSRV")
    sspi_clean_api_data.delete_many({"IndicatorCode": "SANSRV"})
    raw_data = sspi_raw_api_data.fetch_raw_data("SANSRV")
    cleaned = clean_wb_data(raw_data, "SANSRV", "Percent")
    scored_list = score_single_indicator(cleaned, "SANSRV")
    sspi_clean_api_data.insert_many(scored_list)
    return parse_json(scored_list)
