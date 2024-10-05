import pytest
from sspi_flask_app.models.database import SSPICountryCharacteristics
from sspi_flask_app import sspidb
from sspi_flask_app.models.errors import InvalidDocumentFormatError
from sspi_flask_app.api.resources.utilities import parse_json


@pytest.fixture(scope="function")
def sspi_characteristics_db():
    sspi_test_db = sspidb.sspi_test_db
    sspi_test_db.delete_many({})
    sspi_characteristics_database = SSPICountryCharacteristics(sspi_test_db)
    yield sspi_characteristics_database
    sspi_characteristics_database.delete_many({})
    sspi_test_db.delete_many({})
    sspidb.drop_collection(sspi_test_db)


@pytest.fixture(scope="session")
def test_data():
    yield [
        {
            "IntermediateCode": "UNPOPL",
            "CountryCode": "USA",
            "Year": 2015,
            "Unit": "Millions of people",
            "Value": 320,
        },
        {
            "IntermediateCode": "UNPOPL",
            "CountryCode": "USA",
            "Year": 2016,
            "Unit": "Millions of people",
            "Value": 325
        },
        {
            "IntermediateCode": "UNPOPL",
            "CountryCode": "USA",
            "Year": 2017,
            "Unit": "Millions of people",
            "Value": 330
        },
        {
            "ExtraInfo": "IsOK",
            "IntermediateCode": "UNPOPL",
            "CountryCode": "USA",
            "Year": 2017,
            "Unit": "Millions of people",
            "Value": 330
        },
        {
            "IndicatorCode": "UNPOPL",
            "CountryCode": "USA",
            "Year": 2017,
            "Unit": "Millions of people",
            "Value": 330
        },
        {
            "IntermediateCode": "UNPOPL",
            "CountryCode": "USA",
            "Year": 2017,
            "Value": 330
        }
    ]


def test_characteristics_format_validators(sspi_characteristics_db, test_data):
    for i in range(5):
        if i == 4:
            with pytest.raises(InvalidDocumentFormatError) as exception_info:
                sspi_characteristics_db.insert_one(test_data[i])
            assert "IntermediateCode" in str(exception_info.value)
        elif i == 5:
            with pytest.raises(InvalidDocumentFormatError) as exception_info:
                sspi_characteristics_db.insert_one(test_data[i])
            assert "Unit" in str(exception_info.value)
        else:
            sspi_characteristics_db.insert_one(test_data[i])
    stored_data = parse_json(sspi_characteristics_db.find({}))
    assert len(stored_data) == 4
