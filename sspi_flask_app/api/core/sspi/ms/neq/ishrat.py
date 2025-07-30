from sspi_flask_app.api.core.sspi import compute_bp
from flask_login import login_required, current_user
from flask import current_app as app, Response
from sspi_flask_app.api.datasource.wid import collect_wid_data, filter_wid_csv
from sspi_flask_app.api.resources.utilities import parse_json, score_indicator, goalpost
from sspi_flask_app.models.database import (
    sspi_metadata,
    sspi_raw_api_data,
    sspi_clean_api_data,
    sspi_incomplete_indicator_data
)
from datetime import datetime


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
    sspi_clean_api_data.delete_many({"IndicatorCode": "ISHRAT"})
    lg, ug = sspi_metadata.get_goalposts("ISHRAT")
    raw_data = sspi_raw_api_data.fetch_raw_data("ISHRAT")
    intermediates_list = []
    current_year = datetime.now().year
    for obs in raw_data:
        filtered_list = filter_wid_csv(
            obs['Raw'], obs["DatasetName"],
            ['p0p50', 'p90p100'], 'sptincj992',
            list(range(1990, current_year))
        )
        intermediates_list += filtered_list
    id_map = {"p90p100": "TOPTEN", "p0p50": "BFIFTY"}
    for obs in intermediates_list:
        obs["IntermediateCode"] = id_map[obs["Percentile"]]
        obs["Unit"] = "Percentile Share of National Income"
    unit = "Ratio of Bottom 50% Income Share to to Top 10% Income Share"
    clean_list, incomplete_list = score_indicator(
        intermediates_list, "ISHRAT",
        score_function=lambda TOPTEN, BFIFTY: goalpost(BFIFTY / TOPTEN, lg, ug),
        unit=unit
    )
    sspi_clean_api_data.insert_many(clean_list)
    sspi_incomplete_indicator_data.insert_many(incomplete_list)
    return parse_json(clean_list)
