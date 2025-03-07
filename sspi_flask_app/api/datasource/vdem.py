
from sspi_flask_app.models.database import sspi_raw_api_data
import csv
import requests
import zipfile
from io import BytesIO, StringIO
from datetime import datetime


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

    username = kwargs.get("username", "unknown")
    url = "https://v-dem.net/media/datasets/V-Dem-CY-FullOthers_csv_v13.zip"
    res = requests.get(url)
    if res.status_code != 200:
        err = f"(HTTP Error {res.status_code})"
        yield "Failed to fetch data from source " + err
        return

    collected_count = 0
    with zipfile.ZipFile(BytesIO(res.content)) as z:
        for filename in z.namelist():
            # Skip macOS system folders or non-CSV files
            if "__MACOSX" in filename or not filename.lower().endswith('.csv'):
                continue
            yield f"Processing file: {filename}\n"
            with z.open(filename) as data:
                csv_string = data.read().decode("utf-8")
                csv_io = StringIO(csv_string)
                reader = csv.DictReader(csv_io)
                # Check if the CSV has the specified SourceIndicatorCode column
                if SourceIndicatorCode not in reader.fieldnames:
                    yield f"Column '{SourceIndicatorCode}' not found in {filename}\n"
                    continue
                # Verify that required additional columns are present
                required_columns = ["country_text_id", "year"]
                missing = [col for col in required_columns if col not in reader.fieldnames]
                if missing:
                    yield f"Missing required columns {missing} in {filename}\n"
                    continue

                # Process each row in the CSV
                for row in reader:
                    # Build the raw data from the row
                    raw_data = {
                        "Value": row.get(SourceIndicatorCode),
                        "Country": row.get("country_text_id"),
                        "Year": row.get("year")
                    }
                    record = {
                        "IndicatorCode": IndicatorCode,
                        "Raw": raw_data,
                        "CollectedAt": datetime.now(),
                        "Username": username
                    }
                    # Insert the record (this function is assumed to be defined elsewhere)
                    sspi_raw_api_data.raw_insert_one(record, IndicatorCode, **kwargs)
                    collected_count += 1

    yield f"Collection complete for {IndicatorCode} (VDEM {SourceIndicatorCode}). {collected_count} records inserted."
