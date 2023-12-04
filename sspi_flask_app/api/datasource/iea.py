from datetime import datetime
import requests
from ..resources.adapters import raw_insert_many

def collectIEAData(IEAIndicatorCode, IndicatorCode, **kwargs):
    raw_data = requests.get(f"https://api.iea.org/stats/indicator/{IEAIndicatorCode}").json()
    count = raw_insert_many(raw_data, IndicatorCode, **kwargs)
    yield f"Successfully inserted {count} observations into the database"
