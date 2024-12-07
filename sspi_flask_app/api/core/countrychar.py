import pandas as pd
import numpy as np
import pycountry
from pycountry import countries
from sspi_flask_app.models.database import sspi_country_characteristics

def insert_pop_data():
    pop_data = pd.read_csv("local/UN_population_data.csv").astype(str).drop(columns = "Unnamed: 0")
    country_codes = []
    missing_codes = []
    for country in pop_data["country"]:
        country_code = ""
        if country == "Republic of Korea":
            country = "KOR"
        if country == "TÃ¼rkiye":
            country = "TUR"
        try:
            country_code = pycountry.countries.search_fuzzy(country)[0].alpha_3
        except LookupError:
            missing_codes.append(country)
            country_code = np.nan
            country_codes.append(country_code)
            continue
        country_codes.append(country_code)
    pop_data["CountryCode"] = country_codes
    pop_data = pop_data.dropna()
    pop_data["year"] = (pop_data["year"]).astype(int)
    pop_data["pop"] = (pop_data["pop"]).astype(int)
    print(pop_data)
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
