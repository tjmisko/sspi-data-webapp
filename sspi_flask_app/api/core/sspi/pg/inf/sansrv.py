from sspi_flask_app.api.core.sspi import compute_bp, impute_bp
from flask import current_app as app, Response
from sspi_flask_app.models.database import (
    sspi_clean_api_data,
    sspi_indicator_data,
    sspi_metadata,
    sspi_imputed_data
)
from sspi_flask_app.api.resources.utilities import (
    parse_json,
    score_indicator,
    goalpost,
    extrapolate_backward,
    extrapolate_forward
)
from flask_login import login_required, current_user


@compute_bp.route("/SANSRV", methods=["POST"])
@login_required
def compute_sansrv():
    app.logger.info("Running /api/v1/compute/SANSRV")
    sspi_indicator_data.delete_many({"IndicatorCode": "SANSRV"})
    sansrv_clean = sspi_clean_api_data.find({"DatasetCode": "WB_SANSRV"})
    lg, ug = sspi_metadata.get_goalposts("SANSRV")
    scored_list, _ = score_indicator(
        sansrv_clean, "SANSRV",
        score_function=lambda WB_SANSRV: goalpost(WB_SANSRV, lg, ug),
        unit="Percent"
    )
    sspi_indicator_data.insert_many(scored_list)
    return parse_json(scored_list)

 my_country_imputations = [
        {"CountryCode": "ARE", "Year": 2024, "IndicatorCode": "SANSRV", "Value": 99.00},
        {"CountryCode": "ARG", "Year": 2024, "IndicatorCode": "SANSRV", "Value": 93.1},
        {"CountryCode": "AUS", "Year": 2024, "IndicatorCode": "SANSRV", "Value": 98.9},
        {"CountryCode": "CHN", "Year": 2024, "IndicatorCode": "SANSRV", "Value": 91.20},
        {"CountryCode": "EGY", "Year": 2024, "IndicatorCode": "SANSRV", "Value": 79.00},
        {"CountryCode": "IND", "Year": 2024, "IndicatorCode": "SANSRV", "Value": 76.00},
        {"CountryCode": "KEN", "Year": 2024, "IndicatorCode": "SANSRV", "Value": 50.30},
        {"CountryCode": "SAU", "Year": 2024, "IndicatorCode": "SANSRV", "Value": 97.70},
        {"CountryCode": "THA", "Year": 2024, "IndicatorCode": "SANSRV", "Value": 94.40},
        {"CountryCode": "TUR", "Year": 2024, "IndicatorCode": "SANSRV", "Value": 91.20},
        {"CountryCode": "URU", "Year": 2024, "IndicatorCode": "SANSRV", "Value": 93.5}
    ]


@impute_bp.route("/SANSRV", methods=["POST"])
@login_required
def impute_sansrv():
    app.logger.info("Running /api/v1/impute/SANSRV")
    sspi_imputed_data.delete_many({"IndicatorCode": "SANSRV"})
    sansrv_clean = sspi_clean_api_data.find({"DatasetCode": "WB_SANSRV"})
    forward_imputations = extrapolate_forward(sansrv_clean, 2023, series_id=["CountryCode", "DatasetCode"], impute_only=True)
    backward_imputations = extrapolate_backward(sansrv_clean, 2000, series_id=["CountryCode", "DatasetCode"], impute_only=True)
    lg, ug = sspi_metadata.get_goalposts("SANSRV")
    scored_list, _ = score_indicator(
        forward_imputations + backward_imputations + my_country_imputations, "SANSRV",
        score_function=lambda WB_SANSRV: goalpost(WB_SANSRV, lg, ug),
        unit="Percent"
    )
    sspi_imputed_data.insert_many(scored_list)
    return parse_json(scored_list)
