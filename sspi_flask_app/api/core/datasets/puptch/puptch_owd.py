## itu_cybsec.py is the indicator that opens collects and clean the csv files
## import the puptch cleaner from puptch for csv file in the line below
from sspi_flask_app.api.datasource.puptch import collect_puptch_csv_data
from sspi_flask_app.models.database import sspi_raw_api_data, sspi_clean_api_data, sspi_metadata
from sspi_flask_app.api.resources.utilities import parse_json
from sspi_flask_app.api.core.datasets import dataset_collector, dataset_cleaner
import json


@dataset_collector("ITU_CYBSEC")
def collect_itu_cybsec(**kwargs):
    yield from collect_puptch_csv_data(**kwargs)
    