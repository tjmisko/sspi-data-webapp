import logging
import requests
from sspi_flask_app.api.core.datasets import dataset_collector, dataset_cleaner
from sspi_flask_app.models.database import sspi_raw_api_data, sspi_clean_api_data, sspi_metadata

@dataset_collector("SIPRI_ARMEXP")
def collect_sipri_armexp(**kwargs):
    log = logging.getLogger(__name__)
    url = "https://atbackend.sipri.org/api/p/trades/import-export-csv-str/"
    source_info = sspi_metadata.get_source_info("SIPRI_ARMEXP")
    log.info(f"Requesting ARMEXP data from URL: {url}")
    headers = {
        "Content-Type": "application/json",
        "Origin": "https://armstransfers.sipri.org",
        "Referer": "https://armstransfers.sipri.org",
    }
    query_payload = {
        "filters": [
            {
                "field": "Year range 1",
                "oldField": "",
                "condition": "contains",
                "value1": 1990,
                "value2": 2025,
                "listData": []
            },
            {
                "field": "orderbyseller",
                "oldField": "",
                "condition": "",
                "value1": "",
                "value2": "",
                "listData": []
            },
            {
                "field": "DeliveryType",
                "oldField": "",
                "condition": "",
                "value1": "delivered",
                "value2": "",
                "listData": []
            },
            {
                "field": "Status",
                "oldField": "",
                "condition": "",
                "value1": "0",
                "value2": "",
                "listData": []
            }
        ],
        "logic": "AND"
    }
    response = requests.post(url, headers=headers, json=query_payload)
    sspi_raw_api_data.raw_insert_one(response.json(), source_info, **kwargs)
    yield "Collected ARMEXP data"


@dataset_cleaner("SIPRI_ARMEXP")
def clean_sipri_armexp():
    source_info = sspi_metadata.get_source_info("SIPRI_ARMEXP")
    raw_data = sspi_raw_api_data.fetch_raw_data(source_info)
    return raw_data # You can look at the data as you go by returning it here
    # Simply call `sspi clean sipri_armexp | jq` to see the raw data in your terminal
    # Clean the raw data here
    # ...
    # sspi_clean_api_data.insert_many(cleaned_data)
    # return cleaned data
