from sspi_flask_app.models.database import sspi_raw_api_data
import requests
import time
from pycountry import countries
from ..resources.utilities import string_to_float


def collectUISdata(UISIndicatorCode, IndicatorCode, **kwargs):
    yield f"Collecting data for UNESCO Institute for Statistics Indicator {UISIndicatorCode}\n"
    url_source = f"https://api.uis.unesco.org/api/public/data/indicators?indicator={UISIndicatorCode}"
    response = requests.get(url_source).json()
    count = 0
    document_list = []
    for obs in response["records"]:
        count += 1
        document_list.append(obs)
    sspi_raw_api_data.raw_insert_many(document_list, IndicatorCode, **kwargs)
    yield f"Inserted {count} data points; collection complete for UNESCO Institute for Statistics Indicator {UISIndicatorCode}"


def cleanUISdata(raw_data, IndicatorCode, unit, description):
    clean_data_list = []
    for obs in raw_data:
        country = obs["Raw"]["geoUnit"]
        country_data = countries.get(alpha_3 = country)
        if not country_data:
            continue
        year = int(obs["Raw"]["year"])
        value = obs["Raw"]["value"]
        if value == "NaN" or value is None or not value:
            continue
        clean_obs = {
            "CountryCode": country,
            "IndicatorCode": IndicatorCode,
            "Description": description,
            "Year": year,
            "Unit": unit,
            "Value": string_to_float(value)
        }
        clean_data_list.append(clean_obs)
    return clean_data_list
