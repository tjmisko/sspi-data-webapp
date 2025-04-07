from sspi_flask_app.models.database import sspi_raw_api_data
import csv
import requests
import zipfile
from io import BytesIO, StringIO
import pandas as pd


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


def cleanEDEMOCdata(raw_data):
    fragments = []
    for obs in raw_data:
        try:
            fragment_num = obs.get("FragmentNumber")
            csv_fragment = obs.get("Raw", {}).get("csv_fragment", "")
            if fragment_num is not None and csv_fragment:
                fragments.append((fragment_num, csv_fragment))
        except Exception as e:
            continue

    if not fragments:
        return "No CSV fragments found for EDEMOC."
    fragments.sort(key=lambda x: x[0])
    full_csv = "".join(fragment for _, fragment in fragments)
    try:
        df = pd.read_csv(StringIO(full_csv))
    except Exception as e:
        return f"Error reading CSV data: {e}"
    filtered_df = df[['country_text_id', 'year', 'v2x_polyarchy']]
    filtered_df = df[(df["year"] > 1900) & (df["year"] < 2030)]
    # Identify year columns. If none are found (since 'year' is already present), we use the existing 'year'.
    year_columns = [col for col in filtered_df.columns if col.isdigit()]
    id_vars = [col for col in filtered_df.columns if col not in year_columns]
    if year_columns:
        df_melted = filtered_df.melt(
            id_vars=id_vars,
            value_vars=year_columns,
            var_name="Year",
            value_name="Value"
        )
        df_melted["Year"] = df_melted["Year"].astype(int)
    else:
        df_melted = filtered_df.rename(columns={"year": "Year", "v2x_polyarchy": "Value"})
        df_melted["Year"] = df_melted["Year"].astype(int)

    df_sorted = df_melted.sort_values(by=["country_text_id", "Year"])
    df_sorted["CountryCode"] = df_sorted["country_text_id"]
    df_sorted["Unit"] = "Index"
    df_sorted["Description"] = "Index seeks to embody the core values that make rulers responsive to citizens through elections and freedom of expression."
    df_sorted["IndicatorCode"] = "EDEMOC"
    df_final = df_sorted[["CountryCode", "Year", "Value", "Unit", "IndicatorCode", "Description"]]
    records = df_final.to_dict(orient="records")
    return records
