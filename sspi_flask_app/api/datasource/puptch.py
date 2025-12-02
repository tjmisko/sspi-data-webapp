from sspi_flask_app.models.database import sspi_raw_api_data
import pandas as pd 
from ..resources.utilities import get_country_code, parse_json
import requests
import zipfile
import json
import re
import io
from sspi_flask_app.models.database import sspi_raw_api_data, sspi_clean_api_data, sspi_metadata

def collect_puptch_csv_data(**kwargs):
    local_csv_file_owd = pd.read_csv('https://ourworldindata.org/grapher/pupil-teacher-ratio-for-primary-education-by-country.csv?v=1&csvType=full&useColumnShortNames=true')
    csv_string_owd = local_csv_file_owd.to_csv(index=False)  
    source_info_owd = {
        "OrganizationName": "Global Change Data Lab",
        "OrganizationCode": "GCDL",
        "OrganizationSeriesCode": "GCDL",
        "QueryCode": "GCDL",
        "BaseURL": "https://ourworldindata.org/grapher/pupil-teacher-ratio-for-primary-education-by-country.csv?v=1&csvType=full&useColumnShortNames=true"
    }
    count_owd = sspi_raw_api_data.raw_insert_one(csv_string_owd, source_info_owd, **kwargs)
    # yield f"\nInserted {count_owd} observations into the database from puptch_owd csv file.\n"



def collect_puptch_zip_data(**kwargs):
    url = "https://api.uis.unesco.org/api/public/data/indicators/export?indicator=PTRHC.1.QUALIFIED&start=2000&end=2025&indicatorMetadata=false&footnotes=false&version=20250917-73f4b95c&format=csv"
    res = requests.get(url)
    if res.status_code != 200:
        err = f"(HTTP Error {res.status_code})"
        yield "Failed to fetch data from source" + err
        return
    with zipfile.ZipFile(io.BytesIO(res.content)) as z:
        for f in z.namelist():
            if "data.csv" in f:
                with z.open(f) as data:
                    # yield f"Processing file: {f}\n"
                    csv_string_unesco = data.read().decode("utf-8")
                    source_inf_unesco = {
                        "OrganizationName": "United Nations Educational, Scientific and Cultural Organization",
                        "OrganizationCode": "UNESCO",
                        "OrganizationSeriesCode": "UNESCO",
                        "QueryCode": "UNESCO",
                        "BaseURL": "https://api.uis.unesco.org/api/public/data/indicators/export?indicator=PTRHC.1.QUALIFIED&start=2000&end=2025&indicatorMetadata=false&footnotes=false&version=20250917-73f4b95c&format=csv"
                    }
                    sspi_raw_api_data.raw_insert_one(
                        csv_string_unesco, source_inf_unesco, **kwargs
                    )
    # yield "Collection complete for EPI Indicators\n"





def clean_puptch_csv_data(raw_data, dataset_code, unit, description):
    source_info = sspi_metadata.get_source_info(dataset_code)
    base_url = source_info['BaseURL']
    csv_Raw_text_data = None

    #iterate through each value in list to get the dictionaries 
    # then check whether the base URL for the DatasetCode equal to the url from the raw data
    for i in range(len(raw_data)):
        entry = raw_data[i]
        if entry['Source']['BaseURL'] == base_url:
            csv_Raw_text_data = entry['Raw'] 
    if csv_Raw_text_data == None:
        raise ValueError(f"csv_Raw_data in clean_puptch_csv_data is None")

    df = pd.read_csv(io.StringIO(csv_Raw_text_data))
    df = df.rename(columns = {"pupil_qualified_teacher_ratio_in_primary_education__headcount_basis__ptrhc_1_qualified": "Value"})
    df['DatasetCode'] = dataset_code
    df['Description'] = description
    df['Unit'] = unit
    df['CountryCode'] = df['Entity'].apply(get_country_code)
    # df['CountryCode'] = df['Code']
    df['Year'] = df['Year'].astype(int)
    df = df.loc[:, ["CountryCode", "DatasetCode", "Description", "Unit", "Value", "Year"]]
    df = df[df['CountryCode'].str.len() == 3]
    df = df.dropna()

    #drop duplicate rows and keep the row that has the maximum value 
    # for example, I had {"CountryCode": "KOR", "DatasetCode": "PUPTCH_OWD", "Year": 2018, "Value": 20.16}
    # and another duplicate row {"CountryCode": "KOR", "DatasetCode": "PUPTCH_OWD", "Year": 2018, "Value": 16.04}
    # so I kept the row with the maximum value so I can only have unique combinations of 
    # "CountryCode", "DatasetCode", "Year" and the dataset only contains 
    # {"CountryCode": "KOR", "DatasetCode": "PUPTCH_OWD", "Year": 2018, "Value": 20.16}
    df = df.loc[df.groupby(["CountryCode", "DatasetCode", "Year"])["Value"].idxmax()]
    df = df.reset_index(drop=True)
    rows = df.to_dict(orient="records")
    return parse_json(rows)



def clean_puptch_zip_data(raw_data, dataset_code, unit, description):
    source_info = sspi_metadata.get_source_info(dataset_code)
    base_url = source_info['BaseURL']
    csv_Raw_text_data = None

    #iterate through each value in list to get the dictionaries 
    # then check whether the base URL for the DatasetCode equal to the url from the raw data
    for i in range(len(raw_data)):
        entry = raw_data[i]
        if entry['Source']['BaseURL'] == base_url:
            raw = entry['Raw'] 
            csv_Raw_text_data = raw.encode('utf-8').decode('unicode_escape')

    if csv_Raw_text_data == None:
        raise ValueError(f"csv_Raw_data in clean_puptch_csv_data is None")
    
    csv_Raw_text_data = io.StringIO(csv_Raw_text_data)
    df = pd.read_csv(csv_Raw_text_data)
    df_long = df.loc[:, ['geoUnit', 'year', 'value']]

    df_long = df_long.rename(columns={"geoUnit": "Country_name", "value": "Value"})
    df_long['DatasetCode'] = dataset_code
    df_long['Description'] = description
    df_long['Unit'] = unit
    df_long['CountryCode'] = df_long['Country_name']
    ## Only keeping CountryCode that is 3 letters long 
    ## Deleted CountryCode that were ALECSO: Gulf countries and others that were alike since
    ## They were not a specific unique country, it covered groups of countries in one category ALECSO
    df_long = df_long[df_long['CountryCode'].str.len() == 3]
    df_long['Year'] = df_long['year'].astype(int)
    df_long = df_long.loc[:, ["CountryCode", "DatasetCode", "Description", "Unit", "Value", "Year"]]
    df_long = df_long.dropna()
    rows = df_long.to_dict(orient="records")
    return parse_json(rows)






