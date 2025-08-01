from sspi_flask_app.api.datasource.fsi import collect_fsi_data, clean_fsi_data
from sspi_flask_app.models.database import (
    sspi_raw_api_data,
    sspi_clean_api_data,
    sspi_metadata
)
from sspi_flask_app.api.resources.utilities import parse_json
from sspi_flask_app.api.core.datasets import dataset_collector, dataset_cleaner


@dataset_collector("FSI_SECAPP")
def collect_fsi_secapp(**kwargs):
    yield from collect_fsi_data("SECAPP", **kwargs)


@dataset_cleaner("FSI_SECAPP")
def clean_fsi_secapp():
    sspi_clean_api_data.delete_many({"DatasetCode": "FSI_SECAPP"})
    source_info = sspi_metadata.get_source_info("FSI_SECAPP")
    raw_data = sspi_raw_api_data.fetch_raw_data(source_info)
    description = (
        "The Security Apparatus is a component of the Fragile State Index, "
        "which considers the security threats to a state such as bombings, "
        "attacks/battle-related deaths, rebel movements, mutinies, coups, or "
        "terrorism. It is an index scored between 0 and 10."
    )
    cleaned_data = clean_fsi_data(raw_data, "FSI_SECAPP", "Index", description)
    sspi_clean_api_data.insert_many(cleaned_data)
    return parse_json(cleaned_data)