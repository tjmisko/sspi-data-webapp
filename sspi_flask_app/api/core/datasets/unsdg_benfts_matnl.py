#####################################################################
# Documentation: datasets/unsdg/unsdg_benfts_matnl/documentation.md #
#####################################################################
from sspi_flask_app.api.datasource.unsdg import collect_sdg_indicator_data, extract_sdg, filter_sdg
from sspi_flask_app.models.database import (
    sspi_raw_api_data,
    sspi_clean_api_data,
    sspi_metadata
)
from sspi_flask_app.api.resources.utilities import parse_json
from sspi_flask_app.api.core.datasets import dataset_collector, dataset_cleaner


@dataset_collector("UNSDG_BENFTS_MATNL")
def collect_unsdg_benfts_matnl(**kwargs):
    yield from collect_sdg_indicator_data("1.3.1", **kwargs)


@dataset_cleaner("UNSDG_BENFTS_MATNL")
def clean_unsdg_benfts_matnl():
    sspi_clean_api_data.delete_many({"DatasetCode": "UNSDG_BENFTS_MATNL"})
    source_info = sspi_metadata.get_source_info("UNSDG_BENFTS_MATNL")
    raw_data = sspi_raw_api_data.fetch_raw_data(source_info)
    extracted_data = extract_sdg(raw_data)
    cleaned_data = filter_sdg(
        extracted_data, {"SI_COV_MATNL": "UNSDG_BENFTS_MATNL"},
    )
    for obs in cleaned_data:
        obs["DatasetCode"] = "UNSDG_BENFTS_MATNL"
    sspi_clean_api_data.insert_many(cleaned_data)
    sspi_metadata.record_dataset_range(cleaned_data, "UNSDG_BENFTS_MATNL")
    return parse_json(cleaned_data)
