from sspi_flask_app.api.datasource.who import collect_who_data, clean_who_data
from sspi_flask_app.models.database import (
    sspi_raw_api_data,
    sspi_clean_api_data,
    sspi_metadata
)
from sspi_flask_app.api.resources.utilities import parse_json
from sspi_flask_app.api.core.datasets import dataset_collector, dataset_cleaner


@dataset_collector("WHO_ATBRTH")
def collect_who_atbrth(**kwargs):
    yield from collect_who_data("MDG_0000000025", **kwargs)


@dataset_cleaner("WHO_ATBRTH")
def clean_who_atbrth():
    sspi_clean_api_data.delete_many({"DatasetCode": "WHO_ATBRTH"})
    source_info = sspi_metadata.get_source_info("WHO_ATBRTH")
    raw_data = sspi_raw_api_data.fetch_raw_data(source_info)
    description = (
        "The proportion of births attended by trained and/or skilled "
        "health personnel"
    )
    cleaned_data = clean_who_data(raw_data, "WHO_ATBRTH", "Percent", description)
    sspi_clean_api_data.insert_many(cleaned_data)
    sspi_metadata.record_dataset_range(cleaned_data, "WHO_ATBRTH")
    return parse_json(cleaned_data)
