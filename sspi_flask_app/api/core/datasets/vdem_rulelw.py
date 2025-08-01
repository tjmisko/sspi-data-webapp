from sspi_flask_app.api.datasource.vdem import collect_vdem_data
from sspi_flask_app.models.database import (
    sspi_raw_api_data,
    sspi_clean_api_data,
    sspi_metadata
)
from sspi_flask_app.api.resources.utilities import parse_json
from sspi_flask_app.api.core.datasets import dataset_collector, dataset_cleaner
from datetime import datetime
from io import StringIO
import pandas as pd
import json


@dataset_collector("VDEM_RULELW")
def collect_vdem_rulelw(**kwargs):
    yield from collect_vdem_data(**kwargs)


@dataset_cleaner("VDEM_RULELW")
def clean_vdem_rulelw():
    sspi_clean_api_data.delete_many({"DatasetCode": "VDEM_RULELW"})
    source_info = sspi_metadata.get_source_info("VDEM_RULELW")
    raw_data = sspi_raw_api_data.fetch_raw_data(source_info)
    df = pd.read_csv(StringIO(raw_data[0]["Raw"]))
    filtered_df = df[['country_text_id', 'year', 'v2x_rule']]
    current_year = datetime.now().year
    filtered_df = filtered_df[(filtered_df["year"] > 1990) & (filtered_df["year"] < current_year)]
    obs_list = json.loads(str(filtered_df.to_json(orient='records')))
    cleaned_data = []
    for obs in obs_list:
        if obs["v2x_rule"] is None:
            continue
        cleaned_data.append({
            "DatasetCode": "VDEM_RULELW",
            "CountryCode": obs["country_text_id"],
            "Year": obs["year"],
            "Value": obs["v2x_rule"],
            "Unit": "Index"
        })
    sspi_clean_api_data.insert_many(cleaned_data)
    return parse_json(cleaned_data)