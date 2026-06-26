###########################################################
# Documentation: datasets/who/who_cstunt/documentation.md #
###########################################################
from sspi_flask_app.api.datasource.who import collect_who_data, clean_who_data
from sspi_flask_app.models.database import (
    sspi_raw_api_data,
    sspi_clean_api_data,
    sspi_metadata
)
from sspi_flask_app.api.resources.utilities import parse_json
from sspi_flask_app.api.core.datasets import dataset_collector, dataset_cleaner


@dataset_collector("WHO_CSTUNT")
def collect_gho_cstunt(**kwargs):
    yield from collect_who_data("NUTSTUNTINGPREV", **kwargs)


@dataset_cleaner("WHO_CSTUNT")
def clean_gho_cstunt():
    sspi_clean_api_data.delete_many({"DatasetCode": "WHO_CSTUNT"})
    source_info = sspi_metadata.get_source_info("WHO_CSTUNT")
    raw_data = sspi_raw_api_data.fetch_raw_data(source_info)
    unit = "Percent"
    description = "Estimated prevalence of stunting in children under 5 (%)."
    # GHO disaggregates NUTSTUNTINGPREV by SEX; keep the both-sexes total.
    cleaned_data = clean_who_data(
        raw_data, "WHO_CSTUNT", unit, description,
        dimension_values={"Dim1": "SEX_BTSX"},
    )
    sspi_clean_api_data.insert_many(cleaned_data)
    sspi_metadata.record_dataset_range(cleaned_data, "WHO_CSTUNT")
    return parse_json(cleaned_data)
