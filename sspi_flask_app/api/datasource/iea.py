from datetime import datetime
import requests
from ... import sspi_raw_api_data
from flask_login import current_user
from flask import redirect, url_for
from ..api import store_raw_observation

def collectIEAData(IndicatorCode, RawDataDestination):
    collection_time = datetime.now()
    response = requests.get("https://api.iea.org/stats/indicator/" + IndicatorCode + "/").json()
    print(response)
    for observation in response:  
        store_raw_observation(observation, collection_time, RawDataDestination)
    return redirect(url_for('client_bp.data'))