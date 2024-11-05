import pandas as pd
import numpy as np
from pycountry import countries
from sspi_flask_app.models.database import sspi_outcome_data

def insert_outcome_data():
    outcome_data = pd.read_excel("local/2024-10-20 - FROZEN 3.0 Indicator and Outcome Data.xlsx", 
                sheet_name = "Outcome Variables").loc[4:52, :].rename(columns = {"Source": "Country", "Unnamed: 1": 
                "Country_code", "Unnamed: 2": "Region", "Unnamed: 3": "Region", "World Bank": "GDP per capita"}).reset_index(drop = True)
    obs_list = []
    count = 0
    for index in range(0, len(outcome_data)):
        row = outcome_data.iloc[index, :]
        for index in row.index[4:]:
            obs = {"CountryCode": row["Country_code"],
                    "Value": row[index],
                    "Year": 2018,
                    "Unit": index,
                    "IntermediateCode": "OCDATA"}
            obs_list.append(obs)
            count += 1
    sspi_outcome_data.insert_many(obs_list)
    yield f"Done! {count} outcome variable observations inserted into sspi_outcome_data"
    # return outcome_data
    # pop_data["CountryCode"] = pop_data["country"].map(lambda cou: countries.get(name = cou).alpha_3 
    #                                                    if countries.get(name = cou) is not None else np.nan)
    # pop_data = pop_data.dropna()
    # pop_data["year"] = (pop_data["year"]).astype(int)
    # pop_data["pop"] = (pop_data["pop"]).astype(int)
    # obs_list = []
    # intermediate_code = "UNPOPL"
    # country_list = pop_data["CountryCode"].unique().tolist()
    # count = 0
    # for country in country_list:
    #     country_df = pop_data[pop_data["CountryCode"] == country]
    #     country_years = country_df["year"].tolist()
    #     for year in country_years:
    #         value = country_df[country_df["year"] == year]["pop"].values[0]
    #         obs = {"CountryCode": country,
    #                "Value": int(value),
    #                "Year": year,
    #                "Unit": "population",
    #                "IntermediateCode": intermediate_code
    #         }
    #         count += 1
    #         obs_list.append(obs)
    # sspi_country_characteristics.insert_many(obs_list)
    # yield f"Done! {count} UN population observations inserted into sspi_country_characteristics"