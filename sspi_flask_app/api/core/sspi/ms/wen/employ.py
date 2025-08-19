from sspi_flask_app.api.core.sspi import compute_bp
from flask import current_app as app
from flask_login import login_required
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


@compute_bp.route("/EMPLOY", methods=['GET'])
@login_required
def compute_employ():
    app.logger.info("Running /api/v1/compute/EMPLOY")
    sspi_indicator_data.delete_many({"IndicatorCode": "EMPLOY"})
    # Fetch clean dataset
    employ_clean = sspi_clean_api_data.find({"DatasetCode": "ILO_EMPLOY"})
    lg, ug = sspi_metadata.get_goalposts("EMPLOY")
    scored_list, _ = score_indicator(
        employ_clean, "EMPLOY",
        score_function=lambda ILO_EMPLOY: goalpost(ILO_EMPLOY, lg, ug),
        unit="Percentage"
    )
    sspi_indicator_data.insert_many(scored_list)
    return parse_json(scored_list)
