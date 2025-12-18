import logging
from flask import Response, current_app as app
from flask_login import login_required, current_user
from sspi_flask_app.api.core.sspi import compute_bp, impute_bp
from sspi_flask_app.api.resources.utilities import (
    parse_json,
    score_indicator,
    goalpost,
    extrapolate_forward,
    extrapolate_backward,
    interpolate_linear,
    impute_reference_class_average,
    filter_imputations)

from sspi_flask_app.auth.decorators import admin_required
from sspi_flask_app.models.database import (
    sspi_raw_api_data,
    sspi_clean_api_data,
    sspi_metadata,
    sspi_indicator_data,
    sspi_imputed_data
)

log = logging.getLogger(__name__)

@compute_bp.route("/STCONS", methods=['POST'])
@admin_required
def compute_stcons():
    lg, ug = sspi_metadata.get_goalposts("STCONS")
    def stcons_score_function(WID_CARBON_TOT_P90P100, WID_CARBON_TOT_P0P100, FPI_ECOFPT_PER_CAP):
        return goalpost(FPI_ECOFPT_PER_CAP*WID_CARBON_TOT_P90P100 / WID_CARBON_TOT_P0P100, lg, ug)
    sspi_indicator_data.delete_many({"IndicatorCode": "STCONS"})
    dataset_list = sspi_clean_api_data.find(
        {"DatasetCode": {"$in": [
            "WID_CARBON_TOT_P0P100", "WID_CARBON_TOT_P90P100", "FPI_ECOFPT_PER_CAP"]
    }})
    scored_data, _ = score_indicator(
        dataset_list, "STCONS",
        score_function=stcons_score_function,
        unit="Index"
    )
    sspi_indicator_data.insert_many(scored_data)
    return parse_json(scored_data)


@impute_bp.route("/STCONS", methods=["POST"])
@admin_required
def impute_stcons():
    lg, ug = sspi_metadata.get_goalposts("STCONS")
    def stcons_score_function(WID_CARBON_TOT_P90P100, WID_CARBON_TOT_P0P100, FPI_ECOFPT_PER_CAP):
        return goalpost(FPI_ECOFPT_PER_CAP * WID_CARBON_TOT_P90P100 / WID_CARBON_TOT_P0P100, lg, ug)

    mongo_query = {"IndicatorCode": "STCONS"}
    sspi_imputed_data.delete_many(mongo_query)

    sspi_67 = sspi_metadata.country_group("SSPI67")
    reference_class_averages = []

    # Extract and impute WID_CARBON_TOT_P0P100 data
    wid_p0p100 = sspi_clean_api_data.find({"DatasetCode": "WID_CARBON_TOT_P0P100"})
    missing_p0p100 = set(sspi_67) - set([d.get("CountryCode", "") for d in wid_p0p100])
    for country in missing_p0p100:
        reference_class_averages.extend(
            impute_reference_class_average(country, 2000, 2023, "Dataset", "WID_CARBON_TOT_P0P100", wid_p0p100)
        )
    imputed_p0p100 = extrapolate_backward(
        wid_p0p100, 2000, series_id=["CountryCode", "DatasetCode"]
    )
    imputed_p0p100 = extrapolate_forward(
        imputed_p0p100, 2023, series_id=["CountryCode", "DatasetCode"]
    )
    imputed_p0p100 = interpolate_linear(
        imputed_p0p100, series_id=["CountryCode", "DatasetCode"]
    )

    # Extract and impute WID_CARBON_TOT_P90P100 data
    wid_p90p100 = sspi_clean_api_data.find({"DatasetCode": "WID_CARBON_TOT_P90P100"})
    missing_p90p100 = set(sspi_67) - set([d.get("CountryCode", "") for d in wid_p90p100])
    for country in missing_p90p100:
        reference_class_averages.extend(
            impute_reference_class_average(country, 2000, 2023, "Dataset", "WID_CARBON_TOT_P90P100", wid_p90p100)
        )
    imputed_p90p100 = extrapolate_backward(
        wid_p90p100, 2000, series_id=["CountryCode", "DatasetCode"]
    )
    imputed_p90p100 = extrapolate_forward(
        imputed_p90p100, 2023, series_id=["CountryCode", "DatasetCode"]
    )
    imputed_p90p100 = interpolate_linear(
        imputed_p90p100, series_id=["CountryCode", "DatasetCode"]
    )

    # Extract and impute FPI_ECOFPT_PER_CAP data
    fpi_ecofpt = sspi_clean_api_data.find({"DatasetCode": "FPI_ECOFPT_PER_CAP"})
    missing_fpi = set(sspi_67) - set([d.get("CountryCode", "") for d in fpi_ecofpt])
    for country in missing_fpi:
        reference_class_averages.extend(
            impute_reference_class_average(country, 2000, 2023, "Dataset", "FPI_ECOFPT_PER_CAP", fpi_ecofpt)
        )
    imputed_fpi = extrapolate_backward(
        fpi_ecofpt, 2000, series_id=["CountryCode", "DatasetCode"]
    )
    imputed_fpi = extrapolate_forward(
        imputed_fpi, 2023, series_id=["CountryCode", "DatasetCode"]
    )
    imputed_fpi = interpolate_linear(
        imputed_fpi, series_id=["CountryCode", "DatasetCode"]
    )

    # Combine all imputed datasets and score the indicator
    all_imputed_datasets = imputed_p0p100 + imputed_p90p100 + imputed_fpi + reference_class_averages
    overall_stcons, _ = score_indicator(
        all_imputed_datasets, "STCONS",
        score_function=stcons_score_function,
        unit="Index"
    )

    # Filter to only get imputations
    imputed_stcons = filter_imputations(overall_stcons)

    # Insert into database
    if imputed_stcons:
        sspi_imputed_data.insert_many(imputed_stcons)

    return parse_json(imputed_stcons)