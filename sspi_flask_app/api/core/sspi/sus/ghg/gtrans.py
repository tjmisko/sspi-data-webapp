from sspi_flask_app.api.core.sspi import compute_bp, impute_bp
from flask_login import login_required
from flask import current_app as app
from sspi_flask_app.models.database import (
    sspi_clean_api_data,
    sspi_indicator_data,
    sspi_incomplete_indicator_data,
    sspi_metadata,
    sspi_imputed_data
)
from sspi_flask_app.api.resources.utilities import (
    goalpost,
    parse_json,
    score_indicator,
    slice_dataset,
    extrapolate_forward,
    filter_imputations
)


@compute_bp.route("/GTRANS", methods=["POST"])
@login_required
def compute_gtrans():
    app.logger.info("Running /api/v1/compute/GTRANS")
    sspi_indicator_data.delete_many({"IndicatorCode": "GTRANS"})
    sspi_incomplete_indicator_data.delete_many({"IndicatorCode": "GTRANS"})
    tco2em_clean = sspi_clean_api_data.find({"DatasetCode": "IEA_TCO2EM"})
    populn_clean = sspi_clean_api_data.find({"DatasetCode": "WB_POPULN"})
    combined_list = tco2em_clean + populn_clean
    lg, ug = sspi_metadata.get_goalposts("GTRANS")
    clean_list, incomplete_list = score_indicator(
        combined_list,
        "GTRANS",
        score_function=lambda IEA_TCO2EM, WB_POPULN: goalpost(IEA_TCO2EM / WB_POPULN, lg, ug),
        unit="Index",
    )
    sspi_indicator_data.insert_many(clean_list)
    sspi_incomplete_indicator_data.insert_many(incomplete_list)
    return parse_json(clean_list)

@impute_bp.route("/GTRANS", methods=["POST"])
@login_required
def impute_gtrans():
    mongo_query = {"IndicatorCode": "GTRANS", "Year": {"$gte": 2000, "$lte": 2023}}
    sspi_imputed_data.delete_many(mongo_query)
    clean_list = sspi_indicator_data.find(mongo_query)
    incomplete_list = sspi_incomplete_indicator_data.find(mongo_query)
    clean_wb_populn = slice_dataset(clean_list, "WB_POPULN") + \
        slice_dataset(incomplete_list, "WB_POPULN")
    clean_iea_tco2em = slice_dataset(clean_list, "IEA_TCO2EM") + \
        slice_dataset(incomplete_list, "IEA_TCO2EM")
    imputed_iea_tco2em = extrapolate_forward(
        clean_iea_tco2em, 2023, series_id=["CountryCode", "DatasetCode"]
    )
    lg, ug = sspi_metadata.get_goalposts("GTRANS")
    overall_gtrans, missing_imputations = score_indicator(
        imputed_iea_tco2em + clean_wb_populn, "GTRANS",
        score_function=lambda IEA_TCO2EM, WB_POPULN: goalpost(IEA_TCO2EM / WB_POPULN, lg, ug),
        unit="Index",
    )
    imputed_gtrans = filter_imputations(overall_gtrans)
    sspi_imputed_data.insert_many(imputed_gtrans)
    return parse_json(imputed_gtrans)

