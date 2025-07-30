from sspi_flask_app.api.core.sspi import compute_bp
from flask import current_app as app, Response
from sspi_flask_app.models.database import (
    sspi_raw_api_data,
    sspi_clean_api_data,
    sspi_metadata
)
from flask_login import login_required, current_user
from sspi_flask_app.api.resources.utilities import (
    parse_json,
    score_indicator,
    goalpost
)
from sspi_flask_app.api.datasource.who import (
    collect_who_data,
    clean_who_data
)
from sspi_flask_app.api.datasource.unsdg import (
    collect_sdg_indicator_data,
)

# # PHYSPC for Correlation Analysis with UHC
# @collect_bp.route("/PHYSPC", methods=['GET'])
# @login_required
# def physpc():
#     def collect_iterator(**kwargs):
#         yield from collect_who_data("UHC_INDEX_REPORTED", "PHYSPC", **kwargs)
#     return Response(collect_iterator(Username=current_user.username), mimetype='text/event-stream')


# @collect_bp.route("/PHYSPC", methods=['GET'])
# @login_required
# def physpc():
#     def collect_iterator(**kwargs):
#         yield from collect_who_data("HWF_0001", "PHYSPC", **kwargs)
#         yield from collect_sdg_indicator_data("3.8.1", "PHYSPC", **kwargs)
#     return Response(collect_iterator(Username=current_user.username), mimetype='text/event-stream')


@compute_bp.route("/PHYSPC")
@login_required
def compute_physpc():
    app.logger.info("Running /api/v1/compute/PHYSPC")
    sspi_clean_api_data.delete_many({"IndicatorCode": "PHYSPC"})
    raw_data = sspi_raw_api_data.fetch_raw_data("PHYSPC")
    unit = "Doctors per 10000"
    description = (
        "Number of medical doctors (physicians), both generalists and "
        "specialists, expressed per 10,000 people."
    )
    cleaned = clean_who_data(raw_data, "PHYSPC", unit, description)
    lg, ug = sspi_metadata.get_goalposts("PHYSPC")
    scored_list, _ = score_indicator(
        cleaned, "PHYSPC", 
        score_function=lambda WHO_PHYSPC: goalpost(WHO_PHYSPC, lg, ug),
        unit="Rate"
    )
    sspi_clean_api_data.insert_many(scored_list)
    return parse_json(scored_list)
