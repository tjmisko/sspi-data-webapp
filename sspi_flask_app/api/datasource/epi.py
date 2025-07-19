import requests
from io import BytesIO
import zipfile
from sspi_flask_app.models.database import sspi_raw_api_data


def collect_epi_data(epi_indicator_code, **kwargs):
    url = "https://epi.yale.edu/downloads/epi2024indicators.zip"
    res = requests.get(url)
    if res.status_code != 200:
        err = f"(HTTP Error {res.status_code})"
        yield "Failed to fetch data from source" + err
        return
    with zipfile.ZipFile(BytesIO(res.content)) as z:
        for f in z.namelist():
            if "__MACOSX" in f:
                continue
            yield str(f) + "\n"
            if epi_indicator_code in f:
                with z.open(f) as data:
                    csv_string = data.read().decode("utf-8")
                    source_info = {
                        "OrganizationName": "Environmental Performance Index",
                        "OrganizationCode": "EPI",
                        "OrganizationSeriesCode": epi_indicator_code,
                        "BaseURL": url,
                        "URL": url
                    }
                    sspi_raw_api_data.raw_insert_one(
                        csv_string, source_info, **kwargs
                    )
    yield f"Collection complete for EPI Indicator {epi_indicator_code})"
