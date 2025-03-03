import requests
from sspi_flask_app.models.database import sspi_raw_api_data
from io import StringIO
import json
import pandas as pd


## Note: Tax Foundation doesn't offer any APIs for dynamic data retrieval, 
## so I was stuck using their latest data.

def collectTaxFoundationData(IndicatorCode, **kwargs):
    url = "https://taxfoundation.org/wp-content/uploads/2025/01/rates_final.csv"
    res = requests.get(url)
    if res.status_code != 200:
        err = f"(HTTP Error {res.status_code})"
        yield "Failed to fetch data from source" + err
        return
    csv_string = res.text
    sspi_raw_api_data.raw_insert_one(
                            {"csv": csv_string}, IndicatorCode, **kwargs
                        )
    yield f"Collection complete for {IndicatorCode}"

def cleanTaxFoundation(RawData, IndName, Unit, Description):
    csv_file = StringIO(RawData[0]['Raw']['csv'])
    csv_file.seek(0)

    crptax = pd.read_csv(csv_file)
    crptax_clean = crptax.drop(columns=["Unnamed: 0", "iso_2", "continent", "country"])
    crptax_melted = pd.melt(crptax_clean, id_vars=['iso_3'],var_name='Year',value_name='Value')
    crptax_melted = crptax_melted.rename(columns={'iso_3':'CountryCode'})
    crptax_melted = crptax_melted.dropna()
    crptax_melted = crptax_melted.sort_values(['CountryCode','Year'],ascending=[True,False]).reset_index(drop=True)
    #crptax_melted["Year"] = crptax_melted["Year"].map(lambda x: int(x))
    crptax_melted['IndicatorCode'] = IndName
    crptax_melted['Unit'] = Unit
    crptax_melted['Description'] = Description
    crptax_str = crptax_melted.to_json(orient='records',lines=False)
    crptax = json.loads(crptax_str)
    return crptax
    