import logging
from flask import Response
from flask import current_app as app
from flask_login import current_user, login_required
from sspi_flask_app.api.core.sspi import compute_bp, impute_bp
from sspi_flask_app.api.datasource.unsdg import (
    collect_sdg_indicator_data,
    extract_sdg,
    filter_sdg,
)
from sspi_flask_app.api.resources.utilities import parse_json, score_indicator
from sspi_flask_app.models.database import (
    sspi_clean_api_data,
    sspi_indicator_data,
    sspi_incomplete_indicator_data,
    sspi_imputed_data,
)

log = logging.getLogger(__name__)


@compute_bp.route("/BIODIV", methods=["POST"])
@login_required
def compute_biodiv():
    def score_biodiv(UNSDG_MARINE, UNSDG_TERRST, UNSDG_FRSHWT):
        return (UNSDG_MARINE + UNSDG_TERRST + UNSDG_FRSHWT) / 3 / 100

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
@login_required
def impute_biodiv():
    def score_biodiv(UNSDG_MARINE, UNSDG_TERRST, UNSDG_FRSHWT):
        return (UNSDG_MARINE + UNSDG_TERRST + UNSDG_FRSHWT) / 3 / 100
        
    from sspi_flask_app.api.resources.utilities import (
        extrapolate_backward,
        extrapolate_forward,
        interpolate_linear,
        slice_dataset,
        filter_imputations,
        impute_reference_class_average
    )
    
    mongo_query = {"IndicatorCode": "BIODIV"}
    sspi_imputed_data.delete_many(mongo_query)
    
    # Get complete and incomplete data
    clean_list = sspi_indicator_data.find(mongo_query)
    incomplete_list = sspi_incomplete_indicator_data.find(mongo_query)
    
    # Process each dataset separately
    # Extract and impute UNSDG_MARINE data
    clean_marine = slice_dataset(clean_list, "UNSDG_MARINE") + \
        slice_dataset(incomplete_list, "UNSDG_MARINE")
    imputed_marine = extrapolate_backward(
        clean_marine, 2000, series_id=["CountryCode", "DatasetCode"]
    )
    imputed_marine = extrapolate_forward(
        imputed_marine, 2023, series_id=["CountryCode", "DatasetCode"]
    )
    imputed_marine = interpolate_linear(
        imputed_marine, series_id=["CountryCode", "DatasetCode"]
    )
    
    # Extract and impute UNSDG_TERRST data  
    clean_terrst = slice_dataset(clean_list, "UNSDG_TERRST") + \
        slice_dataset(incomplete_list, "UNSDG_TERRST")
    imputed_terrst = extrapolate_backward(
        clean_terrst, 2000, series_id=["CountryCode", "DatasetCode"]
    )
    imputed_terrst = extrapolate_forward(
        imputed_terrst, 2023, series_id=["CountryCode", "DatasetCode"]
    )
    imputed_terrst = interpolate_linear(
        imputed_terrst, series_id=["CountryCode", "DatasetCode"]
    )
    
    # Extract and impute UNSDG_FRSHWT data
    clean_frshwt = slice_dataset(clean_list, "UNSDG_FRSHWT") + \
        slice_dataset(incomplete_list, "UNSDG_FRSHWT")
    imputed_frshwt = extrapolate_backward(
        clean_frshwt, 2000, series_id=["CountryCode", "DatasetCode"]
    )
    imputed_frshwt = extrapolate_forward(
        imputed_frshwt, 2023, series_id=["CountryCode", "DatasetCode"]
    )
    imputed_frshwt = interpolate_linear(
        imputed_frshwt, series_id=["CountryCode", "DatasetCode"]
    )
    
    # For countries with no data at all, impute reference class average
    # Countries with no observations: CHE, SVK, HUN, ETH, SGP, AUT, LUX, KWT, CZE
    countries_no_data = ["CHE", "SVK", "HUN", "ETH", "SGP", "AUT", "LUX", "KWT", "CZE"]
    
    # Get reference class averages for each dataset (only non-imputed data)
    marine_ref = [d for d in clean_marine if d["CountryCode"] not in countries_no_data and not d.get("Imputed", False)]
    terrst_ref = [d for d in clean_terrst if d["CountryCode"] not in countries_no_data and not d.get("Imputed", False)]
    frshwt_ref = [d for d in clean_frshwt if d["CountryCode"] not in countries_no_data and not d.get("Imputed", False)]
    
    # Impute missing countries using reference class averages
    imputed_countries = []
    for country in countries_no_data:
        if marine_ref:
            imputed_countries.extend(
                impute_reference_class_average(country, 2000, 2023, "Dataset", "UNSDG_MARINE", marine_ref)
            )
        if terrst_ref:
            imputed_countries.extend(
                impute_reference_class_average(country, 2000, 2023, "Dataset", "UNSDG_TERRST", terrst_ref)
            )
        if frshwt_ref:
            imputed_countries.extend(
                impute_reference_class_average(country, 2000, 2023, "Dataset", "UNSDG_FRSHWT", frshwt_ref)
            )
    
    # Get original datasets that have imputed values and combine with new imputations
    from sspi_flask_app.api.resources.utilities import deduplicate_dictionary_list
    
    # Filter to only the imputed values from extrapolation/interpolation
    existing_imputed = [d for d in imputed_marine + imputed_terrst + imputed_frshwt if d.get("Imputed", False)]
    
    # Combine all imputed data and remove duplicates
    all_imputed_datasets = deduplicate_dictionary_list(existing_imputed + imputed_countries)
    
    # Recompute indicator scores for imputed data only
    overall_biodiv, missing_imputations = score_indicator(
        all_imputed_datasets, "BIODIV",
        score_function=score_biodiv,
        unit="Index",
    )
    
    # All these should be imputed already, but filter just to be safe
    imputed_biodiv = filter_imputations(overall_biodiv)
    
    # Insert into database
    if imputed_biodiv:
        sspi_imputed_data.insert_many(imputed_biodiv)
    
    return parse_json(imputed_biodiv)
