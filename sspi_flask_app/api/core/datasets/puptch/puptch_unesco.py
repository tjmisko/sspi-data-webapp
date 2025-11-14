## epi_nitrog.pyis the indicator that opens collects and clean the zip files
## import the puptch cleaner from puptch for zip file in the line below
from sspi_flask_app.api.datasource.puptch import collect_puptch_zip_data, clean_puptch_zip_data
from sspi_flask_app.api.core.datasets import dataset_collector, dataset_cleaner
from sspi_flask_app.models.database import sspi_raw_api_data, sspi_clean_api_data, sspi_metadata
from sspi_flask_app.api.resources.utilities import parse_json


@dataset_collector("PUPTCH_UNESCO")
def collect_puptch_unesco(**kwargs):
    yield from collect_puptch_zip_data(**kwargs)


@dataset_cleaner("PUPTCH_UNESCO")
def clean_puptch_owd():
    DatasetCode = "PUPTCH_UNESCO"
    sspi_clean_api_data.delete_many({"DatasetCode": DatasetCode})
    source_info = sspi_metadata.get_source_info("PUPTCH_UNESCO")
    raw_data = sspi_raw_api_data.fetch_raw_data(source_info)
    unit = 'average'
    detail = sspi_metadata.get_dataset_detail(DatasetCode)
    if not detail:
        raise ValueError(f"Dataset code PUPTCH_UNESCO not found in metadata.")
    description = detail['Description']

    cleaned_data = clean_puptch_zip_data(raw_data, DatasetCode, unit, description)


    sspi_clean_api_data.insert_many(cleaned_data)
    sspi_metadata.record_dataset_range(cleaned_data, DatasetCode)
    return parse_json(cleaned_data)

