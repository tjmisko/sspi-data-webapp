from datetime import datetime
import requests
from ... import sspi_raw_api_data
from flask_login import current_user
from flask import redirect, url_for
from ..api import raw_insert_many
def collectIEAData(IEAIndicatorCode, IndicatorCode, IntermediateCode="NA"):
    response = requests.get(f"https://api.iea.org/stats/indicator/{IEAIndicatorCode}").json()
    count = raw_insert_many(response, IndicatorCode, IntermediateCode)
    yield f"Successfully inserted {count} observations into the database"