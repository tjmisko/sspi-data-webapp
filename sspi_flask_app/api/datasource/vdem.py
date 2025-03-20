import requests
from io import BytesIO
import zipfile
from sspi_flask_app.models.database import sspi_raw_api_data


def collectVDEMData(SourceIndicatorCode, IndicatorCode, **kwargs):
    url = "https://v-dem.net/media/datasets/V-Dem-CY-FullOthers_csv_v13.zip"
    res = requests.get(url)
    if res.status_code != 200:
        err = f"(HTTP Error {res.status_code})"
        yield "Failed to fetch data from source " + err
        return "Failed to fetch data from source " + err
    collected_count = 0
    with zipfile.ZipFile(BytesIO(res.content)) as z:
        for filename in z.namelist():
            if ".csv" not in filename:
                continue
            yield f"Processing file: {filename}\n"
            with z.open(filename) as data:
                csv_string = data.read().decode("utf-8")
                print(len(csv_string))
                sspi_raw_api_data.raw_insert_one(
                    {"csv": csv_string}, IndicatorCode, **kwargs)
    yield f"Collection complete for {IndicatorCode} (VDEM {SourceIndicatorCode}). {collected_count} records inserted."
