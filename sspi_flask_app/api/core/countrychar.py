import pandas as pd
import numpy as np
from pycountry import countries
from ... import sspi_country_characteristics

def insert_pop_data():
    pop_data = pd.read_csv("local/UN_population_data.csv").astype(str).drop(columns = "Unnamed: 0")
    pop_data["CountryCode"] = pop_data["country"].map(lambda cou: countries.get(name = cou).alpha_3 
                                                       if countries.get(name = cou) is not None else np.nan)
    pop_data = pop_data.dropna()
    pop_data["year"] = (pop_data["year"]).astype(int)
    pop_data["pop"] = (pop_data["pop"]).astype(int)
    obs_list = []
    intermediate_code = "UNPOPL"
    country_list = pop_data["CountryCode"].unique().tolist()
    count = 0
    for country in country_list:
        country_df = pop_data[pop_data["CountryCode"] == country]
        country_years = country_df["year"].tolist()
        for year in country_years:
            value = country_df[country_df["year"] == year]["pop"].values[0]
            obs = {"CountryCode": country,
                   "Value": int(value),
                   "Year": year,
                   "Unit": "population",
                   "IntermediateCode": intermediate_code
            }
            count += 1
            obs_list.append(obs)
    sspi_country_characteristics.insert_many(obs_list)
    yield f"Done! {count} UN population observations inserted into sspi_country_characteristics"
