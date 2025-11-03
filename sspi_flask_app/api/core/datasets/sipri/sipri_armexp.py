###############################################################
# Documentation: datasets/sipri/sipri_armexp/documentation.md #
###############################################################
import logging
import requests
from sspi_flask_app.api.core.datasets import dataset_collector, dataset_cleaner
from sspi_flask_app.models.database import sspi_raw_api_data, sspi_clean_api_data, sspi_metadata
import pandas as pd
from io import StringIO
from sspi_flask_app.api.resources.utilities import get_country_code

@dataset_collector("SIPRI_ARMEXP")
def collect_sipri_armexp(**kwargs):
    log = logging.getLogger(__name__)
    url = "https://atbackend.sipri.org/api/p/trades/import-export-csv-str/"
    source_info = sspi_metadata.get_source_info("SIPRI_ARMEXP")
    log.info(f"Requesting ARMEXP data from URL: {url}")
    headers = {
        "Content-Type": "application/json",
        "Origin": "https://armstransfers.sipri.org",
        "Referer": "https://armstransfers.sipri.org",
    }
    query_payload = {
        "filters": [
            {
                "field": "Year range 1",
                "oldField": "",
                "condition": "contains",
                "value1": 1990,
                "value2": 2025,
                "listData": []
            },
            {
                "field": "orderbyseller",
                "oldField": "",
                "condition": "",
                "value1": "",
                "value2": "",
                "listData": []
            },
            {
                "field": "DeliveryType",
                "oldField": "",
                "condition": "",
                "value1": "delivered",
                "value2": "",
                "listData": []
            },
            {
                "field": "Status",
                "oldField": "",
                "condition": "",
                "value1": "0",
                "value2": "",
                "listData": []
            }
        ],
        "logic": "AND"
    }
    response = requests.post(url, headers=headers, json=query_payload)
    sspi_raw_api_data.raw_insert_one(response.json(), source_info, **kwargs)
    yield "Collected ARMEXP data"


@dataset_cleaner("SIPRI_ARMEXP")
def clean_sipri_armexp():
    sspi_clean_api_data.delete_many({"DatasetCode": "SIPRI_ARMEXP"})
    source_info = sspi_metadata.get_source_info("SIPRI_ARMEXP")
    raw_data = sspi_raw_api_data.fetch_raw_data(source_info)
    csv_string = raw_data[0]["Raw"]["result"]
    lines = csv_string.strip().split('\n')
    header_idx = None
    for i, line in enumerate(lines):
        if line.startswith("Exports by,"):
            header_idx = i
            break
    if header_idx is None:
        return []
    csv_data = '\n'.join(lines[header_idx:])
    df = pd.read_csv(StringIO(csv_data))
    df = df[~df['Exports by'].str.contains('Total world export|Sum total years', na=False)]
    year_columns = [col for col in df.columns if col.isdigit() and 1990 <= int(col) <= 2025]
    df_melted = df.melt(
        id_vars=['Exports by'],
        value_vars=year_columns,
        var_name='Year',
        value_name='Value'
    )
    df_melted.rename(columns={'Exports by': 'Country'}, inplace=True)
    df_melted['Value'] = df_melted['Value'].replace('', None)
    df_melted['Value'] = df_melted['Value'].replace('0 ', '0')
    df_melted = df_melted.dropna(subset=['Value'])
    df_melted['Value'] = pd.to_numeric(df_melted['Value'], errors='coerce')
    df_melted = df_melted.dropna(subset=['Value'])
    df_melted['Year'] = df_melted['Year'].astype(int)
    skip_countries = [
        'soviet union',
        'yugoslavia', 
        'czechoslovakia',
        'east germany (gdr)',
        'unknown supplier(s)',
        'european union**',
        'fmln (el salvador)*',
        'mujahedin (afghanistan)*',
        'hor (libya)*'
    ]
    cleaned_data = []
    
    for _, row in df_melted.iterrows():
        country_name = row['Country'].strip().lower()
        if country_name in skip_countries:
            continue
            
        # Handle Korea specifically since utility function has logic issues
        if 'north korea' in country_name:
            country_code = 'PRK'
        elif 'south korea' in country_name:
            country_code = 'KOR'
        else:
            country_code = get_country_code(row['Country'])
            
        if country_code and len(country_code) == 3:
            cleaned_data.append({
                'CountryCode': country_code,
                'Year': int(row['Year']),
                'Value': float(row['Value']),
                'Unit': 'Millions SIPRI TIV',
                'DatasetCode': 'SIPRI_ARMEXP',
                'Description': 'Arms transfers: the supply of military weapons through sales, aid, gifts, and those made through manufacturing licenses.'
            })
    
    if cleaned_data:
        sspi_clean_api_data.insert_many(cleaned_data)
    return cleaned_data
