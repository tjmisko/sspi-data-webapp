from sspi_flask_app.api.datasource.unpd import collect_fampln_data, clean_fampln_csv
from sspi_flask_app.models.database import (
    sspi_raw_api_data,
    sspi_clean_api_data,
    sspi_metadata
)
from sspi_flask_app.api.resources.utilities import parse_json
from sspi_flask_app.api.core.datasets import dataset_collector, dataset_cleaner


@dataset_collector("UNPD_FAMPLN")
def collect_fampln(**kwargs):
    yield from collect_fampln_data(**kwargs)


@dataset_cleaner("UNPD_FAMPLN")
def clean_fampln():
    sspi_clean_api_data.delete_many({"DatasetCode": "UNPD_FAMPLN"})
    source_info = sspi_metadata.get_source_info("UNPD_FAMPLN")
    raw_data = sspi_raw_api_data.fetch_raw_data(source_info)
    
    intermediate_document_list = clean_fampln_csv(raw_data, "UNPD_FAMPLN")
    
    sspi_clean_api_data.insert_many(intermediate_document_list)
    sspi_metadata.record_dataset_range(intermediate_document_list, "UNPD_FAMPLN")
    return parse_json(intermediate_document_list)
    