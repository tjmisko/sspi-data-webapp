from flask import Response
from flask import current_app as app
from flask_login import current_user, login_required

from sspi_flask_app.api.core.sspi import compute_bp
from sspi_flask_app.api.resources.utilities import (
    goalpost,
    parse_json,
    score_indicator,
)
from sspi_flask_app.models.database import (
    sspi_clean_api_data,
    sspi_indicator_data,
    sspi_incomplete_indicator_data,
    sspi_metadata,
)

# @collect_bp.route("/PRISON", methods=["POST"])
# @login_required
# def prison():
#     def collect_iterator(**kwargs):
#         yield from collect_wb_data(
#             "SP.POP.TOTL", "PRISON", IntermediateCode="POPULN", **kwargs
#         )
#         yield from collect_prison_studies_data(IntermediateCode="PRIPOP", **kwargs)
#     return Response(
#         collect_iterator(Username=current_user.username), mimetype="text/event-stream"
#     )


@compute_bp.route("/PRISON", methods=["POST"])
@login_required
def compute_prison():
    app.logger.info("Running /api/v1/compute/PRISON")
    sspi_indicator_data.delete_many({"IndicatorCode": "PRISON"})
    sspi_incomplete_indicator_data.delete_many({"IndicatorCode": "PRISON"})
    # Fetch clean datasets
    wb_populn = sspi_clean_api_data.find({"DatasetCode": "WB_POPULN"})
    ps_pripop = sspi_clean_api_data.find({"DatasetCode": "PS_PRIPOP"})
    combined_list = wb_populn + ps_pripop
    lg, ug = sspi_metadata.get_goalposts("PRISON")
    clean_list, incomplete_list = score_indicator(
        combined_list,
        "PRISON",
        score_function=lambda WB_POPULN, PS_PRIPOP: goalpost(PS_PRIPOP / WB_POPULN * 100000, lg, ug),
        unit=lambda WB_POPULN, PS_PRIPOP: "Prisoners Per 100,000"
    )
    sspi_indicator_data.insert_many(clean_list)
    sspi_incomplete_indicator_data.insert_many(incomplete_list)
    return parse_json(clean_list)
