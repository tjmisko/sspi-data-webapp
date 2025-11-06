import logging
from flask import Response, current_app as app
from flask_login import login_required, current_user
from sspi_flask_app.api.core.sspi import compute_bp
from sspi_flask_app.api.datasource.unsdg import (
    collect_sdg_indicator_data,
    extract_sdg,
    filter_sdg,
)
from sspi_flask_app.api.resources.utilities import (
    parse_json,
    score_indicator,
    goalpost
)
from sspi_flask_app.models.database import (
    sspi_raw_api_data,
    sspi_clean_api_data,
    sspi_metadata,
    sspi_indicator_data
)

log = logging.getLogger(__name__)

@compute_bp.route("/REDLST", methods=['POST'])
@login_required
def compute_redlst():
    sspi_indicator_data.delete_many({"IndicatorCode": "REDLST"})
    dataset_list = sspi_clean_api_data.find({"DatasetCode": "UNSDG_REDLST"})
    lg, ug = sspi_metadata.get_goalposts("REDLST") 
    scored_data, _ = score_indicator(
        dataset_list, "REDLST",
        score_function=lambda UNSDG_REDLST: goalpost(UNSDG_REDLST, lg, ug),
        unit="Index"
    )
    sspi_indicator_data.insert_many(scored_data)
    return parse_json(scored_data)
