import logging
import json
import requests
from sspi_flask_app.api.datasource.sipri import clean_sipri_data
from sspi_flask_app.api.core.datasets import dataset_collector, dataset_cleaner
from sspi_flask_app.models.database import sspi_raw_api_data, sspi_clean_api_data, sspi_metadata

@dataset_collector("SIPRI_MILEXP")
def collect_sipri_milexp(**kwargs):
    source_info = sspi_metadata.get_source_info("SIPRI_MILEXP")
    log = logging.getLogger(__name__)
    url = "https://backend.sipri.org/api/p/excel-export/preview"
    msg = f"Requesting MILEXP data from URL: {url}\n"
    yield msg
    log.info(msg)
    headers = {
        "Content-Type": "application/json",
        "Origin": "https://milex.sipri.org",
        "Referer": "https://milex.sipri.org/",
    }
    query_payload = {
        "regionalTotals": False,
        "currencyFY": False,
        "currencyCY": True,
        "constantUSD": False,
        "currentUSD": False,
        "shareOfGDP": True,
        "perCapita": False,
        "shareGovt": False,
        "regionDataDetails": False,
        "getLiveData": False,
        "yearFrom": None,
        "yearTo": None,
        "yearList": [1990, 2024],
        "countryList": []
    }
    raw = requests.post(
        url, headers=headers, json=query_payload, verify=False
    ).json()
    sspi_raw_api_data.raw_insert_one(
        raw, source_info, **kwargs
    )
    yield "Successfully collected MILEXP data"


@dataset_cleaner("SIPRI_MILEXP")
def clean_sipri_milexp():
    source_info = sspi_metadata.get_source_info("SIPRI_MILEXP")
    raw_data = sspi_raw_api_data.fetch_raw_data(source_info)
    sspi_clean_api_data.delete_many({"IndicatorCode": "MILEXP"})
    milexp_raw = sspi_raw_api_data.fetch_raw_data("MILEXP")
    milexp_raw = milexp_raw[0]["Raw"]
    unit = (
        "Military expenditure (local currency at current prices) "
        "according to the calendar year as a percentage of GDP."
    )
    cleaned_list = clean_sipri_data(milexp_raw, 'MILEXP', "Percent", unit)
    obs_list = json.loads(str(cleaned_list.to_json(orient="records")))
    sspi_clean_api_data.insert_many(obs_list)
    return raw_data
