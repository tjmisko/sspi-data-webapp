from sspi_flask_app.models.database import sspi_raw_api_data
import csv
import requests
import zipfile
from io import BytesIO, StringIO


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
    if res.status_code != 200:
        err = f"(HTTP Error {res.status_code})"
        yield "Failed to fetch data from source " + err
        return "Failed to fetch data from source " + err

    collected_count = 0
    num_fragments = 24

    with zipfile.ZipFile(BytesIO(res.content)) as z:
        for filename in z.namelist():
            if ".csv" not in filename:
                continue
            yield f"Processing file: {filename}\n"
            with z.open(filename) as data:
                csv_string = data.read().decode("utf-8")
                # Determine fragment size. Use integer division;
                # the last fragment will contain any remaining characters.
                frag_length = len(csv_string) // num_fragments
                for i in range(num_fragments):
                    start = i * frag_length
                    # For the last fragment, include the remainder
                    if i == num_fragments - 1:
                        fragment = csv_string[start:]
                    else:
                        fragment = csv_string[start:start + frag_length]
                    sspi_raw_api_data.raw_insert_one(
                        {"csv_fragment": fragment},
                        IndicatorCode,
                        FragmentNumber=i,  # 0-indexed order; change to i+1 if desired
                        **kwargs
                    )
                    collected_count += 1
    yield f"Collection complete for {IndicatorCode} (VDEM {SourceIndicatorCode}). {collected_count} fragments inserted."
