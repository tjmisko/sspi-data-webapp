from sspi_flask_app.api.core.sspi import compute_bp
from flask import current_app as app, Response
from sspi_flask_app.models.database import (
    sspi_raw_api_data,
    sspi_clean_api_data,
    sspi_metadata
)
from flask_login import login_required, current_user
from sspi_flask_app.api.resources.utilities import (
    parse_json,
    score_indicator,
    goalpost
)
from sspi_flask_app.api.datasource.vdem import collect_vdem_data
from datetime import datetime
from io import StringIO
import pandas as pd
import json


# @collect_bp.route("/RULELW", methods=['GET'])
# @login_required
# def rulelw():
#     def collect_iterator(**kwargs):
#         yield from collect_vdem_data("v2x_rule", "RULELW", **kwargs)
#     return Response(collect_iterator(Username=current_user.username), mimetype='text/event-stream')


@compute_bp.route("/RULELW", methods=['GET'])
@login_required
def compute_rulelw():
    app.logger.info("Running /api/v1/compute/RULELW")
    sspi_clean_api_data.delete_many({"IndicatorCode": "RULELW"})
    raw_data = sspi_raw_api_data.fetch_raw_data("RULELW")
    df = pd.read_csv(StringIO(raw_data[0]["Raw"]))
    filtered_df = df[['country_text_id', 'year', 'v2x_rule']]
    current_year = datetime.now().year
    filtered_df = filtered_df[(filtered_df["year"] > 1990) & (filtered_df["year"] < current_year)]
    obs_list = json.loads(str(filtered_df.to_json(orient='records')))
    clean_list = []
    for obs in obs_list:
        if obs["v2x_rule"] is None:
            continue
        clean_list.append({
            "IndicatorCode": "RULELW",
            "CountryCode": obs["country_text_id"],
            "Year": obs["year"],
            "Value": obs["v2x_rule"],
            "Unit": "Index"
        })
    lg, ug = sspi_metadata.get_goalposts("RULELW")
    scored_list, _ = score_indicator(
        clean_list, "RULELW",
        score_function=lambda VDEM_RULELW: goalpost(VDEM_RULELW, lg, ug),
        unit="Index"
    )
    sspi_clean_api_data.insert_many(scored_list)
    return parse_json(scored_list)
