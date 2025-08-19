from sspi_flask_app.api.datasource.worldbank import collect_wb_data, clean_wb_data
from sspi_flask_app.api.core.datasets import dataset_collector, dataset_cleaner
from sspi_flask_app.models.database import sspi_raw_api_data, sspi_clean_api_data, sspi_metadata
from sspi_flask_app.api.resources.utilities import parse_json

@dataset_collector("WB_TAXREV")
def collect_wb_taxrev(**kwargs):
    yield from collect_wb_data("GC.TAX.TOTL.GD.ZS", **kwargs)


@dataset_cleaner("WB_TAXREV")
def clean_wb_taxrev():
    sspi_clean_api_data.delete_many({"DatasetCode": "WB_TAXREV"})
    source_info = sspi_metadata.get_source_info("WB_TAXREV")
    raw_data = sspi_raw_api_data.fetch_raw_data(source_info)
    cleaned_data = clean_wb_data(raw_data, "WB_TAXREV", "% of GDP")
    sspi_clean_api_data.insert_many(cleaned_data)
    sspi_metadata.record_dataset_range(cleaned_data, "WB_TAXREV")
    return parse_json(cleaned_data)