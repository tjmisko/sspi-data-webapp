
from sspi_flask_app.api.datasource.worldbank import collect_wb_data, clean_wb_data
from sspi_flask_app.api.core.datasets import dataset_collector, dataset_cleaner
from sspi_flask_app.models.database import sspi_raw_api_data, sspi_clean_api_data, sspi_metadata

@dataset_collector("WB_RAILPC")
def collect_wb_railpc(**kwargs):
    yield from collect_wb_data("IS.RRS.PASG.KM", **kwargs)

@dataset_cleaner("WB_RAILPC")
def clean_wb_railpc():
    sspi_clean_api_data.delete_many({"DatasetCode": "WB_RAILPC"})
    source_info = sspi_metadata.get_source_info("WB_RAILPC")
    raw_data = sspi_raw_api_data.fetch_raw_data(source_info)
    wb_railpc = clean_wb_data(raw_data, "WB_RAILPC", "Passenger-Kilometers (million)")
    count = sspi_clean_api_data.insert_many(wb_railpc)
    sspi_metadata.record_dataset_range(wb_railpc, "WB_RAILPC")
    return wb_railpc
