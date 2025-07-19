from sspi_flask_app.api.core.sspi import compute_bp
from flask import current_app as app, Response
from flask_login import login_required, current_user
from sspi_flask_app.api.datasource.sipri import (
    collectSIPRIdata,
    cleanSIPRIData,
)
from sspi_flask_app.api.resources.utilities import (
    parse_json,
    score_single_indicator,
)
from sspi_flask_app.models.database import (
    sspi_raw_api_data,
    sspi_clean_api_data,
)
import json

# @collect_bp.route("/MILEXP", methods=['GET'])
# @login_required
# def milexp():
#     def collect_iterator(**kwargs):
#         yield from collectSIPRIdata("MILEXP", **kwargs)
#     return Response(collect_iterator(Username=current_user.username), mimetype='text/event-stream')


@compute_bp.route("/MILEXP", methods=['GET'])
@login_required
def compute_milexp():
    app.logger.info("Running /api/v1/compute/MILEXP")
    sspi_clean_api_data.delete_many({"IndicatorCode": "MILEXP"})
    milexp_raw = sspi_raw_api_data.fetch_raw_data("MILEXP")
    cleaned_list = cleanSIPRIData(milexp_raw, 'MILEXP')
    obs_list = json.loads(cleaned_list.to_json(orient="records"))
    scored_list = score_single_indicator(obs_list, "MILEXP")
    sspi_clean_api_data.insert_many(scored_list)
    return parse_json(scored_list)
