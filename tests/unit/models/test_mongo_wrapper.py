from datetime import datetime
import pytest
from sspi_flask_app.models.database import MongoWrapper
from sspi_flask_app import sspidb
from sspi_flask_app.models.errors import InvalidDocumentFormatError

@pytest.fixture(scope="function")
def test_db():
    sspi_test_db = sspidb.sspi_test_db
    sspi_test_db.delete_many({})
    yield sspi_test_db
    sspi_test_db.delete_many({})
    sspidb.drop_collection(sspi_test_db)

def test_database_init(test_db):
    sspi_test_db = MongoWrapper(test_db)
    assert sspi_test_db.name == "sspi_test_db"
    assert sspi_test_db._mongo_database.name == "sspi_test_db"

@pytest.fixture(scope="function")
def mongo_wrapper(test_db):
    mongo_wrapper_obj = MongoWrapper(test_db)
    yield mongo_wrapper_obj

@pytest.fixture(scope="session")
def test_documents():
    test_documents = {
        0: {"IndicatorCode": "BIODIV", "Raw": "1", "CollectedAt": datetime(2020, 1, 1)},
        1: {"IndicatorCod": "REDLST", "CountryCode": "USA", "Raw": "1", "CollectedAt": datetime(2020, 1, 1)},
        2: {"IndicatorCode": "REDLST", "CountryCode": "USA", "Raw": "1", "CollectedAt": datetime(2020, 1, 2)},
        3: {"IndicatorCode": "NITROG", "CountryCode": "CAN", "Raw": {"Value": 1}, "CollectedAt": datetime(2020, 1, 3)},
        4: {"IndicatorCode": "BIODIV", "CountryCode": "US", "Unit": "m/s", "Year": 2015, "Value": "25", "CollectedAt": datetime(2020, 1, 4)},
        5: {"IndicatorCode": "BIODIV", "CountryCode": "usa", "Units": "m/s", "Year": 2015, "Value": 25, "CollectedAt": datetime(2020, 1, 6), "Intermediates": {"a": 1, "b": 2}},
        6: {"IndicatorCode": "BIODIv", "CountryCode": "USA", "Unit": "m/s", "Year": 215, "Value": 25.1, "CollectedAt": datetime(2020, 1, 1), "Intermediates": {"FRHWTR": 1, "TERRST": 2}},
        7: {"IndicatorCode": "BIODI", "CountryCode": "USA", "Unit": "m/s", "Year": 2015, "Value": 2, "CollectedAt": datetime(2020, 1, 1), "Intermediates": {"FRHWTR": 1, "TERRST": 2}},
        8: {"IndicatorCode": "BIODIR", "CountryCode": "USA", "Unit": "m/s", "Year": 2015, "Value": "25", "CollectedAt": "2020-1-1", "Intermediates": {"FRHWTR": 1, "TERRST": 2}},
        "a": {"IndicatorCode": "BIODIV", "CountryCode": "USA", "Unit": "m/s", "Year": 2015, "Value": 25, "CollectedAt": datetime(2020, 1, 6), "Intermediates": {"FRHWTR": 1, "TERRST": 2}},
        "b": {"IndicatorCode": "REDLST", "CountryCode": "USA", "Unit": "m/s", "Year": 2015, "Value": 25.2, "CollectedAt": datetime(2020, 1, 6), "Intermediates": {"FRHWTR": 1, "TERRST": 2}},
        "c": {"IndicatorCode": "NITROG", "CountryCode": "USA", "Unit": "m/s", "Year": 2015, "Value": 25, "CollectedAt": datetime(2020, 1, 6), "Intermediates": {"FRHWTR": 1, "TERRST": 2}},
        "d": {"IndicatorCode": "NITROG", "CountryCode": "USA", "Unit": "m/s", "Year": 2015, "Value": 25, "CollectedAt": datetime(2020, 1, 6), "Intermediates": {"FRHWTR": 1, "TERRST": 2}}
    }
    yield test_documents

def test_validate_country_code(test_documents, mongo_wrapper):
    for i in range(9):
        if i == 0 or i == 4 or i == 5:
            with pytest.raises(InvalidDocumentFormatError) as exception_info:
                mongo_wrapper.validate_country_code(test_documents[i], i)
            assert "CountryCode" in str(exception_info.value)
            assert f"document {i}" in str(exception_info.value)
        else:
            mongo_wrapper.validate_country_code(test_documents[i], i)

def test_validate_indicator_code(test_documents, mongo_wrapper):
    for i in range(9):
        if i == 1 or i == 6 or i == 7:
            with pytest.raises(InvalidDocumentFormatError) as exception_info:
                mongo_wrapper.validate_indicator_code(test_documents[i], i)
            assert "IndicatorCode" in str(exception_info.value)
            assert f"document {i}" in str(exception_info.value)
        else:
            mongo_wrapper.validate_indicator_code(test_documents[i], i)

