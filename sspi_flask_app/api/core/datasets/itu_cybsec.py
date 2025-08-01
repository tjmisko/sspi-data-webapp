from sspi_flask_app.api.datasource.itu import load_itu_data_from_local_transcription, clean_itu_data
from sspi_flask_app.models.database import (
    sspi_raw_api_data,
    sspi_clean_api_data,
    sspi_metadata
)
from sspi_flask_app.api.resources.utilities import parse_json
from sspi_flask_app.api.core.datasets import dataset_collector, dataset_cleaner
import json


@dataset_collector("ITU_CYBSEC")
def collect_itu_cybsec(**kwargs):
    yield from load_itu_data_from_local_transcription(**kwargs)


@dataset_cleaner("ITU_CYBSEC")
def clean_itu_cybsec():
    sspi_clean_api_data.delete_many({"DatasetCode": "ITU_CYBSEC"})
    source_info = sspi_metadata.get_source_info("ITU_CYBSEC")
    raw_data = sspi_raw_api_data.fetch_raw_data(source_info)
    cleaned_df = clean_itu_data(raw_data)
    cleaned_data = json.loads(str(cleaned_df.to_json(orient="records")))
    # Add DatasetCode to each observation
    for obs in cleaned_data:
        obs["DatasetCode"] = "ITU_CYBSEC"
    sspi_clean_api_data.insert_many(cleaned_data)
    return parse_json(cleaned_data)