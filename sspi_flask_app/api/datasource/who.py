import requests
from sspi_flask_app.models.database import sspi_raw_api_data


def collectCSTUNTData(**kwargs):
    yield "Collecting data from WHO API\n"
    base_url = "https://apps.who.int/gho/athena/data/GHO/"
    stub = "NUTSTUNTINGPREV,NUTRITION_ANT_HAZ_NE2.json?filter=COUNTRY:*&ead="
    yield "Fetching from {}\n".format(base_url + stub)
    raw = requests.get(base_url + stub).json()
    sspi_raw_api_data.raw_insert_one(raw, "CSTUNT", **kwargs)
    yield "Succesfully stored raw CSTUNT data in sspi_raw_api_database!\n"
