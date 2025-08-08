from sspi_flask_app.api.datasource.wid import collect_wid_data
from sspi_flask_app.api.core.datasets import dataset_collector, dataset_cleaner
from sspi_flask_app.models.database import sspi_raw_api_data, sspi_clean_api_data, sspi_metadata
from sspi_flask_app.api.resources.utilities import parse_json

@dataset_collector("WID_TOPTEN")
def collect_wid_topten(**kwargs):
    yield from collect_wid_data(**kwargs)


@dataset_cleaner("WID_TOPTEN")
def clean_wid_topten():
    sspi_clean_api_data.delete_many({"DatasetCode": "WID_TOPTEN"})
    source_info = sspi_metadata.get_source_info("WID_TOPTEN")
    raw_data = sspi_raw_api_data.fetch_raw_data(source_info)
    # TODO: Implement cleaning logic for WID_TOPTEN
    # This will be implemented in the next task
    cleaned_data = []
    sspi_clean_api_data.insert_many(cleaned_data)
    sspi_metadata.record_dataset_range(cleaned_data, "WID_TOPTEN")
    return parse_json(cleaned_data)