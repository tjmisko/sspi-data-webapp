from flask_login import login_required, current_user
from flask import Response, current_app as app
from sspi_flask_app.api.datasource.epi import collect_epi_data
from sspi_flask_app.api.core.sspi import compute_bp
from sspi_flask_app.models.database import (
    sspi_clean_api_data,
    sspi_indicator_data,
    sspi_metadata)

from sspi_flask_app.auth.decorators import admin_required
from sspi_flask_app.api.resources.utilities import (
    parse_json,
    score_indicator,
    goalpost
)
import pandas as pd
import re
from io import StringIO
import json


@compute_bp.route("/NITROG", methods=['POST'])
@admin_required
def compute_nitrog():
    sspi_indicator_data.delete_many({"IndicatorCode": "NITROG"})
    obs_list = sspi_clean_api_data.find({"DatasetCode": "EPI_NITROG"})
    lg, ug = sspi_metadata.get_goalposts("NITROG")
    scored_list, _ = score_indicator(
        obs_list, "NITROG",
        score_function=lambda EPI_NITROG: goalpost(EPI_NITROG, lg, ug),
        unit="Index"
    )
    sspi_indicator_data.insert_many(scored_list)
    return parse_json(scored_list)


