from sspi_flask_app.api.datasource.wid import collect_wid_data
from sspi_flask_app.api.core.datasets import dataset_collector, dataset_cleaner
from sspi_flask_app.models.database import sspi_raw_api_data, sspi_clean_api_data, sspi_metadata
from sspi_flask_app.api.resources.utilities import parse_json

@dataset_collector("WID_BFIFTY")
def collect_wid_bfifty(**kwargs):
    yield from collect_wid_data(**kwargs)


@dataset_cleaner("WID_BFIFTY")
def clean_wid_bfifty():
    sspi_clean_api_data.delete_many({"DatasetCode": "WID_BFIFTY"})
    source_info = sspi_metadata.get_source_info("WID_BFIFTY")
    raw_data = sspi_raw_api_data.fetch_raw_data(source_info)
    # TODO: Implement cleaning logic for WID_BFIFTY
    # This will be implemented in the next task
    cleaned_data = []
    sspi_clean_api_data.insert_many(cleaned_data)
    return parse_json(cleaned_data)
