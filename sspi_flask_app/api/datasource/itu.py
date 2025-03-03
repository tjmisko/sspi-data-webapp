from sspi_flask_app.models.database import sspi_raw_api_data
import pycountry 
import pandas as pd 
from ..resources.utilities import get_country_code
def collect_itu_data(IndicatorCode, **kwargs):
    local_csv_file = pd.read_csv('local/gci-local-indicator-summary.csv')
    csv_string = local_csv_file.to_csv(index=False)  
    count = sspi_raw_api_data.raw_insert_one(csv_string, IndicatorCode, **kwargs)
    yield f"\nInserted {count} observations into the database.\n"
    yield f"Collection complete for {IndicatorCode}\n"

def cleanITUData_cybsec(RawData, IndName):
    local_csv_file = pd.read_csv('local/gci-local-indicator-summary.csv')
    columns = ['Country', '2014', 'Rank_2014', '2017', 'Rank_2017', '2018', 'Rank_2018','2020', 'Rank_2020', '2024', 'Rank_2024']
    df = pd.DataFrame(local_csv_file, columns=columns)
    #initial data manipulation
    df['2024'] = df['2024'] / 100
    df['2020'] = df['2020'] / 100
    df['Country'] = df['Country'].replace('Cape Verde', 'Cabo Verde')
    df['Country'] = df['Country'].replace('Swaziland', 'Eswatini')

    #narrow down focus and clean the format
    df_year_only = df.drop(['Rank_2014','Rank_2017', 'Rank_2018', 'Rank_2020', 'Rank_2024'], axis = 1)
    df_melted = df_year_only.melt(id_vars=['Country'], 
                     value_vars=['2014', '2017', '2018', '2020', '2024'], 
                     var_name='Year', 
                     value_name='Value')
    
    df_melted['Unit'] = 'Percentage'
    df_melted['IndicatorCode'] = 'CYBSEC'
    #country with only one year data might not be ideal - no over time comparison.
    df_final = df_melted.dropna()

    #manually adjust the code
    df_final['CountryCode'] = df_final['Country'].apply(get_country_code)
    df_final['Year'] = df_final['Year'].astype(int)
    # df_final.loc[df_final['Country'] == 'Korea (the Republic of)', 'CountryCode'] = 'KOR'
    # df_final.loc[df_final['Country'] == 'Democratic Republic of the Congo', 'CountryCode'] = 'COD'
    # df_final.loc[df_final['Country'] == 'Niger', 'CountryCode'] = 'NER'
    df_f = df_final.drop('Country', axis = 1)
    return df_f
    
    