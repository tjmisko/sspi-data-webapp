from sspi_flask_app.api.datasource.unfao import collect_unfao_data, format_fao_data_series
from sspi_flask_app.models.database import (
    sspi_raw_api_data,
    sspi_clean_api_data,
    sspi_metadata
)
from sspi_flask_app.api.resources.utilities import parse_json
from sspi_flask_app.api.core.datasets import dataset_collector, dataset_cleaner


@dataset_collector("UNFAO_CRBNAV")
def collect_unfao_crbnav(**kwargs):
    yield from collect_unfao_data("7215", "6646", "RL", **kwargs)


@dataset_cleaner("UNFAO_CRBNAV")
def clean_unfao_crbnav():
    sspi_clean_api_data.delete_many({"DatasetCode": "UNFAO_CRBNAV"})
    source_info = sspi_metadata.get_source_info("UNFAO_CRBNAV")
    raw_data = sspi_raw_api_data.fetch_raw_data(source_info)
    
    clean_obs_list = format_fao_data_series(raw_data[0]["Raw"]["data"], "UNFAO_CRBNAV")
    
    # Calculate 1990s averages
    average_1990s_dict = {}
    all_years = set()
    for obs in clean_obs_list:
        all_years.add(obs["Year"])
        if obs["Year"] not in list(range(1990, 2000)):
            continue
        if obs["CountryCode"] not in average_1990s_dict.keys():
            average_1990s_dict[obs["CountryCode"]] = {"Values": []}
        average_1990s_dict[obs["CountryCode"]]["Values"].append(obs["Value"])
    
    # Create average records rolled forward to all years
    avg_data_list = []
    for country in average_1990s_dict.keys():
        if len(average_1990s_dict[country]["Values"]) > 0:
            avg_value = sum(average_1990s_dict[country]["Values"]) / len(average_1990s_dict[country]["Values"])
            # Roll forward the 1990s average to every year in the dataset
            for year in sorted(all_years):
                avg_data_list.append({
                    "DatasetCode": "UNFAO_CRBNAV",
                    "CountryCode": country,
                    "Year": year,
                    "Value": avg_value,
                    "Unit": "millions of kilograms (1990s Average)"
                })
    
    sspi_clean_api_data.insert_many(avg_data_list)
    sspi_metadata.record_dataset_range(avg_data_list, "UNFAO_CRBNAV")
    return parse_json(avg_data_list)