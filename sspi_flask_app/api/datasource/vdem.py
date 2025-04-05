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


                df = df[[SourceIndicatorCode]].rename(columns={SourceIndicatorCode: IndicatorCode})


                filtered_csv_string = df.to_csv(index=False)
                
                print(csv_string)

                sspi_raw_api_data.raw_insert_one({"csv": filtered_csv_string}, IndicatorCode, **kwargs)
                
    yield f"Collection complete for {IndicatorCode} (EPI {SourceIndicatorCode})"


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
    df_sorted["IndicatorCode"] = "EDEMOC"
    df_final = df_sorted[["CountryCode", "Year", "Value", "Unit", "IndicatorCode"]]
    records = df_final.to_dict(orient="records")
    return records
