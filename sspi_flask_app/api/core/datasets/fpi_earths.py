from sspi_flask_app.api.datasource.fpi import collect_fpi_data, clean_fpi_data
from sspi_flask_app.api.core.datasets import dataset_collector, dataset_cleaner
from sspi_flask_app.models.database import sspi_raw_api_data, sspi_clean_api_data, sspi_metadata
from sspi_flask_app.api.resources.utilities import parse_json


@dataset_collector("FPI_EARTHS")
def collect_fpi_earths(**kwargs):
    yield from collect_fpi_data("earth", **kwargs)


@dataset_cleaner("FPI_EARTHS")
def clean_fpi_earths():
    sspi_clean_api_data.delete_many({"DatasetCode": "FPI_EARTHS"})
    source_info = sspi_metadata.get_source_info("FPI_EARTHS")
    raw_data = sspi_raw_api_data.fetch_raw_data(source_info)
    description = "EFConsPerCap of Country / EFConsPerCap of World"
    cleaned_data = clean_fpi_data(raw_data, "FPI_EARTHS", "Earths", description)
    sspi_clean_api_data.insert_many(cleaned_data)
    return parse_json(cleaned_data)