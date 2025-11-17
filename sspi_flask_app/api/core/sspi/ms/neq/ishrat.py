from sspi_flask_app.api.core.sspi import compute_bp
from flask_login import login_required
from flask import current_app as app
from sspi_flask_app.api.resources.utilities import parse_json, score_indicator, goalpost
from sspi_flask_app.models.database import (
    sspi_metadata,
    sspi_clean_api_data,
    sspi_indicator_data,
    sspi_incomplete_indicator_data)

from sspi_flask_app.auth.decorators import admin_required


@compute_bp.route("/ISHRAT", methods=["POST"])
@admin_required
def compute_ishrat():
    app.logger.info("Running /api/v1/compute/ISHRAT")
    sspi_indicator_data.delete_many({"IndicatorCode": "ISHRAT"})
    sspi_incomplete_indicator_data.delete_many({"IndicatorCode": "ISHRAT"})
    lg, ug = sspi_metadata.get_goalposts("ISHRAT")
    # Fetch clean datasets
    topten_clean = sspi_clean_api_data.find({"DatasetCode": "WID_NINCSH_PRETAX_P90P100"})
    bfifty_clean = sspi_clean_api_data.find({"DatasetCode": "WID_NINCSH_PRETAX_P0P50"})
    combined_list = topten_clean + bfifty_clean
    unit = "Ratio of Bottom 50% Income Share to to Top 10% Income Share"
    clean_list, incomplete_list = score_indicator(
        combined_list, "ISHRAT",
        score_function=lambda WID_NINCSH_PRETAX_P90P100, WID_NINCSH_PRETAX_P0P50: goalpost(WID_NINCSH_PRETAX_P0P50 / WID_NINCSH_PRETAX_P90P100, lg, ug),
        unit=unit
    )
    sspi_indicator_data.insert_many(clean_list)
    sspi_incomplete_indicator_data.insert_many(incomplete_list)
    return parse_json(clean_list)
