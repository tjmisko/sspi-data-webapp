
from sspi_flask_app.models.database import sspi_raw_api_data
import pandas as pd 
from ..resources.utilities import get_country_code
import requests



def collectSIPRIdata(RawData, IndicatorCode, **kwargs):
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
    print(RawData)
    local_csv_file = pd.read_csv(RawData)
   # columns = ['Country', '1949', '1950' '1951', '1952', '1953', '1954', '1955', '1956', '1957', '1958', '1959', '1960', '1961', '1962', '1963', '1964', '1965', '1966', '1967', '1968', '1969', '1970', '1971', '1972', '1973', '1974', '1975', '1976', '1977', '1978', '1979', '1980', '1981', '1982', '1983', '1984', '1985', '1986', '1987', '1988', '1989', '1990', '1991', '1992', '1993', '1994', '1995', '1996', '1997', '1998', '1999', '2000', '2001', '2002', '2003', '2004', '2005', '2006', '2007', '2008', '2009', '2010', '2011', '2012', '2013', '2014', '2015', '2016', '2017', '2018', '2019', '2020', '2021', '2022', '2023']
    df = pd.DataFrame(local_csv_file, columns=local_csv_file.columns)

    #df_year_only = df.drop(['Rank_2014','Rank_2017', 'Rank_2018', 'Rank_2020', 'Rank_2024'], axis = 1)
    df_melted = df.melt(id_vars=['Country'], 
                     value_vars=df.columns, 
                     var_name='Year', 
                     value_name='Value')
    
    df_melted['Unit'] = Unit
    df_melted["Description"] = Description
    df_melted['IndicatorCode'] = IndName
    # df_melted.to_csv('transformed_data.csv', index=False)
    df_final = df_melted.dropna()
   # df_final['CountryCode'] = df_final['Country'].apply(get_country_code)
    df_final['CountryCode'] = df_final['Country'].apply(
    lambda country: get_country_code(country) if country.lower() not in ['czechoslovakia', 'german democratic republic', 'yemen north'] else None)


    df_final.loc[df_final['Country'] == 'Czechoslovakia', 'CountryCode'] = 'CSK'
    df_final.loc[df_final['Country'] == 'German Democratic Republic', 'CountryCode'] = 'DDR'
    df_final.loc[df_final['Country'] == 'Yemen North', 'CountryCode'] = 'YMD'
   # df_final['CountryCode'] = df_final['Country'].astype(str) 
    df_final['Year'] = df_final['Year'].astype(int)
    df_f = df_final.drop('Country', axis = 1)
    return df_f
    
    