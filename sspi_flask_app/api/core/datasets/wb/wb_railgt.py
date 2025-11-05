#########################################################
# Documentation: datasets/wb/wb_railgt/documentation.md #
#########################################################

from sspi_flask_app.api.datasource.worldbank import collect_wb_data, clean_wb_data
from sspi_flask_app.api.core.datasets import dataset_collector, dataset_cleaner
from sspi_flask_app.models.database import sspi_raw_api_data, sspi_clean_api_data, sspi_metadata

@dataset_collector("WB_RAILGT")
def collect_wb_railgt(**kwargs):
    yield from collect_wb_data("IS.RRS.GOOD.MT.K6", **kwargs)

@dataset_cleaner("WB_RAILGT")
def clean_wb_railgt():
    sspi_clean_api_data.delete_many({"DatasetCode": "WB_RAILGT"})
    source_info = sspi_metadata.get_source_info("WB_RAILGT")
    raw_data = sspi_raw_api_data.fetch_raw_data(source_info)
    wb_railgt = clean_wb_data(raw_data, "WB_RAILGT", "Ton-Kilometers (million)")
    count = sspi_clean_api_data.insert_many(wb_railgt)
    sspi_metadata.record_dataset_range(wb_railgt, "WB_RAILGT")
    return wb_railgt
