from flask import Response, current_app as app
from sspi_flask_app.api.core.sspi import compute_bp
from sspi_flask_app.models.database import (
    sspi_raw_api_data,
    sspi_clean_api_data
)
from sspi_flask_app.api.datasource.uis import (
    collect_uis_data,
    clean_uis_data,
)
from flask_login import login_required, current_user
from sspi_flask_app.api.resources.utilities import (
    parse_json,
    score_single_indicator
)


# @collect_bp.route("/ENRSEC", methods=['GET'])
# @login_required
# def enrsec():
#     def collect_iterator(**kwargs):
#         yield from collect_uis_data("NERT.2.CP", "ENRSEC", **kwargs)
#     return Response(collect_iterator(Username=current_user.username), mimetype='text/event-stream')


@compute_bp.route("/ENRSEC", methods=['GET'])
@login_required
def compute_enrsec():
    app.logger.info("Running /api/v1/compute/ENRSEC")
    sspi_clean_api_data.delete_many({"IndicatorCode": "ENRSEC"})
    raw_data = sspi_raw_api_data.fetch_raw_data("ENRSEC")
    description = "Net enrollment in lower secondary school (%)"
    cleaned_list = clean_uis_data(raw_data, "ENRSEC", "Percent", description)
    scored_list = score_single_indicator(cleaned_list, "ENRSEC")
    sspi_clean_api_data.insert_many(scored_list)
    return parse_json(scored_list)
