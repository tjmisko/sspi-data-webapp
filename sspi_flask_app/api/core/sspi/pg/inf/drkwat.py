from sspi_flask_app.api.core.sspi import collect_bp
from sspi_flask_app.api.core.sspi import compute_bp
from flask import current_app as app, Response
from sspi_flask_app.models.database import (
    sspi_raw_api_data,
    sspi_clean_api_data
)
from sspi_flask_app.api.resources.utilities import (
    parse_json,
    score_single_indicator
)
from sspi_flask_app.api.datasource.worldbank import clean_wb_data, collectWorldBankdata
from flask_login import login_required, current_user


# @collect_bp.route("/DRKWAT", methods=['GET'])
# @login_required
# def drkwat():
#     def collect_iterator(**kwargs):
#         yield from collectWorldBankdata("SH.H2O.SMDW.ZS", "DRKWAT", **kwargs)
#     return Response(collect_iterator(Username=current_user.username), mimetype='text/event-stream')


@compute_bp.route("/DRKWAT")
@login_required
def compute_drkwat():
    app.logger.info("Running /api/v1/compute/DRKWAT")
    sspi_clean_api_data.delete_many({"IndicatorCode": "DRKWAT"})
    raw_data = sspi_raw_api_data.fetch_raw_data("DRKWAT")
    cleaned = clean_wb_data(raw_data, "DRKWAT", "Percent")
    scored_list = score_single_indicator(cleaned, "DRKWAT")
    sspi_clean_api_data.insert_many(scored_list)
    return parse_json(scored_list)
