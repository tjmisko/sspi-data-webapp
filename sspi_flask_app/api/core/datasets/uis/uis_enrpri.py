###########################################################
# Documentation: datasets/uis/uis_enrpri/documentation.md #
###########################################################
from sspi_flask_app.api.datasource.uis import collect_uis_data, clean_uis_data
from sspi_flask_app.models.database import (
    sspi_raw_api_data,
    sspi_clean_api_data,
    sspi_metadata
)
from sspi_flask_app.api.resources.utilities import parse_json
from sspi_flask_app.api.core.datasets import dataset_collector, dataset_cleaner


@dataset_collector("UIS_ENRPRI")
def collect_uis_enrpri(**kwargs):
    yield from collect_uis_data("NERT.1.CP", **kwargs)


@dataset_cleaner("UIS_ENRPRI")
def clean_uis_enrpri():
    sspi_clean_api_data.delete_many({"DatasetCode": "UIS_ENRPRI"})
    source_info = sspi_metadata.get_source_info("UIS_ENRPRI")
    raw_data = sspi_raw_api_data.fetch_raw_data(source_info)
    description = "Net enrollment in primary school (%)"
    cleaned_data = clean_uis_data(raw_data, "UIS_ENRPRI", "Percent", description)
    sspi_clean_api_data.insert_many(cleaned_data)
    sspi_metadata.record_dataset_range(cleaned_data, "UIS_ENRPRI")
    return parse_json(cleaned_data)
