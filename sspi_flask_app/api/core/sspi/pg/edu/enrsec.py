from flask import Response, current_app as app
from sspi_flask_app.api.core.sspi import compute_bp
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


# @collect_bp.route("/ENRSEC", methods=['POST'])
# @login_required
# def enrsec():
#     def collect_iterator(**kwargs):
#         yield from collect_uis_data("NERT.2.CP", "ENRSEC", **kwargs)
#     return Response(collect_iterator(Username=current_user.username), mimetype='text/event-stream')


@compute_bp.route("/ENRSEC", methods=['POST'])
@login_required
def compute_enrsec():
    app.logger.info("Running /api/v1/compute/ENRSEC")
    sspi_indicator_data.delete_many({"IndicatorCode": "ENRSEC"})
    enrsec_clean = sspi_clean_api_data.find({"DatasetCode": "UIS_ENRSEC"})
    lg, ug = sspi_metadata.get_goalposts("ENRSEC")
    scored_list, _ = score_indicator(
        enrsec_clean, "ENRSEC",
        score_function=lambda UIS_ENRSEC: goalpost(UIS_ENRSEC, lg, ug),
        unit="Percent"
    )
    sspi_indicator_data.insert_many(scored_list)
    return parse_json(scored_list)
