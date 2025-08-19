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



# @collect_bp.route("/AQELEC", methods=['GET'])
# @login_required
# def aqelec():
#     def collect_iterator(**kwargs):
#         yield from collect_wb_data("EG.ELC.ACCS.ZS", "AQELEC", IntermediateCode="AVELEC", **kwargs)
#         yield from collect_wef_data("WEF.GCIHH.EOSQ064", **kwargs)
#     return Response(collect_iterator(Username=current_user.username), mimetype='text/event-stream')



@compute_bp.route("/AQELEC", methods=["POST"])
@login_required
def compute_aqelec():
    app.logger.info("Running /api/v1/compute/AQELEC")
    sspi_indicator_data.delete_many({"IndicatorCode": "AQELEC"})
    sspi_incomplete_indicator_data.delete_many({"IndicatorCode": "AQELEC"})
    # Fetch clean datasets
    wb_avelec = sspi_clean_api_data.find({"DatasetCode": "WB_AVELEC"})
    wef_quelec = sspi_clean_api_data.find({"DatasetCode": "WEF_QUELEC"})
    combined_list = wb_avelec + wef_quelec
    clean_list, incomplete_list = score_indicator(
        combined_list, "AQELEC",
        score_function=lambda WB_AVELEC, WEF_QUELEC: 0.5 * WB_AVELEC + 0.5 * WEF_QUELEC,
        unit="Index"
    )
    sspi_indicator_data.insert_many(clean_list)
    sspi_incomplete_indicator_data.insert_many(incomplete_list)
    return parse_json(clean_list)
