from sspi_flask_app.api.datasource.worldbank import collect_wb_data, clean_wb_data
from sspi_flask_app.models.database import (
    sspi_raw_api_data,
    sspi_clean_api_data,
    sspi_metadata
)
from sspi_flask_app.api.resources.utilities import parse_json
from sspi_flask_app.api.core.datasets import dataset_collector, dataset_cleaner


@dataset_collector("WB_INTRNT")
def collect_wb_intrnt(**kwargs):
    yield from collect_wb_data("IT.NET.USER.ZS", **kwargs)


@dataset_cleaner("WB_INTRNT")
def clean_wb_intrnt():
    sspi_clean_api_data.delete_many({"DatasetCode": "WB_INTRNT"})
    source_info = sspi_metadata.get_source_info("WB_INTRNT")
    raw_data = sspi_raw_api_data.fetch_raw_data(source_info)
    cleaned_data = clean_wb_data(raw_data, "WB_INTRNT", "Percent")
    sspi_clean_api_data.insert_many(cleaned_data)
    sspi_metadata.record_dataset_range(cleaned_data, "WB_INTRNT")
    return parse_json(cleaned_data)