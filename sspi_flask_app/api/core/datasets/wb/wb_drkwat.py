#########################################################
# Documentation: datasets/wb/wb_drkwat/documentation.md #
#########################################################
from sspi_flask_app.api.datasource.worldbank import collect_wb_data, clean_wb_data
from sspi_flask_app.models.database import (
    sspi_raw_api_data,
    sspi_clean_api_data,
    sspi_metadata
)
from sspi_flask_app.api.resources.utilities import parse_json
from sspi_flask_app.api.core.datasets import dataset_collector, dataset_cleaner


@dataset_collector("WB_DRKWAT")
def collect_wb_drkwat(**kwargs):
    yield from collect_wb_data("SH.H2O.SMDW.ZS", **kwargs)


@dataset_cleaner("WB_DRKWAT")
def clean_wb_drkwat():
    sspi_clean_api_data.delete_many({"DatasetCode": "WB_DRKWAT"})
    source_info = sspi_metadata.get_source_info("WB_DRKWAT")
    raw_data = sspi_raw_api_data.fetch_raw_data(source_info)
    cleaned_data = clean_wb_data(raw_data, "WB_DRKWAT", "Percent")
    sspi_clean_api_data.insert_many(cleaned_data)
    sspi_metadata.record_dataset_range(cleaned_data, "WB_DRKWAT")
    return parse_json(cleaned_data)