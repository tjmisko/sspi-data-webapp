import json
import pandas as pd
from io import StringIO
from sspi_flask_app.api.datasource.ilo import collect_ilo_data
from sspi_flask_app.api.core.datasets import dataset_collector, dataset_cleaner
from sspi_flask_app.models.database import sspi_raw_api_data, sspi_clean_api_data, sspi_metadata
from sspi_flask_app.api.resources.utilities import parse_json

@dataset_collector("ILO_EMPLOY")
def collect_ilo_employ(**kwargs):
    yield from collect_ilo_data(
        "DF_EAP_DWAP_SEX_AGE_RT",
        QueryParams=".A...AGE_AGGREGATE_Y25-54",
        **kwargs
    )


@dataset_cleaner("ILO_EMPLOY")
def clean_ilo_employ():
    sspi_clean_api_data.delete_many({"DatasetCode": "ILO_EMPLOY"})
    source_info = sspi_metadata.get_source_info("ILO_EMPLOY")
    raw_data = sspi_raw_api_data.fetch_raw_data(source_info)
    csv_virtual_file = StringIO(raw_data[0]["Raw"])
    employ_raw = pd.read_csv(csv_virtual_file)
    employ_raw_f = employ_raw[['REF_AREA', 'TIME_PERIOD', 'MEASURE', 'SEX',
                               'UNIT_MEASURE', 'OBS_VALUE']]
    colmap_rename = {
        'REF_AREA': 'CountryCode',
        'TIME_PERIOD': 'Year',
        'OBS_VALUE': 'Value',
        'UNIT_MEASURE': 'Unit'
    }
    employ_raw_f = employ_raw_f[employ_raw_f['SEX'] == 'SEX_T']
    employ_raw_f = employ_raw_f.rename(columns=colmap_rename, errors="ignore")
    employ_raw_f['DatasetCode'] = 'ILO_EMPLOY'
    employ_raw_f['Unit'] = 'Rate'
    obs_list = json.loads(str(employ_raw_f.to_json(orient="records")))
    sspi_clean_api_data.insert_many(obs_list)
    return parse_json(obs_list)