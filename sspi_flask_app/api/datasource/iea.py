import requests
from ... import sspi_raw_api_data

def collectIEAData(IEAIndicatorCode, IndicatorCode, **kwargs):
    raw_data = requests.get(f"https://api.iea.org/stats/indicator/{IEAIndicatorCode}").json()
    count = sspi_raw_api_data.raw_insert_many(raw_data, IndicatorCode, **kwargs)
    yield f"Successfully inserted {count} observations into the database"
