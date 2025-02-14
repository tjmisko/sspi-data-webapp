import requests
from io import StringIO
import pandas as pd
from sspi_flask_app.models.database import sspi_raw_api_data

def collectIPUData(SourceIndicatorCode, IndicatorCode, **kwargs):
  
    urls = [
        "https://data.ipu.org/export-report/women-ranking/csv?date_month=12&date_year=2024",
        "https://data.ipu.org/export-report/women-ranking/csv?date_month=12&date_year=2023"
        "https://data.ipu.org/export-report/women-ranking/csv?date_month=12&date_year=2022"
        "https://data.ipu.org/export-report/women-ranking/csv?date_month=12&date_year=2021"
        "https://data.ipu.org/export-report/women-ranking/csv?date_month=12&date_year=2020"
    ]
    
    dataframes = []
    
    # Loop through both URLs and process each CSV
    for url in urls:
        res = requests.get(url)
        if res.status_code != 200:
            yield f"Failed to fetch data from {url} (HTTP Error {res.status_code})"
            continue  # Skip to the next URL
        
        csv_string = res.text
        try:
            df = pd.read_csv(StringIO(csv_string))
        except Exception as e:
            yield f"Failed to parse CSV from {url}: {e}"
            continue
        
        if SourceIndicatorCode not in df.columns:
            yield f"Column '{SourceIndicatorCode}' not found in the CSV from {url}."
            continue
        
        dataframes.append(df)
        yield f"Successfully processed data from {url}"
    
    if not dataframes:
        yield "No data was successfully downloaded or processed."
        return
    
    # Combine dataframes from both URLs
    combined_df = pd.concat(dataframes, ignore_index=True)
    
    if SourceIndicatorCode not in combined_df.columns:
        yield f"Column '{SourceIndicatorCode}' not found in the combined data."
        return
    
    # Extract the column of interest and rename it
    combined_df = combined_df[[SourceIndicatorCode]].rename(columns={SourceIndicatorCode: IndicatorCode})
    filtered_csv_string = combined_df.to_csv(index=False)
    
    # Insert the filtered CSV into the database
    sspi_raw_api_data.raw_insert_one({"csv": filtered_csv_string}, IndicatorCode, **kwargs)
    
    yield f"Collection complete for {IndicatorCode} from both 2023 and 2024 (Source column '{SourceIndicatorCode}')."
