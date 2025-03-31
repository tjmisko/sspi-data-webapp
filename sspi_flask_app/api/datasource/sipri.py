
from sspi_flask_app.models.database import sspi_raw_api_data
import pandas as pd 
from ..resources.utilities import get_country_code
def collectSIPRIdata(IndicatorCode, **kwargs):
    local_csv_file = pd.read_csv('local/share.csv')
    csv_string = local_csv_file.to_csv(index=False)  
    count = sspi_raw_api_data.raw_insert_one(csv_string, IndicatorCode, **kwargs)
    yield f"\nInserted {count} observations into the database.\n"
    yield f"Collection complete for {IndicatorCode}\n"

def cleanSIPRIData(RawData, IndName):
    local_csv_file = pd.read_csv('local/share.csv')
   # columns = ['Country', '2014', 'Rank_2014', '2017', 'Rank_2017', '2018', 'Rank_2018','2020', 'Rank_2020', '2024', 'Rank_2024']
    #df = pd.DataFrame(local_csv_file, columns=columns)

    #df_year_only = df.drop(['Rank_2014','Rank_2017', 'Rank_2018', 'Rank_2020', 'Rank_2024'], axis = 1)
    df_melted = local_csv_file.melt(id_vars=['Country'], 
                     value_vars=local_csv_file.columns, 
                     var_name='Year', 
                     value_name='Value')
    
    df_melted['Unit'] = 'Percentage'
    df_melted['IndicatorCode'] = 'MILEXP'
    df_final = df_melted.dropna()

    df_final['CountryCode'] = df_final['Country'].apply(get_country_code)
    df_final['Year'] = df_final['Year'].astype(int)
    df_f = df_final.drop('Country', axis = 1)
    return df_f
    
    