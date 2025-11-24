##########################################################
# Documentation: datasets/wb/wb_landar/documentation.md #
##########################################################
from sspi_flask_app.api.datasource.worldbank import collect_wb_data, clean_wb_data
from sspi_flask_app.api.core.datasets import dataset_collector, dataset_cleaner
from sspi_flask_app.models.database import sspi_raw_api_data, sspi_clean_api_data, sspi_metadata
from sspi_flask_app.api.resources.utilities import parse_json

@dataset_collector("WB_LANDAR")
def collect_wb_landar(**kwargs):
    yield from collect_wb_data("AG.LND.TOTL.K2", **kwargs)


@dataset_cleaner("WB_LANDAR")
def clean_wb_landar():
    sspi_clean_api_data.delete_many({"DatasetCode": "WB_LANDAR"})
    source_info = sspi_metadata.get_source_info("WB_LANDAR")
    raw_data = sspi_raw_api_data.fetch_raw_data(source_info)
    cleaned_data = clean_wb_data(raw_data, "WB_LANDAR", unit="Square Kilometers")
    sspi_clean_api_data.insert_many(cleaned_data)
    sspi_metadata.record_dataset_range(cleaned_data, "WB_LANDAR")
    return parse_json(cleaned_data)
