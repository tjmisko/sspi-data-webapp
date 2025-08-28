from sspi_flask_app.api.datasource.unsdg import collect_sdg_indicator_data, extract_sdg, filter_sdg
from sspi_flask_app.models.database import (
    sspi_raw_api_data,
    sspi_clean_api_data,
    sspi_metadata
)
from sspi_flask_app.api.resources.utilities import parse_json
from sspi_flask_app.api.core.datasets import dataset_collector, dataset_cleaner


@dataset_collector("UNSDG_FAMPLN")
def collect_unsdg_fampln(**kwargs):
    yield from collect_sdg_indicator_data("3.7.1", **kwargs)


@dataset_cleaner("UNSDG_FAMPLN")
def clean_unsdg_fampln():
    sspi_clean_api_data.delete_many({"DatasetCode": "UNSDG_FAMPLN"})
    source_info = sspi_metadata.get_source_info("UNSDG_FAMPLN")
    raw_data = sspi_raw_api_data.fetch_raw_data(source_info)
    extracted_data = extract_sdg(raw_data)
    cleaned_data = filter_sdg(
        extracted_data, {"SH_FPL_MTMM": "FAMPLN"},
    )
    for obs in cleaned_data:
        obs["DatasetCode"] = "UNSDG_FAMPLN"
    sspi_clean_api_data.insert_many(cleaned_data)
    sspi_metadata.record_dataset_range(cleaned_data, "UNSDG_FAMPLN")
    return parse_json(cleaned_data)