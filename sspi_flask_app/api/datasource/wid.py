import requests
import pycountry
import io
import zipfile
from io import StringIO
import pandas as pd
from sspi_flask_app.models.database import sspi_raw_api_data


def collectWIDData(IndicatorCode, **kwargs):
    yield "Requesting WID data from source\n"
    res = requests.get("https://wid.world/bulk_download/wid_all_data.zip")
    res.raise_for_status()
    yield "Received WID data\n"
    zip_file = io.BytesIO(res.content)
    with zipfile.ZipFile(zip_file) as z:
        for file_name in z.namelist():
            yield f"Processing {file_name}\n"
            file_name_fields = file_name.split(".")[0].split("_")
            if len(file_name_fields) != 3 or 'metadata' in file_name_fields:
                yield f"Skipping {file_name}\n"
                continue  # Don't save state-level data or metadata
            with z.open(file_name) as f:
                raw = f.read().decode('utf-8')
                sspi_raw_api_data.raw_insert_one(
                    raw, IndicatorCode, DatasetName=file_name, **kwargs
                )


def filterWIDcsv(csv_string: str, csv_filename: str, target_vars: list[str], variable: str, years: list[int]) -> pd.DataFrame:
    ccode_alpha_2 = csv_filename.split(".")[0].split("_")[2]
    country = pycountry.countries.get(alpha_2=ccode_alpha_2)
    if not country:
        return []
    CountryCode = country.alpha_3
    virtual_csv = StringIO(csv_string)
    raw_df = pd.read_csv(virtual_csv, delimiter=';')
    has_target = raw_df['percentile'].isin(target_vars).any()
    var_filter = variable in raw_df['variable'].values
    if not has_target or not var_filter:
        return []
    ptinc = raw_df[raw_df['variable'] == variable].reset_index(drop=True)
    ptinc = ptinc[ptinc['percentile'].isin(target_vars)]
    ptinc = ptinc[ptinc['year'].isin(years)]
    col_map = {'year': 'Year', 'percentile': 'Percentile', 'value': "Value"}
    ptinc = ptinc[['year', 'value', 'percentile']].rename(columns=col_map)
    ptinc['CountryCode'] = CountryCode
    return ptinc.to_dict(orient="records")
