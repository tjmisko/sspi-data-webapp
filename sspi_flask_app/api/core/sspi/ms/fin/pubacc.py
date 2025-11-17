from sspi_flask_app.api.core.sspi import compute_bp
from flask_login import login_required
from flask import current_app as app
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


# @collect_bp.route("/PUBACC", methods=['POST'])
# @admin_required
# def pubacc():
#     def collect_iterator(**kwargs):
#         yield from collect_wb_data("FX.OWN.TOTL.ZS", "PUBACC", **kwargs)
#     return Response(collect_iterator(Username=current_user.username), mimetype='text/event-stream')


@compute_bp.route("/PUBACC", methods=['POST'])
@admin_required
def compute_pubacc():
    app.logger.info("Running /api/v1/compute/PUBACC")
    sspi_indicator_data.delete_many({"IndicatorCode": "PUBACC"})
    # Fetch clean dataset
    pubacc_clean = sspi_clean_api_data.find({"DatasetCode": "WB_PUBACC"})
    lg, ug = sspi_metadata.get_goalposts("PUBACC")
    pubacc_scored, _ = score_indicator(
        pubacc_clean, "PUBACC",
        score_function=lambda WB_PUBACC: goalpost(WB_PUBACC, lg, ug),
        unit="Percent"
    )
    sspi_indicator_data.insert_many(pubacc_scored)
    return parse_json(pubacc_scored)
