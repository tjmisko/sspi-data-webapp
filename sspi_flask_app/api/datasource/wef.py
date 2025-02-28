from sspi_flask_app.models.database import sspi_raw_api_data
import requests
import time
import io
import pandas as pd
from pycountry import countries
from ..resources.utilities import string_to_float

def collectExcelData(IndicatorCode, **kwargs):
    """
    Downloads an Excel file from the specified URL, converts its rows to a list of dictionaries,
    and inserts the raw data into the database.
    """
    yield f"Collecting Excel data for Indicator {IndicatorCode}\n"
    url = "https://thedocs.worldbank.org/en/doc/cf8eee7ff5029398f75e897b342e7320-0050122023/related/WEF-GCIHH.xlsx"
    
    yield "Downloading Excel file...\n"
    response = requests.get(url)
    if response.status_code != 200:
        yield f"Failed to download Excel file. Status code: {response.status_code}\n"
        return
    
    # Load the Excel file from memory
    excel_file = io.BytesIO(response.content)
    try:
        df = pd.read_excel(excel_file)
    except Exception as e:
        yield f"Error reading Excel file: {e}\n"
        return
    
    yield f"Excel file downloaded successfully. Found {len(df)} rows.\n"
    
    # Convert DataFrame rows to a list of dictionaries (flat structure)
    document_list = df.to_dict(orient='records')
    
    # Insert the raw data into the database
    count = sspi_raw_api_data.raw_insert_many(document_list, IndicatorCode, **kwargs)
    yield f"Inserted {count} new observations into sspi_raw_api_data\n"
    yield f"Collection complete for Excel data source for Indicator {IndicatorCode}"


def cleaned_excel_current(RawData, IndName, unit):
    """
    Takes in a list of collected raw Excel data (flat structure) and a 6-letter indicator code,
    and returns a list of dictionaries with only the relevant data from wanted countries.
    
    Expected flat keys include:
      - "countryiso3code"
      - "value"
      - "date"
      - "indicator"
      - "IntermediateCode" (optional)
    """
    clean_data_list = []
    for entry in RawData:
        iso3 = entry.get("countryiso3code")
        if not iso3:
            continue
        
        country_data = countries.get(alpha_3=iso3)
        if not country_data:
            continue
        
        value = entry.get("value")
        if value == "NaN" or value is None:
            continue
        
        clean_obs = {
            "CountryCode": iso3,
            "IndicatorCode": IndName,
            "IntermediateCode": entry.get("IntermediateCode", ""),
            "Description": entry.get("indicator", ""),
            "Year": entry.get("date"),
            "Unit": unit,
            "Value": string_to_float(value)
        }
        clean_data_list.append(clean_obs)
    return clean_data_list
