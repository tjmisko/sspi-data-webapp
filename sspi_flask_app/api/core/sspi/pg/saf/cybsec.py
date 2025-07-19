from sspi_flask_app.api.core.sspi import compute_bp
from flask import current_app as app, Response
from sspi_flask_app.models.database import (
    sspi_raw_api_data,
    sspi_clean_api_data,
)
from flask_login import login_required, current_user
from sspi_flask_app.api.resources.utilities import (
    parse_json,
    score_single_indicator
)
from sspi_flask_app.api.datasource.itu import (
    collect_itu_data,
    cleanITUData_cybsec
)
import json

# @collect_bp.route("/CYBSEC", methods=['GET'])
# @login_required
# def cybsec():
#     def collect_iterator(**kwargs):
#         yield from collect_itu_data("CYBSEC", **kwargs)
#     return Response(collect_iterator(Username=current_user.username), mimetype='text/event-stream')


@compute_bp.route("/CYBSEC", methods=['GET'])
@login_required
def compute_cybsec():
    app.logger.info("Running /api/v1/compute/CYBSEC")
    sspi_clean_api_data.delete_many({"IndicatorCode": "CYBSEC"})
    cybsec_raw = sspi_raw_api_data.fetch_raw_data("CYBSEC")
    cleaned_list = cleanITUData_cybsec(cybsec_raw, 'CYBSEC')
    obs_list = json.loads(str(cleaned_list.to_json(orient="records")))
    scored_list = score_single_indicator(obs_list, "CYBSEC")
    sspi_clean_api_data.insert_many(scored_list)
    return parse_json(scored_list)
