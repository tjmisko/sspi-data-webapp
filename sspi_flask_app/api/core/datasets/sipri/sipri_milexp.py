import logging
import json
import requests
from sspi_flask_app.api.datasource.sipri import clean_sipri_data
from sspi_flask_app.api.core.datasets import dataset_collector, dataset_cleaner
from sspi_flask_app.models.database import sspi_raw_api_data, sspi_clean_api_data, sspi_metadata
from sspi_flask_app.api.resources.utilities import get_country_code

@dataset_collector("SIPRI_MILEXP")
def collect_sipri_milexp(**kwargs):
    source_info = sspi_metadata.get_source_info("SIPRI_MILEXP")
    log = logging.getLogger(__name__)
    url = "https://backend.sipri.org/api/p/excel-export/preview"
    msg = f"Requesting MILEXP data from URL: {url}\n"
    yield msg
    log.info(msg)
    headers = {
        "Content-Type": "application/json",
        "Origin": "https://milex.sipri.org",
        "Referer": "https://milex.sipri.org/",
    }
    query_payload = {
        "regionalTotals": False,
        "currencyFY": False,
        "currencyCY": True,
        "constantUSD": False,
        "currentUSD": False,
        "shareOfGDP": True,
        "perCapita": False,
        "shareGovt": False,
        "regionDataDetails": False,
        "getLiveData": False,
        "yearFrom": None,
        "yearTo": None,
        "yearList": [1990, 2024],
        "countryList": []
    }
    raw = requests.post(
        url, headers=headers, json=query_payload, verify=False
    ).json()
    sspi_raw_api_data.raw_insert_one(
        raw, source_info, **kwargs
    )
    yield "Successfully collected MILEXP data"


@dataset_cleaner("SIPRI_MILEXP")
def clean_sipri_milexp():
    sspi_clean_api_data.delete_many({"DatasetCode": "SIPRI_MILEXP"})
    source_info = sspi_metadata.get_source_info("SIPRI_MILEXP")
    raw_data = sspi_raw_api_data.fetch_raw_data(source_info)
    milexp_raw = raw_data[0]["Raw"]
    share_gdp_data = None
    for section in milexp_raw.get("Data", []):
        if section.get("DataType") == "Share of GDP":
            share_gdp_data = section
            break
    if not share_gdp_data:
        return []
    rows = share_gdp_data.get("Rows", [])
    cleaned_data = []
    years = list(range(2000, 2026))  # 1990 to 2025 (36 years)
    for row in rows:
        if not row or len(row) < 3:  # Need at least country name, marker, and one value
            continue
        country_name = row[0]
        skip_regions = [
          "",
          "Africa",
          "North Africa",
          "sub-Saharan Africa",
          "Americas",
          "North America",
          "Central America and the Caribbean",
          "South America",
          "Asia & Oceania",
          "Central Asia",
          "East Asia",
          "South Asia",
          "South East Asia",
          "Oceania",
          "Europe",
          "Central Europe",
          "Eastern Europe",
          "Western Europe",
          "Middle East"
        ]
        if not country_name or country_name in skip_regions:
            continue
        if "Military expenditure" in country_name or "Countries are" in country_name or \
           "Figures in" in country_name or ". ." in country_name:
            continue
        values_start = 1
        if len(row) > 1 and isinstance(row[1], str) and len(row[1]) <= 3 and any(c in row[1] for c in ['§', '‡', '¶', '*']):
            values_start = 2
        values = row[values_start:]
        if len(values) < 35:
            continue
        for i, year in enumerate(years):
            if year > 2024:  # Skip 2025 data for now
                break
            if i >= len(values):
                break
            value_str = values[i]
            if value_str in [None, "", "...", "xxx", ". .", "n/a", "N/A"]:
                continue
            # Try to convert to float
            try:
                value = float(value_str)
                # Convert to percentage (multiply by 100 if needed - check if values are decimals)
                if value < 1:  # Likely a decimal representation
                    value = value * 100
            except (ValueError, TypeError):
                continue
            # Handle North/South Korea specially since utility function has issues
            if 'north korea' in country_name.lower():
                country_code = 'PRK'
            elif 'south korea' in country_name.lower():
                country_code = 'KOR'
            else:
                country_code = get_country_code(country_name)
            if not country_code or len(country_code) != 3:
                continue
            cleaned_data.append({
                'CountryCode': country_code,
                'Year': year,
                'Value': value,
                'Unit': 'Percent of GDP',
                'DatasetCode': 'SIPRI_MILEXP',
                'Description': 'Military expenditure (local currency at current prices) according to the calendar year as a percentage of GDP.'
            })
    sspi_clean_api_data.insert_many(cleaned_data)
    return cleaned_data
