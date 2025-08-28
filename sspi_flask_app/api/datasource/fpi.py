import pandas as pd
from sspi_flask_app.api.resources.utilities import parse_json, string_to_float
import requests
import zipfile
import json
import re
from io import BytesIO, StringIO
from os import environ
from sspi_flask_app.models.database import sspi_raw_api_data
from pycountry import countries
import time


def collect_fpi_data(fpi_indicator_code, **kwargs):
    api_key = environ.get("SSPI_FPI_API_KEY", None)
    if not api_key:
        yield "SSPI_FPI_API_KEY environment variable is not set. Ask @tjmisko for access."
        return
    
    username = "tjmisko"
    yield f"Collecting data for FPI Indicator {fpi_indicator_code}\n"
    
    # Iterate through years from 2000 to 2025
    for year in range(2000, 2026):
        # Construct URL for all countries for this year
        data_url = f"https://api.footprintnetwork.org/v1/data/all/{year}/{fpi_indicator_code}"
        
        yield f"Fetching data for year {year}...\n"
        
        try:
            response = requests.get(data_url, auth=(username, api_key))
            if response.ok:
                data = response.json()
                
                # Insert raw data with source info
                source_info = {
                    "OrganizationName": "Footprint Network",
                    "OrganizationCode": "FPI",
                    "OrganizationSeriesCode": fpi_indicator_code,
                    "QueryCode": fpi_indicator_code,
                    "URL": data_url,
                    "BaseURL": "https://api.footprintnetwork.org/v1/data"
                }
                
                # Wrap data to match expected format
                if data:
                    count = sspi_raw_api_data.raw_insert_many(data, source_info, **kwargs)
                    yield f"Inserted {count} observations for year {year}\n"
                else:
                    yield f"No data available for year {year}\n"
            elif response.status_code == 404:
                yield f"No data endpoint for year {year} (404 Not Found)\n"
            else:
                yield f"Failed to fetch data for year {year} (HTTP {response.status_code})\n"
                
        except requests.exceptions.RequestException as e:
            yield f"Network error fetching data for year {year}: {str(e)}\n"
        except Exception as e:
            yield f"Unexpected error fetching data for year {year}: {str(e)}\n"
            
        # Rate limiting - sleep for at least 3 seconds between requests
        time.sleep(3)
    
    yield f"Collection complete for FPI Indicator {fpi_indicator_code}"


def clean_fpi_data(raw_data, dataset_code, unit, description) -> list[dict]:
    clean_data_list = []
    for entry in raw_data:
        raw = entry.get("Raw", {})
        # Extract country code - FPI uses 2-letter ISO codes
        iso2_code = raw.get("isoa2")
        if not iso2_code:
            continue
            
        # Convert ISO2 to ISO3 code
        try:
            country_data = countries.get(alpha_2=iso2_code)
            if not country_data:
                # Skip countries that don't match
                continue
            country_code = country_data.alpha_3
        except:
            continue
            
        # Extract year and value
        year = raw.get("year")
        value = raw.get("value")
        
        if not year or value is None:
            continue
            
        clean_obs = {
            "CountryCode": country_code,
            "DatasetCode": dataset_code,
            "Description": description,
            "Year": int(year),
            "Unit": unit,
            "Value": string_to_float(value)
        }
        clean_data_list.append(clean_obs)
    
    return clean_data_list
