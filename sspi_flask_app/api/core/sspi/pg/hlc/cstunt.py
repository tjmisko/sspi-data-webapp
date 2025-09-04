from sspi_flask_app.api.core.sspi import compute_bp
from flask import current_app as app, Response
from sspi_flask_app.models.database import (
    sspi_clean_api_data,
    sspi_indicator_data,
    sspi_metadata
)
from flask_login import login_required, current_user
from sspi_flask_app.api.resources.utilities import (
    parse_json,
    score_indicator,
    goalpost
)


@compute_bp.route("/CSTUNT", methods=['POST'])
@login_required
def compute_cstunt():
    """
    UNSDG Reports Two Different Kinds of Series:
    1. NUTRITION_ANT_HAZ_NE2 - Survey-based estimates of child stunting
    2. NUTSTUNTINGPREV       - Model-based estimates of child stunting

    Modeled data has better coverage:
    NUTRITION_ANT_HAZ_NE2 - 999 observations
    NUTSTUNTINGPREV       - 3634 observations
    """
    app.logger.info("Running /api/v1/compute/CSTUNT")
    sspi_indicator_data.delete_many({"IndicatorCode": "CSTUNT"})
    cstunt_clean = sspi_clean_api_data.find({"DatasetCode": "UNSDG_CSTUNT"})
    lg, ug = sspi_metadata.get_goalposts("CSTUNT")
    scored_list, _ = score_indicator(
        cstunt_clean, "CSTUNT",
        score_function=lambda UNSDG_CSTUNT: goalpost(UNSDG_CSTUNT, lg, ug),
        unit = "%"
    )
    sspi_indicator_data.insert_many(scored_list)
    return parse_json(scored_list)
