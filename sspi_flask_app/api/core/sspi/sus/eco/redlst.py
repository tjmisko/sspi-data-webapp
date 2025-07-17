import logging
from flask import Response, current_app as app
from flask_login import login_required, current_user
from sspi_flask_app.api.core.sspi import collect_bp
from sspi_flask_app.api.core.sspi import compute_bp
from sspi_flask_app.api.datasource.sdg import (
    collectSDGIndicatorData,
    extract_sdg,
    filter_sdg,
)
from sspi_flask_app.api.resources.utilities import (
    parse_json,
    score_single_indicator,
)
from sspi_flask_app.models.database import (
    sspi_raw_api_data,
    sspi_clean_api_data,
)

log = logging.getLogger(__name__)

# @collect_bp.route("/REDLST", methods=['GET'])
# @login_required
# def redlst():
#     def collect_iterator(**kwargs):
#         yield from collectSDGIndicatorData("15.5.1", "REDLST", **kwargs)
#     log.info("Running /api/v1/collect/REDLST")
#     return Response(collect_iterator(Username=current_user.username), mimetype='text/event-stream')

@compute_bp.route("/REDLST", methods=['GET'])
@login_required
def compute_rdlst():
    app.logger.info("Running /api/v1/compute/REDLST")
    sspi_clean_api_data.delete_many({"IndicatorCode": "REDLST"})
    raw_data = sspi_raw_api_data.fetch_raw_data("REDLST")
    extracted_redlst = extract_sdg(raw_data)
    idcode_map = {
        "ER_RSK_LST": "REDLST",
    }
    filtered_redlst = filter_sdg(
        extracted_redlst,
        idcode_map,
    )
    scored_data = score_single_indicator(filtered_redlst, "REDLST")
    sspi_clean_api_data.insert_many(scored_data)
    return parse_json(scored_data)
