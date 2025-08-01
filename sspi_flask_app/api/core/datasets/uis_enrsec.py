from sspi_flask_app.api.datasource.uis import collect_uis_data, clean_uis_data
from sspi_flask_app.models.database import (
    sspi_raw_api_data,
    sspi_clean_api_data,
    sspi_metadata
)
from sspi_flask_app.api.resources.utilities import parse_json
from sspi_flask_app.api.core.datasets import dataset_collector, dataset_cleaner


@dataset_collector("UIS_ENRSEC")
def collect_uis_enrsec(**kwargs):
    yield from collect_uis_data("NERT.2.CP", **kwargs)


@dataset_cleaner("UIS_ENRSEC")
def clean_uis_enrsec():
    sspi_clean_api_data.delete_many({"DatasetCode": "UIS_ENRSEC"})
    source_info = sspi_metadata.get_source_info("UIS_ENRSEC")
    raw_data = sspi_raw_api_data.fetch_raw_data(source_info)
    description = "Net enrollment in lower secondary school (%)"
    cleaned_data = clean_uis_data(raw_data, "UIS_ENRSEC", "Percent", description)
    sspi_clean_api_data.insert_many(cleaned_data)
    return parse_json(cleaned_data)