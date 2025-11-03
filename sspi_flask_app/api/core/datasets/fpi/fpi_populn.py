###########################################################
# Documentation: datasets/fpi/fpi_populn/documentation.md #
###########################################################
from sspi_flask_app.api.datasource.fpi import collect_fpi_data, clean_fpi_data
from sspi_flask_app.api.core.datasets import dataset_collector, dataset_cleaner
from sspi_flask_app.models.database import sspi_raw_api_data, sspi_clean_api_data, sspi_metadata
from sspi_flask_app.api.resources.utilities import parse_json


@dataset_collector("FPI_POPULN")
def collect_fpi_populn(**kwargs):
    yield from collect_fpi_data("pop", **kwargs)


@dataset_cleaner("FPI_POPULN")
def clean_fpi_populn():
    sspi_clean_api_data.delete_many({"DatasetCode": "FPI_POPULN"})
    source_info = sspi_metadata.get_source_info("FPI_POPULN")
    raw_data = sspi_raw_api_data.fetch_raw_data(source_info)
    description = "Population"
    cleaned_data = clean_fpi_data(raw_data, "FPI_POPULN", "People", description)
    sspi_clean_api_data.insert_many(cleaned_data)
    sspi_metadata.record_dataset_range(cleaned_data, "FPI_POPULN")
    return parse_json(cleaned_data)