from datetime import datetime
import requests
from ... import sspi_raw_api_data
from flask_login import current_user
from flask import redirect, url_for


def collectIEAData(IndicatorCode, RawDataDestination):
    collection_time = datetime.now()
    response = requests.get("https://api.iea.org/stats/indicator/" + IndicatorCode + "/").json()
    store_raw_api_data(response, collection_time, RawDataDestination)
    return redirect(url_for('home_bp.data'))

def store_raw_api_data(response, collection_time, RawDataDestination):
    """
    Store the response from an API call in the database
    """
    try:
        for r in response:
            sspi_raw_api_data.insert_one(
                {"collection-info": {"CollectedBy": current_user.username,
                                    "RawDataDestination": RawDataDestination,
                                    "CollectedAt": collection_time}, 
                "observation": r}) 
        return response
    except Exception as e:
        print("Error storing API data:", e)
        return "Error storing API data"




