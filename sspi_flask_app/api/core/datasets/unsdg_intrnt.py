from sspi_flask_app.api.datasource.unsdg import collect_sdg_indicator_data, extract_sdg, filter_sdg
from sspi_flask_app.models.database import (
    sspi_raw_api_data,
    sspi_clean_api_data,
    sspi_metadata
)
from sspi_flask_app.api.resources.utilities import parse_json
from sspi_flask_app.api.core.datasets import dataset_collector, dataset_cleaner


@dataset_collector("UNSDG_INTRNT")
def collect_unsdg_intrnt(**kwargs):
    yield from collect_sdg_indicator_data("17.6.1", **kwargs)


@dataset_cleaner("UNSDG_INTRNT")
def clean_unsdg_intrnt():
    sspi_clean_api_data.delete_many({"DatasetCode": "UNSDG_INTRNT"})
    source_info = sspi_metadata.get_source_info("UNSDG_INTRNT")
    raw_data = sspi_raw_api_data.fetch_raw_data(source_info)
    extracted_data = extract_sdg(raw_data)
    idcode_map = {"IT_NET_BBND": "QUINTR"}
    filtered_data = filter_sdg(
        extracted_data, idcode_map,
        type_of_speed="10MBPS"
    )
    for obs in filtered_data:
        obs["DatasetCode"] = "UNSDG_INTRNT"
    sspi_clean_api_data.insert_many(filtered_data)
    return parse_json(filtered_data)