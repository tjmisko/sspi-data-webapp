import requests
import io
import zipfile
import pycountry
import bson
from io import StringIO
import pandas as pd
import csv
from sspi_flask_app.models.database import sspi_raw_api_data

from sspi_flask_app.api.resources.utilities import (parse_json)

MAXBITESIZE = 16790000


def collectWIDData(IndicatorCode, **kwargs):
    yield "Requesting WID data from source\n"
    res = requests.get("https://wid.world/bulk_download/wid_all_data.zip")
    res.raise_for_status()
    yield "Received WID data\n"
    zip_file = io.BytesIO(res.content)

    with zipfile.ZipFile(zip_file) as z:
        doc_index = 0
        for file_name in z.namelist():
            yield f"Processing {file_name}\n"
            with z.open(file_name) as f:
                raw = f.read().decode('utf-8')
                num_chunks = (len(raw) + MAXBITESIZE - 1) // MAXBITESIZE
                len_chunk = len(raw) / num_chunks
                file_name_fields = file_name.split(".")[0].split("_")
                if len(file_name_fields) != 3:
                    # Don't save state-level data
                    yield f"Skipping {file_name}\n"
                    continue
                dataset_type = file_name_fields[1]
                country_code_alpha2 = file_name_fields[2]
                country_code = ""

                try:
                    country_code = pycountry.countries.get(
                        alpha_2=country_code_alpha2).alpha_3
                except AttributeError:
                    country_code = ""
                if len(country_code) != 3:
                    # Don't save state-level data
                    continue

                for i in range(num_chunks - 1):
                    start = int(i * len_chunk)
                    end = int((i + 1) * len_chunk if i < num_chunks - 1 else len(raw))
                    chunk = raw[start:end]
                    observation = {
                    "SourceOrganization": "WID",
                    "SourceOrganizationName": "World Inequality Database",
                    "SourceOrganizationURL": "https://wid.world/",
                    "SourceOrganizationDownloadURL": "https://wid.world/bulk_download/wid_all_data.zip",
                    "DatasetName": file_name,
                    "CountryCode": country_code,
                    "DatasetDescription": f"World Inequality Database All {dataset_type} for {country_code}",
                    f"Chunk {i}": chunk,
                    "RawPage": doc_index,
                    "RawFormat": "csv"
                    }
                    sspi_raw_api_data.raw_insert_one(observation, IndicatorCode, **kwargs)
    
def cleanWIDData(raw_data):

    raw_csv = raw_data[0]['Raw']['Raw']

    virtual_csv = StringIO(raw_csv)
    raw_df = pd.read_csv(virtual_csv, delimiter=';')
    ptinc = raw_df[raw_df['variable'] == 'sptincj992'].reset_index(drop=True)
    target_vars = ['p0p50', 'p90p100']
    country_code = pycountry.countries.get(alpha_2=ptinc['country'][0]).alpha_3
    ptinc_vars = ptinc[ptinc['percentile'].isin(target_vars)]
    ptinc_vars = ptinc_vars.drop(columns='variable')
    ptinc_pivot = ptinc_vars.pivot(index='year',columns='percentile',values='value')
    ptinc_pivot['country'] = 'AD'
    ptinc_pivot['ratio'] = ptinc_pivot['p0p50'] / ptinc_pivot['p90p100']
    ptinc_pivot = ptinc_pivot.drop(columns=['p0p50', 'p90p100'])
    

    ''' 
      country    variable percentile  year  value  age pop
    0      AD  adiincj992      p0p10  1980  550.3  992   j
    1      AD  adiincj992      p0p10  1981  511.0  992   j
    2      AD  adiincj992      p0p10  1982  491.5  992   j
    3      AD  adiincj992      p0p10  1983  495.5  992   j
    4      AD  adiincj992      p0p10  1984  500.5  992   j
    5      AD  adiincj992      p0p10  1985  474.9  992   j
    6      AD  adiincj992      p0p10  1986  471.5  992   j
    7      AD  adiincj992      p0p10  1987  477.3  992   j
    8      AD  adiincj992      p0p10  1988  502.8  992   j
    9      AD  adiincj992      p0p10  1989  505.9  992   j
    
    
    cleaned_wid_list = []

    for entry in reader:
        if entry['percentile'] != 'p0p50': 
            continue
        if entry['variable'] != 'sptincj992':
            continue

        observation = {
            "CountryCode": entry['country'],
            "IndicatorCode": "ISHRAT",
            "Year": entry['year'],
            "Value":entry['value'],
            "Unit": "Index",
            "Description":""

        }
        cleaned_wid_list.append(observation)
    '''
    return [1,2,3]
