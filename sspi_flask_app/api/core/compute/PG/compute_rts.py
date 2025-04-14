from flask_login import login_required
from sspi_flask_app.api.core.compute import compute_bp
from sspi_flask_app.models.database import (
    sspi_raw_api_data,
    sspi_clean_api_data
)
from sspi_flask_app.api.resources.utilities import (
    parse_json,
    score_single_indicator
)
from sspi_flask_app.api.datasource.vdem import (
    cleanEDEMOCdata
)
from flask import current_app as app


@compute_bp.route("/EDEMOC", methods=['GET'])
@login_required
def compute_edemoc():
    app.logger.info("Running /api/v1/compute/EDEMOC")
    sspi_clean_api_data.delete_many({"IndicatorCode": "EDEMOC"})
    raw_data = sspi_raw_api_data.fetch_raw_data("EDEMOC")
    cleaned_list = cleanEDEMOCdata(raw_data)
    scored_list = score_single_indicator(cleaned_list, "EDEMOC")
    sspi_clean_api_data.insert_many(scored_list)
    return parse_json(scored_list)
