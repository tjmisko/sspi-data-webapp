from sspi_flask_app.api.datasource.worldbank import collect_wb_data, clean_wb_data
from sspi_flask_app.models.database import (
    sspi_raw_api_data,
    sspi_clean_api_data,
    sspi_metadata
)
from sspi_flask_app.api.resources.utilities import parse_json
from sspi_flask_app.api.core.datasets import dataset_collector, dataset_cleaner


@dataset_collector("WB_AVELEC")
def collect_wb_avelec(**kwargs):
    yield from collect_wb_data("EG.ELC.ACCS.ZS", **kwargs)


@dataset_cleaner("WB_AVELEC")
def clean_wb_avelec():
    sspi_clean_api_data.delete_many({"DatasetCode": "WB_AVELEC"})
    source_info = sspi_metadata.get_source_info("WB_AVELEC")
    raw_data = sspi_raw_api_data.fetch_raw_data(source_info)
    cleaned_data = clean_wb_data(raw_data, "WB_AVELEC", "Percent")
    # Remove unnecessary fields for intermediate use
    for d in cleaned_data:
        d.pop("Description", None)
        d.pop("IndicatorCode", None)
    sspi_clean_api_data.insert_many(cleaned_data)
    sspi_metadata.record_dataset_range(cleaned_data, "WB_AVELEC")
    return parse_json(cleaned_data)