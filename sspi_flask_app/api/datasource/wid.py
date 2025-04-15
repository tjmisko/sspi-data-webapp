import requests
import io
import zipfile
from pycountry import countries
from io import StringIO
import pandas as pd
from sspi_flask_app.models.database import sspi_raw_api_data


def collectWIDData(IndicatorCode, **kwargs):
    byte_max = sspi_raw_api_data.maximum_document_size_bytes
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
                num_fragments = (len(raw) + byte_max - 1) // byte_max
                for i in range(num_fragments):
                    obs = {
                        "DatasetName": file_name,
                        "SourceOrganization": "WID",
                        "Raw": raw[byte_max * i:byte_max * i + byte_max],
                    }
                    if num_fragments > 1:
                        obs.update({
                            "FragmentGroupID": file_name,
                            "FragmentNumber": i,
                            "FragmentTotal": num_fragments,
                        })
                    sspi_raw_api_data.raw_insert_one(obs, IndicatorCode, **kwargs)


def processCSV(curr_csv, CountryCode):
    virtual_csv = StringIO(curr_csv)
    raw_df = pd.read_csv(virtual_csv, delimiter=';')
    target_vars = ['p0p50', 'p90p100']

    if not raw_df['percentile'].isin(target_vars).any() or 'sptincj992' not in raw_df['variable'].values:
        return []

    else:
        ptinc = raw_df[raw_df['variable'] ==
                       'sptincj992'].reset_index(drop=True)
        ptinc = ptinc[ptinc['percentile'].isin(target_vars)]
        ptinc['country'] = CountryCode
        ptinc = ptinc[['country', 'year', 'value', 'percentile']].rename(
            columns={'country': 'CountryCode', 'year': 'Year', 'percentile': 'Percentile'})

        return ptinc.to_dict(orient='records')


def cleanWIDData(raw_data):
    cleaned_obs = []
    for csv in raw_data:
        observation_cleaned = processCSV(
            csv['Raw']['Raw'], csv['Raw']['CountryCode'])
        cleaned_obs += observation_cleaned
    cleaned_df = pd.DataFrame(cleaned_obs)
    p0p50 = cleaned_df[cleaned_df['Percentile']
                       == 'p0p50'].drop(columns=['Percentile'])
    p90p100 = cleaned_df[cleaned_df['Percentile']
                         == 'p90p100'].drop(columns=['Percentile'])
    merged_df = pd.merge(p0p50, p90p100, on=[
                         'CountryCode', 'Year'], suffixes=('_p0p50', '_p90p100'))
    merged_df['Value'] = merged_df['value_p0p50'] / merged_df['value_p90p100']
    merged_df['IndicatorCode'] = 'ISHRAT'
    merged_df['Description'] = "The pre-tax national income share of the bottom 50% of households divided by the pre-tax national income share of the top 10% of households."
    merged_df['Unit'] = 'Proportion'
    merged_df = merged_df.drop(columns=['value_p0p50', 'value_p90p100'])
    merged_df = merged_df[merged_df['Year'] >= 1930]
    return merged_df.to_dict(orient='records')
