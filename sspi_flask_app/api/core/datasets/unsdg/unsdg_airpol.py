###############################################################
# Documentation: datasets/unsdg/unsdg_airpol/documentation.md #
###############################################################
from sspi_flask_app.api.datasource.unsdg import collect_sdg_indicator_data, extract_sdg, filter_sdg
from sspi_flask_app.api.core.datasets import dataset_collector, dataset_cleaner
from sspi_flask_app.models.database import sspi_raw_api_data, sspi_clean_api_data, sspi_metadata
from sspi_flask_app.api.resources.utilities import parse_json

@dataset_collector("UNSDG_AIRPOL")
def collect_unsdg_airpol(**kwargs):
    yield from collect_sdg_indicator_data("11.6.2", **kwargs)


@dataset_cleaner("UNSDG_AIRPOL")
def clean_unsdg_airpol():
    sspi_clean_api_data.delete_many({"DatasetCode": "UNSDG_AIRPOL"})
    source_info = sspi_metadata.get_source_info("UNSDG_AIRPOL")
    raw_data = sspi_raw_api_data.fetch_raw_data(source_info)
    extracted_airpol = extract_sdg(raw_data)
    filtered_airpol = filter_sdg(
        extracted_airpol, {"EN_ATM_PM25": "UNSDG_AIRPOL"},
        location="ALLAREA"
    )
    sspi_clean_api_data.insert_many(filtered_airpol)
    sspi_metadata.record_dataset_range(filtered_airpol, "UNSDG_AIRPOL")
    return parse_json(filtered_airpol)