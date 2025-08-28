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


# @collect_bp.route("/FAMPLN", methods=['GET'])
# @login_required
# def fampln():
#     def collect_iterator(**kwargs):
#         yield from collect_sdg_indicator_data("3.7.1", "FAMPLN", **kwargs)
#     return Response(collect_iterator(Username=current_user.username), mimetype='text/event-stream')


@compute_bp.route("/FAMPLN", methods=["POST"])
@login_required
def compute_fampln():
    app.logger.info("Running /api/v1/compute/FAMPLN")
    sspi_indicator_data.delete_many({"IndicatorCode": "FAMPLN"})
    fampln_clean = sspi_clean_api_data.find({"DatasetCode": "UNSDG_FAMPLN"})
    lg, ug = sspi_metadata.get_goalposts("FAMPLN")
    scored_list, _ = score_indicator(
        fampln_clean, "FAMPLN",
        score_function=lambda UNSDG_FAMPLN: goalpost(UNSDG_FAMPLN, lg, ug),
        unit="%"
    )
    sspi_indicator_data.insert_many(scored_list)
    return parse_json(scored_list)
