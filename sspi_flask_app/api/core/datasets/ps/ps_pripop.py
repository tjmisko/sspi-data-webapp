from sspi_flask_app.api.datasource.prisonstudies import collect_prison_studies_data, scrape_stored_pages_for_data
from sspi_flask_app.models.database import (
    sspi_raw_api_data,
    sspi_clean_api_data,
    sspi_metadata
)
from sspi_flask_app.api.resources.utilities import parse_json
from sspi_flask_app.api.core.datasets import dataset_collector, dataset_cleaner


@dataset_collector("PS_PRIPOP")
def collect_ps_pripop(**kwargs):
    yield from collect_prison_studies_data(**kwargs)


@dataset_cleaner("PS_PRIPOP")
def clean_ps_pripop():
    sspi_clean_api_data.delete_many({"DatasetCode": "PS_PRIPOP"})
    source_info = sspi_metadata.get_source_info("PS_PRIPOP")
    raw_data = sspi_raw_api_data.fetch_raw_data(source_info)
    cleaned_data, _ = scrape_stored_pages_for_data()
    # Add DatasetCode to each observation
    for obs in cleaned_data:
        obs["DatasetCode"] = "PS_PRIPOP"
    sspi_clean_api_data.insert_many(cleaned_data)
    sspi_metadata.record_dataset_range(cleaned_data, "PS_PRIPOP")
    return parse_json(cleaned_data)