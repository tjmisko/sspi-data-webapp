from sspi_flask_app.api.datasource.unsdg import collect_sdg_indicator_data, extract_sdg, filter_sdg
from sspi_flask_app.models.database import (
    sspi_raw_api_data,
    sspi_clean_api_data,
    sspi_metadata
)
from sspi_flask_app.api.resources.utilities import parse_json
from sspi_flask_app.api.core.datasets import dataset_collector, dataset_cleaner


@dataset_collector("UNSDG_LABMKT_PROG")
def collect_unsdg_labmkt_prog(**kwargs):
    yield from collect_sdg_indicator_data("1.3.1", **kwargs)


@dataset_cleaner("UNSDG_LABMKT_PROG")
def clean_unsdg_labmkt_prog():
    sspi_clean_api_data.delete_many({"DatasetCode": "UNSDG_LABMKT_PROG"})
    source_info = sspi_metadata.get_source_info("UNSDG_LABMKT_PROG")
    raw_data = sspi_raw_api_data.fetch_raw_data(source_info)
    extracted_data = extract_sdg(raw_data)
    cleaned_data = filter_sdg(
        extracted_data, {"SI_COV_LMKT": "UNSDG_LABMKT_PROG"},
    )
    for obs in cleaned_data:
        obs["DatasetCode"] = "UNSDG_LABMKT_PROG"
    sspi_clean_api_data.insert_many(cleaned_data)
    sspi_metadata.record_dataset_range(cleaned_data, "UNSDG_LABMKT_PROG")
    return parse_json(cleaned_data)
