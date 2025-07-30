from sspi_flask_app.api.core.sspi import compute_bp
from flask import current_app as app, Response
from flask_login import login_required, current_user
from sspi_flask_app.api.datasource.unsdg import collect_sdg_indicator_data, extract_sdg, filter_sdg
from sspi_flask_app.models.database import (
    sspi_raw_api_data,
    sspi_clean_api_data,
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
    sspi_clean_api_data.delete_many({"IndicatorCode": "AIRPOL"})
    raw_data = sspi_raw_api_data.fetch_raw_data("AIRPOL")
    extracted_airpol = extract_sdg(raw_data)
    filtered_airpol = filter_sdg(
        extracted_airpol, {"EN_ATM_PM25": "AIRPOL"},
        location="ALLAREA"
    )
    lg, ug = sspi_metadata.get_goalposts("AIRPOL")
    scored_list, _ = score_indicator(
        filtered_airpol, "AIRPOL",
        score_function=lambda UNSDG_AIRPOL: goalpost(UNSDG_AIRPOL, lg, ug),
        unit="Pollution Level"
    )
    sspi_clean_api_data.insert_many(scored_list)
    return parse_json(scored_list)
