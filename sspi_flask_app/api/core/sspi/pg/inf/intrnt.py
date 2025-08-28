from sspi_flask_app.api.core.sspi import compute_bp
from flask import current_app as app, Response
from sspi_flask_app.models.database import (
    sspi_clean_api_data,
    sspi_indicator_data,
    sspi_incomplete_indicator_data
)
from flask_login import login_required, current_user
from sspi_flask_app.api.resources.utilities import (
    parse_json,
    score_indicator,
)


# @collect_bp.route("/INTRNT", methods=['POST'])
# @login_required
# def intrnt():
#     def collect_iterator(**kwargs):
#         yield from collect_wb_data("IT.NET.USER.ZS", "INTRNT", IntermediateCode="AVINTR", **kwargs)
#         yield from collect_sdg_indicator_data("17.6.1", "INTRNT", IntermediateCode="QUINTR", **kwargs)
#     return Response(collect_iterator(Username=current_user.username), mimetype='text/event-stream')


@compute_bp.route("/INTRNT", methods=['POST'])
@login_required
def compute_intrnt():
    app.logger.info("Running /api/v1/compute/INTRNT")
    sspi_indicator_data.delete_many({"IndicatorCode": "INTRNT"})
    sspi_incomplete_indicator_data.delete_many({"IndicatorCode": "INTRNT"})
    # Fetch clean datasets
    wb_intrnt = sspi_clean_api_data.find({"DatasetCode": "WB_INTRNT"})
    unsdg_intrnt = sspi_clean_api_data.find({"DatasetCode": "UNSDG_INTRNT"})
    combined_list = wb_intrnt + unsdg_intrnt
    clean_list, incomplete_list = score_indicator(
        combined_list, "INTRNT",
        score_function=lambda WB_INTRNT, UNSDG_INTRNT: (WB_INTRNT + UNSDG_INTRNT) / 2,
        unit="Index"
    )
    sspi_indicator_data.insert_many(clean_list)
    sspi_incomplete_indicator_data.insert_many(incomplete_list)
    return parse_json(clean_list)


