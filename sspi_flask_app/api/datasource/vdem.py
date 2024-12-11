import requests
from io import BytesIO
import zipfile
from sspi_flask_app.models.database import sspi_raw_api_data


def collectVDEMData(SourceIndicatorCode, IndicatorCode, **kwargs):
    url = "https://v-dem.net/media/datasets/V-Dem-CY-FullOthers_csv_v13.zip"
    res = requests.get(url)
    if res.status_code != 200:
        err = f"(HTTP Error {res.status_code})"
        yield "Failed to fetch data from source" + err
        return
    with zipfile.ZipFile(BytesIO(res.content)) as z:
        for f in z.namelist():
            if "__MACOSX" in f:
                continue
            yield str(f) + "\n"
            if SourceIndicatorCode in f:
                with z.open(f) as data:
                    csv_string = data.read().decode("utf-8")
                    sspi_raw_api_data.raw_insert_one(
                        {"csv": csv_string}, IndicatorCode, **kwargs
                    )
    yield f"Collection complete for {IndicatorCode} (EPI {SourceIndicatorCode})"


