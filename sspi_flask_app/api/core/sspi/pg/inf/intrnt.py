from sspi_flask_app.api.core.sspi import compute_bp
from flask import current_app as app, Response
from sspi_flask_app.models.database import (
    sspi_raw_api_data,
    sspi_clean_api_data,
    sspi_incomplete_api_data
)
from flask_login import login_required, current_user
from sspi_flask_app.api.resources.utilities import (
    parse_json,
    score_indicator,
)
from sspi_flask_app.api.datasource.worldbank import (
    collect_world_bank_data,
    clean_wb_data
)
from sspi_flask_app.api.datasource.unsdg import collect_sdg_indicator_data, extract_sdg, filter_sdg


# @collect_bp.route("/INTRNT", methods=['GET'])
# @login_required
# def intrnt():
#     def collect_iterator(**kwargs):
#         yield from collect_world_bank_data("IT.NET.USER.ZS", "INTRNT", IntermediateCode="AVINTR", **kwargs)
#         yield from collect_sdg_indicator_data("17.6.1", "INTRNT", IntermediateCode="QUINTR", **kwargs)
#     return Response(collect_iterator(Username=current_user.username), mimetype='text/event-stream')


@compute_bp.route("/INTRNT", methods=['GET'])
@login_required
def compute_intrnt():
    app.logger.info("Running /api/v1/compute/INTRNT")
    sspi_clean_api_data.delete_many({"IndicatorCode": "INTRNT"})
    # AVINTR (WorldBank)
    wb_raw = sspi_raw_api_data.fetch_raw_data(
        "INTRNT", IntermediateCode="AVINTR"
    )
    clean_avintr = clean_wb_data(wb_raw, "INTRNT", unit="Percent")
    # QUINTR (SDG)
    sdg_raw = sspi_raw_api_data.fetch_raw_data(
        "INTRNT", IntermediateCode="QUINTR"
    )
    extracted_quintr = extract_sdg(sdg_raw)
    idcode_map = {"IT_NET_BBND": "QUINTR"}
    filtered_quintr = filter_sdg(
        extracted_quintr, idcode_map,
        type_of_speed="10MBPS"
    )
    for obs in filtered_quintr:
        obs["IntermediateCode"] = "QUINTR"
    clean_list, incomplete_list = score_indicator(
        clean_avintr + filtered_quintr, "INTRNT",
        score_function=lambda AVINTR, QUINTR: (AVINTR + QUINTR) / 2,
        unit="Index"
    )
    sspi_clean_api_data.insert_many(clean_list)
    sspi_incomplete_api_data.insert_many(incomplete_list)
    return parse_json(clean_list)


