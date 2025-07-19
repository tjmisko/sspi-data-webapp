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
from sspi_flask_app.api.datasource.who import (
    collectWHOdata,
    cleanWHOdata
)
from sspi_flask_app.api.datasource.sdg import (
    collectSDGIndicatorData,
)

# # PHYSPC for Correlation Analysis with UHC
# @collect_bp.route("/PHYSPC", methods=['GET'])
# @login_required
# def physpc():
#     def collect_iterator(**kwargs):
#         yield from collectWHOdata("UHC_INDEX_REPORTED", "PHYSPC", **kwargs)
#     return Response(collect_iterator(Username=current_user.username), mimetype='text/event-stream')


# @collect_bp.route("/PHYSPC", methods=['GET'])
# @login_required
# def physpc():
#     def collect_iterator(**kwargs):
#         yield from collectWHOdata("HWF_0001", "PHYSPC", **kwargs)
#         yield from collectSDGIndicatorData("3.8.1", "PHYSPC", **kwargs)
#     return Response(collect_iterator(Username=current_user.username), mimetype='text/event-stream')


@compute_bp.route("/PHYSPC")
@login_required
def compute_physpc():
    app.logger.info("Running /api/v1/compute/PHYSPC")
    sspi_clean_api_data.delete_many({"IndicatorCode": "PHYSPC"})
    raw_data = sspi_raw_api_data.fetch_raw_data("PHYSPC")
    unit = "Doctors per 10000"
    description = (
        "Number of medical doctors (physicians), both generalists and "
        "specialists, expressed per 10,000 people."
    )
    cleaned = cleanWHOdata(raw_data, "PHYSPC", unit, description)
    scored_list = score_single_indicator(cleaned, "PHYSPC")
    sspi_clean_api_data.insert_many(scored_list)
    return parse_json(scored_list)
