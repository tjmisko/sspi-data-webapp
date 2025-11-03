#########################################################
# Documentation: datasets/wb/wb_railln/documentation.md #
#########################################################

from sspi_flask_app.api.datasource.worldbank import collect_wb_data, clean_wb_data
from sspi_flask_app.api.core.datasets import dataset_collector, dataset_cleaner
from sspi_flask_app.models.database import sspi_raw_api_data, sspi_clean_api_data, sspi_metadata

@dataset_collector("WB_RAILLN")
def collect_wb_railln(**kwargs):
    yield from collect_wb_data("IS.RRS.TOTL.KM", **kwargs)

@dataset_cleaner("WB_RAILLN")
def clean_wb_railln():
    sspi_clean_api_data.delete_many({"DatasetCode": "WB_RAILLN"})
    source_info = sspi_metadata.get_source_info("WB_RAILLN")
    raw_data = sspi_raw_api_data.fetch_raw_data(source_info)
    wb_railln = clean_wb_data(raw_data, "WB_RAILLN", "Kilometers")
    count = sspi_clean_api_data.insert_many(wb_railln)
    sspi_metadata.record_dataset_range(wb_railln, "WB_RAILLN")
    return wb_railln
