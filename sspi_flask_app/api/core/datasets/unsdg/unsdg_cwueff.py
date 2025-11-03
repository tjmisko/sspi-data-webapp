###############################################################
# Documentation: datasets/unsdg/unsdg_cwueff/documentation.md #
###############################################################
from sspi_flask_app.api.datasource.unsdg import collect_sdg_indicator_data, filter_sdg, extract_sdg
from sspi_flask_app.api.core.datasets import dataset_collector, dataset_cleaner
from sspi_flask_app.models.database import sspi_raw_api_data, sspi_clean_api_data, sspi_metadata
from sspi_flask_app.api.resources.utilities import parse_json

@dataset_collector("UNSDG_CWUEFF")
def collect_unsdg_cwueff(**kwargs):
    yield from collect_sdg_indicator_data("6.4.1", **kwargs)

@dataset_cleaner("UNSDG_CWUEFF")
def clean_unsdg_cwueff():
    sspi_clean_api_data.delete_many({"DatasetCode": "UNSDG_CWUEFF"})
    source_info = sspi_metadata.get_source_info("UNSDG_CWUEFF")
    raw_data = sspi_raw_api_data.fetch_raw_data(source_info)
    extracted_unsdg_cwueff = extract_sdg(raw_data)
    idcode_map = {
        "ER_H2O_WUEYST": "UNSDG_CWUEFF",
    }
    rename_map = {"units": "Unit", "seriesDescription": "Description"}
    drop_list = [
        "goal",
        "indicator", 
        "series",
        "seriesCount",
        "target",
        "geoAreaCode",
        "geoAreaName",
    ]
    unsdg_cwueff_raw = filter_sdg(
        extracted_unsdg_cwueff,
        idcode_map,
        rename_map,
        drop_list,
        activity="TOTAL"
    )
    # Group data by country to compute 2000-2005 baseline averages
    country_data = {}
    for obs in unsdg_cwueff_raw:
        country_code = obs["CountryCode"]
        year = obs["Year"]
        value = obs["Value"]
        
        if country_code not in country_data:
            country_data[country_code] = {"baseline_values": [], "yearly_values": {}}
        
        # Collect 2000-2005 data for baseline average
        if 2000 <= year <= 2005:
            country_data[country_code]["baseline_values"].append(value)
        
        # Store all year values from 2006 onward for comparison
        if year >= 2006:
            country_data[country_code]["yearly_values"][year] = value
    
    # Compute change from 2000-2005 average for all years from 2006 onward
    unsdg_cwueff = []
    for country_code, country_info in country_data.items():
        # Calculate 2000-2005 baseline average if we have data
        if country_info["baseline_values"]:
            baseline_avg = sum(country_info["baseline_values"]) / len(country_info["baseline_values"])
            
            # Create change observations for each year from 2006 onward
            for year, value in country_info["yearly_values"].items():
                # Calculate percentage change from baseline average
                if baseline_avg != 0:
                    change_value = ((value - baseline_avg) / baseline_avg) * 100
                else:
                    change_value = 0
                
                # Create new observation with the change value
                cwueff_obs = {
                    "DatasetCode": "UNSDG_CWUEFF",
                    "CountryCode": country_code,
                    "Year": year,
                    "Value": change_value,
                    "Unit": "Percent",
                    "Description": "Change in Water Use Efficiency compared with 2000-2005 average"
                }
                unsdg_cwueff.append(cwueff_obs)
    
    count = sspi_clean_api_data.insert_many(unsdg_cwueff)
    sspi_metadata.record_dataset_range(unsdg_cwueff, "UNSDG_CWUEFF")
    return unsdg_cwueff
