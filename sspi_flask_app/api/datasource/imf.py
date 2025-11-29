from sspi_flask_app.models.database import sspi_raw_api_data
import requests
import time
from pycountry import countries
from ..resources.utilities import parse_json, string_to_float
import pandas as pd


''' 
The following pulls from the imf api at https://www.imf.org/external/datamapper/api/help
It contains the indexes and descriptions of all the IMF datasets available

This helper function returns a dataframe of all the available IMF indexes with their index and descriptions. You can use these indexes in the following methods
'''
def _get_API_indexes():
    url = "https://www.imf.org/external/datamapper/api/v1/indicators"
    response = requests.get(url)
    response.raise_for_status() # Add this to catch HTTP errors
    data = response.json()
    data_clean = pd.DataFrame.from_dict(data['indicators'], orient='index')
    df = data_clean.drop(['source', 'unit'], axis = 1)
    return df

'''
imf-index: index of indicators available from IMF API (Ex: LP)
for kwargs: first argument is 'countries' which is a list of country codes (Ex: ['US', 'CA'])
second argument is 'years' which is a list of years (Ex: [2020, 2021])
'''
def collect_imf_data(index, **kwargs):
    yield f"Collecting data for IMF Indicator {index}\n"
    
    url = f"https://www.imf.org/external/datamapper/api/v1/{index}"

    countries = kwargs.get('countries', None)
    years = kwargs.get('years', None)

    if countries:
        for country in countries:
            url += f"/{country}"

    if years:
        url += '?periods='
        for year in years:
            url += f"{year},"
        url = url[:-1]

    response = requests.get(url)
    myData = response.json()

    # Check the keys in the gdp_data dictionary
    print("Keys in data:", myData.keys())

    # Access the data under the 'values' key and the specific indicator code
    indicator_data = myData['values'][index]

    # The data is nested by country and then by period.
    # We need to flatten this structure into a DataFrame.
    # Let's create a list of records to build the DataFrame
    records = []
    for country, periods_data in indicator_data.items():
        for period, value in periods_data.items():
            records.append({'COUNTRY': country, 'PERIOD': period, 'VALUE': value})

    myData = pd.DataFrame(records)

    #converting it into sspi form/requirements!

    # Convert DF → list of dicts for insertion
    records = myData.to_dict(orient="records")

    # Build required metadata
    source_info = {
        "OrganizationName": "International Monetary Fund",
        "OrganizationCode": "IMF",
        "OrganizationSeriesCode": index,   # your indicator code
        "QueryCode": index,
        "URL": url,        # the API URL you used
        "BaseURL": "https://www.imf.org/external/datamapper/api/v1/"
    }

    # Insert into database
    count = sspi_raw_api_data.raw_insert_many(records, source_info, **kwargs)

    yield f"Inserted {count} IMF observations for indicator {index}\n"
    time.sleep(5)
    yield f"Collection complete for IMF Indicator {index}"

    return myData

'''
clean_imf_data: cleans raw IMF data into SSPI format
raw_data: list of raw data entries from sspi_raw_api_data
dataset_code: code of IMF dataset we're cleaning
unit: unit of measurement for the dataset
'''
def clean_imf_data(raw_data, dataset_code, unit) -> list[dict]:

    indexesDF = _get_API_indexes()  # to get the index descriptions
    description = indexesDF.loc[indexesDF.index==dataset_code, 'description'].values[0]

    clean_data_list = []
    for entry in raw_data:
        clean_obs = {
            "CountryCode": entry['COUNTRY'],
            "DatasetCode": dataset_code,
            "Description": description,
            "Year": entry['PERIOD'],
            "Unit": unit,
            "Value": entry['VALUE']
        }
        clean_data_list.append(clean_obs)
    return parse_json(clean_data_list)
    #return clean_data_list