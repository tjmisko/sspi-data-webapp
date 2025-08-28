import json
from sspi_flask_app.api.datasource.ilo import collect_ilo_data, extract_ilo, filter_ilo
from sspi_flask_app.api.core.datasets import dataset_collector, dataset_cleaner
from sspi_flask_app.models.database import sspi_raw_api_data, sspi_clean_api_data, sspi_metadata
from sspi_flask_app.api.resources.utilities import parse_json

@dataset_collector("ILO_COLBAR")
def collect_ilo_colbar(**kwargs):
    url_params = ["startPeriod=1990-01-01", "endPeriod=2024-12-31"]
    yield from collect_ilo_data(
        "DF_ILR_CBCT_NOC_RT", URLParams=url_params, **kwargs
    )


@dataset_cleaner("ILO_COLBAR")
def clean_ilo_colbar():
    sspi_clean_api_data.delete_many({"DatasetCode": "ILO_COLBAR"})
    source_info = sspi_metadata.get_source_info("ILO_COLBAR")
    raw_data = sspi_raw_api_data.fetch_raw_data(source_info)
    
    # Extract and filter ILO data using utility functions
    extracted_data = extract_ilo(raw_data)
    obs_list = filter_ilo(extracted_data, "ILO_COLBAR", unit_label="Proportion")
    
    sspi_clean_api_data.insert_many(obs_list)
    sspi_metadata.record_dataset_range(obs_list, "ILO_COLBAR")
    return parse_json(obs_list)