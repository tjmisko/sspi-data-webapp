from datetime import datetime
import requests
from ..resources.adapters import raw_insert_many

def collectIEAData(IEAIndicatorCode, IndicatorCode, IntermediateCode="NA", Username="NA"):
    response = requests.get(f"https://api.iea.org/stats/indicator/{IEAIndicatorCode}").json()
    count = raw_insert_many(response, IndicatorCode, IntermediateCode, Username)
    yield f"Successfully inserted {count} observations into the database"