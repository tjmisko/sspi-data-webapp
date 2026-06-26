###########################################################
# Documentation: datasets/who/who_fampln/documentation.md #
###########################################################
from sspi_flask_app.api.datasource.who import collect_who_data, clean_who_data
from sspi_flask_app.models.database import (
    sspi_raw_api_data,
    sspi_clean_api_data,
    sspi_metadata
)
from sspi_flask_app.api.resources.utilities import parse_json
from sspi_flask_app.api.core.datasets import dataset_collector, dataset_cleaner


@dataset_collector("WHO_FAMPLN")
def collect_who_fampln(**kwargs):
    yield from collect_who_data("SDGFPALL", **kwargs)


@dataset_cleaner("WHO_FAMPLN")
def clean_who_fampln():
    sspi_clean_api_data.delete_many({"DatasetCode": "WHO_FAMPLN"})
    source_info = sspi_metadata.get_source_info("WHO_FAMPLN")
    raw_data = sspi_raw_api_data.fetch_raw_data(source_info)
    unit = "Percent"
    description = (
        "Proportion of women of reproductive age (15-49 years) who have "
        "their need for family planning satisfied with modern methods (%)."
    )
    cleaned_data = clean_who_data(raw_data, "WHO_FAMPLN", unit, description)
    sspi_clean_api_data.insert_many(cleaned_data)
    sspi_metadata.record_dataset_range(cleaned_data, "WHO_FAMPLN")
    return parse_json(cleaned_data)
