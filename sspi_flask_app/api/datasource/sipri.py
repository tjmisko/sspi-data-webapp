from sspi_flask_app.models.database import sspi_raw_api_data
import logging
import pandas as pd
from ..resources.utilities import get_country_code
import requests
from io import StringIO
import json


def clean_sipri_data(raw_data, dataset_code, unit, description):
    df = pd.read_csv(StringIO(raw_data))
    print(df)
    df.rename(columns={"Country": "Countries"}, inplace=True)
    year_columns = [col for col in df.columns if col != 'Countries']
    df_melted = df.melt(
        id_vars=['Countries'],
        value_vars=year_columns,
        var_name='Year',
        value_name='Value')
    df_melted['Unit'] = unit
    df_melted["Description"] = description
    df_melted['DatasetCode'] = dataset_code
    df_melted.replace("", "#N/A", inplace=True)
    df_final = df_melted.dropna()
    df_final['Countries'] = df_final['Countries'].str.lower()
    df_final = df_final[~df_final['Countries'].isin(
        ['unknown supplier(s)', 'yugoslavia', 'soviet union',
         'east germany (gdr)', 'united nations**', 'south vietnam', 'south yemen', 'north yemen',
         'european union**']
    )]
    special_cases = {
        'fmln (el salvador)*': 'SLV',
        'czechoslovakia': 'CSK',
        'german democratic republic': 'DDR',
        'yemen north': None,
        'uae': 'UAE',
        'mujahedin (afghanistan)*': 'AFG',
        'bosnia-herzegovina': 'BIH',
        'hor (libya)*': 'LBY'
    }
    df_final['CountryCode'] = df_final['Countries'].apply(
        lambda country: (
            special_cases.get(country.strip().lower())
            if country.strip().lower() in special_cases
            else get_country_code(country)
        )
    )
    df_final['Year'] = df_final['Year'].astype(int)
    df_f = df_final.drop('Countries', axis=1)
    return df_f
