import requests
from io import BytesIO
import pandas as pd
from sspi_flask_app.models.database import sspi_raw_api_data

def collectWEFdata(SourceIndicatorCode, IndicatorCode, **kwargs):
    url = "https://thedocs.worldbank.org/en/doc/cf8eee7ff5029398f75e897b342e7320-0050122023/related/WEF-GCIHH.xlsx"
    res = requests.get(url)
    if res.status_code != 200:
        err = f"(HTTP Error {res.status_code})"
        yield "Failed to fetch data from source " + err
        return
    

    df = pd.read_excel(BytesIO(res.content))
    
    if SourceIndicatorCode in df.columns:
        df = df[[SourceIndicatorCode]]  #
        df = df.rename(columns={SourceIndicatorCode: IndicatorCode})
    else:
        yield f"Column {SourceIndicatorCode} not found in the Excel sheet."
        return


    csv_string = df.to_csv(index=False)


    sspi_raw_api_data.raw_insert_one({"csv": csv_string}, IndicatorCode, **kwargs)
    
    yield f"Collection complete for {IndicatorCode} (WEF {SourceIndicatorCode})"

