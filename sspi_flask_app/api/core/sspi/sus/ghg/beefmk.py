from flask import current_app as app
from flask_login import login_required
from sspi_flask_app.api.core.sspi import compute_bp, impute_bp
from sspi_flask_app.models.database import (
    sspi_clean_api_data,
    sspi_indicator_data,
    sspi_incomplete_indicator_data,
    sspi_imputed_data,
    sspi_metadata)

from sspi_flask_app.auth.decorators import admin_required
from sspi_flask_app.api.resources.utilities import (
    goalpost,
    parse_json,
    score_indicator,
    extrapolate_forward,
    extrapolate_backward,
    impute_reference_class_average
)


# @collect_bp.route("/BEEFMK", methods=["POST"])
# @admin_required
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
@admin_required
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


@impute_bp.route("/BEEFMK", methods=["POST"])
@admin_required
def impute_beefmk():
    mongo_query = {"IndicatorCode": "BEEFMK"}
    sspi_imputed_data.delete_many(mongo_query)
    
    # Get complete indicator data
    clean_list = sspi_indicator_data.find(mongo_query)
    
    # Extrapolate indicator scores backward to 2000 and forward to 2023
    imputed_backward = extrapolate_backward(
        clean_list, 2000, series_id=["CountryCode", "IndicatorCode"], impute_only=True
    )
    imputed_forward = extrapolate_forward(
        clean_list, 2023, series_id=["CountryCode", "IndicatorCode"], impute_only=True
    )
    imputed_beefmk = imputed_backward + imputed_forward
    
    # Handle countries with no data using reference class average
    # From coverage report, SGP has no observations
    countries_no_data = ["SGP"]
    ref_data = [d for d in clean_list if d["CountryCode"] not in countries_no_data]
    
    for country in countries_no_data:
        if ref_data:
            country_imputed = impute_reference_class_average(
                country, 2000, 2023, "Indicator", "BEEFMK", ref_data
            )
            imputed_beefmk.extend(country_imputed)
    
    # Insert into database
    if imputed_beefmk:
        sspi_imputed_data.insert_many(imputed_beefmk)
    
    return parse_json(imputed_beefmk)
