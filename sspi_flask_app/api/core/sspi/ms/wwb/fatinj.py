from sspi_flask_app.api.core.sspi import compute_bp
from flask import current_app as app, Response
from flask_login import login_required, current_user
from sspi_flask_app.models.database import (
    sspi_clean_api_data,
    sspi_indicator_data,
    sspi_metadata
)
from sspi_flask_app.api.resources.utilities import (
    parse_json,
    score_indicator,
    goalpost
)


# @collect_bp.route("/FATINJ")
# @login_required
# def fatinj():
#     def collect_iterator(**kwargs):
#         yield from collect_ilo_data("DF_SDG_F881_SEX_MIG_RT", "FATINJ", **kwargs)
#     return Response(
#         collect_iterator(Username=current_user.username), mimetype="text/event-stream"
#     )


@compute_bp.route("/FATINJ", methods=["POST"])
@login_required
def compute_fatinj():
    app.logger.info("Running /api/v1/compute/FATINJ")
    sspi_indicator_data.delete_many({"IndicatorCode": "FATINJ"})
    fatinj_clean = sspi_clean_api_data.find({"DatasetCode": "ILO_FATINJ"})
    lg, ug = sspi_metadata.get_goalposts("FATINJ")
    scored_data, _ = score_indicator(
        fatinj_clean, "FATINJ",
        score_function=lambda ILO_FATINJ: goalpost(ILO_FATINJ, lg, ug),
        unit="Rate"
    )
    sspi_indicator_data.insert_many(scored_data)
    return parse_json(scored_data)
