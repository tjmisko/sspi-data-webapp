from datetime import datetime
import pytest
from sspi_flask_app.models.database import MongoWrapper

@pytest.fixture(scope="session")
def test_documents():
    test_documents = [
        {"IndicatorCode": "BIODIV", "Raw": "1", "CollectedAt": datetime(2020, 1, 1)},
        {"IndicatorCode": "REDLST", "CountryCode": "USA", "Raw": "1", "CollectedAt": datetime(2020, 1, 1)},
        {"IndicatorCode": "NITROG", "CountryCode": "CAN", "Raw": {"Value": 1}, "CollectedAt": datetime(2020, 1, 1)},
        {"IndicatorCode": "BIODIV", "CountryCode": "USA", "Units": "m/s", "Year": "2015", "Value": "25", "CollectedAt": datetime(2020, 1, 1)},
        {"IndicatorCode": "BIODIV", "CountryCode": "USA", "Units": "m/s", "Year": "2015", "Value": "25", "CollectedAt": datetime(2020, 1, 1), "Intermediates": {"a": 1, "b": 2}},
        {"IndicatorCode": "BIODIv", "CountryCode": "USA", "Units": "m/s", "Year": "2015", "Value": "25", "CollectedAt": datetime(2020, 1, 1), "Intermediates": {"FRHWTR": 1, "TERRST": 2}},
        {"IndicatorCode": "BIODIR", "CountryCode": "USA", "Units": "m/s", "Year": "2015", "Value": "25", "CollectedAt": datetime(2020, 1, 1), "Intermediates": {"FRHWTR": 1, "TERRST": 2}}
    ]
    yield test_documents

def test_insert_one(test_documents, mongo_database):
    mongo_database.insert_one(test_documents[0])
    assert mongo_database.find_one({"IndicatorCode": "BIODIV"}) == test_documents[0]
