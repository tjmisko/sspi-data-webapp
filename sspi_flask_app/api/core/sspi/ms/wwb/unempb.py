from sspi_flask_app.api.core.sspi import compute_bp
from flask_login import login_required, current_user
from flask import current_app as app, Response
from sspi_flask_app.models.database import (
    sspi_clean_api_data,
    sspi_indicator_data,
    sspi_metadata
)
from sspi_flask_app.api.resources.utilities import (
    parse_json,
    score_indicator,
    goalpost
)


@compute_bp.route("/UNEMPB", methods=['POST'])
@login_required
def compute_unempb():
    app.logger.info("Running /api/v1/compute/UNEMPB")
    sspi_indicator_data.delete_many({"IndicatorCode": "UNEMPB"})
    unempb_clean = sspi_clean_api_data.find({"DatasetCode": "UNSDG_BENFTS_UNEMP"})
    lg, ug = sspi_metadata.get_goalposts("UNEMPB")
    scored_data, _ = score_indicator(
        unempb_clean, "UNEMPB",
        score_function=lambda UNSDG_BENFTS_UNEMP: goalpost(UNSDG_BENFTS_UNEMP, lg, ug),
        unit="Benefits Coverage (%)"
    )
    sspi_indicator_data.insert_many(scored_data)
    return parse_json(scored_data)
