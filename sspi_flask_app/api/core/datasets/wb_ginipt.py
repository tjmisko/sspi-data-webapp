from sspi_flask_app.api.datasource.worldbank import collect_wb_data, clean_wb_data
from sspi_flask_app.api.core.datasets import dataset_collector, dataset_cleaner
from sspi_flask_app.models.database import sspi_raw_api_data, sspi_clean_api_data, sspi_metadata
from sspi_flask_app.api.resources.utilities import parse_json

@dataset_collector("WB_GINIPT")
def collect_wb_ginipt(**kwargs):
    yield from collect_wb_data("SI.POV.GINI", **kwargs)


@dataset_cleaner("WB_GINIPT")
def clean_wb_ginipt():
    sspi_clean_api_data.delete_many({"DatasetCode": "WB_GINIPT"})
    source_info = sspi_metadata.get_source_info("WB_GINIPT")
    raw_data = sspi_raw_api_data.fetch_raw_data(source_info)
    cleaned_data = clean_wb_data(raw_data, "WB_GINIPT", "GINI Coeffecient")
    sspi_clean_api_data.insert_many(cleaned_data)
    return parse_json(cleaned_data)