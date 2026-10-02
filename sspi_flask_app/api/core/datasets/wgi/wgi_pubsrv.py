#############################################################
# Documentation: datasets/wgi/wgi_pubsrv/documentation.md   #
#############################################################
from sspi_flask_app.api.datasource.worldbank import collect_wb_data, clean_wb_data
from sspi_flask_app.api.core.datasets import dataset_collector, dataset_cleaner
from sspi_flask_app.models.database import sspi_raw_api_data, sspi_clean_api_data, sspi_metadata
from sspi_flask_app.api.resources.utilities import parse_json

# GOV_WGI_GE.EST is only resolvable inside World Bank source database 3
# (Worldwide Governance Indicators); without source=3 the API reports the
# indicator as not found.
WGI_WORLD_BANK_SOURCE_ID = 3


@dataset_collector("WGI_PUBSRV")
def collect_wgi_pubsrv(**kwargs):
    yield from collect_wb_data(
        "GOV_WGI_GE.EST",
        source=WGI_WORLD_BANK_SOURCE_ID,
        organization_code="WGI",
        organization_name="World Bank - Worldwide Governance Indicators",
        **kwargs
    )


@dataset_cleaner("WGI_PUBSRV")
def clean_wgi_pubsrv():
    sspi_clean_api_data.delete_many({"DatasetCode": "WGI_PUBSRV"})
    source_info = sspi_metadata.get_source_info("WGI_PUBSRV")
    raw_data = sspi_raw_api_data.fetch_raw_data(source_info)
    cleaned_data = clean_wb_data(
        raw_data, "WGI_PUBSRV", "Governance estimate (approx. -2.5 to +2.5)"
    )
    sspi_clean_api_data.insert_many(cleaned_data)
    sspi_metadata.record_dataset_range(cleaned_data, "WGI_PUBSRV")
    return parse_json(cleaned_data)
