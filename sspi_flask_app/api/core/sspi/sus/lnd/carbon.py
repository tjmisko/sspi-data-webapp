from sspi_flask_app.api.core.sspi import compute_bp
from flask import current_app as app
from flask_login import login_required
from sspi_flask_app.models.database import (
    sspi_clean_api_data,
    sspi_indicator_data,
    sspi_incomplete_indicator_data,
    sspi_metadata
)
from sspi_flask_app.api.resources.utilities import (
    parse_json,
    goalpost,
    score_indicator
)


@compute_bp.route("/CARBON", methods=['POST'])
@login_required
def compute_carbon():
    sspi_indicator_data.delete_many({"IndicatorCode": "CARBON"})
    sspi_incomplete_indicator_data.delete_many({"IndicatorCode": "CARBON"})
    crbnlv_clean = sspi_clean_api_data.find({"DatasetCode": "UNFAO_CRBNLV"})
    crbnav_clean = sspi_clean_api_data.find({"DatasetCode": "UNFAO_CRBNAV"})
    combined_list = crbnlv_clean + crbnav_clean
    filtered_combined = []
    for obs in combined_list:
        if obs.get("DatasetCode") == "UNFAO_CRBNLV" and obs.get("Year", 0) >= 2000:
            filtered_combined.append(obs)
        elif obs.get("DatasetCode") == "UNFAO_CRBNAV":
            filtered_combined.append(obs)
    
    lg, ug = sspi_metadata.get_goalposts("CARBON")
    
    clean_list, incomplete_list = score_indicator(
        filtered_combined,
        "CARBON",
        score_function=lambda UNFAO_CRBNLV, UNFAO_CRBNAV: goalpost((UNFAO_CRBNLV - UNFAO_CRBNAV) / UNFAO_CRBNAV * 100, lg, ug),
        unit="Index",
    )
    sspi_indicator_data.insert_many(clean_list)
    sspi_incomplete_indicator_data.insert_many(incomplete_list)
    return parse_json(clean_list)
