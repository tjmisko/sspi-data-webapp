import requests
from sspi_flask_app.models.database import sspi_raw_api_data


def collect_ilo_data(ilo_indicator_code, QueryParams="", URLParams=[], **kwargs):
    yield "Sending Data Request to ILO API\n"
    base_url = f"https://sdmx.ilo.org/rest/data/ILO,{ilo_indicator_code}"
    if QueryParams:
        api_url = base_url + f"/{QueryParams}/?format=csv"
    else:
        api_url = base_url + "/?format=csv"
    if URLParams:
        api_url += "&"
        api_url += "&".join(URLParams)
    yield "Requesting data from " + api_url
    response_obj = requests.get(api_url)
    org_series_code = "fIndicator={ilo_indicator_code};Parameters={QueryParams}"
    source_info = {
        "OrganizationName": "International Labor Organization",
        "OrganizationCode": "ILO",
        "OrganizationSeriesCode": ilo_indicator_code,
        "QueryCode": org_series_code.format(
            ilo_indicator_code=ilo_indicator_code, QueryParams=QueryParams
        ),
        "BaseURL": base_url,
        "URL": api_url
    }
    if response_obj.status_code != 200:
        err = f"(HTTP Error {response_obj.status_code})"
        yield "\nFailed to fetch data from source" + err
        return
    csv_string = response_obj.content.decode("utf-8")
    count = sspi_raw_api_data.raw_insert_one(csv_string, source_info, **kwargs)
    yield f"\nInserted {count} observations into the database.\n"
    yield f"Collection complete for ILO {ilo_indicator_code}\n"
