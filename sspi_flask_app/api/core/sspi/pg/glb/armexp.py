from sspi_flask_app.api.core.sspi import compute_bp
from flask import current_app as app, Response
from flask_login import login_required, current_user
from sspi_flask_app.api.datasource.sipri import (
    collectSIPRIdata,
    cleanSIPRIData,
)
from sspi_flask_app.api.resources.utilities import (
    parse_json,
    score_single_indicator
)
from sspi_flask_app.models.database import (
    sspi_raw_api_data,
    sspi_clean_api_data
)
import json


# @collect_bp.route("/ARMEXP", methods=['GET'])
# @login_required
# def armexp():
#     def collect_iterator(**kwargs):
#         yield from collectSIPRIdata("local/ARMEXP/armexp.csv", "ARMEXP", **kwargs)
#     return Response(collect_iterator(Username=current_user.username), mimetype='text/event-stream')


@compute_bp.route("/ARMEXP", methods=['GET'])
@login_required
def compute_armexp():
    app.logger.info("Running /api/v1/compute/ARMEXP")
    sspi_clean_api_data.delete_many({"IndicatorCode": "ARMEXP"})
    armexp_raw = sspi_raw_api_data.fetch_raw_data("ARMEXP")
    description = (
        "The supply of military weapons through sales, aid, gifts, and those "
        "made through manufacturing licenses."
    )
    cleaned_list = cleanSIPRIData(
        'local/armexp.csv',
        'ARMEXP',
        'Millions of arms',
        description
    ) 
    obs_list = json.loads(str(cleaned_list.to_json(orient="records")))
    scored_list = score_single_indicator(obs_list, "ARMEXP")
    sspi_clean_api_data.insert_many(scored_list)
    return parse_json(scored_list)
