from sspi_flask_app.api.datasource.ilo import collect_ilo_data, extract_ilo, filter_ilo
from sspi_flask_app.models.database import (
    sspi_raw_api_data,
    sspi_clean_api_data,
    sspi_metadata
)
from sspi_flask_app.api.resources.utilities import parse_json
from sspi_flask_app.api.core.datasets import dataset_collector, dataset_cleaner
import json


@dataset_collector("ILO_FATINJ")
def collect_ilo_fatinj(**kwargs):
    yield from collect_ilo_data("DF_SDG_F881_SEX_MIG_RT", **kwargs)


@dataset_cleaner("ILO_FATINJ")
def clean_ilo_fatinj():
    sspi_clean_api_data.delete_many({"DatasetCode": "ILO_FATINJ"})
    source_info = sspi_metadata.get_source_info("ILO_FATINJ")
    raw_data = sspi_raw_api_data.fetch_raw_data(source_info)
    
    # Extract and filter ILO data using utility functions
    extracted_data = extract_ilo(raw_data)
    cleaned_data = filter_ilo(extracted_data, "ILO_FATINJ", unit_label="Rate per 100,000", 
                              SEX="SEX_T", MIG="MIG_STATUS_TOTAL")
    
    sspi_clean_api_data.insert_many(cleaned_data)
    sspi_metadata.record_dataset_range(cleaned_data, "ILO_FATINJ")
    return parse_json(cleaned_data)