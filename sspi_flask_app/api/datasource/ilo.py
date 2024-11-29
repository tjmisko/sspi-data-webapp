import requests
from sspi_flask_app.models.database import sspi_raw_api_data
from io import BytesIO
import zipfile


def collectILOData(ILOIndicatorCode, IndicatorCode, QueryParams="", URLParams=[], **kwargs):
    yield "Sending Data Request to ILO API\n"
    api_url = f"https://sdmx.ilo.org/rest/data/ILO,{ILOIndicatorCode}"
    if QueryParams:
        api_url += f"/{QueryParams}/?format=csv"
    else:
        api_url += "/?format=csv"
    if URLParams:
        api_url += "&"
        api_url += "&".join(URLParams)
    yield "Requesting data from " + api_url
    response_obj = requests.get(api_url)
    if response_obj.status_code != 200:
        err = f"(HTTP Error {response_obj.status_code})"
        yield "\nFailed to fetch data from source" + err
        return
    csv_string = response_obj.content.decode("utf-8")
    count = sspi_raw_api_data.raw_insert_one(
        csv_string, IndicatorCode, **kwargs
    )
    yield f"\nInserted {count} observations into the database.\n"
    yield f"Collection complete for {IndicatorCode} (ILO {ILOIndicatorCode})\n"
