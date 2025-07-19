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
from sspi_flask_app.api.datasource.fsi import (
    collectFSIdata,
    cleanFSIdata
)


# @collect_bp.route("/SECAPP", methods=['GET'])
# @login_required
# def secapp():
#     def collect_iterator(**kwargs):
#         yield from collectFSIdata("SECAPP", **kwargs)
#     return Response(collect_iterator(Username=current_user.username), mimetype='text/event-stream')


@compute_bp.route("/SECAPP")
@login_required
def compute_secapp():
    app.logger.info("Running /api/v1/compute/SECAPP")
    sspi_clean_api_data.delete_many({"IndicatorCode": "SECAPP"})
    raw_data = sspi_raw_api_data.fetch_raw_data("SECAPP")
    description = (
        "The Security Apparatus is a component of the Fragile State Index, "
        "which considers the security threats to a state such as bombings, "
        "attacks/battle-related deaths, rebel movements, mutinies, coups, or "
        "terrorism. It is an index scored between 0 and 10."
    )
    cleaned_list = cleanFSIdata(
        raw_data, "SECAPP", "Index", description
    )
    scored_list = score_single_indicator(cleaned_list, "SECAPP")
    sspi_clean_api_data.insert_many(scored_list)
    return parse_json(scored_list)
