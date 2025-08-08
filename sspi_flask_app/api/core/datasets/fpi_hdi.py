from sspi_flask_app.api.datasource.fpi import collect_fpi_data, clean_fpi_data
from sspi_flask_app.api.core.datasets import dataset_collector, dataset_cleaner
from sspi_flask_app.models.database import sspi_raw_api_data, sspi_clean_api_data, sspi_metadata
from sspi_flask_app.api.resources.utilities import parse_json


@dataset_collector("FPI_HDI")
def collect_fpi_hdi(**kwargs):
    yield from collect_fpi_data("hdi", **kwargs)


@dataset_cleaner("FPI_HDI")
def clean_fpi_hdi():
    sspi_clean_api_data.delete_many({"DatasetCode": "FPI_HDI"})
    source_info = sspi_metadata.get_source_info("FPI_HDI")
    raw_data = sspi_raw_api_data.fetch_raw_data(source_info)
    description = "Human Development Index; Source: Trends in the Human Development Index, 19915, downloaded 01/15/2018 from https://hdr.undp.org/en/composite/trends"
    cleaned_data = clean_fpi_data(raw_data, "FPI_HDI", "Index", description)
    sspi_clean_api_data.insert_many(cleaned_data)
    sspi_metadata.record_dataset_range(cleaned_data, "FPI_HDI")
    return parse_json(cleaned_data)