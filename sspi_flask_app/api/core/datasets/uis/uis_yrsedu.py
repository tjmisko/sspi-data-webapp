###########################################################
# Documentation: datasets/uis/uis_yrsedu/documentation.md #
###########################################################
from sspi_flask_app.api.datasource.uis import collect_uis_data, clean_uis_data
from sspi_flask_app.api.core.datasets import dataset_collector, dataset_cleaner
from sspi_flask_app.models.database import sspi_raw_api_data, sspi_clean_api_data, sspi_metadata
from sspi_flask_app.api.resources.utilities import parse_json

@dataset_collector("UIS_YRSEDU")
def collect_uis_yrsedu(**kwargs):
    yield from collect_uis_data("YEARS.FC.COMP.1T3", **kwargs)


@dataset_cleaner("UIS_YRSEDU")
def clean_uis_yrsedu():
    sspi_clean_api_data.delete_many({"DatasetCode": "UIS_YRSEDU"})
    source_info = sspi_metadata.get_source_info("UIS_YRSEDU")
    raw_data = sspi_raw_api_data.fetch_raw_data(source_info)
    description = (
        "Number of years of compulsory primary and secondary "
        "education guaranteed in legal frameworks"
    )
    cleaned_data = clean_uis_data(raw_data, "UIS_YRSEDU", "Years", description)
    sspi_clean_api_data.insert_many(cleaned_data)
    sspi_metadata.record_dataset_range(cleaned_data, "UIS_YRSEDU")
    return parse_json(cleaned_data)