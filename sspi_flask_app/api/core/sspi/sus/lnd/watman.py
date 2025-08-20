from sspi_flask_app.api.core.sspi import compute_bp
from sspi_flask_app.api.core.sspi import impute_bp
from flask_login import login_required
from flask import current_app as app
from sspi_flask_app.models.database import (
    sspi_clean_api_data,
    sspi_indicator_data,
    sspi_incomplete_indicator_data,
    sspi_imputed_data
)
from sspi_flask_app.api.resources.utilities import (
    parse_json,
    score_indicator,
    goalpost,
    extrapolate_backward,
    extrapolate_forward,
    slice_dataset,
    filter_imputations,
    impute_reference_class_average
)


@compute_bp.route("/WATMAN", methods=['POST'])
@login_required
def compute_watman():
    def score_watman(UNSDG_CWUEFF, UNSDG_WTSTRS) -> float:
        """
        Score WATMAN using CWUEFF and WTSTRS.
        """
        return (goalpost(UNSDG_CWUEFF, -20, 50) + goalpost(UNSDG_WTSTRS, 100, 0)) / 2

    app.logger.info("Running /api/v1/compute/WATMAN")
    sspi_indicator_data.delete_many({"IndicatorCode": "WATMAN"})
    sspi_incomplete_indicator_data.delete_many({"IndicatorCode": "WATMAN"})
    wuseff_clean = sspi_clean_api_data.find({"DatasetCode": "UNSDG_WUSEFF"})
    cwueff_clean = sspi_clean_api_data.find({"DatasetCode": "UNSDG_CWUEFF"})
    wtstrs_clean = sspi_clean_api_data.find({"DatasetCode": "UNSDG_WTSTRS"})
    combined_list = cwueff_clean + wtstrs_clean
    clean_list, incomplete_list = score_indicator(
        combined_list, "WATMAN",
        score_function=score_watman,
        unit="Index",
    )
    sspi_indicator_data.insert_many(clean_list)
    sspi_incomplete_indicator_data.insert_many(incomplete_list)
    return parse_json(clean_list)

