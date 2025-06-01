from flask import Response, current_app as app
from sspi_flask_app.api.core.sspi import collect_bp
from sspi_flask_app.api.core.sspi import compute_bp
from sspi_flask_app.models.database import (
    sspi_raw_api_data,
    sspi_clean_api_data
)
from sspi_flask_app.api.datasource.uis import (
    collectUISdata,
    cleanUISdata,
)
from flask_login import login_required, current_user
from sspi_flask_app.api.resources.utilities import (
    parse_json,
    score_single_indicator
)

@collect_bp.route("/ENRPRI", methods=['GET'])
@login_required
def enrpri():
    def collect_iterator(**kwargs):
        yield from collectUISdata("NERT.1.CP", "ENRPRI", **kwargs)
    return Response(collect_iterator(Username=current_user.username), mimetype='text/event-stream')


@compute_bp.route("/ENRPRI", methods=['GET'])
@login_required
def compute_enrpri():
    app.logger.info("Running /api/v1/compute/ENRPRI")
    sspi_clean_api_data.delete_many({"IndicatorCode": "ENRPRI"})
    raw_data = sspi_raw_api_data.fetch_raw_data("ENRPRI")
    description = "Net enrollment in primary school (%)"
    cleaned_list = cleanUISdata(raw_data, "ENRPRI", "Percent", description)
    scored_list = score_single_indicator(cleaned_list, "ENRPRI")
    sspi_clean_api_data.insert_many(scored_list)
    return parse_json(scored_list)
