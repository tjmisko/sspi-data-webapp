import requests
from sspi_flask_app.models.database import sspi_raw_api_data


def collect_unfao_data(UNFAO_element: str, UNFAO_item: str, UNFAO_domain: str, IndicatorCode: str, **kwargs):
    yield "Collecting UNFAO data\n"
    base_url = f"https://faostatservices.fao.org/api/v1/en/data/{UNFAO_domain}?"
    element = f"&element={UNFAO_element}"
    item = f"&item={UNFAO_item}"
    default_options = "&area_cs=ISO3&show_codes=true&show_unit=true&show_flags=true"
    default_options += "&show_notes=true&null_values=false&output_type=objects"
    url = f"{base_url}{element}{item}{default_options}"
    org_series_code = f"Domain={UNFAO_domain};Element={UNFAO_element};Item={UNFAO_item}"
    res = requests.get(url)
    raw_data = res.json()
    source_info = {
        "OrganizationName": "Environmental Performance Index",
        "OrganizationCode": "EPI",
        "OrganizationSeriesCode": org_series_code,
        "BaseURL": url,
        "URL": url
    }
    sspi_raw_api_data.raw_insert_one(raw_data, source_info, **kwargs)
    yield "UNFAO Data Collection Complete\n"


def format_fao_data_series(raw_data: list, IndicatorCode: str):
    clean_obs_list = []
    for raw in raw_data:
        if not len(raw["Area Code (ISO3)"]) == 3:
            continue
        if any([str(i) in raw["Area Code (ISO3)"] for i in range(0, 10)]):
            continue
        if not raw["Value"]:
            continue
        clean_obs_list.append({
            "IndicatorCode": IndicatorCode,
            "CountryCode": raw["Area Code (ISO3)"],
            "Year": int(raw["Year"]),
            "Value": float(raw["Value"]),
            "Unit": raw["Unit"]
        })
    return clean_obs_list
