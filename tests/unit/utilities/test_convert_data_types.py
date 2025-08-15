import pytest
from sspi_flask_app.api.resources.utilities import convert_data_types


def test_convert_data_types_basic():
    """Test basic type conversion for Year and Value fields."""
    documents = [
        {"Year": "2020", "Value": "100.5", "CountryCode": "USA"},
        {"Year": "2021", "Value": "200", "CountryCode": "CAN"}
    ]
    
    result = convert_data_types(documents)
    
    assert result[0]["Year"] == 2020
    assert isinstance(result[0]["Year"], int)
    assert result[0]["Value"] == 100.5
    assert isinstance(result[0]["Value"], float)
    
    assert result[1]["Year"] == 2021
    assert isinstance(result[1]["Year"], int)
    assert result[1]["Value"] == 200.0
    assert isinstance(result[1]["Value"], float)


def test_convert_data_types_already_correct_types():
    """Test that already correct types remain unchanged."""
    documents = [
        {"Year": 2020, "Value": 100.5, "CountryCode": "USA"},
        {"Year": 2021, "Value": 200.0, "CountryCode": "CAN"}
    ]
    
    result = convert_data_types(documents)
    
    assert result[0]["Year"] == 2020
    assert result[0]["Value"] == 100.5
    assert result[1]["Year"] == 2021
    assert result[1]["Value"] == 200.0


def test_convert_data_types_float_year_to_int():
    """Test conversion of float Year values to int."""
    documents = [
        {"Year": 2020.0, "Value": "100", "CountryCode": "USA"},
        {"Year": 2021.5, "Value": "200", "CountryCode": "CAN"}  # Will truncate
    ]
    
    result = convert_data_types(documents)
    
    assert result[0]["Year"] == 2020
    assert isinstance(result[0]["Year"], int)
    assert result[1]["Year"] == 2021  # Truncated from 2021.5
    assert isinstance(result[1]["Year"], int)


def test_convert_data_types_scientific_notation():
    """Test conversion of scientific notation strings."""
    documents = [
        {"Year": "2020", "Value": "1.5e3", "CountryCode": "USA"},
        {"Year": "2021", "Value": "2E-2", "CountryCode": "CAN"}
    ]
    
    result = convert_data_types(documents)
    
    assert result[0]["Value"] == 1500.0  # 1.5e3
    assert result[1]["Value"] == 0.02  # 2E-2


def test_convert_data_types_negative_values():
    """Test conversion of negative values."""
    documents = [
        {"Year": "2020", "Value": "-100.5", "CountryCode": "USA"},
        {"Year": "-2021", "Value": "-200", "CountryCode": "CAN"}  # Negative year
    ]
    
    result = convert_data_types(documents)
    
    assert result[0]["Value"] == -100.5
    assert result[1]["Value"] == -200.0
    assert result[1]["Year"] == -2021  # Negative year preserved


def test_convert_data_types_whitespace_in_strings():
    """Test conversion of strings with whitespace."""
    documents = [
        {"Year": " 2020 ", "Value": " 100.5 ", "CountryCode": "USA"},
        {"Year": "\t2021\n", "Value": "\n200\t", "CountryCode": "CAN"}
    ]
    
    result = convert_data_types(documents)
    
    assert result[0]["Year"] == 2020
    assert result[0]["Value"] == 100.5
    assert result[1]["Year"] == 2021
    assert result[1]["Value"] == 200.0


def test_convert_data_types_preserves_other_fields():
    """Test that other fields are preserved unchanged."""
    documents = [
        {
            "Year": "2020",
            "Value": "100.5",
            "CountryCode": "USA",
            "DatasetCode": "TEST_DATA",
            "Unit": "Index",
            "Notes": "Some notes",
            "Metadata": {"source": "test"}
        }
    ]
    
    result = convert_data_types(documents)
    
    assert result[0]["CountryCode"] == "USA"
    assert result[0]["DatasetCode"] == "TEST_DATA"
    assert result[0]["Unit"] == "Index"
    assert result[0]["Notes"] == "Some notes"
    assert result[0]["Metadata"] == {"source": "test"}


def test_convert_data_types_empty_list():
    """Test conversion of empty document list."""
    documents = []
    
    result = convert_data_types(documents)
    
    assert result == []


