## itu_cybsec.py is the indicator that opens collects and clean the csv files
## import the puptch cleaner from puptch for csv file in the line below
from sspi_flask_app.api.datasource.puptch import collect_puptch_csv_data, clean_puptch_csv_data
from sspi_flask_app.models.database import sspi_raw_api_data, sspi_clean_api_data, sspi_metadata
from sspi_flask_app.api.resources.utilities import parse_json
from sspi_flask_app.api.core.datasets import dataset_collector, dataset_cleaner
import json


@dataset_collector("PUPTCH_OWD")
def collect_puptch_owd(**kwargs):
    yield from collect_puptch_csv_data(**kwargs)


@dataset_cleaner("PUPTCH_OWD")
def clean_puptch_owd():
    DatasetCode = "PUPTCH_OWD"
    sspi_clean_api_data.delete_many({"DatasetCode": DatasetCode})
    source_info = sspi_metadata.get_source_info("PUPTCH_OWD")
    raw_data = sspi_raw_api_data.fetch_raw_data(source_info)
    unit = 'average'
    detail = sspi_metadata.get_dataset_detail(DatasetCode)
    if not detail:
        raise ValueError(f"Dataset code PUPTCH_OWD not found in metadata.")
    description = detail['Description']

    cleaned_data_json = clean_puptch_csv_data(raw_data, DatasetCode, unit, description)
    

    sspi_clean_api_data.insert_many(cleaned_data_json)
    sspi_metadata.record_dataset_range(cleaned_data_json, DatasetCode)
    return cleaned_data_json
