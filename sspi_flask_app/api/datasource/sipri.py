
from sspi_flask_app.models.database import sspi_raw_api_data
import pandas as pd 
from ..resources.utilities import get_country_code
import requests
from io import StringIO
import json

def collectSIPRIdataNEW(IndicatorCode, **kwargs):
    if IndicatorCode == "ARMEXP":

        url = "https://atbackend.sipri.org/api/p/trades/import-export-csv-str/"
        headers = {
            "Origin": "https://armstransfers.sipri.org",
            "Referer": "https://armstransfers.sipri.org",
            "Content-Type": "application/json"
            }
        query_payload = {
            "filters":[{"field":"Year range 1","oldField":"","condition":"contains","value1":1990,"value2":2025,"listData":[]},
                    {"field":"orderbyseller","oldField":"","condition":"","value1":"","value2":"","listData":[]},
                    {"field":"DeliveryType","oldField":"","condition":"","value1":"delivered","value2":"","listData":[]},
                    {"field":"Status","oldField":"","condition":"","value1":"0","value2":"","listData":[]}],
            "logic":"AND"}
        response = requests.post(url, headers = headers, json = query_payload)
        json_string = response.content.decode('utf-8')
        json_parsed = json.loads(json_string)
        data_string = json_parsed["result"]
        print(data_string)
    if IndicatorCode == "MILEXP":
        url = "https://backend.sipri.org/api/p/excel-export/preview"
        headers = {
            "Origin": "https://milex.sipri.org",
            "Referer": "https://milex.sipri.org/",
            "Content-Type": "application/json"
            }
        query_payload = {
            "regionalTotals": False,"currencyFY": False,"currencyCY": True,"constantUSD": False,"currentUSD": False,"shareOfGDP": True,"perCapita": False,
             "shareGovt": False,"regionDataDetails": False,"getLiveData":False,"yearFrom": None,"yearTo":None,"yearList":[1990,2024],
             "countryList":["Afghanistan","Albania","Algeria","Angola","Argentina","Armenia","Australia","Austria",
                            "Azerbaijan","Bahrain","Bangladesh","Belarus","Belgium","Belize","Benin","Bolivia","Bosnia and Herzegovina","Botswana","Brazil",
                            "Brunei","Bulgaria","Burkina Faso","Burundi","Cambodia","Cameroon","Canada","Cape Verde","Central African Republic","Chad","Chile",
                            "China","Colombia","Congo, DR","Congo, Republic","Costa Rica","Cote d'Ivoire","Croatia","Cuba","Cyprus","Czechia","Czechoslovakia",
                            "Denmark","Djibouti","Dominican Republic","Ecuador","Egypt","El Salvador","Equatorial Guinea","Eritrea","Estonia","Eswatini","Ethiopia",
                            "European Union","Fiji","Finland","France","Gabon","Gambia, The","Georgia","German Democratic Republic","Germany","Ghana","Greece",
                            "Guatemala","Guinea","Guinea-Bissau","Guyana","Haiti","Honduras","Hungary","Iceland","India","Indonesia","Iran","Iraq","Ireland",
                            "Israel","Italy","Jamaica","Japan","Jordan","Kazakhstan","Kenya","Korea, North","Korea, South","Kosovo","Kuwait","Kyrgyz Republic",
                            "Laos","Latvia","Lebanon","Lesotho","Liberia","Libya","Lithuania","Luxembourg","Madagascar","Malawi","Malaysia","Mali","Malta",
                            "Mauritania","Mauritius","Mexico","Moldova","Mongolia","Montenegro","Morocco","Mozambique","Myanmar","Namibia","Nepal","Netherlands",
                            "New Zealand","Nicaragua","Niger","Nigeria","North Macedonia","Norway","Oman","Pakistan","Panama","Papua New Guinea","Paraguay","Peru",
                            "Philippines","Poland","Portugal","Qatar","Romania","Russia","Rwanda","Saudi Arabia","Senegal","Serbia","Seychelles","Sierra Leone",
                            "Singapore","Slovakia","Slovenia","Somalia","South Africa","South Sudan","Spain","Sri Lanka","Sudan","Sweden","Switzerland","Syria",
                            "Taiwan","Tajikistan","Tanzania","Thailand","Timor Leste","Togo","Trinidad and Tobago","Tunisia","Turkmenistan","Türkiye","USSR",
                            "Uganda","Ukraine","United Arab Emirates","United Kingdom","United States of America","Uruguay","Uzbekistan","Venezuela","Viet Nam",
                            "Yemen","Yemen, North","Yugoslavia","Zambia","Zimbabwe"]
            }
        response = requests.post(url, headers = headers, json = query_payload, verify = False)
        print(response.content)
    yield f"Collected {IndicatorCode} data"

def collectSIPRIdata(RawData, IndicatorCode, **kwargs):
    if IndicatorCode == "ARMEXP":

        url = "https://atbackend.sipri.org/api/p/trades/import-export-csv/"
        headers = {
            "Origin": "https://armstransfers.sipri.org",
            "Referer": "https://armstransfers.sipri.org",
            "Content-Type": "application/json"
            }
        query_payload = {
            "filters":[{"field":"Year range 1","oldField":"","condition":"contains","value1":1990,"value2":2025,"listData":[]},
                    {"field":"orderbyseller","oldField":"","condition":"","value1":"","value2":"","listData":[]},
                    {"field":"DeliveryType","oldField":"","condition":"","value1":"delivered","value2":"","listData":[]},
                    {"field":"Status","oldField":"","condition":"","value1":"0","value2":"","listData":[]}],
            "logic":"AND"}
        response = requests.post(url, headers = headers, payload = query_payload)
        print(response.content)

    local_csv_file = pd.read_csv(RawData)
    csv_string = local_csv_file.to_csv(index=False)  
    count = sspi_raw_api_data.raw_insert_one(csv_string, IndicatorCode, **kwargs)
    yield f"\nInserted {count} observations into the database.\n"
    yield f"Collection complete for {IndicatorCode}\n"

def cleanSIPRIData(RawData, IndName, Unit, Description):  
    df = pd.read_csv(StringIO(RawData))
    df_melted = df.melt(id_vars=['Countries'], 
                     value_vars=df.columns, 
                     var_name='Year', 
                     value_name='Value')
    
    df_melted['Unit'] = Unit
    df_melted["Description"] = Description
    df_melted['IndicatorCode'] = IndName
    # df_melted.to_csv('transformed_data.csv', index=False)
    df_melted.replace("", "#N/A", inplace=True)
    df_final = df_melted.dropna()
    df_final['Countries'] = df_final['Countries'].str.lower()
    df_final = df_final[~df_final['Countries'].isin(['unknown supplier(s)', 'yugoslavia','soviet union', 
                                                     'east germany (gdr)','united nations**', 'south vietnam','south yemen','north yemen',
                                                     'european union**'
                                                     ])]

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
    df_f = df_final.drop('Countries', axis = 1)
    
    return df_f
    
    