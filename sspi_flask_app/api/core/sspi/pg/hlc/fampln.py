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
from sspi_flask_app.api.datasource.sdg import (
    collectSDGIndicatorData,
    extract_sdg,
    filter_sdg,
)


# @collect_bp.route("/FAMPLN", methods=['GET'])
# @login_required
# def fampln():
#     def collect_iterator(**kwargs):
#         yield from collectSDGIndicatorData("3.7.1", "FAMPLN", **kwargs)
#     return Response(collect_iterator(Username=current_user.username), mimetype='text/event-stream')


@compute_bp.route("/FAMPLN")
@login_required
def compute_fampln():
    app.logger.info("Running /api/v1/compute/FAMPLN")
    sspi_clean_api_data.delete_many({"IndicatorCode": "FAMPLN"})
    raw_data = sspi_raw_api_data.fetch_raw_data("FAMPLN")
    extracted_fampln = extract_sdg(raw_data)
    filtered_fampln = filter_sdg(
        extracted_fampln, {"SH_FPL_MTMM": "FAMPLN"},
    )
    scored_list = score_single_indicator(filtered_fampln, "FAMPLN")
    sspi_clean_api_data.insert_many(scored_list)
    return parse_json(scored_list)
