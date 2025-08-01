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


@dataset_collector("ILO_UNEMPL")
def collect_ilo_unempl(**kwargs):
    yield from collect_ilo_data("DF_SDG_0131_SEX_SOC_RT", **kwargs)


@dataset_cleaner("ILO_UNEMPL")
def clean_ilo_unempl():
    sspi_clean_api_data.delete_many({"DatasetCode": "ILO_UNEMPL"})
    source_info = sspi_metadata.get_source_info("ILO_UNEMPL")
    raw_data = sspi_raw_api_data.fetch_raw_data(source_info)
    csv_virtual_file = StringIO(raw_data[0]["Raw"])
    unempl_raw = pd.read_csv(csv_virtual_file)
    unempl_raw_f = unempl_raw[unempl_raw['SOC'] == 'SOC_CONTIG_UNE']
    unempl_raw_f = unempl_raw_f[['REF_AREA', 'TIME_PERIOD', 'UNIT_MEASURE', 'OBS_VALUE']]
    colmap_rename = {
        'REF_AREA': 'CountryCode',
        'TIME_PERIOD': 'Year',
        'OBS_VALUE': 'Value',
        'UNIT_MEASURE': 'Unit'
    }
    unempl_raw_f = unempl_raw_f.rename(columns=colmap_rename)
    unempl_raw_f['DatasetCode'] = 'ILO_UNEMPL'
    unempl_raw_f['Unit'] = 'Rate'
    cleaned_data = json.loads(str(unempl_raw_f.to_json(orient="records")))
    sspi_clean_api_data.insert_many(cleaned_data)
    return parse_json(cleaned_data)