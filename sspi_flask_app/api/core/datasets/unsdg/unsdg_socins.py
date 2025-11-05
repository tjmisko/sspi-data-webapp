###############################################################
# Documentation: datasets/unsdg/unsdg_socins/documentation.md #
###############################################################
from sspi_flask_app.api.datasource.unsdg import collect_sdg_indicator_data, extract_sdg, filter_sdg
from sspi_flask_app.models.database import (
    sspi_raw_api_data,
    sspi_clean_api_data,
    sspi_metadata
)
from sspi_flask_app.api.resources.utilities import parse_json
from sspi_flask_app.api.core.datasets import dataset_collector, dataset_cleaner


@dataset_collector("UNSDG_SOCINS")
def collect_unsdg_socins(**kwargs):
    yield from collect_sdg_indicator_data("1.3.1", **kwargs)


@dataset_cleaner("UNSDG_SOCINS")
def clean_unsdg_socins():
    sspi_clean_api_data.delete_many({"DatasetCode": "UNSDG_SOCINS"})
    source_info = sspi_metadata.get_source_info("UNSDG_SOCINS")
    raw_data = sspi_raw_api_data.fetch_raw_data(source_info)
    extracted_data = extract_sdg(raw_data)
    cleaned_data = filter_sdg(
        extracted_data, {"SI_COV_SOCINS": "UNSDG_SOCINS"}, sex="BOTHSEX",
    )
    for obs in cleaned_data:
        obs["DatasetCode"] = "UNSDG_SOCINS"
    sspi_clean_api_data.insert_many(cleaned_data)
    sspi_metadata.record_dataset_range(cleaned_data, "UNSDG_SOCINS")
    return parse_json(cleaned_data)
