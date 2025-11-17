from sspi_flask_app.api.core.sspi import compute_bp, impute_bp
from flask import current_app as app, Response
from sspi_flask_app.models.database import (
    sspi_clean_api_data,
    sspi_indicator_data,
    sspi_imputed_data,
    sspi_metadata
)
from flask_login import login_required, current_user
from sspi_flask_app.api.resources.utilities import (
    parse_json,
    score_indicator,
    goalpost,
    extrapolate_backward,
    extrapolate_forward,
    interpolate_linear,
    regression_imputation)

from sspi_flask_app.auth.decorators import admin_required


@compute_bp.route("/CSTUNT", methods=['POST'])
@admin_required
def compute_cstunt():
    """
    UNSDG Reports Two Different Kinds of Series:
    1. NUTRITION_ANT_HAZ_NE2 - Survey-based estimates of child stunting
    2. NUTSTUNTINGPREV       - Model-based estimates of child stunting

    Modeled data has better coverage:
    NUTRITION_ANT_HAZ_NE2 - 999 observations
    NUTSTUNTINGPREV       - 3634 observations
    """
    app.logger.info("Running /api/v1/compute/CSTUNT")
    sspi_indicator_data.delete_many({"IndicatorCode": "CSTUNT"})
    cstunt_clean = sspi_clean_api_data.find({"DatasetCode": "UNSDG_CSTUNT"})
    lg, ug = sspi_metadata.get_goalposts("CSTUNT")
    scored_list, _ = score_indicator(
        cstunt_clean, "CSTUNT",
        score_function=lambda UNSDG_CSTUNT: goalpost(UNSDG_CSTUNT, lg, ug),
        unit = "%"
    )
    sspi_indicator_data.insert_many(scored_list)
    return parse_json(scored_list)


@impute_bp.route("/CSTUNT", methods=['POST'])
@admin_required
def impute_cstunt():
    sspi_imputed_data.delete_many({"IndicatorCode": "CSTUNT"})
    clean_cstunt = sspi_indicator_data.find({"IndicatorCode": "CSTUNT"})
    cstunt_dataset = sspi_clean_api_data.find({"DatasetCode": "UNSDG_CSTUNT"})
    forward = extrapolate_forward(cstunt_dataset, 2023, ["CountryCode", "DatasetCode"], impute_only=True)
    backward = extrapolate_backward(cstunt_dataset, 2000, ["CountryCode", "DatasetCode"], impute_only=True)
    interpolated = interpolate_linear(cstunt_dataset, ["CountryCode", "DatasetCode"], impute_only=True)
    lg, ug = sspi_metadata.get_goalposts("CSTUNT")
    imputed_cstunt, _ = score_indicator(
        forward + backward + interpolated, "CSTUNT",
        score_function=lambda UNSDG_CSTUNT: goalpost(UNSDG_CSTUNT, lg, ug),
        unit="Coefficient"
    )
    imputed_codes = {obs["CountryCode"] for obs in imputed_cstunt}
    clean_codes = {obs["CountryCode"] for obs in clean_cstunt}
    # Impute missing CSTUNT by predicting them with WB_GDP_PERCAP_CURPRICE_USD data
    gdp_data = sspi_clean_api_data.find(
        {"DatasetCode": "WB_GDP_PERCAP_CURPRICE_USD"}
    )
    prediction_input = sspi_clean_api_data.find(
        {"DatasetCode": "WB_GDP_PERCAP_CURPRICE_USD", "CountryCode": {"$nin": list(imputed_codes) + list(clean_codes)}}
    )
    unit = clean_cstunt[0]["Unit"]
    imputation_details = (
        "WB_GDP_PERCAP_CURPRICE_USD is a predictor of the prevalence of Child Stunting"
    )
    lg, ug = sspi_metadata.get_goalposts("CSTUNT")
    for obs in gdp_data:
        obs["FeatureCode"] = "WB_GDP_PERCAP_CURPRICE_USD"
        obs["Score"] = goalpost(obs["Value"], 0, 100000)
    for obs in prediction_input:
        obs["FeatureCode"] = "WB_GDP_PERCAP_CURPRICE_USD"
        obs["Score"] = goalpost(obs["Value"], 0, 100000)
    predicted_cstunt = regression_imputation(
        gdp_data,
        clean_cstunt,
        prediction_input,
        "CSTUNT",
        unit,
        "CSTUNT ~ WB_GDP_PERCAP_CURPRICE_USD + y_0 + e",
        imputation_details,
        lg=lg,
        ug=ug,
    )
    sspi_imputed_data.insert_many(imputed_cstunt + predicted_cstunt)
    return parse_json(imputed_cstunt + predicted_cstunt)
