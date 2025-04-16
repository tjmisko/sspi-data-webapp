from sspi_flask_app.models.database import sspi_raw_api_data
import requests
import zipfile
from io import BytesIO


def collectVDEMData(SourceIndicatorCode, IndicatorCode, **kwargs):
    """
    Collect V-Dem data for the given indicator.
    Updated to fragment large CSV files into 24 slices to avoid exceeding BSON document size limits.

    For each CSV file in the downloaded zip file, the CSV is read as a string.
    That string is then divided into 24 fragments. Each fragment is inserted separately
    using sspi_raw_api_data.raw_insert_one. Each inserted record has:

      - IndicatorCode: provided indicator code.
      - Raw: a dict containing one fragment of the CSV file (under the key "csv_fragment").
      - FragmentNumber: an integer (0-based) indicating the order of the fragment for later reassembly.
      - CollectedAt, Username, etc.: passed via kwargs.

    The function yields status messages as it processes each file and fragment.
    """
    url = "https://v-dem.net/media/datasets/V-Dem-CY-FullOthers_csv_v13.zip"
    res = requests.get(url)
    with zipfile.ZipFile(BytesIO(res.content)) as z:
        for filename in z.namelist():
            if ".csv" not in filename:
                continue
            yield f"Processing file: {filename}\n"
            with z.open(filename) as data:
                csv_string = data.read().decode("utf-8")
                sspi_raw_api_data.raw_insert_one(
                    csv_string,
                    IndicatorCode,
                    **kwargs
                )
    yield f"Collection complete for {IndicatorCode} (VDEM {SourceIndicatorCode})."
