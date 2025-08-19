from sspi_flask_app.api.datasource.ilo import collect_ilo_data
from sspi_flask_app.models.database import (
    sspi_raw_api_data,
    sspi_clean_api_data,
    sspi_metadata
)
from sspi_flask_app.api.resources.utilities import parse_json
from sspi_flask_app.api.core.datasets import dataset_collector, dataset_cleaner
from io import StringIO
import pandas as pd
import json


@dataset_collector("ILO_FATINJ")
def collect_ilo_fatinj(**kwargs):
    yield from collect_ilo_data("DF_SDG_F881_SEX_MIG_RT", **kwargs)


@dataset_cleaner("ILO_FATINJ")
def clean_ilo_fatinj():
    sspi_clean_api_data.delete_many({"DatasetCode": "ILO_FATINJ"})
    source_info = sspi_metadata.get_source_info("ILO_FATINJ")
    raw_data = sspi_raw_api_data.fetch_raw_data(source_info)
    csv_virtual_file = StringIO(raw_data[0]["Raw"])
    fatinj_raw = pd.read_csv(csv_virtual_file)
    fatinj_raw = fatinj_raw[fatinj_raw["SEX"] == "SEX_T"]
    fatinj_raw = fatinj_raw[["REF_AREA", "TIME_PERIOD", "UNIT_MEASURE", "OBS_VALUE"]]
    fatinj_raw = fatinj_raw.rename(
        columns={
            "REF_AREA": "CountryCode",
            "TIME_PERIOD": "Year",
            "OBS_VALUE": "Value",
            "UNIT_MEASURE": "Unit",
        }
    )
    fatinj_raw["DatasetCode"] = "ILO_FATINJ"
    fatinj_raw["Unit"] = "Rate per 100,000"
    fatinj_raw.dropna(subset=["Value"], inplace=True)
    cleaned_data = json.loads(str(fatinj_raw.to_json(orient="records")))
    sspi_clean_api_data.insert_many(cleaned_data)
    sspi_metadata.record_dataset_range(cleaned_data, "ILO_FATINJ")
    return parse_json(cleaned_data)