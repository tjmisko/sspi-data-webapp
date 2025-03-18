from sspi_flask_app.models.database import sspi_raw_api_data
import requests
import time
from pycountry import countries
from ..resources.utilities import string_to_float

def collectUISdata(UISIndicatorCode, IndicatorCode, **kwargs):
    yield f"Collecting data for UNESCO Institute for Statistics Indicator {UISIndicatorCode}\n"
    url_source = f"https://api.uis.unesco.org/api/public/data/indicators?indicator={UISIndicatorCode}]"
    response = requests.get(url_source).json()
    count = 0
    for obs in response["records"]:
        count += 1
    sspi_raw_api_data.raw_insert_many(response, IndicatorCode, **kwargs)
    yield f"Inserted {count} data points; collection complete for UNESCO Institute for Statistics Indicator {UISIndicatorCode}"