def test_validate_year(test_documents, mongo_wrapper):
    for i in range(9):
        if i < 4 or i == 6:
            with pytest.raises(InvalidDocumentFormatError) as exception_info:
                mongo_wrapper.validate_year(test_documents[i], i)
            assert "Year" in str(exception_info.value)
            assert f"document {i}" in str(exception_info.value)
        else:
            mongo_wrapper.validate_year(test_documents[i], i)

def test_validate_value(test_documents, mongo_wrapper):
    for i in range(9):
        if i < 5 or i == 8:
            with pytest.raises(InvalidDocumentFormatError) as exception_info:
                mongo_wrapper.validate_value(test_documents[i], i)
            assert "Value" in str(exception_info.value)
            assert f"document {i}" in str(exception_info.value)
        else:
            mongo_wrapper.validate_value(test_documents[i], i)

def test_validate_unit(test_documents, mongo_wrapper):
    for i in range(9):
        if i < 4 or i == 5:
            with pytest.raises(InvalidDocumentFormatError) as exception_info:
                mongo_wrapper.validate_unit(test_documents[i], i)
            assert "Unit" in str(exception_info.value)
            assert f"document {i}" in str(exception_info.value)
        else:
            mongo_wrapper.validate_unit(test_documents[i], i)

def test_insert_one(test_documents, mongo_wrapper):
    for i in range(9):
        with pytest.raises(InvalidDocumentFormatError) as exception_info:
            mongo_wrapper.insert_one(test_documents[1])
        assert "document 0" in str(exception_info.value)
    mongo_wrapper.insert_one(test_documents["a"])
    assert mongo_wrapper._mongo_database.count_documents({}) == 1
    assert mongo_wrapper._mongo_database.find_one({"IndicatorCode": "BIODIV"}) == test_documents["a"]
    mongo_wrapper.insert_one(test_documents["b"])
    assert mongo_wrapper._mongo_database.count_documents({}) == 2
    assert mongo_wrapper._mongo_database.find_one({"IndicatorCode": "REDLST"}) == test_documents["b"]
    mongo_wrapper.insert_one(test_documents["c"])
    assert mongo_wrapper._mongo_database.count_documents({}) == 3
    assert mongo_wrapper._mongo_database.find_one({"IndicatorCode": "NITROG"}) == test_documents["c"]

def test_insert_many(test_documents, mongo_wrapper):
    with pytest.raises(InvalidDocumentFormatError) as exception_info:
        mongo_wrapper.insert_many(list(test_documents.values()))
    assert "CountryCode" in str(exception_info.value)
    assert "document 0" in str(exception_info.value)
    mongo_wrapper.insert_many([test_documents["a"], test_documents["b"]])
    assert mongo_wrapper._mongo_database.count_documents({}) == 2
    assert mongo_wrapper._mongo_database.find_one({"IndicatorCode": "BIODIV"}) == test_documents["a"]
    assert mongo_wrapper._mongo_database.find_one({"IndicatorCode": "REDLST"}) == test_documents["b"]
    with pytest.raises(InvalidDocumentFormatError) as exception_info:
        mongo_wrapper.insert_many(test_documents["c"])
    assert "Type" in str(exception_info.value)
    assert "dict" in str(exception_info.value)
    assert mongo_wrapper._mongo_database.count_documents({}) == 2
    mongo_wrapper.insert_many([test_documents["c"]])
    assert mongo_wrapper._mongo_database.find_one({"IndicatorCode": "NITROG"}) == test_documents["c"]

def test_tabulate_ids(test_documents, mongo_wrapper):
    mongo_wrapper.insert_many([v for k, v in test_documents.items() if type(k) is str])
    table = mongo_wrapper.tabulate_ids()
    assert type(table) is list
    assert len(table) == 3
    assert all([type(document) is dict for document in table])
    for document in table:
        if document["_id"]["IndicatorCode"] == "BIODIV" or document["_id"]["IndicatorCode"] == "REDLST":
            assert document["count"] == 1
        else:
            assert document["count"] == 2

def test_drop_duplicates(test_documents, mongo_wrapper):
    mongo_wrapper.insert_many([v for k, v in test_documents.items() if type(k) is str])
    mongo_wrapper.drop_duplicates()
    assert mongo_wrapper.count_documents({}) == 3
    document_list = mongo_wrapper.find({})
    assert type(document_list) is list
    assert len(document_list) == 3
    assert all([type(document) is dict for document in document_list])
    assert len(mongo_wrapper.find({"IndicatorCode": "BIODIV"})) == 1
    assert len(mongo_wrapper.find({"IndicatorCode": "REDLST"})) == 1
    assert len(mongo_wrapper.find({"IndicatorCode": "NITROG"})) == 1

