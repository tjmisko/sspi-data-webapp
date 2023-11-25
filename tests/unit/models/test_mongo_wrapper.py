from datetime import datetime
import pytest
from sspi_flask_app.models.database import MongoWrapper
from sspi_flask_app import sspidb
from sspi_flask_app.models.errors import InvalidObservationFormatError

@pytest.fixture(scope="session")
def test_db():
    sspi_test_db = sspidb.sspi_test_db
    yield sspi_test_db
    sspidb.drop_collection(sspi_test_db)

@pytest.fixture(scope="session")
def mongo_wrapper(test_db):
    yield MongoWrapper(test_db)

@pytest.fixture(scope="session")
def test_documents():
    test_documents = [
        {"IndicatorCode": "BIODIV", "Raw": "1", "CollectedAt": datetime(2020, 1, 1)},
        {"IndicatorCod": "REDLST", "CountryCode": "USA", "Raw": "1", "CollectedAt": datetime(2020, 1, 1)},
        {"IndicatorCode": "REDLST", "CountryCode": "USA", "Raw": "1", "CollectedAt": datetime(2020, 1, 1)},
        {"IndicatorCode": "NITROG", "CountryCode": "CAN", "Raw": {"Value": 1}, "CollectedAt": datetime(2020, 1, 1)},
        {"IndicatorCode": "BIODIV", "CountryCode": "USA", "Units": "m/s", "Year": "2015", "Value": "25", "CollectedAt": datetime(2020, 1, 1)},
        {"IndicatorCode": "BIODIV", "CountryCode": "USA", "Units": "m/s", "Year": "2015", "Value": "25", "CollectedAt": datetime(2020, 1, 1), "Intermediates": {"a": 1, "b": 2}},
        {"IndicatorCode": "BIODIv", "CountryCode": "USA", "Units": "m/s", "Year": "2015", "Value": "25", "CollectedAt": datetime(2020, 1, 1), "Intermediates": {"FRHWTR": 1, "TERRST": 2}},
        {"IndicatorCode": "BIODIR", "CountryCode": "USA", "Units": "m/s", "Year": "2015", "Value": "25", "CollectedAt": datetime(2020, 1, 1), "Intermediates": {"FRHWTR": 1, "TERRST": 2}}
    ]
    yield test_documents

def test_database_init(test_db):
    sspi_test_db = MongoWrapper(test_db)
    assert sspi_test_db.name == "sspi_test_db"
    assert sspi_test_db._mongo_database.name == "sspi_test_db"

def test_insert_one(test_documents, mongo_wrapper):
    mongo_wrapper.insert_one(test_documents[0])
    assert mongo_wrapper._mongo_database.find_one({"IndicatorCode": "BIODIV"}) == test_documents[0]
    with pytest.raises(InvalidObservationFormatError):
        mongo_wrapper.insert_one(test_documents[1])
    mongo_wrapper.insert_one(test_documents[2])
    assert mongo_wrapper._mongo_database.count_documents() == 2
    assert mongo_wrapper._mongo_database.find_one({"IndicatorCode": "REDLST"}) == test_documents[2]
    assert mongo_wrapper._mongo_database.find_one({"IndicatorCode": "BIODIV"}) == test_documents[0]