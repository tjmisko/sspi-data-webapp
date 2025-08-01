from sspi_flask_app.api.datasource.who import collect_who_data, clean_who_data
from sspi_flask_app.models.database import (
    sspi_raw_api_data,
    sspi_clean_api_data,
    sspi_metadata
)
from sspi_flask_app.api.resources.utilities import parse_json
from sspi_flask_app.api.core.datasets import dataset_collector, dataset_cleaner


@dataset_collector("WHO_DPTCOV")
def collect_who_dptcov(**kwargs):
    yield from collect_who_data("vdpt", **kwargs)


@dataset_cleaner("WHO_DPTCOV")
def clean_who_dptcov():
    sspi_clean_api_data.delete_many({"DatasetCode": "WHO_DPTCOV"})
    source_info = sspi_metadata.get_source_info("WHO_DPTCOV")
    raw_data = sspi_raw_api_data.fetch_raw_data(source_info)
    description = "DTP3 immunization coverage among one-year-olds (%)"
    cleaned_data = clean_who_data(raw_data, "WHO_DPTCOV", "Percent", description)
    sspi_clean_api_data.insert_many(cleaned_data)
    return parse_json(cleaned_data)