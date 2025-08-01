from flask import Response
from flask import current_app as app
from flask_login import current_user, login_required

from sspi_flask_app.api.core.sspi import compute_bp, impute_bp
from sspi_flask_app.api.resources.utilities import (
    extrapolate_backward,
    extrapolate_forward,
    interpolate_linear,
    parse_json,
    score_indicator,
    regression_imputation,
    goalpost
)
from sspi_flask_app.models.database import (
    sspi_clean_api_data,
    sspi_indicator_data,
    sspi_imputed_data,
    sspi_metadata
)


# @collect_bp.route("/GINIPT", methods=["GET"])
# @login_required
# def ginipt():
#     def collect_iterator(**kwargs):
#         yield from collect_wb_data("SI.POV.GINI", "GINIPT", **kwargs)
#     return Response(
#         collect_iterator(Username=current_user.username), mimetype="text/event-stream"
#     )


@compute_bp.route("/GINIPT")
@login_required
def compute_ginipt():
    app.logger.info("Running /api/v1/compute/GINIPT")
    sspi_indicator_data.delete_many({"IndicatorCode": "GINIPT"})
    # Fetch clean dataset
    clean_ginipt = sspi_clean_api_data.find({"DatasetCode": "WB_GINIPT"})
    lg, ug = sspi_metadata.get_goalposts("GINIPT")
    scored_list, _ = score_indicator(
        clean_ginipt, "GINIPT",
        score_function=lambda WB_GINIPT: goalpost(WB_GINIPT, lg, ug),
        unit="Coefficient"
    )
    sspi_indicator_data.insert_many(scored_list)
    return parse_json(scored_list)


@impute_bp.route("/GINIPT", methods=["POST"])
@login_required
def impute_ginipt():
    app.logger.info("Running /api/v1/impute/GINIPT")
    sspi_imputed_data.delete_many({"IndicatorCode": "GINIPT"})
    clean_ginipt = sspi_clean_api_data.find({"IndicatorCode": "GINIPT"})
    forward = extrapolate_forward(clean_ginipt, 2023, impute_only=True)
    backward = extrapolate_backward(clean_ginipt, 2000, impute_only=True)
    interpolated = interpolate_linear(clean_ginipt, impute_only=True)
    imputed_ginipt = forward + backward + interpolated
    country_codes = {obs["CountryCode"] for obs in imputed_ginipt}
    print(list(country_codes))
    # Impute missing GINIPT by predicting them with ISHRAT data
    ishrat_data = sspi_clean_api_data.find(
        {"IndicatorCode": "ISHRAT"}
    )
    prediction_input = sspi_clean_api_data.find(
        {"IndicatorCode": "ISHRAT", "CountryCode": {"$nin": list(country_codes)}}
    )
    unit = clean_ginipt[0]["Unit"]
    imputation_details = (
        "ISHRAT and GINIPT both describe income inequality. Both are derived "
        "from the income distribution of a country. They are somewhat "
        "correlated: enough so that ISHRAT is a reasonable predictor of GINIPT "
        "in the absence of GINIPT data, but not so much that we feel we should "
        "only use ISHRAT data to measure income inequality. We use a simple "
        "linear regression model to predict GINIPT from ISHRAT data."
    )
    lg, ug = sspi_metadata.get_goalposts("GINIPT")
    for obs in ishrat_data:
        obs["FeatureCode"] = "ISHRAT"
    for obs in prediction_input:
        obs["FeatureCode"] = "ISHRAT"
    predicted = regression_imputation(
        ishrat_data,
        clean_ginipt,
        prediction_input,
        "GINIPT",
        unit,
        "GINIPT ~ ISHRAT + y_0 + e",
        imputation_details,
        lg=lg,
        ug=ug,
    )
    sspi_imputed_data.insert_many(imputed_ginipt + predicted)
    return parse_json(imputed_ginipt + predicted)
