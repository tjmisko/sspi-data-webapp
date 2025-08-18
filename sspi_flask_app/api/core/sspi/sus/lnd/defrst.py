from sspi_flask_app.api.core.sspi import compute_bp
from flask_login import login_required
from flask import current_app as app
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


# @collect_bp.route("/DEFRST", methods=['POST'])
# @login_required
# def defrst():
#     def collect_iterator(**kwargs):
#         yield from collect_unfao_data("5110", "6717", "RL", "DEFRST", **kwargs)
#     return Response(collect_iterator(Username=current_user.username), mimetype='text/event-stream')


@compute_bp.route("/DEFRST", methods=['POST'])
@login_required
def compute_defrst():
    app.logger.info("Running /api/v1/compute/DEFRST")
    sspi_indicator_data.delete_many({"IndicatorCode": "DEFRST"})
    sspi_incomplete_indicator_data.delete_many({"IndicatorCode": "DEFRST"})
    
    # Fetch clean datasets
    frstlv_clean = sspi_clean_api_data.find({"DatasetCode": "UNFAO_FRSTLV"})
    frstav_clean = sspi_clean_api_data.find({"DatasetCode": "UNFAO_FRSTAV"})
    combined_list = frstlv_clean + frstav_clean
    
    # Filter to post-2000 data for FRSTLV
    filtered_combined = []
    for obs in combined_list:
        if obs.get("DatasetCode") == "UNFAO_FRSTLV" and obs.get("Year", 0) >= 2000:
            filtered_combined.append(obs)
        elif obs.get("DatasetCode") == "UNFAO_FRSTAV":
            filtered_combined.append(obs)
    
    lg, ug = sspi_metadata.get_goalposts("DEFRST")
    
    clean_list, incomplete_list = score_indicator(
        filtered_combined,
        "DEFRST",
        score_function=lambda UNFAO_FRSTLV, UNFAO_FRSTAV: goalpost((UNFAO_FRSTLV - UNFAO_FRSTAV) / UNFAO_FRSTAV * 100, lg, ug),
        unit="Index",
    )
    sspi_indicator_data.insert_many(clean_list)
    sspi_incomplete_indicator_data.insert_many(incomplete_list)
    return parse_json(clean_list)


