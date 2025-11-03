###############################################################
# Documentation: datasets/unsdg/unsdg_nrgint/documentation.md #
###############################################################
from sspi_flask_app.api.datasource.unsdg import collect_sdg_indicator_data, extract_sdg, filter_sdg
from sspi_flask_app.models.database import (
    sspi_raw_api_data,
    sspi_clean_api_data,
    sspi_metadata
)
from sspi_flask_app.api.resources.utilities import parse_json
from sspi_flask_app.api.core.datasets import dataset_collector, dataset_cleaner


@dataset_collector("UNSDG_NRGINT")
def collect_unsdg_nrgint(**kwargs):
    yield from collect_sdg_indicator_data("7.3.1", **kwargs)


@dataset_cleaner("UNSDG_NRGINT")
def clean_unsdg_nrgint():
    sspi_clean_api_data.delete_many({"DatasetCode": "UNSDG_NRGINT"})
    source_info = sspi_metadata.get_source_info("UNSDG_NRGINT")
    raw_data = sspi_raw_api_data.fetch_raw_data(source_info)
    extracted_data = extract_sdg(raw_data)
    idcode_map = {"EG_EGY_PRIM": "UNSDG_NRGINT"}
    filtered_data = filter_sdg(
        extracted_data, idcode_map
    )
    for obs in filtered_data:
        obs["DatasetCode"] = "UNSDG_NRGINT"
    sspi_clean_api_data.insert_many(filtered_data)
    sspi_metadata.record_dataset_range(filtered_data, "UNSDG_NRGINT")
    return parse_json(filtered_data)
