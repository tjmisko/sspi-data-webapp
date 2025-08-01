from sspi_flask_app.api.core.sspi import compute_bp
from flask import current_app as app, Response
from sspi_flask_app.models.database import (
    sspi_clean_api_data,
    sspi_indicator_data,
    sspi_metadata
)
from flask_login import login_required, current_user
from sspi_flask_app.api.resources.utilities import (
    parse_json,
    score_indicator,
    goalpost
)


# @collect_bp.route("/RULELW", methods=['GET'])
# @login_required
# def rulelw():
#     def collect_iterator(**kwargs):
#         yield from collect_vdem_data("v2x_rule", "RULELW", **kwargs)
#     return Response(collect_iterator(Username=current_user.username), mimetype='text/event-stream')


@compute_bp.route("/RULELW", methods=['GET'])
@login_required
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
