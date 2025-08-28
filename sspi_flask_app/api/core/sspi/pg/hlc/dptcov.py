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


@compute_bp.route("/DPTCOV", methods=["POST"])
@login_required
def compute_dptcov():
    app.logger.info("Running /api/v1/compute/DPTCOV")
    sspi_indicator_data.delete_many({"IndicatorCode": "DPTCOV"})
    dptcov_clean = sspi_clean_api_data.find({"DatasetCode": "WHO_DPTCOV"})
    lg, ug = sspi_metadata.get_goalposts("DPTCOV")
    scored_list, _ = score_indicator(
        dptcov_clean, "DPTCOV",
        score_function=lambda WHO_DPTCOV: goalpost(WHO_DPTCOV, lg, ug),
        unit="%"
    )
    sspi_indicator_data.insert_many(scored_list)
    return parse_json(scored_list)
