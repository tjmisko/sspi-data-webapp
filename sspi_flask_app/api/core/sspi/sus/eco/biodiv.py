import logging
from flask import Response
from flask import current_app as app
from flask_login import current_user, login_required
from sspi_flask_app.api.core.sspi import compute_bp, impute_bp
from sspi_flask_app.api.resources.utilities import parse_json, score_indicator, goalpost
from sspi_flask_app.models.database import (
    sspi_clean_api_data,
    sspi_indicator_data,
    sspi_incomplete_indicator_data,
    sspi_imputed_data,
    sspi_metadata
)
from sspi_flask_app.auth.decorators import admin_required
from sspi_flask_app.api.resources.utilities import (
    extrapolate_backward,
    extrapolate_forward,
    interpolate_linear,
    slice_dataset,
    filter_imputations,
    impute_reference_class_average
)
    

log = logging.getLogger(__name__)


@compute_bp.route("/BIODIV", methods=["POST"])
@admin_required
def compute_biodiv():
    def score_biodiv(UNSDG_MARINE, UNSDG_TERRST, UNSDG_FRSHWT):
        frshwt = goalpost(UNSDG_FRSHWT, 0, 100)
        terrst = goalpost(UNSDG_TERRST, 0, 100)
        marine = goalpost(UNSDG_MARINE, 0, 100)
        return (frshwt + terrst + marine) / 3

    sspi_indicator_data.delete_many({"IndicatorCode": "BIODIV"})
    sspi_incomplete_indicator_data.delete_many({"IndicatorCode": "BIODIV"})
    dataset_list = sspi_clean_api_data.find(
        {"DatasetCode": {"$in": ["UNSDG_MARINE", "UNSDG_TERRST", "UNSDG_FRSHWT"]}}
    )
    clean_list, incomplete_list = score_indicator(
        dataset_list,
        "BIODIV",
        score_function=score_biodiv,
        unit="Index",
    )
    sspi_indicator_data.insert_many(clean_list)
    sspi_incomplete_indicator_data.insert_many(incomplete_list)
    return parse_json(clean_list)


@impute_bp.route("/BIODIV", methods=["POST"])
@admin_required
def impute_biodiv():
    def score_biodiv(UNSDG_MARINE, UNSDG_TERRST, UNSDG_FRSHWT):
        return (UNSDG_MARINE + UNSDG_TERRST + UNSDG_FRSHWT) / 3 / 100
    mongo_query = {"IndicatorCode": "BIODIV"}
    sspi_imputed_data.delete_many(mongo_query)
    # Extract and impute UNSDG_MARINE data
    sspi_67 = sspi_metadata.country_group("SSPI67")
    unsdg_marine = sspi_clean_api_data.find(
        {"DatasetCode": {"$in": ["UNSDG_MARINE"]}}
    )
    missing_marine = set(sspi_67) - set([m.get("CountryCode", "") for m in unsdg_marine])
    reference_class_averages = []
    for country in missing_marine:
        reference_class_averages.extend(
            impute_reference_class_average(country, 2000, 2023, "Dataset", "UNSDG_MARINE", unsdg_marine)
        )
    imputed_marine = extrapolate_backward(
        unsdg_marine, 2000, series_id=["CountryCode", "DatasetCode"]
    )
    imputed_marine = extrapolate_forward(
        imputed_marine, 2023, series_id=["CountryCode", "DatasetCode"]
    )
    imputed_marine = interpolate_linear(
        imputed_marine, series_id=["CountryCode", "DatasetCode"]
    )
    # Extract and impute UNSDG_TERRST data  
    unsdg_terrst = sspi_clean_api_data.find(
        {"DatasetCode": {"$in": ["UNSDG_TERRST"]}}
    )
    missing_terrst = set(sspi_67) - set([m.get("CountryCode", "") for m in unsdg_terrst])
    for country in missing_terrst:
        reference_class_averages.extend(
            impute_reference_class_average(country, 2000, 2023, "Dataset", "UNSDG_TERRST", unsdg_terrst)
        )
    imputed_terrst = extrapolate_backward(
        unsdg_terrst, 2000, series_id=["CountryCode", "DatasetCode"]
    )
    imputed_terrst = extrapolate_forward(
        imputed_terrst, 2023, series_id=["CountryCode", "DatasetCode"]
    )
    imputed_terrst = interpolate_linear(
        imputed_terrst, series_id=["CountryCode", "DatasetCode"]
    )
    # Extract and impute UNSDG_FRSHWT data
    unsdg_frshwt = sspi_clean_api_data.find(
        {"DatasetCode": {"$in": ["UNSDG_FRSHWT"]}}
    )
    missing_frshwt = set(sspi_67) - set([m.get("CountryCode", "") for m in unsdg_frshwt])
    for country in missing_frshwt:
        reference_class_averages.extend(
            impute_reference_class_average(country, 2000, 2023, "Dataset", "UNSDG_FRSHWT", unsdg_frshwt)
        )
    imputed_frshwt = extrapolate_backward(
        unsdg_frshwt, 2000, series_id=["CountryCode", "DatasetCode"]
    )
    imputed_frshwt = extrapolate_forward(
        imputed_frshwt, 2023, series_id=["CountryCode", "DatasetCode"]
    )
    imputed_frshwt = interpolate_linear(
        imputed_frshwt, series_id=["CountryCode", "DatasetCode"]
    )
    overall_biodiv, missing_imputations = score_indicator(
        imputed_terrst + imputed_marine + imputed_frshwt + reference_class_averages, "BIODIV",
        score_function=score_biodiv,
        unit="Index",
    )
    # All these should be imputed already, but filter just to be safe
    imputed_biodiv = filter_imputations(overall_biodiv)
    # Insert into database
    if imputed_biodiv:
        sspi_imputed_data.insert_many(imputed_biodiv)
    return parse_json(imputed_biodiv)
