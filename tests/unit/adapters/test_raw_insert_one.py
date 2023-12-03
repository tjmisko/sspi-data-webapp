from datetime import datetime
import pytest
from sspi_flask_app.models.database import MongoWrapper
from sspi_flask_app import sspidb
from sspi_flask_app.models.errors import InvalidDocumentFormatError
from sspi_flask_app import sspi_raw_api_data
from sspi_flask_app.api.resources.adapters import raw_insert_one

@pytest.fixture(scope="function")
def test_db():
    sspi_test_db = sspidb.sspi_test_db
    sspi_test_db.delete_many({})
    yield sspi_test_db
    sspi_test_db.delete_many({})
    sspidb.drop_collection(sspi_test_db)

def test_kwargs():
    raw_insert_one({"a":1, "b":2},"TESTDB",Username="anything", other="somethingelse", test=True)
    doc = sspi_raw_api_data.find({"IndicatorCode": "TESTDB"})
    assert doc["other"]=="somethingelse"
    sspi_raw_api_data.delete_many({"test": True})
    assert sspi_raw_api_data.find({"IndicatorCode": "TESTDB"}) == []