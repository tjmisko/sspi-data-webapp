from sspi_flask_app.api.datasource.unfao import collect_unfao_data, format_fao_data_series
from sspi_flask_app.models.database import (
    sspi_raw_api_data,
    sspi_clean_api_data,
    sspi_metadata
)
from sspi_flask_app.api.resources.utilities import parse_json
from sspi_flask_app.api.core.datasets import dataset_collector, dataset_cleaner


@dataset_collector("UNFAO_FRSTAV")
def collect_unfao_frstav(**kwargs):
    yield from collect_unfao_data("5110", "6717", "RL", **kwargs)


@dataset_cleaner("UNFAO_FRSTAV")
def clean_unfao_frstav():
    sspi_clean_api_data.delete_many({"DatasetCode": "UNFAO_FRSTAV"})
    source_info = sspi_metadata.get_source_info("UNFAO_FRSTAV")
    raw_data = sspi_raw_api_data.fetch_raw_data(source_info)
    
    clean_obs_list = format_fao_data_series(raw_data[0]["Raw"]["data"], "UNFAO_FRSTAV")
    
    # Calculate 1990s averages
    average_1990s_dict = {}
    for obs in clean_obs_list:
        if obs["Year"] not in list(range(1990, 2000)):
            continue
        if obs["CountryCode"] not in average_1990s_dict.keys():
            average_1990s_dict[obs["CountryCode"]] = {"Values": []}
        average_1990s_dict[obs["CountryCode"]]["Values"].append(obs["Value"])
    
    # Create average records
    avg_data_list = []
    for country in average_1990s_dict.keys():
        if len(average_1990s_dict[country]["Values"]) > 0:
            avg_value = sum(average_1990s_dict[country]["Values"]) / len(average_1990s_dict[country]["Values"])
            avg_data_list.append({
                "DatasetCode": "UNFAO_FRSTAV",
                "CountryCode": country,
                "Year": 1995,  # Representative year for 1990s average
                "Value": avg_value,
                "Unit": "hectares (1990s Average)"
            })
    
    sspi_clean_api_data.insert_many(avg_data_list)
    return parse_json(avg_data_list)