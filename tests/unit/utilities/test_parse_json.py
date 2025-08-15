import pytest
from datetime import datetime
from bson import ObjectId, json_util
from sspi_flask_app.api.resources.utilities import parse_json


def test_parse_json_simple_dict():
    """Test parsing a simple dictionary."""
    data = {"key": "value", "number": 42}
    result = parse_json(data)
    
    assert result == data
    assert isinstance(result, dict)
    assert result["key"] == "value"
    assert result["number"] == 42


def test_parse_json_nested_dict():
    """Test parsing nested dictionaries."""
    data = {
        "level1": {
            "level2": {
                "key": "value",
                "number": 123
            }
        }
    }
    result = parse_json(data)
    
    assert result == data
    assert result["level1"]["level2"]["key"] == "value"
    assert result["level1"]["level2"]["number"] == 123


def test_parse_json_list():
    """Test parsing lists."""
    data = [1, 2, 3, "string", {"nested": "dict"}]
    result = parse_json(data)
    
    assert result == data
    assert isinstance(result, list)
    assert len(result) == 5
    assert result[4]["nested"] == "dict"


def test_parse_json_with_objectid():
    """Test parsing data containing MongoDB ObjectId."""
    obj_id = ObjectId()
    data = {"_id": obj_id, "name": "test"}
    result = parse_json(data)
    
    # ObjectId should be converted to a string representation
    assert isinstance(result, dict)
    assert "_id" in result
    assert "$oid" in result["_id"]  # BSON ObjectId format
    assert result["name"] == "test"


def test_parse_json_with_datetime():
    """Test parsing data containing datetime objects."""
    dt = datetime(2023, 1, 15, 10, 30, 45)
    data = {"timestamp": dt, "value": 100}
    result = parse_json(data)
    
    # Datetime should be converted to BSON date format
    assert isinstance(result, dict)
    assert "timestamp" in result
    assert "$date" in result["timestamp"]  # BSON datetime format
    assert result["value"] == 100


def test_parse_json_mixed_bson_types():
    """Test parsing data with mixed BSON-specific types."""
    obj_id = ObjectId()
    dt = datetime(2023, 5, 20, 14, 25, 30)
    
    data = {
        "_id": obj_id,
        "created": dt,
        "data": {
            "values": [1, 2, 3],
            "metadata": {
                "type": "test",
                "another_id": ObjectId()
            }
        }
    }
    
    result = parse_json(data)
    
    assert isinstance(result, dict)
    assert "$oid" in result["_id"]
    assert "$date" in result["created"]
    assert result["data"]["values"] == [1, 2, 3]
    assert result["data"]["metadata"]["type"] == "test"
    assert "$oid" in result["data"]["metadata"]["another_id"]


def test_parse_json_empty_structures():
    """Test parsing empty data structures."""
    
    # Empty dict
    assert parse_json({}) == {}
    
    # Empty list
    assert parse_json([]) == []
    
    # Dict with empty values
    data = {"empty_list": [], "empty_dict": {}, "null_value": None}
    result = parse_json(data)
    assert result["empty_list"] == []
    assert result["empty_dict"] == {}
    assert result["null_value"] is None


def test_parse_json_none_values():
    """Test parsing data with None values."""
    data = {"key1": None, "key2": "value", "key3": None}
    result = parse_json(data)
    
    assert result == data
    assert result["key1"] is None
    assert result["key2"] == "value"
    assert result["key3"] is None


def test_parse_json_numeric_types():
    """Test parsing various numeric types."""
    data = {
        "int": 42,
        "float": 3.14159,
        "negative": -100,
        "zero": 0,
        "large_int": 999999999999
    }
    result = parse_json(data)
    
    assert result == data
    assert isinstance(result["int"], int)
    assert isinstance(result["float"], float)
    assert result["negative"] == -100
    assert result["zero"] == 0


def test_parse_json_boolean_values():
    """Test parsing boolean values."""
    data = {"true_val": True, "false_val": False, "mixed": [True, False, True]}
    result = parse_json(data)
    
    assert result == data
    assert result["true_val"] is True
    assert result["false_val"] is False
    assert result["mixed"] == [True, False, True]


def test_parse_json_string_types():
    """Test parsing various string types."""
    data = {
        "simple": "hello",
        "empty": "",
        "unicode": "café",
        "special_chars": "!@#$%^&*()",
        "multiline": "line1\nline2\nline3"
    }
    result = parse_json(data)
    
    assert result == data
    assert all(isinstance(v, str) for v in result.values())


def test_parse_json_complex_mongodb_document():
    """Test parsing a complex document similar to what would come from MongoDB."""
    obj_id1 = ObjectId()
    obj_id2 = ObjectId()
    dt1 = datetime(2023, 1, 1, 0, 0, 0)
    dt2 = datetime(2023, 12, 31, 23, 59, 59)
    
    data = {
        "_id": obj_id1,
        "CountryCode": "USA",
        "Year": 2023,
        "Value": 85.7,
        "DatasetCode": "TEST_DATA",
        "created_at": dt1,
        "updated_at": dt2,
        "metadata": {
            "source_id": obj_id2,
            "tags": ["economic", "social"],
            "validated": True,
            "notes": None
        },
        "history": [
            {"date": dt1, "value": 80.0},
            {"date": dt2, "value": 85.7}
        ]
    }
    
    result = parse_json(data)
    
    # Check that BSON types are properly converted
    assert "$oid" in result["_id"]
    assert "$date" in result["created_at"]
    assert "$date" in result["updated_at"]
    assert "$oid" in result["metadata"]["source_id"]
    
    # Check that regular data is preserved
    assert result["CountryCode"] == "USA"
    assert result["Year"] == 2023
    assert result["Value"] == 85.7
    assert result["metadata"]["tags"] == ["economic", "social"]
    assert result["metadata"]["validated"] is True
    assert result["metadata"]["notes"] is None
    
    # Check that nested BSON types in arrays are converted
    assert len(result["history"]) == 2
    assert "$date" in result["history"][0]["date"]
    assert "$date" in result["history"][1]["date"]


def test_parse_json_idempotency():
    """Test that parsing the same data multiple times gives the same result."""
    data = {
        "_id": ObjectId(),
        "timestamp": datetime.now(),
        "data": {"key": "value"}
    }
    
    result1 = parse_json(data)
    result2 = parse_json(data)
    
    # Results should be identical (though not necessarily the same object)
    assert result1 == result2


def test_parse_json_preserves_structure():
    """Test that the overall structure is preserved after parsing."""
    data = {
        "level1": {
            "level2": {
                "level3": [
                    {"item": 1, "id": ObjectId()},
                    {"item": 2, "id": ObjectId()},
                ]
            }
        }
    }
    
    result = parse_json(data)
    
    # Structure should be preserved
    assert "level1" in result
    assert "level2" in result["level1"]
    assert "level3" in result["level1"]["level2"]
    assert len(result["level1"]["level2"]["level3"]) == 2
    assert result["level1"]["level2"]["level3"][0]["item"] == 1
    assert "$oid" in result["level1"]["level2"]["level3"][0]["id"]