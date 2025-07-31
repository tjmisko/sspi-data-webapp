from sspi_flask_app.api.datasource.epi import collect_epi_data, parse_epi_csv
from sspi_flask_app.api.core.datasets import dataset_collector, dataset_cleaner
from sspi_flask_app.models.database import sspi_raw_api_data, sspi_clean_api_data, sspi_metadata
from sspi_flask_app.api.resources.utilities import parse_json

@dataset_collector("EPI_NITROG")
def collect_epi_nitrog(**kwargs):
    yield from collect_epi_data("SNM", **kwargs)


@dataset_cleaner("EPI_NITROG")
def clean_epi_nitrog():
    sspi_clean_api_data.delete_many({"DatasetCode": "EPI_NITROG"})
    source_info = sspi_metadata.get_source_info("EPI_NITROG")
    raw_data = sspi_raw_api_data.fetch_raw_data(source_info)
    parsed_epi_data = parse_epi_csv(raw_data[0]["Raw"], "EPI_NITROG")
    sspi_clean_api_data.insert_many(parsed_epi_data)
    return parse_json(parsed_epi_data)
