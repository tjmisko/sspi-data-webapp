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
    goalpost)

from sspi_flask_app.auth.decorators import admin_required


# @collect_bp.route("/SECAPP", methods=['GET'])
# @admin_required
# def secapp():
#     def collect_iterator(**kwargs):
#         yield from collectFSIdata("SECAPP", **kwargs)
#     return Response(collect_iterator(Username=current_user.username), mimetype='text/event-stream')


@compute_bp.route("/SECAPP", methods=["POST"])
@admin_required
def compute_secapp():
    app.logger.info("Running /api/v1/compute/SECAPP")
    sspi_indicator_data.delete_many({"IndicatorCode": "SECAPP"})
    secapp_clean = sspi_clean_api_data.find({"DatasetCode": "FSI_SECAPP"})
    lg, ug = sspi_metadata.get_goalposts("SECAPP")
    scored_list, _ = score_indicator(
        secapp_clean, "SECAPP",
        score_function=lambda FSI_SECAPP: goalpost(FSI_SECAPP, lg, ug),
        unit="Index"
    )
    sspi_indicator_data.insert_many(scored_list)
    return parse_json(scored_list)
