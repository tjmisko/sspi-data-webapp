from sspi_flask_app.models.database import sspi_raw_api_data
import logging
import pandas as pd
from ..resources.utilities import get_country_code
import requests
from io import StringIO
import json


def collectMILEXP(**kwargs):
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
        raw, "MILEXP", SourceOrganization="SIPRI", **kwargs
    )
    yield "Successfully collected MILEXP data"


def collectARMEXP(**kwargs):
    pass


def collectSIPRIdataNEW(IndicatorCode, **kwargs):
    log = logging.getLogger(__name__)
    headers = {"Content-Type": "application/json"}
    if IndicatorCode == "ARMEXP":
        url = "https://atbackend.sipri.org/api/p/trades/import-export-csv-str/"
        log.info(f"Requesting ARMEXP data from URL: {url}")
        headers.update({
            "Origin": "https://armstransfers.sipri.org",
            "Referer": "https://armstransfers.sipri.org",
        })
        query_payload = {
            "filters": [{"field": "Year range 1", "oldField": "", "condition": "contains", "value1": 1990, "value2": 2025, "listData": []},
                        {"field": "orderbyseller", "oldField": "", "condition": "",
                            "value1": "", "value2": "", "listData": []},
                        {"field": "DeliveryType", "oldField": "", "condition": "",
                            "value1": "delivered", "value2": "", "listData": []},
                        {"field": "Status", "oldField": "", "condition": "", "value1": "0", "value2": "", "listData": []}],
            "logic": "AND"}
        response = requests.post(url, headers=headers, json=query_payload)
        json_string = response.content.decode('utf-8')
        json_parsed = json.loads(json_string)
        data_string = json_parsed["result"]
        print(data_string)
    yield f"Collected {IndicatorCode} data"


def cleanSIPRIData(RawData, IndName, Unit, Description):
    df = pd.read_csv(StringIO(RawData))
    print(df)
    df.rename(columns={"Country": "Countries"}, inplace=True)
    year_columns = [col for col in df.columns if col != 'Countries']
    df_melted = df.melt(
        id_vars=['Countries'],
        value_vars=year_columns,
        var_name='Year',
        value_name='Value')
    df_melted['Unit'] = Unit
    df_melted["Description"] = Description
    df_melted['IndicatorCode'] = IndName
    # df_melted.to_csv('transformed_data.csv', index=False)
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
