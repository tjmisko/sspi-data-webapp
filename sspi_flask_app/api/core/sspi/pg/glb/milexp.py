from sspi_flask_app.api.core.sspi import compute_bp
from flask import current_app as app, Response
from flask_login import login_required, current_user
from sspi_flask_app.api.resources.utilities import (
    parse_json,
    score_indicator,
    goalpost
)
from sspi_flask_app.models.database import (
    sspi_clean_api_data,
    sspi_indicator_data,
    sspi_metadata
)
import json

@compute_bp.route("/MILEXP", methods=['POST'])
@login_required
def compute_milexp():
    sspi_indicator_data.delete_many({"IndicatorCode": "MILEXP"})
    sipri_milexp_clean = sspi_clean_api_data.find({"DatasetCode": "SIPRI_MILEXP"})
    lg, ug = sspi_metadata.get_goalposts("MILEXP")
    scored_list, _ = score_indicator(
        sipri_milexp_clean, "MILEXP",
        score_function=lambda SIPRI_MILEXP: goalpost(SIPRI_MILEXP, lg, ug),
        unit="%"
    )
    sspi_indicator_data.insert_many(scored_list)
    return parse_json(scored_list)


