from datetime import datetime
import requests
from ... import sspi_raw_api_data
from flask_login import current_user
from flask import redirect, url_for
from ..api import store_raw_api_data

def collectIEAData(IndicatorCode, RawDataDestination):
    collection_time = datetime.now()
    response = requests.get("https://api.iea.org/stats/indicator/" + IndicatorCode + "/").json()
    store_raw_api_data(response, collection_time, RawDataDestination)
    return redirect(url_for('home_bp.data'))





