from sspi_flask_app.api.core.sspi import compute_bp
from flask_login import login_required, current_user
from flask import current_app as app, Response
from sspi_flask_app.api.datasource.worldbank import (
    collect_wb_data,
    clean_wb_data,
)
from sspi_flask_app.api.resources.utilities import (
    parse_json,
    score_indicator,
    goalpost
)
from sspi_flask_app.models.database import (
    sspi_raw_api_data,
    sspi_clean_api_data,
    sspi_metadata
)


# @collect_bp.route("/PUPTCH", methods=['GET'])
# @login_required
# def puptch():
#     def collect_iterator(**kwargs):
#         yield from collect_wb_data("SE.PRM.ENRL.TC.ZS", "PUPTCH", **kwargs)
#     return Response(collect_iterator(Username=current_user.username), mimetype='text/event-stream')



@compute_bp.route("/PUPTCH", methods=['GET'])
@login_required
def compute_puptch():
    app.logger.info("Running /api/v1/compute/PUPTCH")
    sspi_clean_api_data.delete_many({"IndicatorCode": "PUPTCH"})
    raw_data = sspi_raw_api_data.fetch_raw_data("PUPTCH")
    cleaned_list = clean_wb_data(raw_data, "PUPTCH", "Average")
    lg, ug = sspi_metadata.get_goalposts("PUPTCH")
    scored_list, _ = score_indicator(
        cleaned_list, "PUPTCH",
        score_function=lambda WB_PUPTCH: goalpost(WB_PUPTCH, lg, ug),
        unit="Ratio"
    )
    sspi_clean_api_data.insert_many(scored_list)
    return parse_json(scored_list)
