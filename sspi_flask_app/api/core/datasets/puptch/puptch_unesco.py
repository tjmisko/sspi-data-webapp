## epi_nitrog.pyis the indicator that opens collects and clean the zip files
## import the puptch cleaner from puptch for zip file in the line below
from sspi_flask_app.api.datasource.puptch import collect_puptch_zip_data
from sspi_flask_app.api.core.datasets import dataset_collector, dataset_cleaner
from sspi_flask_app.models.database import sspi_raw_api_data, sspi_clean_api_data, sspi_metadata
from sspi_flask_app.api.resources.utilities import parse_json


@dataset_collector("EPI_NITROG")
def collect_epi_nitrog(**kwargs):
    yield from collect_puptch_zip_data(**kwargs)

