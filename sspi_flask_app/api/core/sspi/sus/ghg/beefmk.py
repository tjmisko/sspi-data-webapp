from flask import current_app as app
from flask_login import login_required
from sspi_flask_app.api.core.sspi import compute_bp
from sspi_flask_app.models.database import (
    sspi_clean_api_data,
    sspi_indicator_data,
    sspi_incomplete_indicator_data,
    sspi_metadata
)
from sspi_flask_app.api.resources.utilities import (
    goalpost,
    parse_json,
    score_indicator,
)


# @collect_bp.route("/BEEFMK", methods=["POST"])
# @login_required
# def beefmk():
#     def collect_iterator(**kwargs):
#         # yield from collect_unfao_data("2312%2C2313", "1806%2C1746", "QCL", "BEEFMK", **kwargs)
#         # yield from collect_unfao_data("C2510%2C2111%2C2413", "1806%2C1746", "QCL", "BEEFMK", **kwargs)
#         # yield from collect_wb_data("SP.POP.TOTL", "BEEFMK", IntermediateCode="POPULN", **kwargs)
#         yield from collectUNFAOData(
#             "2910%2C645%2C2610%2C2510%2C511", "2731%2C2501", "FBS", "BEEFMK", **kwargs
#         )
#     return Response(
#         collect_iterator(Username=current_user.username), mimetype="text/event-stream"
#     )


@compute_bp.route("/BEEFMK", methods=["POST"])
@login_required
def compute_beefmk():
    app.logger.info("Running /api/v1/compute/BEEFMK")
    sspi_indicator_data.delete_many({"IndicatorCode": "BEEFMK"})
    sspi_incomplete_indicator_data.delete_many({"IndicatorCode": "BEEFMK"})
    
    # Fetch clean datasets
    bfprod_clean = sspi_clean_api_data.find({"DatasetCode": "UNFAO_BFPROD"})
    bfcons_clean = sspi_clean_api_data.find({"DatasetCode": "UNFAO_BFCONS"})
    combined_list = bfprod_clean + bfcons_clean
    
    prod_lg, prod_ug = 50, 0
    cons_lg, cons_ug = 50, 0
    populn_clean = sspi_clean_api_data.find({"DatasetCode": "WB_POPULN"})
    
    # Add population data to combined list
    combined_list.extend(populn_clean)
    
    def score_beefmk(UNFAO_BFPROD, UNFAO_BFCONS, WB_POPULN):
        prod_per_cap = UNFAO_BFPROD / WB_POPULN
        score_prod = goalpost(prod_per_cap, prod_lg, prod_ug)
        score_cons = goalpost(UNFAO_BFCONS, cons_lg, cons_ug)
        return (score_prod + score_cons) / 2
    
    clean_list, incomplete_list = score_indicator(
        combined_list, "BEEFMK", 
        score_function=score_beefmk, 
        unit="Index"
    )
    sspi_indicator_data.insert_many(clean_list)
    sspi_incomplete_indicator_data.insert_many(incomplete_list)
    return parse_json(clean_list)
