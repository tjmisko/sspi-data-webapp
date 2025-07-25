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


# @collect_bp.route("/DPTCOV", methods=['GET'])
# @login_required
# def dptcov():
#     def collect_iterator(**kwargs):
#         yield from collect_who_data("vdpt", "DPTCOV", **kwargs)
#     return Response(collect_iterator(Username=current_user.username), mimetype='text/event-stream')


@compute_bp.route("/DPTCOV")
@login_required
def compute_dptcov():
    app.logger.info("Running /api/v1/compute/DPTCOV")
    sspi_clean_api_data.delete_many({"IndicatorCode": "DPTCOV"})
    raw_data = sspi_raw_api_data.fetch_raw_data("DPTCOV")
    description = "DTP3 immunization coverage among one-year-olds (%)"
    cleaned = clean_who_data(raw_data, "DPTCOV", "Percent", description)
    scored_list = score_single_indicator(cleaned, "DPTCOV")
    sspi_clean_api_data.insert_many(scored_list)
    return parse_json(scored_list)
