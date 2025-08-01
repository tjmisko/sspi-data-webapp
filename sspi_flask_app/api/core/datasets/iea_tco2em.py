from sspi_flask_app.api.datasource.iea import collect_iea_data, clean_IEA_data_GTRANS
from sspi_flask_app.models.database import (
    sspi_raw_api_data,
    sspi_clean_api_data,
    sspi_metadata
)
from sspi_flask_app.api.resources.utilities import parse_json
from sspi_flask_app.api.core.datasets import dataset_collector, dataset_cleaner


@dataset_collector("IEA_TCO2EM")
def collect_iea_tco2em(**kwargs):
    yield from collect_iea_data("CO2BySector", **kwargs)


@dataset_cleaner("IEA_TCO2EM")
def clean_iea_tco2em():
    sspi_clean_api_data.delete_many({"DatasetCode": "IEA_TCO2EM"})
    source_info = sspi_metadata.get_source_info("IEA_TCO2EM")
    raw_data = sspi_raw_api_data.fetch_raw_data(source_info)
    
    cleaned_data = clean_IEA_data_GTRANS(raw_data, "IEA_TCO2EM", "CO2 from transport sources")
    
    # Assign DatasetCode to all records
    for obs in cleaned_data:
        obs["DatasetCode"] = "IEA_TCO2EM"
    
    sspi_clean_api_data.insert_many(cleaned_data)
    return parse_json(cleaned_data)