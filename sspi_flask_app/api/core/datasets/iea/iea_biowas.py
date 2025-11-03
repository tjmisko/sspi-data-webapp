###########################################################
# Documentation: datasets/iea/iea_biowas/documentation.md #
###########################################################
from sspi_flask_app.api.datasource.iea import collect_iea_data, filter_iea_data
from sspi_flask_app.models.database import (
    sspi_raw_api_data,
    sspi_clean_api_data,
    sspi_metadata
)
from sspi_flask_app.api.resources.utilities import parse_json
from sspi_flask_app.api.core.datasets import dataset_collector, dataset_cleaner


@dataset_collector("IEA_BIOWAS")
def collect_iea_biowas(**kwargs):
    yield from collect_iea_data("TESbySource", **kwargs)


@dataset_cleaner("IEA_BIOWAS")
def clean_iea_biowas():
    sspi_clean_api_data.delete_many({"DatasetCode": "IEA_BIOWAS"})
    source_info = sspi_metadata.get_source_info("IEA_BIOWAS")
    raw_data = sspi_raw_api_data.fetch_raw_data(source_info)
    
    intermediate_document_list = filter_iea_data(raw_data, "IEA_BIOWAS", "COMRENEW")
    
    sspi_clean_api_data.insert_many(intermediate_document_list)
    sspi_metadata.record_dataset_range(intermediate_document_list, "IEA_BIOWAS")
    return parse_json(intermediate_document_list)