@impute_bp.route("/WATMAN", methods=["POST"])
@login_required
def impute_watman():
    def score_watman(UNSDG_CWUEFF, UNSDG_WTSTRS) -> float:
        """
        Score WATMAN using CWUEFF and WTSTRS.
        """
        return (goalpost(UNSDG_CWUEFF, -20, 50) + goalpost(UNSDG_WTSTRS, 100, 0)) / 2
        
    def create_synthetic_cwueff(country_code, wuseff_data):
        """
        Create synthetic CWUEFF data from WUSEFF by extrapolating backward to create baseline.
        """
        from sspi_flask_app.api.resources.utilities import interpolate_linear
        
        # Extrapolate WUSEFF backward to 2000-2005 for baseline  
        extended_wuseff = extrapolate_backward(
            wuseff_data, 2000, series_id=["CountryCode", "DatasetCode"]
        )
        extended_wuseff = extrapolate_forward(
            extended_wuseff, 2023, series_id=["CountryCode", "DatasetCode"]
        )
        extended_wuseff = interpolate_linear(
            extended_wuseff, series_id=["CountryCode", "DatasetCode"]
        )
        
        # Group by country and compute 2000-2005 baseline average
        country_data = {}
        for obs in extended_wuseff:
            if obs["CountryCode"] == country_code:
                year = obs["Year"]
                value = obs["Value"]
                
                if country_code not in country_data:
                    country_data[country_code] = {"baseline_values": [], "yearly_values": {}}
                
                # Collect 2000-2005 data for baseline
                if 2000 <= year <= 2005:
                    country_data[country_code]["baseline_values"].append(value)
                
                # Store all years from 2006 onward  
                if year >= 2006:
                    country_data[country_code]["yearly_values"][year] = value
        
        # Create synthetic CWUEFF observations
        synthetic_cwueff = []
        if country_code in country_data and country_data[country_code]["baseline_values"]:
            baseline_avg = sum(country_data[country_code]["baseline_values"]) / len(country_data[country_code]["baseline_values"])
            
            # Create CWUEFF for baseline period (2000-2005) - these should be close to 0% change
            for obs in extended_wuseff:
                if obs["CountryCode"] == country_code and 2000 <= obs["Year"] <= 2005:
                    year = obs["Year"]
                    value = obs["Value"]
                    if baseline_avg != 0:
                        change_value = ((value - baseline_avg) / baseline_avg) * 100
                    else:
                        change_value = 0
                    
                    cwueff_obs = {
                        "DatasetCode": "UNSDG_CWUEFF",
                        "CountryCode": country_code,
                        "Year": year,
                        "Value": change_value,
                        "Unit": "Percent",
                        "Description": "Synthetic Change in Water Use Efficiency from extrapolated baseline",
                        "Imputed": True,
                        "ImputationMethod": "Synthetic CWUEFF from WUSEFF extrapolation"
                    }
                    synthetic_cwueff.append(cwueff_obs)
            
            # Create CWUEFF for post-baseline period (2006 onward)
            for year, value in country_data[country_code]["yearly_values"].items():
                if baseline_avg != 0:
                    change_value = ((value - baseline_avg) / baseline_avg) * 100
                else:
                    change_value = 0
                
                cwueff_obs = {
                    "DatasetCode": "UNSDG_CWUEFF",
                    "CountryCode": country_code,
                    "Year": year,
                    "Value": change_value,
                    "Unit": "Percent",
                    "Description": "Synthetic Change in Water Use Efficiency from extrapolated baseline",
                    "Imputed": True,
                    "ImputationMethod": "Synthetic CWUEFF from WUSEFF extrapolation"
                }
                synthetic_cwueff.append(cwueff_obs)
        
        return synthetic_cwueff
    
    mongo_query = {"IndicatorCode": "WATMAN"}
    sspi_imputed_data.delete_many(mongo_query)
    clean_list = sspi_indicator_data.find(mongo_query)
    incomplete_list = sspi_incomplete_indicator_data.find(mongo_query)
    
    # Extract existing CWUEFF data and extrapolate 
    clean_cwueff = slice_dataset(clean_list, "UNSDG_CWUEFF") + \
        slice_dataset(incomplete_list, "UNSDG_CWUEFF")
    imputed_cwueff = extrapolate_backward(
        clean_cwueff, 2000, series_id=["CountryCode", "DatasetCode"]
    )
    imputed_cwueff = extrapolate_forward(
        imputed_cwueff, 2023, series_id=["CountryCode", "DatasetCode"]
    )
    
    # Get WUSEFF data to create synthetic CWUEFF for missing countries
    from sspi_flask_app.models.database import sspi_clean_api_data
    wuseff_data = sspi_clean_api_data.find({"DatasetCode": "UNSDG_WUSEFF"})
    
    # Countries missing CWUEFF but having WUSEFF (excluding SGP handled separately)
    missing_cwueff_countries = ["AUS", "BGD", "CAN", "CHE", "CHL", "DEU", "ISL", "LVA", "PER", "PHL", "SVN", "THA"]
    
    # Create synthetic CWUEFF for each missing country
    synthetic_cwueff_all = []
    for country in missing_cwueff_countries:
        country_wuseff = [obs for obs in wuseff_data if obs["CountryCode"] == country]
        if country_wuseff:
            synthetic_cwueff = create_synthetic_cwueff(country, country_wuseff)
            synthetic_cwueff_all.extend(synthetic_cwueff)
    
    # Impute CWUEFF Data for SGP using reference class average
    sgp_cwueff = impute_reference_class_average("SGP", 2000, 2023, "Dataset", "UNSDG_CWUEFF", clean_cwueff)
    
    # Extract and impute WTSTRS data
    clean_wtstrs = slice_dataset(clean_list, "UNSDG_WTSTRS") + \
        slice_dataset(incomplete_list, "UNSDG_WTSTRS")
    imputed_wtstrs = extrapolate_backward(
        clean_wtstrs, 2000, series_id=["CountryCode", "DatasetCode"]
    )
    imputed_wtstrs = extrapolate_forward(
        imputed_wtstrs, 2023, series_id=["CountryCode", "DatasetCode"]
    )
    
    # Combine all CWUEFF sources
    all_cwueff = imputed_cwueff + synthetic_cwueff_all + sgp_cwueff
    
    # Compute WATMAN indicator scores
    overall_watman, missing_imputations = score_indicator(
        imputed_wtstrs + all_cwueff, "WATMAN",
        score_function=score_watman,
        unit="Index",
    )
    
    # Filter to only imputed observations
    imputed_watman = filter_imputations(overall_watman)
    
    # Insert into database
    if imputed_watman:
        sspi_imputed_data.insert_many(imputed_watman)
    
    return parse_json(imputed_watman)

