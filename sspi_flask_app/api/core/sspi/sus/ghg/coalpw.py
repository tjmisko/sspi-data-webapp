from flask_login import login_required
from flask import current_app as app
from sspi_flask_app.api.core.sspi import compute_bp
from sspi_flask_app.models.database import (
    sspi_clean_api_data,
    sspi_indicator_data,
    sspi_incomplete_indicator_data,
    sspi_metadata
)
from sspi_flask_app.api.resources.utilities import (
    goalpost,
    parse_json,
    score_indicator,
)


# @collect_bp.route("/COALPW", methods=["POST"])
# @login_required
# def coalpw():
#     def collect_iterator(**kwargs):
#         yield from collect_iea_data("TESbySource", "COALPW", **kwargs)
#     return Response(
#         collect_iterator(Username=current_user.username), mimetype="text/event-stream"
#     )


@compute_bp.route("/COALPW", methods=["POST"])
@login_required
def compute_coalpw():
    app.logger.info("Running /api/v1/compute/COALPW")
    sspi_indicator_data.delete_many({"IndicatorCode": "COALPW"})
    sspi_incomplete_indicator_data.delete_many({"IndicatorCode": "COALPW"})
    
    # Fetch clean dataset
    coalpw_clean = sspi_clean_api_data.find({"DatasetCode": "IEA_COALPW"})
    lg, ug = sspi_metadata.get_goalposts("COALPW")
    
    clean_list, incomplete_list = score_indicator(
        coalpw_clean,
        "COALPW",
        score_function=lambda TLCOAL, TTLSUM: goalpost((TLCOAL / TTLSUM) * 100, lg, ug),
        unit="Index",
    )
    sspi_indicator_data.insert_many(clean_list)
    sspi_incomplete_indicator_data.insert_many(incomplete_list)
    return parse_json(clean_list)
