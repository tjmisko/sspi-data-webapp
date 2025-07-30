import pytest
from sspi_flask_app.models.database import sspidb
from sspi_flask_app.models.database.sspi_raw_api_data import SSPIRawAPIData


@pytest.fixture(scope="function")
def sspi_raw_api_data():
    sspi_test_db = sspidb.sspi_test_db
    sspi_test_db.delete_many({})
    sspi_raw_api_data = SSPIRawAPIData(sspi_test_db)
    yield sspi_raw_api_data 
    sspi_raw_api_data.delete_many({})


@pytest.fixture(scope="function")
def source_info():
    yield {
        "OrganizationName": "Sustainable and Shared-Prosperity Policy Index",
        "OrganizationCode": "SSPI",
        "OrganizationSeriesCode": "TESTDB",
        "URL": "https://sspi.world",
    }

def test_build_source_query(sspi_raw_api_data, source_info):
    query = sspi_raw_api_data.build_source_query(source_info)
    assert query == {
        "Source.OrganizationName": "Sustainable and Shared-Prosperity Policy Index",
        "Source.OrganizationCode": "SSPI",
        "Source.OrganizationSeriesCode": "TESTDB",
        "Source.URL": "https://sspi.world",
    }

def test_raw_data_available(sspi_raw_api_data, source_info):
    assert not sspi_raw_api_data.raw_data_available(source_info)
    sspi_raw_api_data.raw_insert_one(
        {"a": 1, "b": 2}, source_info, 
        username="test_user", 
        other="test_value"
    )
    assert sspi_raw_api_data.raw_data_available(source_info)
    assert not sspi_raw_api_data.raw_data_available(
        {"OrganizationSeriesCode": "NONEXISTENT"}
    )

def test_raw_insert_one_kwargs(sspi_raw_api_data, source_info):
    sspi_raw_api_data.raw_insert_one(
        {"a": 1, "b": 2}, source_info, 
        username="anything", 
        other="somethingelse", 
        test=True
    )
    doc = sspi_raw_api_data.find({"Source.OrganizationSeriesCode": "TESTDB"})[0]
    assert doc["other"] == "somethingelse"
    assert sspi_raw_api_data.find({"IndicatorCode": "TESTDB"}) == []

def test_fetch_raw_data(sspi_raw_api_data, source_info):
    sspi_raw_api_data.raw_insert_one(
        {"a": 1, "b": 2}, source_info, 
        username="test_user", 
        other="test_value"
    )
    doc = sspi_raw_api_data.fetch_raw_data(source_info)[0]
    assert doc["Raw"]["a"] == 1
    assert doc["Raw"]["b"] == 2
    assert doc["Source"]["OrganizationName"] == "Sustainable and Shared-Prosperity Policy Index"
    assert doc["username"] == "test_user"
    assert doc["other"] == "test_value"

def test_fragment_insertion(sspi_raw_api_data, source_info):
    size = sspi_raw_api_data.maximum_document_size_bytes
    raw_too_big = "a" * (size * 3)
    raw_length = len(raw_too_big)
    sspi_raw_api_data.raw_insert_one(
        raw_too_big, source_info, 
        username="test_user", 
        other="test_value"
    )
    

def test_fragment_reassembly(sspi_raw_api_data, source_info):
    size = sspi_raw_api_data.maximum_document_size_bytes
    raw_too_big = "a" * (size * 3)
    raw_length = len(raw_too_big)
    sspi_raw_api_data.raw_insert_one(
        raw_too_big, source_info, 
        username="test_user", 
        other="test_value"
    )
    assert sspi_raw_api_data.raw_data_available(source_info)
    raw_data = sspi_raw_api_data.fetch_raw_data(source_info)
    assert len(raw_data) == 1
    doc = raw_data[0]
    assert isinstance(doc["Raw"], str)
    assert len(doc["Raw"]) == raw_length
    assert doc["Source"]["OrganizationName"] == "Sustainable and Shared-Prosperity Policy Index"
    assert doc["username"] == "test_user"
    assert doc["other"] == "test_value"
    assert len
