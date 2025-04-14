from flask import current_app as app
from flask_login import login_required
from sspi_flask_app.api.core.compute import compute_bp
from sspi_flask_app.models.database import (
    sspi_raw_api_data,
    sspi_clean_api_data
)
from sspi_flask_app.api.resources.utilities import (
    jsonify_df,
    parse_json,
    score_single_indicator
)
from sspi_flask_app.api.datasource.vdem import (
    cleanEDEMOCdata
)
import pandas as pd
from io import StringIO
from datetime import datetime
import json


@compute_bp.route("/RULELW", methods=['GET'])
@login_required
def compute_rulelw():
    app.logger.info("Running /api/v1/compute/RULELW")
    sspi_clean_api_data.delete_many({"IndicatorCode": "RULELW"})
    raw_data = sspi_raw_api_data.fetch_raw_data("RULELW")
    fragments = []
    for obs in raw_data:
        fragments.append((obs["FragmentNumber"], obs["Raw"]["csv_fragment"]))
    fragments.sort(key=lambda x: x[0])
    full_csv = "".join(fragment for _, fragment in fragments)
    df = pd.read_csv(StringIO(full_csv))
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
    scored_list = score_single_indicator(clean_list, "RULELW")
    sspi_clean_api_data.insert_many(scored_list)
    return parse_json(scored_list)


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
