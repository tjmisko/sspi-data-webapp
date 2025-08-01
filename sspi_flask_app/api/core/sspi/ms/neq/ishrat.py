from sspi_flask_app.api.core.sspi import compute_bp
from flask_login import login_required
from flask import current_app as app
from sspi_flask_app.api.resources.utilities import parse_json, score_indicator, goalpost
from sspi_flask_app.models.database import (
    sspi_metadata,
    sspi_clean_api_data,
    sspi_indicator_data,
    sspi_incomplete_indicator_data
)


# @collect_bp.route("/ISHRAT", methods=['GET'])
# @login_required
# def ishrat():
#     def collect_iterator(**kwargs):
#         yield from collect_wid_data(IndicatorCode="ISHRAT", **kwargs)
#     return Response(collect_iterator(Username=current_user.username), mimetype='text/event-stream')


@compute_bp.route("/ISHRAT")
@login_required
def compute_ishrat():
    app.logger.info("Running /api/v1/compute/ISHRAT")
    sspi_indicator_data.delete_many({"IndicatorCode": "ISHRAT"})
    sspi_incomplete_indicator_data.delete_many({"IndicatorCode": "ISHRAT"})
    lg, ug = sspi_metadata.get_goalposts("ISHRAT")
    # Fetch clean datasets
    topten_clean = sspi_clean_api_data.find({"DatasetCode": "WID_TOPTEN"})
    bfifty_clean = sspi_clean_api_data.find({"DatasetCode": "WID_BFIFTY"})
    combined_list = topten_clean + bfifty_clean
    unit = "Ratio of Bottom 50% Income Share to to Top 10% Income Share"
    clean_list, incomplete_list = score_indicator(
        combined_list, "ISHRAT",
        score_function=lambda TOPTEN, BFIFTY: goalpost(BFIFTY / TOPTEN, lg, ug),
        unit=unit
    )
    sspi_indicator_data.insert_many(clean_list)
    sspi_incomplete_indicator_data.insert_many(incomplete_list)
    return parse_json(clean_list)
