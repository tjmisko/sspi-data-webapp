import pandas as pd
import requests
import zipfile
import json
import re
from io import BytesIO, StringIO
from sspi_flask_app.models.database import sspi_raw_api_data


def collect_epi_data(epi_indicator_code, **kwargs):
    url = "https://epi.yale.edu/downloads/epi2024indicators.zip"
    res = requests.get(url)
    if res.status_code != 200:
        err = f"(HTTP Error {res.status_code})"
        yield "Failed to fetch data from source" + err
        return
    with zipfile.ZipFile(BytesIO(res.content)) as z:
        for f in z.namelist():
            if "__MACOSX" in f:
                continue
            if epi_indicator_code in f:
                with z.open(f) as data:
                    csv_string = data.read().decode("utf-8")
                    source_info = {
                        "OrganizationName": "Environmental Performance Index",
                        "OrganizationCode": "EPI",
                        "OrganizationSeriesCode": epi_indicator_code,
                        "BaseURL": url,
                        "URL": url
                    }
                    sspi_raw_api_data.raw_insert_one(
                        csv_string, source_info, **kwargs
                    )
    yield f"Collection complete for EPI Indicator {epi_indicator_code}\n"

def parse_epi_csv(raw_csv_string: str, dataset_code: str) -> list[dict]:
    csv_virtual_file = StringIO(raw_csv_string)
    EPI_raw = pd.read_csv(csv_virtual_file)
    EPI_raw = EPI_raw.drop(columns=['code', 'country'])
    EPI_raw = EPI_raw.rename(columns={'iso': 'CountryCode'})
    EPI_long = EPI_raw.melt(
        id_vars=['CountryCode'],
        var_name='YearString',
        value_name='Value'
    )
    EPI_long["Year"] = [
        re.search(r"\d{4}", s).group(0)
        for s in EPI_long["YearString"]
    ]
    EPI_long["Year"] = pd.to_numeric(EPI_long["Year"], errors='coerce')
    EPI_long.drop(columns=['YearString'], inplace=True)
    EPI_long.drop(EPI_long[EPI_long['Value'] < 0].index.tolist(), inplace=True)
    EPI_long.drop(EPI_long[EPI_long['Value'].isna()].index.tolist(), inplace=True)
    EPI_long['DatasetCode'] = dataset_code
    EPI_long['Unit'] = 'Index'
    return json.loads(str(EPI_long.to_json(orient="records")))

