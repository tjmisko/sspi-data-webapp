from flask import current_app as app
from flask_login import login_required

from sspi_flask_app.api.core.sspi import compute_bp
from sspi_flask_app.api.resources.utilities import parse_json, score_indicator, goalpost
from sspi_flask_app.models.database import sspi_clean_api_data, sspi_indicator_data, sspi_metadata

# @collect_bp.route("/COLBAR")
# @login_required
# def colbar():
#     def collect_iterator(**kwargs):
#         url_params = ["startPeriod=1990-01-01", "endPeriod=2024-12-31"]
#         yield from collect_ilo_data(
#             "DF_ILR_CBCT_NOC_RT", "COLBAR", URLParams=url_params, **kwargs
#         )
#     return Response(
#         collect_iterator(Username=current_user.username), mimetype="text/event-stream"
#     )


@compute_bp.route("/COLBAR", methods=["GET"])
@login_required
def compute_colbar():
    app.logger.info("Running /api/v1/compute/COLBAR")
    sspi_indicator_data.delete_many({"IndicatorCode": "COLBAR"})
    # Fetch clean dataset
    colbar_clean = sspi_clean_api_data.find({"DatasetCode": "ILO_COLBAR"})
    lg, ug = sspi_metadata.get_goalposts("COLBAR")
    scored_list, _ = score_indicator(
        colbar_clean, "COLBAR",
        score_function=lambda ILO_COLBAR: goalpost(ILO_COLBAR, lg, ug),
        unit="%"
    )
    sspi_indicator_data.insert_many(scored_list)
    return parse_json(scored_list)
