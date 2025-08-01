import json
import pandas as pd
from io import StringIO
from sspi_flask_app.api.datasource.ilo import collect_ilo_data
from sspi_flask_app.api.core.datasets import dataset_collector, dataset_cleaner
from sspi_flask_app.models.database import sspi_raw_api_data, sspi_clean_api_data, sspi_metadata
from sspi_flask_app.api.resources.utilities import parse_json

@dataset_collector("ILO_COLBAR")
def collect_ilo_colbar(**kwargs):
    url_params = ["startPeriod=1990-01-01", "endPeriod=2024-12-31"]
    yield from collect_ilo_data(
        "DF_ILR_CBCT_NOC_RT", URLParams=url_params, **kwargs
    )


@dataset_cleaner("ILO_COLBAR")
def clean_ilo_colbar():
    sspi_clean_api_data.delete_many({"DatasetCode": "ILO_COLBAR"})
    source_info = sspi_metadata.get_source_info("ILO_COLBAR")
    raw_data = sspi_raw_api_data.fetch_raw_data(source_info)
    csv_virtual_file = StringIO(raw_data[0]["Raw"])
    colbar_raw = pd.read_csv(csv_virtual_file)
    colbar_raw = colbar_raw[["REF_AREA", "TIME_PERIOD", "UNIT_MEASURE", "OBS_VALUE"]]
    colbar_raw = colbar_raw.rename(
        columns={
            "REF_AREA": "CountryCode",
            "TIME_PERIOD": "Year",
            "OBS_VALUE": "Value",
            "UNIT_MEASURE": "Unit",
        }
    )
    colbar_raw["DatasetCode"] = "ILO_COLBAR"
    colbar_raw["Unit"] = "Proportion"
    obs_list = json.loads(str(colbar_raw.to_json(orient="records")))
    sspi_clean_api_data.insert_many(obs_list)
    return parse_json(obs_list)