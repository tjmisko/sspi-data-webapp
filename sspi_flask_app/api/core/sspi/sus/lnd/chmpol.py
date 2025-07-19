from sspi_flask_app.api.core.sspi import compute_bp
from flask_login import login_required, current_user
from flask import Response, current_app as app
from sspi_flask_app.api.datasource.sdg import (
    collectSDGIndicatorData,
    extract_sdg,
    filter_sdg,
)
from sspi_flask_app.models.database import (
    sspi_raw_api_data,
    sspi_clean_api_data,
)
from sspi_flask_app.api.resources.utilities import (
    score_single_indicator,
    parse_json,
)


# @collect_bp.route("/CHMPOL", methods=["GET"])
# @login_required
# def chmpol():
#     def collect_iterator(**kwargs):
#         yield from collectSDGIndicatorData("12.4.1", "CHMPOL", **kwargs)
#     return Response(
#         collect_iterator(Username=current_user.username), mimetype="text/event-stream"
#     )


@compute_bp.route("/CHMPOL", methods=["GET"])
@login_required
def compute_chmpol():
    app.logger.info("Running /api/v1/compute/CHMPOL")
    sspi_clean_api_data.delete_many({"IndicatorCode": "CHMPOL"})
    raw_data = sspi_raw_api_data.fetch_raw_data("CHMPOL")
    extracted_chmpol = extract_sdg(raw_data)
    filtered_chmpol = filter_sdg(
        extracted_chmpol,
        {"SG_HAZ_CMRSTHOLM": "CHMPOL"},
    )
    scored_list = score_single_indicator(filtered_chmpol, "CHMPOL")
    sspi_clean_api_data.insert_many(scored_list)
    return parse_json(scored_list)
