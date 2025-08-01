from sspi_flask_app.api.core.sspi import compute_bp
from flask import current_app as app
from flask_login import login_required
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


# @collect_bp.route("/AIRPOL", methods=['GET'])
# @login_required
# def airpol():
#     def collect_iterator(**kwargs):
#         yield from collect_sdg_indicator_data("11.6.2", "AIRPOL", **kwargs)
#     return Response(collect_iterator(Username=current_user.username), mimetype='text/event-stream')


@compute_bp.route("/AIRPOL")
@login_required
def compute_airpol():
    app.logger.info("Running /api/v1/compute/AIRPOL")
    sspi_indicator_data.delete_many({"IndicatorCode": "AIRPOL"})
    
    # Fetch clean dataset
    airpol_clean = sspi_clean_api_data.find({"DatasetCode": "UNSDG_AIRPOL"})
    lg, ug = sspi_metadata.get_goalposts("AIRPOL")
    
    scored_list, _ = score_indicator(
        airpol_clean, "AIRPOL",
        score_function=lambda UNSDG_AIRPOL: goalpost(UNSDG_AIRPOL, lg, ug),
        unit="Index"
    )
    sspi_indicator_data.insert_many(scored_list)
    return parse_json(scored_list)
