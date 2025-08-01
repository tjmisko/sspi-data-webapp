from sspi_flask_app.api.datasource.unfao import collect_unfao_data, format_fao_data_series
from sspi_flask_app.models.database import (
    sspi_raw_api_data,
    sspi_clean_api_data,
    sspi_metadata
)
from sspi_flask_app.api.resources.utilities import parse_json
from sspi_flask_app.api.core.datasets import dataset_collector, dataset_cleaner


@dataset_collector("UNFAO_FRSTLV")
def collect_unfao_frstlv(**kwargs):
    yield from collect_unfao_data("5110", "6717", "RL", **kwargs)


@dataset_cleaner("UNFAO_FRSTLV")
def clean_unfao_frstlv():
    sspi_clean_api_data.delete_many({"DatasetCode": "UNFAO_FRSTLV"})
    source_info = sspi_metadata.get_source_info("UNFAO_FRSTLV")
    raw_data = sspi_raw_api_data.fetch_raw_data(source_info)
    
    clean_obs_list = format_fao_data_series(raw_data[0]["Raw"]["data"], "UNFAO_FRSTLV")
    
    # Assign DatasetCode to all records
    for obs in clean_obs_list:
        obs["DatasetCode"] = "UNFAO_FRSTLV"
    
    sspi_clean_api_data.insert_many(clean_obs_list)
    return parse_json(clean_obs_list)