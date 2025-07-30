from sspi_flask_app.api.core.sspi import compute_bp
from flask import current_app as app, Response
from sspi_flask_app.models.database import (
    sspi_raw_api_data,
    sspi_clean_api_data,
    sspi_metadata
)
from flask_login import login_required, current_user
from sspi_flask_app.api.resources.utilities import (
    parse_json,
    score_indicator,
    goalpost
)
from sspi_flask_app.api.datasource.itu import (
    load_itu_data_from_local_transcription,
    clean_itu_data
)
import json

# @collect_bp.route("/CYBSEC", methods=['GET'])
# @login_required
# def cybsec():
#     def collect_iterator(**kwargs):
#         yield from load_itu_data_from_local_transcription(**kwargs)
#     return Response(collect_iterator(Username=current_user.username), mimetype='text/event-stream')


@compute_bp.route("/CYBSEC", methods=['GET'])
@login_required
def compute_cybsec():
    app.logger.info("Running /api/v1/compute/CYBSEC")
    sspi_clean_api_data.delete_many({"IndicatorCode": "CYBSEC"})
    cybsec_raw = sspi_raw_api_data.fetch_raw_data("CYBSEC")
    cleaned_list = clean_itu_data(cybsec_raw)
    obs_list = json.loads(str(cleaned_list.to_json(orient="records")))
    lg, ug = sspi_metadata.get_goalposts("CYBSEC")
    scored_list, _ = score_indicator(
        obs_list, "CYBSEC",
        score_function=lambda ITU_CYBSEC: goalpost(ITU_CYBSEC, lg, ug),
        unit="Index"
    )
    sspi_clean_api_data.insert_many(scored_list)
    return parse_json(scored_list)
