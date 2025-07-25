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
    collect_who_data,
    clean_who_data
)


# @collect_bp.route("/ATBRTH", methods=['GET'])
# @login_required
# def atbrth():
#     def collect_iterator(**kwargs):
#         yield from collect_who_data("MDG_0000000025", "ATBRTH", **kwargs)
#     return Response(collect_iterator(Username=current_user.username), mimetype='text/event-stream')


@compute_bp.route("/ATBRTH")
@login_required
def compute_atbrth():
    app.logger.info("Running /api/v1/compute/ATBRTH")
    sspi_clean_api_data.delete_many({"IndicatorCode": "ATBRTH"})
    raw_data = sspi_raw_api_data.fetch_raw_data("ATBRTH")
    description = """
    The proportion of births attended by trained and/or skilled
    health personnel
    """
    cleaned = clean_who_data(raw_data, "ATBRTH", "Percent", description)
    scored_list = score_single_indicator(cleaned, "ATBRTH")
    sspi_clean_api_data.insert_many(scored_list)
    return parse_json(scored_list)
