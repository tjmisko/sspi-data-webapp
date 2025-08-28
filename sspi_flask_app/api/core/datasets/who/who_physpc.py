from sspi_flask_app.api.datasource.who import collect_who_data, clean_who_data
from sspi_flask_app.models.database import (
    sspi_raw_api_data,
    sspi_clean_api_data,
    sspi_metadata
)
from sspi_flask_app.api.resources.utilities import parse_json
from sspi_flask_app.api.core.datasets import dataset_collector, dataset_cleaner


@dataset_collector("WHO_PHYSPC")
def collect_who_physpc(**kwargs):
    yield from collect_who_data("HWF_0001", **kwargs)


@dataset_cleaner("WHO_PHYSPC")
def clean_who_physpc():
    sspi_clean_api_data.delete_many({"DatasetCode": "WHO_PHYSPC"})
    source_info = sspi_metadata.get_source_info("WHO_PHYSPC")
    raw_data = sspi_raw_api_data.fetch_raw_data(source_info)
    unit = "Doctors per 10000"
    description = (
        "Number of medical doctors (physicians), both generalists and "
        "specialists, expressed per 10,000 people."
    )
    cleaned_data = clean_who_data(raw_data, "WHO_PHYSPC", unit, description)
    sspi_clean_api_data.insert_many(cleaned_data)
    sspi_metadata.record_dataset_range(cleaned_data, "WHO_PHYSPC")
    return parse_json(cleaned_data)