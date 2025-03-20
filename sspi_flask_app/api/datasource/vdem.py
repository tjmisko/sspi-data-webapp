from sspi_flask_app.models.database import sspi_raw_api_data
import requests
import zipfile
from io import BytesIO


# Assuming sspi_raw_api_data.raw_insert_one(record, IndicatorCode, **kwargs) is available
# It should insert a document with the given record.
def collectVDEMData(SourceIndicatorCode, IndicatorCode, **kwargs):
    """
    Collect V-Dem data for the given indicator.
    For each CSV file in the downloaded zip, if the CSV contains a column named
    SourceIndicatorCode, then for every row, a record is created and inserted using
    sspi_raw_api_data.raw_insert_one. Each record has the following required fields:

      - IndicatorCode: provided indicator code.
      - Raw: a dict containing the source indicator value, the three-letter country code,
             and the year.
      - CollectedAt: the datetime when the collection was performed.
      - Username: the application user running the collection (from kwargs, default "unknown").

    The function yields status messages as it processes files.
    """
    url = "https://v-dem.net/media/datasets/V-Dem-CY-FullOthers_csv_v13.zip"
    res = requests.get(url)
    if res.status_code != 200:
        err = f"(HTTP Error {res.status_code})"
        yield "Failed to fetch data from source " + err
        return
    collected_count = 0
    with zipfile.ZipFile(BytesIO(res.content)) as z:
        for filename in z.namelist():
            if ".csv" not in filename:
                continue
            yield f"Processing file: {filename}\n"
            with z.open(filename) as data:
                csv_string = data.read().decode("utf-8")
                print(len(csv_string))
                sspi_raw_api_data.raw_insert_one({"csv": csv_string}, IndicatorCode, **kwargs)
    yield f"Collection complete for {IndicatorCode} (VDEM {SourceIndicatorCode}). {collected_count} records inserted."
