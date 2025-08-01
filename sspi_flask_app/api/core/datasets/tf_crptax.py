from sspi_flask_app.api.datasource.taxfoundation import collect_tax_foundation_data, clean_tax_foundation
from sspi_flask_app.api.core.datasets import dataset_collector, dataset_cleaner
from sspi_flask_app.models.database import sspi_raw_api_data, sspi_clean_api_data, sspi_metadata
from sspi_flask_app.api.resources.utilities import parse_json

@dataset_collector("TF_CRPTAX")
def collect_tf_crptax(**kwargs):
    yield from collect_tax_foundation_data(**kwargs)


@dataset_cleaner("TF_CRPTAX")
def clean_tf_crptax():
    sspi_clean_api_data.delete_many({"DatasetCode": "TF_CRPTAX"})
    source_info = sspi_metadata.get_source_info("TF_CRPTAX")
    raw_data = sspi_raw_api_data.fetch_raw_data(source_info)
    cleaned_data = clean_tax_foundation(raw_data[0]["Raw"], "TF_CRPTAX", "Tax Rate", "Corporate Taxes")
    sspi_clean_api_data.insert_many(cleaned_data)
    return parse_json(cleaned_data)
