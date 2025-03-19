import requests
from io import BytesIO, StringIO
import zipfile
import pandas as pd
from sspi_flask_app.models.database import sspi_raw_api_data


def collectVDEMData(SourceIndicatorCode, IndicatorCode, **kwargs):
    url = "https://v-dem.net/media/datasets/V-Dem-CY-FullOthers_csv_v13.zip"
    res = requests.get(url)
    if res.status_code != 200:
        err = f"(HTTP Error {res.status_code})"
        yield "Failed to fetch data from source " + err
        return

    with zipfile.ZipFile(BytesIO(res.content)) as z:
        for f in z.namelist():
            if "__MACOSX" in f:

                continue
            if f.lower().endswith(".csv"):
                yield f"Found CSV file: {f}\n"
                with z.open(f) as data:
                    csv_string = data.read().decode("utf-8")
                df = pd.read_csv(StringIO(csv_string))
                if SourceIndicatorCode not in df.columns:
                    yield f"Column {SourceIndicatorCode} not found in the CSV."
                    return
                df = df[[SourceIndicatorCode]].rename(
                    columns={SourceIndicatorCode: IndicatorCode})
                filtered_csv_string = df.to_csv(index=False)
                print(csv_string)
                sspi_raw_api_data.raw_insert_one(
                    {"csv": filtered_csv_string}, IndicatorCode, **kwargs)
    yield f"Collection complete for {IndicatorCode} (EPI {SourceIndicatorCode})"