def test_convert_data_types_mutates_in_place():
    """Test that the function mutates the original list."""
    documents = [
        {"Year": "2020", "Value": "100.5", "CountryCode": "USA"}
    ]
    
    result = convert_data_types(documents)
    
    # Should return the same list object
    assert result is documents
    # Original list should be modified
    assert documents[0]["Year"] == 2020
    assert documents[0]["Value"] == 100.5


def test_convert_data_types_invalid_year_raises_error():
    """Test that invalid Year values raise appropriate errors."""
    documents = [
        {"Year": "not_a_year", "Value": "100", "CountryCode": "USA"}
    ]
    
    with pytest.raises(ValueError):
        convert_data_types(documents)


def test_convert_data_types_invalid_value_raises_error():
    """Test that invalid Value values raise appropriate errors."""
    documents = [
        {"Year": "2020", "Value": "not_a_number", "CountryCode": "USA"}
    ]
    
    with pytest.raises(ValueError):
        convert_data_types(documents)


def test_convert_data_types_none_year_raises_error():
    """Test that None Year value raises TypeError."""
    documents = [
        {"Year": None, "Value": "100", "CountryCode": "USA"}
    ]
    
    with pytest.raises(TypeError):
        convert_data_types(documents)


def test_convert_data_types_none_value_raises_error():
    """Test that None Value raises TypeError."""
    documents = [
        {"Year": "2020", "Value": None, "CountryCode": "USA"}
    ]
    
    with pytest.raises(TypeError):
        convert_data_types(documents)


def test_convert_data_types_missing_year_field():
    """Test that missing Year field raises KeyError."""
    documents = [
        {"Value": "100", "CountryCode": "USA"}  # No Year field
    ]
    
    with pytest.raises(KeyError):
        convert_data_types(documents)


def test_convert_data_types_missing_value_field():
    """Test that missing Value field raises KeyError."""
    documents = [
        {"Year": "2020", "CountryCode": "USA"}  # No Value field
    ]
    
    with pytest.raises(KeyError):
        convert_data_types(documents)


def test_convert_data_types_large_numbers():
    """Test conversion of very large numbers."""
    documents = [
        {"Year": "9999", "Value": "1e100", "CountryCode": "USA"},
        {"Year": "1000000", "Value": "999999999999999999", "CountryCode": "CAN"}
    ]
    
    result = convert_data_types(documents)
    
    assert result[0]["Year"] == 9999
    assert result[0]["Value"] == 1e100
    assert result[1]["Year"] == 1000000
    assert result[1]["Value"] == 999999999999999999.0


def test_convert_data_types_zero_values():
    """Test conversion of zero values."""
    documents = [
        {"Year": "0", "Value": "0", "CountryCode": "USA"},
        {"Year": "0000", "Value": "0.0", "CountryCode": "CAN"}
    ]
    
    result = convert_data_types(documents)
    
    assert result[0]["Year"] == 0
    assert result[0]["Value"] == 0.0
    assert result[1]["Year"] == 0
    assert result[1]["Value"] == 0.0


def test_convert_data_types_special_float_strings():
    """Test conversion of special float string values."""
    documents = [
        {"Year": "2020", "Value": "inf", "CountryCode": "USA"},
        {"Year": "2021", "Value": "-inf", "CountryCode": "CAN"},
        {"Year": "2022", "Value": "nan", "CountryCode": "GBR"}
    ]
    
    result = convert_data_types(documents)
    
    assert result[0]["Value"] == float('inf')
    assert result[1]["Value"] == float('-inf')
    assert result[2]["Value"] != result[2]["Value"]  # NaN != NaN


def test_convert_data_types_multiple_documents():
    """Test conversion with multiple documents."""
    documents = [
        {"Year": "2018", "Value": "100", "CountryCode": "USA"},
        {"Year": "2019", "Value": "110", "CountryCode": "USA"},
        {"Year": "2020", "Value": "120", "CountryCode": "USA"},
        {"Year": "2018", "Value": "200", "CountryCode": "CAN"},
        {"Year": "2019", "Value": "210", "CountryCode": "CAN"},
        {"Year": "2020", "Value": "220", "CountryCode": "CAN"}
    ]
    
    result = convert_data_types(documents)
    
    assert len(result) == 6
    assert all(isinstance(doc["Year"], int) for doc in result)
    assert all(isinstance(doc["Value"], float) for doc in result)
    assert all(doc["CountryCode"] in ["USA", "CAN"] for doc in result)