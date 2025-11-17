import pandas as pd
import requests
import zipfile
import json
import re
from io import BytesIO, StringIO
from sspi_flask_app.models.database import sspi_raw_api_data
from sspi_flask_app.api.resources.utilities import get_country_code, parse_json
import gc

# note: data is stagnant from estimations published in 2024
# note: the data tells us about accuracy (whether it is an estimation, variance)

def collect_fampln_data(**kwargs):
    yield "Starting collection for FAMPLN Indicators\n"
    url = "https://population.un.org/wpp/Data_FamilyPlanningIndicators_2024.zip"
    res = requests.get(url)
    if res.status_code != 200:
        err = f"(HTTP Error {res.status_code})"
        yield f"Failed to fetch data from source {err}\n"
        return
    
    with zipfile.ZipFile(BytesIO(res.content)) as z:
        for f in z.namelist():
            if "__MACOSX" in f:
                continue
            with z.open(f) as data:
                yield f"Processing file: {f}\n"
                
                # Read and decode
                raw_bytes = data.read()
                csv_string = raw_bytes.decode('utf-8', errors="replace")
                
                # Split into chunks (10MB each)
                chunk_size = 10 * 1024 * 1024  # 10MB
                total_size = len(csv_string)
                num_chunks = (total_size // chunk_size) + 1
                
                yield f"File size: {total_size / (1024**2):.2f} MB\n"
                yield f"Splitting into {num_chunks} chunks...\n"
                
                data_list = []
                # Process in chunks
                for i in range(0, chunk_size*10, chunk_size):
                    chunk = csv_string[i:i + chunk_size]
                    chunk_num = (i // chunk_size) + 1
                    data_list.append(chunk)
                    
                    yield f"Processing chunk {chunk_num}/{num_chunks}...\n"

                
                source_info = {
                    "OrganizationName": "United Nations Population Division",
                    "OrganizationCode": "UNPD",
                    "QueryCode": f"unpd_fampln_2024_chunk",
                    "URL": url
                }

                yield f"Inserting data list\n"

                sspi_raw_api_data.raw_insert_many(
                        data_list, source_info, **kwargs
                    )

                yield f"Successfully inserted all {num_chunks} chunks\n"
                
    yield "Collection complete for FAMPLN Indicators\n"

# for testing
# csv_string = None
# for message in collect_fampln_data(username = 'claranhc'):
#     if isinstance(message, str):
#         print(message)
#     elif isinstance(message, dict) and "csv_string" in message:
#         csv_string = message["csv_string"]

def clean_fampln_csv(raw_csv_string: str, dataset_code: str) -> list[dict]:
    csv_virtual_file = StringIO(raw_csv_string)
    
    cleaned_chunks = []
    for chunk in pd.read_csv(
        csv_virtual_file,
        chunksize=50000,  
        usecols=['Location', 'Time', 'Value', 'IndicatorId'],  
        dtype={'IndicatorId': 'int8', 'Time': 'int16', 'Value': 'float32'}  
    ):
        chunk = chunk[chunk['IndicatorId'] == 4]        
        if len(chunk) == 0:
            continue
        
        chunk = chunk[['Location', 'Time', 'Value']]
        
        chunk["DatasetCode"] = dataset_code
        chunk["Unit"] = "Proportion of Women"
        chunk.rename(columns={'Location': 'CountryName', 'Time': 'Year'}, inplace=True)
        
        chunk['CountryClean'] = chunk['CountryName'].str.lower().str.replace(r"\s*\(.*\)", "", regex=True).str.strip()
        chunk['CountryCode'] = chunk['CountryClean'].map(lambda x: get_country_code(x))
        chunk['Year'] = pd.to_numeric(chunk['Year'], errors='coerce')
        chunk.drop(columns=['CountryClean', 'CountryName'], inplace=True)
        
        cleaned_chunks.extend(chunk.to_dict(orient='records'))
        
        del chunk
        gc.collect()
    
    print(f"Total cleaned rows: {len(cleaned_chunks)}")
    return cleaned_chunks  

# def clean_fampln_csv(raw_csv_string: str, dataset_code: str) -> list[dict]:
#     csv_virtual_file = StringIO(raw_csv_string)
#     fampln_raw = pd.read_csv(csv_virtual_file)
#     fam_pln = fampln_raw[fampln_raw['IndicatorId'] == 4]
#     fam_pln = fam_pln[(fam_pln['Time'].astype(int) > 1999) & (fam_pln['Time'].astype(int) < 2025)]
#     fam_pln = fam_pln[['Location', 'Time', 'Value']]
#     fam_pln["DatasetCode"] = dataset_code
#     fam_pln["Unit"] = "Proportion of Women"
#     fam_pln = fam_pln.rename(columns={
#         'Location': 'CountryName',
#         'Time': 'Year',
#     })
#     fam_pln['CountryClean'] = fam_pln['CountryName'].str.lower().str.replace(r"\s*\(.*\)", "", regex=True).str.strip()
#     fam_pln['CountryCode'] = fam_pln['CountryClean'].map(lambda country_name: get_country_code(country_name))
#     fam_pln['Year'] = pd.to_numeric(fam_pln['Year'], errors='coerce')
#     fam_pln.drop(columns=['CountryClean', 'CountryName'], inplace=True)
#     print(fam_pln.head().to_string())
#     return json.loads(str(fam_pln.to_json(orient="records")))

# for testing
# output = clean_fampln_csv(raw_csv_string=csv_string, dataset_code="FAMPLN_2024_INDICATORS")
# print(output[:5])


