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


# @collect_bp.route("/ATBRTH", methods=['GET'])
# @login_required
# def atbrth():
#     def collect_iterator(**kwargs):
#         yield from collect_who_data("MDG_0000000025", "ATBRTH", **kwargs)
#     return Response(collect_iterator(Username=current_user.username), mimetype='text/event-stream')


@compute_bp.route("/ATBRTH", methods=["POST"])
@login_required
def compute_atbrth():
    app.logger.info("Running /api/v1/compute/ATBRTH")
    sspi_indicator_data.delete_many({"IndicatorCode": "ATBRTH"})
    atbrth_clean = sspi_clean_api_data.find({"DatasetCode": "WHO_ATBRTH"})
    lg, ug = sspi_metadata.get_goalposts("ATBRTH")
    scored_list, _ = score_indicator(
        atbrth_clean, "ATBRTH",
        score_function=lambda WHO_ATBRTH: goalpost(WHO_ATBRTH, lg, ug),
        unit="%"
    )
    sspi_indicator_data.insert_many(scored_list)
    return parse_json(scored_list)
