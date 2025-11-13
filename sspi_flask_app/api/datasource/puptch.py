from sspi_flask_app.models.database import sspi_raw_api_data
import pandas as pd 
from ..resources.utilities import get_country_code
import requests
import zipfile
import json
import re
from io import BytesIO, StringIO

def collect_puptch_csv_data(**kwargs):
    local_csv_file_owd = pd.read_csv('https://ourworldindata.org/grapher/pupil-teacher-ratio-for-primary-education-by-country.csv?v=1&csvType=full&useColumnShortNames=true')
    csv_string_owd = local_csv_file_owd.to_csv(index=False)  
    source_info_owd = {
        "OrganizationName": "Global Change Data Lab",
        "OrganizationCode": "GCDL",
        "OrganizationSeriesCode": None,
        "QueryCode": None,
        "BaseURL": "https://ourworldindata.org/grapher/pupil-teacher-ratio-for-primary-education-by-country.csv?v=1&csvType=full&useColumnShortNames=true"
    }
    count_owd = sspi_raw_api_data.raw_insert_one(csv_string_owd, source_info_owd, **kwargs)
    yield f"\nInserted {count_owd} observations into the database from puptch_owd csv file.\n"



def collect_puptch_zip_data(**kwargs):
    url = "https://api.uis.unesco.org/api/public/data/indicators/export?indicator=PTRHC.1.QUALIFIED&start=2000&end=2025&indicatorMetadata=false&footnotes=false&version=20250917-73f4b95c&format=csv"
    res = requests.get(url)
    if res.status_code != 200:
        err = f"(HTTP Error {res.status_code})"
        yield "Failed to fetch data from source" + err
        return
    with zipfile.ZipFile(BytesIO(res.content)) as z:
        for f in z.namelist():
            if "data.csv" in f:
                with z.open(f) as data:
                    yield f"Processing file: {f}\n"
                    csv_string_unesco = data.read().decode("utf-8")
                    source_inf_unesco = {
                        "OrganizationName": "United Nations Educational, Scientific and Cultural Organization",
                        "OrganizationCode": "UNESCO",
                        "OrganizationSeriesCode": None,
                        "QueryCode": None,
                        "BaseURL": "https://api.uis.unesco.org/api/public/data/indicators/export?indicator=PTRHC.1.QUALIFIED&start=2000&end=2025&indicatorMetadata=false&footnotes=false&version=20250917-73f4b95c&format=csv"

                    }
                    sspi_raw_api_data.raw_insert_one(
                        csv_string_unesco, source_inf_unesco, **kwargs
                    )
    yield "Collection complete for EPI Indicators\n"





# def clean_puptch_data(raw_data):
#     local_csv_file = pd.read_csv('https://ourworldindata.org/grapher/pupil-teacher-ratio-for-primary-education-by-country.csv?v=1&csvType=full&useColumnShortNames=true')
#     columns = ['Country', '2014', 'Rank_2014', '2017', 'Rank_2017', '2018', 'Rank_2018','2020', 'Rank_2020', '2024', 'Rank_2024']
#     df = pd.DataFrame(local_csv_file, columns=columns)

#     df['2024'] = df['2024'] / 100
#     df['2020'] = df['2020'] / 100

#     df_year_only = df.drop(['Rank_2014','Rank_2017', 'Rank_2018', 'Rank_2020', 'Rank_2024'], axis = 1)
#     df_melted = df_year_only.melt(id_vars=['Country'], 
#                      value_vars=['2014', '2017', '2018', '2020', '2024'], 
#                      var_name='Year', 
#                      value_name='Value')
    
#     df_melted['Unit'] = 'Percentage'
#     df_melted['IndicatorCode'] = 'CYBSEC'
#     df_final = df_melted.dropna()

#     df_final['CountryCode'] = df_final['Country'].apply(get_country_code)
#     df_final['Year'] = df_final['Year'].astype(int)
#     df_f = df_final.drop('Country', axis = 1)
#     return df_f