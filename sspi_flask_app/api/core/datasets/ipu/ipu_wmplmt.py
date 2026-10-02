#############################################################
# Documentation: datasets/ipu/ipu_wmplmt/documentation.md   #
#############################################################
from sspi_flask_app.api.datasource.worldbank import collect_wb_data, clean_wb_data
from sspi_flask_app.api.core.datasets import dataset_collector, dataset_cleaner
from sspi_flask_app.models.database import sspi_raw_api_data, sspi_clean_api_data, sspi_metadata
from sspi_flask_app.api.resources.utilities import parse_json

# SG.GEN.PARL.ZS is Inter-Parliamentary Union data redistributed through the
# World Bank World Development Indicators API.


@dataset_collector("IPU_WMPLMT")
def collect_ipu_wmplmt(**kwargs):
    yield from collect_wb_data(
        "SG.GEN.PARL.ZS",
        organization_code="IPU",
        organization_name="Inter-Parliamentary Union",
        **kwargs
    )


@dataset_cleaner("IPU_WMPLMT")
def clean_ipu_wmplmt():
    sspi_clean_api_data.delete_many({"DatasetCode": "IPU_WMPLMT"})
    source_info = sspi_metadata.get_source_info("IPU_WMPLMT")
    raw_data = sspi_raw_api_data.fetch_raw_data(source_info)
    cleaned_data = clean_wb_data(raw_data, "IPU_WMPLMT", "% of parliamentary seats")
    sspi_clean_api_data.insert_many(cleaned_data)
    sspi_metadata.record_dataset_range(cleaned_data, "IPU_WMPLMT")
    return parse_json(cleaned_data)
