from sspi_flask_app.api.datasource.unsdg import collect_sdg_indicator_data, extract_sdg, filter_sdg
from sspi_flask_app.models.database import (
    sspi_raw_api_data,
    sspi_clean_api_data,
    sspi_metadata
)
from sspi_flask_app.api.resources.utilities import parse_json
from sspi_flask_app.api.core.datasets import dataset_collector, dataset_cleaner


@dataset_collector("UNSDG_RDFUND")
def collect_unsdg_rdfund(**kwargs):
    yield from collect_sdg_indicator_data("9.5.1", **kwargs)
    yield from collect_sdg_indicator_data("9.5.2", **kwargs)


@dataset_cleaner("UNSDG_RDFUND")
def clean_unsdg_rdfund():
    sspi_clean_api_data.delete_many({"DatasetCode": "UNSDG_RDFUND"})
    source_info = sspi_metadata.get_source_info("UNSDG_RDFUND")
    raw_data = sspi_raw_api_data.fetch_raw_data(source_info)
    extracted_data = extract_sdg(raw_data)
    intermediate_map = {
        "GB_XPD_RSDV": "GVTRDP",
        "GB_POP_SCIERD": "NRSRCH"
    }
    cleaned_data = filter_sdg(
        extracted_data, intermediate_map, activity="TOTAL"
    )
    for obs in cleaned_data:
        obs["DatasetCode"] = "UNSDG_RDFUND"
    sspi_clean_api_data.insert_many(cleaned_data)
    sspi_metadata.record_dataset_range(cleaned_data, "UNSDG_RDFUND")
    return parse_json(cleaned_data)