from sspi_flask_app.api.core.sspi import compute_bp, impute_bp
from flask import current_app as app
from flask_login import login_required
from sspi_flask_app.models.database import (
    sspi_clean_api_data,
    sspi_indicator_data,
    sspi_incomplete_indicator_data,
    sspi_imputed_data,
    sspi_metadata
)
from sspi_flask_app.api.resources.utilities import (
    parse_json,
    goalpost,
    score_indicator,
    extrapolate_forward,
    impute_reference_class_average
)


@compute_bp.route("/CARBON", methods=['POST'])
@login_required
def compute_carbon():
    lg, ug = sspi_metadata.get_goalposts("CARBON")
    def score_carbon(UNFAO_CRBNLV, UNFAO_CRBNAV) -> float: 
        if UNFAO_CRBNAV == 0:
            return 0
        return goalpost((UNFAO_CRBNLV - UNFAO_CRBNAV) / UNFAO_CRBNAV * 100, lg, ug)

    sspi_indicator_data.delete_many({"IndicatorCode": "CARBON"})
    sspi_incomplete_indicator_data.delete_many({"IndicatorCode": "CARBON"})
    crbnlv_clean = sspi_clean_api_data.find({"DatasetCode": "UNFAO_CRBNLV"})
    crbnav_clean = sspi_clean_api_data.find({"DatasetCode": "UNFAO_CRBNAV"})
    combined_list = crbnlv_clean + crbnav_clean
    filtered_combined = []
    for obs in combined_list:
        if obs.get("DatasetCode") == "UNFAO_CRBNLV" and obs.get("Year", 0) >= 2000:
            filtered_combined.append(obs)
        elif obs.get("DatasetCode") == "UNFAO_CRBNAV":
            filtered_combined.append(obs)
    
    clean_list, incomplete_list = score_indicator(
        filtered_combined,
        "CARBON",
        score_function=score_carbon,
        unit="Index",
    )
    sspi_indicator_data.insert_many(clean_list)
    sspi_incomplete_indicator_data.insert_many(incomplete_list)
    return parse_json(clean_list)


@impute_bp.route("/CARBON", methods=["POST"])
@login_required
def impute_carbon():
    lg, ug = sspi_metadata.get_goalposts("CARBON")
    def score_carbon(UNFAO_CRBNLV, UNFAO_CRBNAV) -> float: 
        if UNFAO_CRBNAV == 0:
            return 0
        return goalpost((UNFAO_CRBNLV - UNFAO_CRBNAV) / UNFAO_CRBNAV * 100, lg, ug)

    sspi_imputed_data.delete_many({"IndicatorCode": "CARBON"})
    carbon_lv = sspi_clean_api_data.find({"DatasetCode": "UNFAO_CRBNLV"})
    carbon_av = sspi_clean_api_data.find({"DatasetCode": "UNFAO_CRBNAV"})
    kwt_carbon_lv = impute_reference_class_average("KWT", 2000, 2023, "Dataset", "UNFAO_CRBNLV", carbon_lv)
    kwt_carbon_av = impute_reference_class_average("KWT", 2000, 2023, "Dataset", "UNFAO_CRBNAV", carbon_av)
    bel_carbon_lv = impute_reference_class_average("BEL", 2000, 2023, "Dataset", "UNFAO_CRBNLV", carbon_lv)
    bel_carbon_av = impute_reference_class_average("BEL", 2000, 2023, "Dataset", "UNFAO_CRBNAV", carbon_av)
    lux_carbon_lv = impute_reference_class_average("LUX", 2000, 2023, "Dataset", "UNFAO_CRBNLV", carbon_lv)
    lux_carbon_av = impute_reference_class_average("LUX", 2000, 2023, "Dataset", "UNFAO_CRBNAV", carbon_av)
    imputed_carbon, _ = score_indicator(
        kwt_carbon_lv + kwt_carbon_av + bel_carbon_lv + bel_carbon_av + lux_carbon_lv + lux_carbon_av,
        "CARBON",
        score_function=score_carbon,
        unit="Index",
    )
    sspi_imputed_data.insert_many(imputed_carbon)
    return parse_json(imputed_carbon)

