from sspi_flask_app.api.core.sspi import compute_bp
from flask_login import login_required, current_user
from flask import current_app as app, Response
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


# @collect_bp.route("/UNEMPL")
# @login_required
# def unempl():
#     def collect_iterator(**kwargs):
#         yield from collect_ilo_data("DF_SDG_0131_SEX_SOC_RT", "UNEMPL", **kwargs)
#     return Response(collect_iterator(Username=current_user.username), mimetype='text/event-stream')


@compute_bp.route("/UNEMPL", methods=['POST'])
@login_required
def compute_unempl():
    app.logger.info("Running /api/v1/compute/UNEMPL")
    sspi_indicator_data.delete_many({"IndicatorCode": "UNEMPL"})
    unempl_clean = sspi_clean_api_data.find({"DatasetCode": "ILO_UNEMPL"})
    lg, ug = sspi_metadata.get_goalposts("UNEMPL")
    scored_data, _ = score_indicator(
        unempl_clean, "UNEMPL",
        score_function=lambda ILO_UNEMPL: goalpost(ILO_UNEMPL, lg, ug),
        unit="Rate"
    )
    sspi_indicator_data.insert_many(scored_data)
    return parse_json(scored_data)
