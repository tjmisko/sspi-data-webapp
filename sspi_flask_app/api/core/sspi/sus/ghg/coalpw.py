from flask_login import login_required
from flask import current_app as app
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
    interpolate_linear,
    impute_reference_class_average
)
import pandas as pd
import json


@compute_bp.route("/COALPW", methods=["POST"])
@admin_required
def compute_coalpw():
    lg, ug = sspi_metadata.get_goalposts("COALPW")
    def score_coalpw(IEA_TLCOAL, IEA_NATGAS, IEA_NCLEAR, IEA_HYDROP, IEA_GEOPWR, IEA_BIOWAS, IEA_FSLOIL):
        IEA_TTLSUM = IEA_TLCOAL + IEA_NATGAS + IEA_NCLEAR + IEA_HYDROP + IEA_GEOPWR + IEA_BIOWAS + IEA_FSLOIL
        return goalpost(IEA_TLCOAL / IEA_TTLSUM, lg, ug)
        
    sspi_indicator_data.delete_many({"IndicatorCode": "COALPW"})
    sspi_incomplete_indicator_data.delete_many({"IndicatorCode": "COALPW"})
    dataset_codes = ["IEA_TLCOAL", "IEA_NATGAS", "IEA_NCLEAR", "IEA_HYDROP", "IEA_GEOPWR", "IEA_BIOWAS", "IEA_FSLOIL"]
    coalpw_datasets = sspi_clean_api_data.find({"DatasetCode": {"$in": dataset_codes}})
    clean_list, incomplete_list = score_indicator(
        coalpw_datasets,
        "COALPW",
        score_function=score_coalpw,
        unit="Index",
    )
    sspi_indicator_data.insert_many(clean_list)
    sspi_incomplete_indicator_data.insert_many(incomplete_list)
    return parse_json(clean_list)


@impute_bp.route("/COALPW", methods=["POST"])
@admin_required
def impute_coalpw():
    mongo_query = {"IndicatorCode": "COALPW"}
    sspi_imputed_data.delete_many(mongo_query)
    
    # Get SSPI67 countries using metadata
    sspi67_countries = sspi_metadata.country_group("SSPI67")
    
    # Get all datasets for COALPW directly using the ItemCode query
    all_coalpw_datasets = sspi_clean_api_data.find({
        "$or": [
            {"DatasetCode": "IEA_TLCOAL"},
            {"DatasetCode": "IEA_NATGAS"},
            {"DatasetCode": "IEA_NCLEAR"},
            {"DatasetCode": "IEA_HYDROP"},
            {"DatasetCode": "IEA_GEOPWR"},
            {"DatasetCode": "IEA_BIOWAS"},
            {"DatasetCode": "IEA_FSLOIL"}
        ]
    })
    
    # Group datasets by type
    datasets_by_type = {}
    dataset_codes = ["IEA_TLCOAL", "IEA_NATGAS", "IEA_NCLEAR", "IEA_HYDROP", "IEA_GEOPWR", "IEA_BIOWAS", "IEA_FSLOIL"]
    
    for code in dataset_codes:
        datasets_by_type[code] = []
    
    for dataset in all_coalpw_datasets:
        dataset_code = dataset["DatasetCode"]
        if dataset_code in datasets_by_type:
            datasets_by_type[dataset_code].append(dataset)
    
    # Process each dataset type individually
    all_imputed_datasets = []
    
    for dataset_code, dataset_data in datasets_by_type.items():
        # Get countries that have data for this dataset
        dataset_countries = {d["CountryCode"] for d in dataset_data}
        
        # Impute zeros for SSPI67 countries missing from this dataset
        missing_countries = [c for c in sspi67_countries if c not in dataset_countries]
        
        # Add zero imputations for missing countries
        for country in missing_countries:
            for year in range(2000, 2024):
                zero_observation = {
                    "DatasetCode": dataset_code,
                    "CountryCode": country,
                    "Year": year,
                    "Value": 0.0,
                    "Unit": "PJ",
                    "Description": f"Zero imputation for missing energy type {dataset_code}",
                    "Imputed": True,
                    "ImputationMethod": "Zero imputation for missing energy type"
                }
                all_imputed_datasets.append(zero_observation)
        
        # Extrapolate and interpolate existing data to fill temporal gaps
        if dataset_data:
            extrapolated_backward = extrapolate_backward(
                dataset_data, 2000, series_id=["CountryCode", "DatasetCode"], impute_only=True
            )
            extrapolated_forward = extrapolate_forward(
                dataset_data, 2023, series_id=["CountryCode", "DatasetCode"], impute_only=True
            )
            
            # Combine for interpolation
            all_data = dataset_data + extrapolated_backward + extrapolated_forward
            interpolated = interpolate_linear(
                all_data, series_id=["CountryCode", "DatasetCode"], impute_only=True
            )
            
            # Add temporal imputations (only the imputed values)
            all_imputed_datasets.extend(extrapolated_backward + extrapolated_forward + interpolated)
    
    # Combine original datasets with imputations for indicator computation
    combined_datasets = list(all_coalpw_datasets) + all_imputed_datasets
    
    # Now compute COALPW indicator with complete datasets
    lg, ug = sspi_metadata.get_goalposts("COALPW")
    def score_coalpw(IEA_TLCOAL, IEA_NATGAS, IEA_NCLEAR, IEA_HYDROP, IEA_GEOPWR, IEA_BIOWAS, IEA_FSLOIL):
        IEA_TTLSUM = IEA_TLCOAL + IEA_NATGAS + IEA_NCLEAR + IEA_HYDROP + IEA_GEOPWR + IEA_BIOWAS + IEA_FSLOIL
        if IEA_TTLSUM == 0:
            return 1.0  # Perfect score for no energy consumption (or all zeros)
        return goalpost(IEA_TLCOAL / IEA_TTLSUM, lg, ug)
    
    # Recompute indicator scores using complete datasets
    overall_coalpw, missing_imputations = score_indicator(
        combined_datasets, "COALPW",
        score_function=score_coalpw,
        unit="Index"
    )
    
    # Filter to only imputed observations
    from sspi_flask_app.api.resources.utilities import filter_imputations
    imputed_coalpw = filter_imputations(overall_coalpw)
    
    # Insert into database
    if imputed_coalpw:
        sspi_imputed_data.insert_many(imputed_coalpw)
    
    return parse_json(imputed_coalpw)
