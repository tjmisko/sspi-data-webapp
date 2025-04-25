from sspi_flask_app.models.database import sspi_raw_api_data
import requests


def collectIMFData(imf_dataset_code, imf_indicator_code, IndicatorCode, **kwargs):
    """Uses Legacy, Deprecated IMF API
    Somewhat Helpful Documentation: https://datahelp.imf.org/knowledgebase/articles/667681-using-json-restful-web-service
    - [ ] I have the correct Indicator Code and Dataset Name, but I still can't pull the data
    """
    yield f"Requesting {imf_dataset_code} data...\n"
    metadata_url = (
        "http://dataservices.imf.org/REST/SDMX_JSON.svc/"
        f"DataStructure/{imf_dataset_code}"
    )
    metadata = requests.get(metadata_url).json()
    count = sspi_raw_api_data.raw_insert_one(
        "raw", IndicatorCode, Metadata=metadata, **kwargs
    )
    msg = (
        f"Successfully inserted {count} observation of {imf_indicator_code} "
        f"from dataset {imf_dataset_code}"
    )
    yield msg
