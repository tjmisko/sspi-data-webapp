import requests
from sspi_flask_app.models.database import sspi_raw_api_data


def collectUNFAOData(UNFAO_element: str, UNFAO_item: str, IndicatorCode: str, **kwargs):
    yield "Collecting UNFAO data\n"
    base_url = "https://faostatservices.fao.org/api/v1/en/data/RL?"
    element = f"&element={UNFAO_element}"
    item = f"&item={UNFAO_item}"
    default_options = "&area_cs=ISO3&show_codes=true&show_unit=true&show_flags=true"
    default_options += "&show_notes=true&null_values=false&output_type=objects"
    res = requests.get(f"{base_url}{element}{item}{default_options}")
    raw_data = res.json()
    sspi_raw_api_data.raw_insert_one(raw_data, IndicatorCode, **kwargs)
    yield "UNFAO Data Collection Complete\n"


def format_FAO_data_series(raw_data: list, IndicatorCode: str):
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
