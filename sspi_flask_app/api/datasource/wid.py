import io
import json
import time
import zipfile
from io import StringIO

import pandas as pd
import pycountry
import requests
import logging

from sspi_flask_app.models.database import sspi_metadata, sspi_raw_api_data

log = logging.getLogger(__name__)


def collect_wid_data(**kwargs):
    yield "Requesting WID data\n"
    url = "https://wid.world/bulk_download/wid_all_data.zip"
    res = requests.get(url)
    res.raise_for_status()
    yield "Received WID data\n"
    zip_file = io.BytesIO(res.content)
    with zipfile.ZipFile(zip_file) as z:
        for file_name in z.namelist():
            yield f"Processing {file_name}\n"
            with z.open(file_name) as f:
                raw = f.read().decode('utf-8')
                source_info = {
                    "OrganizationName": "World Inequality Database",
                    "OrganizationCode": "WID",
                    "QueryCode": "wid_all_data",
                    "Filename": file_name,
                    "URL": url,
                }
                sspi_raw_api_data.raw_insert_one(
                    raw, source_info, **kwargs
                )
    yield "WID data collection completed\n"

def fetch_wid_raw_data(country_code: str):
    cc_alpha_2 = pycountry.countries.get(alpha_3=country_code)
    if not cc_alpha_2:
        return {}
        # return ""
    cc_alpha_2 = cc_alpha_2.alpha_2
    source_info = {
        "OrganizationCode": "WID",
        "QueryCode": "wid_all_data"
    }
    source_info.update({"Filename": f"WID_data_{cc_alpha_2}.csv"})
    raw = sspi_raw_api_data.fetch_raw_data(source_info)
    source_info.update({"Filename": f"WID_metadata_{cc_alpha_2}.csv"})
    meta = sspi_raw_api_data.fetch_raw_data(source_info)
    assert isinstance(raw, list) and len(raw) == 1, "Expected a single raw document"
    assert isinstance(meta, list) and len(meta) == 1, "Expected a single raw document"
    return raw[0], meta[0]


def filter_wid_csv(dataset_code:str, csv_string: str, country_code: str, percentile: str, variable: str, years: list[int], metadata_csv_string: str = ""):
    """
    Efficiently filter WID CSV data by country, variable, percentile, and years.
    
    Optimizations:
    - Categorical dtypes for memory efficiency
    - Column selection to reduce I/O
    - Chained queries for progressive filtering
    - Optimized data types for performance
    """
    # Define optimized data types for faster parsing and lower memory usage
    dtype_spec = {
        'variable': 'category',   # Categorical for repeated variables  
        'percentile': 'category', # Categorical for repeated percentile
        'year': 'int16',          # Smaller int type for years (handles 1900-2100+)
        'value': 'float32'        # float32 sufficient for most economic data
    }
    
    # Parse CSV with optimizations - only load needed columns (skip country since each CSV is single-country)
    df = pd.read_csv(
        StringIO(csv_string), 
        delimiter=';',
        dtype=dtype_spec,
        usecols=['variable', 'percentile', 'year', 'value']
    )
    log.info(f"Loaded {len(df)} rows from WID CSV data for country {country_code}, variable {variable}, percentile {percentile}, years {years}")
    
    # Chain filters efficiently - each filter reduces dataset size for next operation
    # Order matters: most selective filters first
    log.info(f"Initial dataset size: {len(df)} rows")
    log.debug(f"Available variables in dataset: {sorted(df['variable'].unique().tolist())}")
    filtered = df.query('variable == @variable')
    log.info(f"After variable filter ({variable}): {len(filtered)} rows")
    filtered = filtered.query('percentile == @percentile')
    log.info(f"After percentile filter ({percentile}): {len(filtered)} rows")
    filtered = filtered.query('year.isin(@years)')
    log.info(f"After year filter ({years}): {len(filtered)} rows")
    
    # Rename columns and add CountryCode
    filtered = filtered.rename(columns={
        'value': 'Value',
        'year': 'Year',
    })
    filtered['CountryCode'] = country_code
    filtered['DatasetCode'] = dataset_code
    log.info(f"Final dataset with renamed columns and CountryCode: {len(filtered)} rows")
    if metadata_csv_string:
        log.info(metadata_csv_string[0:1000])
        metadata_df = pd.read_csv(StringIO(metadata_csv_string), delimiter=';')
        filtered_meta = metadata_df.query('variable == @variable').to_dict(orient='records')
        assert len(filtered_meta) == 1, "Expected a single metadata record for the variable"
        log.info(filtered_meta[0].get('simpledes', 'No description available'))
        unit = filtered_meta[0].get('unit', 'No unit available')
        filtered['Unit'] = f"{unit}; percentile {percentile}; {variable}"
        # Drop variable and percentile columns when metadata has been processed
        filtered = filtered.drop(columns=['variable', 'percentile'], errors='ignore')
    return json.loads(str(filtered.to_json(orient='records')))  # Convert to JSON string
