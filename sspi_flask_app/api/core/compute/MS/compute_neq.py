from flask import current_app as app
from flask_login import login_required
from sspi_flask_app.api.core.compute import compute_bp
from sspi_flask_app.models.database import (
    sspi_raw_api_data,
    sspi_clean_api_data
)
from sspi_flask_app.api.resources.utilities import (
    parse_json,
    zip_intermediates,
    score_single_indicator
)
from sspi_flask_app.api.datasource.worldbank import (
    clean_wb_data
)


@compute_bp.route("/GINIPT")
@login_required
def compute_ginipt():
    app.logger.info("Running /api/v1/compute/GINIPT")
    sspi_clean_api_data.delete_many({"IndicatorCode": "GINIPT"})
    raw_data = sspi_raw_api_data.fetch_raw_data("GINIPT")
    clean_ginipt = clean_wb_data(raw_data, "GINIPT", "GINI Coeffecient")
    scored_list = score_single_indicator(clean_ginipt, "GINIPT")
    sspi_clean_api_data.insert_many(scored_list)
    return parse_json(scored_list)
