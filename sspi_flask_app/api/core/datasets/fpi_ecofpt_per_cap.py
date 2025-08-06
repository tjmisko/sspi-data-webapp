from sspi_flask_app.api.datasource.fpi import collect_fpi_data, clean_fpi_data
from sspi_flask_app.api.core.datasets import dataset_collector, dataset_cleaner
from sspi_flask_app.models.database import sspi_raw_api_data, sspi_clean_api_data, sspi_metadata
from sspi_flask_app.api.resources.utilities import parse_json


@dataset_collector("FPI_ECOFPT_PER_CAP")
def collect_fpi_ecofpt_per_cap(**kwargs):
    yield from collect_fpi_data("EFCpc", **kwargs)


@dataset_cleaner("FPI_ECOFPT_PER_CAP")
def clean_fpi_ecofpt_per_cap():
    sspi_clean_api_data.delete_many({"DatasetCode": "FPI_ECOFPT_PER_CAP"})
    source_info = sspi_metadata.get_source_info("FPI_ECOFPT_PER_CAP")
    raw_data = sspi_raw_api_data.fetch_raw_data(source_info)
    description = "Ecological Footprint of consumption in global hectares (gha) divided by population"
    cleaned_data = clean_fpi_data(raw_data, "FPI_ECOFPT_PER_CAP", "gha per capita", description)
    sspi_clean_api_data.insert_many(cleaned_data)
    return parse_json(cleaned_data)