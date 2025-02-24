import requests
from sspi_flask_app.models.database import sspi_raw_api_data
from io import BytesIO
import zipfile
import fitz
import pycountry 
import pandas as pd
#Notes:
#Use google sheet, use a new tab for every report.
#format as it is in the report.
#Source: add the hyperlink
#Final tab, pull all tables in one sheet
#csv, pdf Readme, original pdfs
#have raw data for each sheet, for 2024 have another clean sheet.

def collect_itu_data(IndicatorCode, **kwargs):
    local_csv_file = pd.read_csv('local/gci-local-indicator-summary.csv')
    csv_string = local_csv_file.to_csv(index=False)  # Exclude index for a cleaner format
    count = sspi_raw_api_data.raw_insert_one(csv_string, IndicatorCode, **kwargs)
    yield f"\nInserted {count} observations into the database.\n"
    yield f"Collection complete for {IndicatorCode}\n"

#reorganize the mongo data - pivot and set columns country, country code, year, value, rank - pull this down in collect route.
def cleanITUData_cybsec(RawData, IndName):
    local_csv_file = pd.read_csv('local/gci-local-indicator-summary.csv')
    columns = ['Country', '2014', 'Rank_2014', '2017', 'Rank_2017', '2018', 'Rank_2018', '2020', 'Rank_2020', '2024', 'Rank_2024']
    df = pd.DataFrame(local_csv_file, columns=columns)
    df_year_only = df.drop(['Rank_2014','Rank_2017', 'Rank_2018', 'Rank_2020', 'Rank_2024'], axis = 1)
    df_year_only['2024'] = df_year_only['2024']/ 100
    df_melted = df_year_only.melt(id_vars=['Country'], 
                     value_vars=['2014', '2017', '2018', '2020', '2024'], 
                     var_name='Year', 
                     value_name='Value')
   # print(df_melted)
    df_melted['Unit'] = 'Percentage'
    df_melted['IndicatorCode'] = 'CYBSEC'
    df_final = df_melted.dropna()
    def get_country_code(country_name):
        if pd.isnull(country_name):  # Check if country_name is NaN or null
            return None
        try:
            country = pycountry.countries.get(name=country_name)
            if country:
                return country.alpha_3  # ISO-3 country code
            else:
                return None  # Return None if the country is not found
        except KeyError:
            return None  # Return None if there's an error
    # missing_country_codes = df_final[df_final['CountryCode'].isnull()]
    # print("Countries with missing or invalid codes:")
    # print(missing_country_codes[['Country', 'Value']])
    df_final['CountryCode'] = df_final['Country'].apply(get_country_code)
    

    # result = []
    # for index, row in df.iterrows():
    #     for year in ['2014', '2017', '2018', '2020', '2024']:
    #         if row[year]!= None:
    #             entry = {
    #                 "CountryCode": iso3,
    #                 "IndicatorCode": IndName,
    #                 "Year": year,
    #                 "Value": row[year],
    #                 "Unit": "Percentage"
    #             }
    #             result.append(entry)
    return df_final
    
    
    #    clean_data_list = []
    # for entry in RawData:
    #     iso3 = entry["Raw"]["country"]
    #     country_data = countries.get(alpha_3=iso3)
    #     value = entry["Raw"]['value']
    #     if not country_data:
    #         continue
    #     if not value:
    #         continue
    #     clean_obs = {
    #         "CountryCode": iso3,
    #         "IndicatorCode": IndName,
    #         "Year": entry["Raw"]["year"],
    #         "Value": entry["Raw"]["value"],
    #         "Unit": entry['Raw']['units'],
    #         "IntermediateCode": entry['Raw']['product']
    #     }
    #     clean_data_list.append(clean_obs)
    # return clean_data_list

    # def clean_IEA_data_GTRANS(raw_data, indicator_code, description):
    # def convert_to_kg(value):
    #     return value * 1000000
    # clean_data_list = []
    # for obs in raw_data:
    #     iso3 = obs["Raw"]["country"]
    #     country_data = countries.get(alpha_3=iso3)
    #     value = obs["Raw"]['value']
    #     intermediate_code = obs["IntermediateCode"]
    #     series_label = obs["Raw"]["seriesLabel"]
    #     if series_label != "Transport":
    #         continue
    #     if not country_data:
    #         continue
    #     if not value:
    #         continue
    #     clean_obs = {
    #         "CountryCode": iso3,
    #         "IndicatorCode": indicator_code,
    #         "Year": obs["Raw"]["year"],
    #         "Value": convert_to_kg(obs["Raw"]["value"]),
    #         "Unit": "Tonnes C02 per inhabitant",
    #         "Description": description,
    #         "IntermediateCode": intermediate_code
    #     }
    #     clean_data_list.append(clean_obs)
    # return clean_data_list