import logging
from flask import Response, current_app as app
from flask_login import login_required, current_user
from sspi_flask_app.api.core.sspi import compute_bp
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

@compute_bp.route("/STCONS", methods=['POST'])
@login_required
def compute_stcons():
    sspi_indicator_data.delete_many({"IndicatorCode": "STCONS"})
    dataset_list = sspi_clean_api_data.find({"DatasetCode": "FPI_ECOFPT_PER_CAP"})
    lg, ug = sspi_metadata.get_goalposts("STCONS") 
    scored_data, _ = score_indicator(
        dataset_list, "STCONS",
        score_function=lambda FPI_ECOFPT_PER_CAP: goalpost(FPI_ECOFPT_PER_CAP, lg, ug),
        unit="Index"
    )
    sspi_indicator_data.insert_many(scored_data)
    return parse_json(scored_data)