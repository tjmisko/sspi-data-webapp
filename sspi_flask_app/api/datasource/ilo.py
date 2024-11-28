import requests
from sspi_flask_app.models.database import sspi_raw_api_data


def collectILOData(ILOIndicatorCode, IndicatorCode, **kwargs):
    yield "Sending Data Request to ILO API\n"
    response_obj = requests.get("https://sdmx.ilo.org/rest/data/ILO,DF_ILR_CBCT_NOC_RT/?format=csv&startPeriod=1990-01-01&endPeriod=2024-12-31")
    if response_obj.status_code != 200:
        err = f"(HTTP Error {response_obj.status_code})"
        yield "Failed to fetch data from source" + err
        return
    csv_string = response_obj.content.decode("utf-8")
    count = sspi_raw_api_data.raw_insert_one(
                csv_string, IndicatorCode, **kwargs
        )
    yield f"Inserted {count} observations into the database."
    yield f"Collection complete for {IndicatorCode} (ILO {ILOIndicatorCode})"
