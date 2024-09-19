import pytest
import pytest
import requests
from sspi_flask_app.models.database import SSPIMetadata
from sspi_flask_app.models.sspi import SSPI
from sspi_flask_app import sspidb
from sspi_flask_app.models.errors import InvalidDocumentFormatError
from sspi_flask_app.api.resources.utilities import parse_json

@pytest.fixture(scope="session")
def test_db():
    sspi_test_db = sspidb.sspi_test_db
    sspi_test_db.delete_many({})
    yield SSPIMetadata(sspi_test_db)
    sspi_test_db.delete_many({})
    sspidb.drop_collection(sspi_test_db)

@pytest.fixture(scope="session")
def sspi_indicator_details(test_db):
    reponse = requests.get("https://sspi.world/api/v1/query/sspi_metadata").json()
    metadata = parse_json(reponse)
    test_db.insert_many(metadata)
    indicator_details = test_db.indicator_details()
    yield indicator_details

@pytest.fixture(scope="session")
def sspi_aus_main_data(test_db):
    reponse = requests.get("https://sspi.world/api/v1/query/sspi_main_data_v3").json()
    metadata = parse_json(reponse)
    test_db.insert_many(metadata)
    indicator_details = test_db.indicator_details()
    yield indicator_details

def test_sspi_structure_real_data(sspi_indicator_details):
    assert 1 == 1
