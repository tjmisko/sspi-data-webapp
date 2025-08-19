from sspi_flask_app.api.datasource.unfao import collect_unfao_data, format_fao_data_series
from sspi_flask_app.models.database import (
    sspi_raw_api_data,
    sspi_clean_api_data,
    sspi_metadata
)
from sspi_flask_app.api.resources.utilities import parse_json
from sspi_flask_app.api.core.datasets import dataset_collector, dataset_cleaner


@dataset_collector("UNFAO_LANDAR")
def collect_unfao_landar(**kwargs):
    yield from collect_unfao_data("5112", "5110", "RL", **kwargs)


@dataset_cleaner("UNFAO_LANDAR")
def clean_unfao_landar():
    sspi_clean_api_data.delete_many({"DatasetCode": "UNFAO_LANDAR"})
    source_info = sspi_metadata.get_source_info("UNFAO_LANDAR")
    raw_data = sspi_raw_api_data.fetch_raw_data(source_info)
    
    clean_obs_list = format_fao_data_series(raw_data[0]["Raw"]["data"], "UNFAO_LANDAR")
    
    # Convert unit from hectares to square kilometers for land area
    for obs in clean_obs_list:
        obs["DatasetCode"] = "UNFAO_LANDAR"
        # Convert from hectares to km² (1 hectare = 0.01 km²)
        obs["Value"] = obs["Value"] * 0.01
        obs["Unit"] = "km²"
    
    sspi_clean_api_data.insert_many(clean_obs_list)
    sspi_metadata.record_dataset_range(clean_obs_list, "UNFAO_LANDAR")
    return parse_json(clean_obs_list)