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


@compute_bp.route("/UNEMPL", methods=['POST'])
@login_required
def compute_unempl():
    app.logger.info("Running /api/v1/compute/UNEMPL")
    sspi_indicator_data.delete_many({"IndicatorCode": "UNEMPL"})
    unempl_clean = sspi_clean_api_data.find({"DatasetCode": "UNSDG_BENFTS_UNEMP"})
    lg, ug = sspi_metadata.get_goalposts("UNEMPL")
    scored_data, _ = score_indicator(
        unempl_clean, "UNEMPL",
        score_function=lambda UNSDG_BENFTS_UNEMP: goalpost(UNSDG_BENFTS_UNEMP, lg, ug),
        unit="Benefits Coverage (%)"
    )
    sspi_indicator_data.insert_many(scored_data)
    return parse_json(scored_data)
