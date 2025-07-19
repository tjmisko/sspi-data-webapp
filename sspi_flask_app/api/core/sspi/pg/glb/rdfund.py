from sspi_flask_app.api.core.sspi import compute_bp
from flask import current_app as app, Response
from flask_login import login_required, current_user
from sspi_flask_app.api.datasource.sdg import (
    collectSDGIndicatorData,
    extract_sdg,
    filter_sdg,
)
from sspi_flask_app.models.database import (
    sspi_raw_api_data,
    sspi_clean_api_data,
    sspi_incomplete_api_data
)
from sspi_flask_app.api.resources.utilities import (
    parse_json,
    zip_intermediates,
)


# @collect_bp.route("/RDFUND", methods=['GET'])
# @login_required
# def rdfund():
#     def collect_iterator(**kwargs):
#         yield from collectSDGIndicatorData("9.5.1", "RDFUND", **kwargs)
#         yield from collectSDGIndicatorData("9.5.2", "RDFUND", **kwargs)
#     return Response(collect_iterator(Username=current_user.username), mimetype='text/event-stream')


@compute_bp.route("/RDFUND", methods=['GET'])
@login_required
def compute_rdfund():
    """
    metadata_map = {
        "GB_XPD_RSDV": "GVTRDP",
        "GB_POP_SCIERD": "NRSRCH"
    }
    """
    app.logger.info("Running /api/v1/compute/RDFUND")
    sspi_clean_api_data.delete_many({"IndicatorCode": "RDFUND"})
    raw_data = sspi_raw_api_data.fetch_raw_data("RDFUND")
    watman_data = extract_sdg(raw_data)
    intermediate_map = {
        "GB_XPD_RSDV": "GVTRDP",
        "GB_POP_SCIERD": "NRSRCH"
    }
    intermediate_list = filter_sdg(
        watman_data, intermediate_map, activity="TOTAL"
    )
    clean_list, incomplete_list = zip_intermediates(
        intermediate_list, "RDFUND",
        ScoreFunction=lambda GVTRDP, NRSRCH: (GVTRDP + NRSRCH) / 2,
        ScoreBy="Score"
    )
    sspi_clean_api_data.insert_many(clean_list)
    sspi_incomplete_api_data.insert_many(incomplete_list)
    return parse_json(clean_list)
