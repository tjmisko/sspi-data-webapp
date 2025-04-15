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
                if len(file_name_fields) != 3 or 'metadata' in file_name_fields:
                    # Don't save state-level data or metadata
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
                
                for i in range(max(1, num_chunks - 1)):
                    start = int(i * len_chunk)
                    end = int((i + 1) * len_chunk if i < num_chunks - 1 else len(raw))
                    chunk = "country;variable;percentile;year;value;age;pop\n" + raw[start:end] if i > 0 else raw[start:end]
                    observation = {
                    "SourceOrganization": "WID",
                    "SourceOrganizationName": "World Inequality Database",
                    "SourceOrganizationURL": "https://wid.world/",
                    "SourceOrganizationDownloadURL": "https://wid.world/bulk_download/wid_all_data.zip",
                    "DatasetName": file_name,
                    "CountryCode": country_code,
                    "DatasetDescription": f"World Inequality Database All {dataset_type} for {country_code}",
                    "Raw": chunk,
                    "Chunk Number": i,
                    "RawPage": doc_index,
                    "RawFormat": "csv"
                    }
                    sspi_raw_api_data.raw_insert_one(observation, IndicatorCode, **kwargs)

def processCSV(curr_csv, CountryCode):
    virtual_csv = StringIO(curr_csv)
    raw_df = pd.read_csv(virtual_csv, delimiter=';')
    target_vars = ['p0p50', 'p90p100']

    if not raw_df['percentile'].isin(target_vars).any() or 'sptincj992' not in raw_df['variable'].values:
        return []

    else: 
        ptinc = raw_df[raw_df['variable'] == 'sptincj992'].reset_index(drop=True)
        ptinc = ptinc[ptinc['percentile'].isin(target_vars)]
        ptinc['country'] = CountryCode
        ptinc = ptinc[['country','year', 'value', 'percentile']].rename(columns={'country':'CountryCode','year':'Year','percentile':'Percentile'})
                   
        return ptinc.to_dict(orient='records')


def cleanWIDData(raw_data): 

    cleaned_obs = []
    
    for csv in raw_data:
        observation_cleaned = processCSV(csv['Raw']['Raw'], csv['Raw']['CountryCode'])
        cleaned_obs += observation_cleaned
    
    cleaned_df = pd.DataFrame(cleaned_obs)
    p0p50 = cleaned_df[cleaned_df['Percentile'] == 'p0p50'].drop(columns=['Percentile'])
    p90p100 = cleaned_df[cleaned_df['Percentile'] == 'p90p100'].drop(columns=['Percentile'])

    merged_df = pd.merge(p0p50, p90p100, on=['CountryCode', 'Year'], suffixes=('_p0p50', '_p90p100'))
    merged_df['Value'] = merged_df['value_p0p50'] / merged_df['value_p90p100']
    merged_df['IndicatorCode'] = 'ISHRAT'
    merged_df['Description'] = "The pre-tax national income share of the bottom 50% of households divided by the pre-tax national income share of the top 10% of households."
    merged_df['Unit'] = 'Proportion'
    merged_df = merged_df.drop(columns=['value_p0p50','value_p90p100'])
    merged_df = merged_df[merged_df['Year'] >= 1930]
    
    return merged_df.to_dict(orient='records')



        



