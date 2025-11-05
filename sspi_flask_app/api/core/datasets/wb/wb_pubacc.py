#########################################################
# Documentation: datasets/wb/wb_pubacc/documentation.md #
#########################################################
from sspi_flask_app.api.datasource.worldbank import collect_wb_data, clean_wb_data
from sspi_flask_app.api.core.datasets import dataset_collector, dataset_cleaner
from sspi_flask_app.models.database import sspi_raw_api_data, sspi_clean_api_data, sspi_metadata
from sspi_flask_app.api.resources.utilities import parse_json

@dataset_collector("WB_PUBACC")
def collect_wb_pubacc(**kwargs):
    yield from collect_wb_data("FX.OWN.TOTL.ZS", **kwargs)


@dataset_cleaner("WB_PUBACC")
def clean_wb_pubacc():
    sspi_clean_api_data.delete_many({"DatasetCode": "WB_PUBACC"})
    source_info = sspi_metadata.get_source_info("WB_PUBACC")
    raw_data = sspi_raw_api_data.fetch_raw_data(source_info)
    cleaned_data = clean_wb_data(raw_data, "WB_PUBACC", "Percent")
    sspi_clean_api_data.insert_many(cleaned_data)
    sspi_metadata.record_dataset_range(cleaned_data, "WB_PUBACC")
    return parse_json(cleaned_data)