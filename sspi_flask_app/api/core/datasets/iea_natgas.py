from sspi_flask_app.api.datasource.iea import collect_iea_data, filter_iea_data
from sspi_flask_app.models.database import (
    sspi_raw_api_data,
    sspi_clean_api_data,
    sspi_metadata
)
from sspi_flask_app.api.resources.utilities import parse_json
from sspi_flask_app.api.core.datasets import dataset_collector, dataset_cleaner


@dataset_collector("IEA_NATGAS")
def collect_iea_natgas(**kwargs):
    yield from collect_iea_data("TESbySource", **kwargs)


@dataset_cleaner("IEA_NATGAS")
def clean_iea_natgas():
    sspi_clean_api_data.delete_many({"DatasetCode": "IEA_NATGAS"})
    source_info = sspi_metadata.get_source_info("IEA_NATGAS")
    raw_data = sspi_raw_api_data.fetch_raw_data(source_info)
    
    intermediate_document_list = filter_iea_data(raw_data, "IEA_NATGAS", "NATGAS")
    
    sspi_clean_api_data.insert_many(intermediate_document_list)
    sspi_metadata.record_dataset_range(intermediate_document_list, "IEA_NATGAS")
    return parse_json(intermediate_document_list)
