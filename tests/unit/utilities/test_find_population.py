import pytest
from unittest.mock import patch, MagicMock
from sspi_flask_app.api.resources.utilities import find_population


@patch('sspi_flask_app.api.resources.utilities.sspi_country_characteristics')
def test_find_population_valid_inputs(mock_country_characteristics):
    """Test find_population with valid country code and year."""
    
    # Mock successful population data retrieval
    mock_population_data = {
        "CountryCode": "USA",
        "Year": 2020,
        "Value": 331449281,
        "Unit": "People",
        "DatasetCode": "POPULN"
    }
    mock_country_characteristics.fetch_population_data.return_value = mock_population_data
    
    result = find_population("USA", 2020)
    
    assert result == mock_population_data
    mock_country_characteristics.fetch_population_data.assert_called_once_with("POPULN", "USA", 2020)


@patch('sspi_flask_app.api.resources.utilities.sspi_country_characteristics')
def test_find_population_different_countries(mock_country_characteristics):
    """Test find_population with different country codes."""
    
    test_cases = [
        ("USA", 2020, 331449281),
        ("CAN", 2020, 38067903),
        ("GBR", 2020, 67886011),
        ("FRA", 2020, 67320216),
        ("DEU", 2020, 83190556)
    ]
    
    for country_code, year, expected_population in test_cases:
        mock_population_data = {
            "CountryCode": country_code,
            "Year": year,
            "Value": expected_population,
            "Unit": "People",
            "DatasetCode": "POPULN"
        }
        mock_country_characteristics.fetch_population_data.return_value = mock_population_data
        
        result = find_population(country_code, year)
        
        assert result == mock_population_data
        mock_country_characteristics.fetch_population_data.assert_called_with("POPULN", country_code, year)


@patch('sspi_flask_app.api.resources.utilities.sspi_country_characteristics')
def test_find_population_different_years(mock_country_characteristics):
    """Test find_population with different years."""
    
    years = [2000, 2010, 2015, 2020, 2023]
    
    for year in years:
        mock_population_data = {
            "CountryCode": "USA",
            "Year": year,
            "Value": 280000000 + (year - 2000) * 1000000,  # Simulated growth
            "Unit": "People",
            "DatasetCode": "POPULN"
        }
        mock_country_characteristics.fetch_population_data.return_value = mock_population_data
        
        result = find_population("USA", year)
        
        assert result == mock_population_data
        mock_country_characteristics.fetch_population_data.assert_called_with("POPULN", "USA", year)


@patch('sspi_flask_app.api.resources.utilities.sspi_country_characteristics')
def test_find_population_no_data_found(mock_country_characteristics):
    """Test find_population when no data is found."""
    
    # Mock returning None when no data is found
    mock_country_characteristics.fetch_population_data.return_value = None
    
    result = find_population("XXX", 2020)  # Non-existent country
    
    assert result is None
    mock_country_characteristics.fetch_population_data.assert_called_once_with("POPULN", "XXX", 2020)


@patch('sspi_flask_app.api.resources.utilities.sspi_country_characteristics')
def test_find_population_empty_result(mock_country_characteristics):
    """Test find_population when empty result is returned."""
    
    # Mock returning empty dict
    mock_country_characteristics.fetch_population_data.return_value = {}
    
    result = find_population("USA", 1900)  # Very old year with no data
    
    assert result == {}
    mock_country_characteristics.fetch_population_data.assert_called_once_with("POPULN", "USA", 1900)


@patch('sspi_flask_app.api.resources.utilities.sspi_country_characteristics')
def test_find_population_database_exception(mock_country_characteristics):
    """Test find_population when database raises an exception."""
    
    # Mock database raising an exception
    mock_country_characteristics.fetch_population_data.side_effect = Exception("Database connection error")
    
    with pytest.raises(Exception) as exc_info:
        find_population("USA", 2020)
    
    assert "Database connection error" in str(exc_info.value)
    mock_country_characteristics.fetch_population_data.assert_called_once_with("POPULN", "USA", 2020)


@patch('sspi_flask_app.api.resources.utilities.sspi_country_characteristics')
def test_find_population_always_uses_populn_dataset(mock_country_characteristics):
    """Test that find_population always uses 'POPULN' as the dataset code."""
    
    mock_population_data = {"Value": 123456}
    mock_country_characteristics.fetch_population_data.return_value = mock_population_data
    
    # Test multiple calls to ensure POPULN is always used
    test_cases = [
        ("USA", 2020),
        ("CAN", 2019),
        ("GBR", 2021)
    ]
    
    for country_code, year in test_cases:
        find_population(country_code, year)
        
        # Verify that first argument is always "POPULN"
        args, kwargs = mock_country_characteristics.fetch_population_data.call_args
        assert args[0] == "POPULN", f"First argument should always be 'POPULN' for {country_code}, {year}"


@patch('sspi_flask_app.api.resources.utilities.sspi_country_characteristics')
def test_find_population_parameter_types(mock_country_characteristics):
    """Test find_population with different parameter types."""
    
    mock_population_data = {"Value": 123456}
    mock_country_characteristics.fetch_population_data.return_value = mock_population_data
    
    # Test with string year (should still work)
    result = find_population("USA", "2020")
    assert result == mock_population_data
    mock_country_characteristics.fetch_population_data.assert_called_with("POPULN", "USA", "2020")
    
    # Test with float year
    result = find_population("USA", 2020.0)
    assert result == mock_population_data
    mock_country_characteristics.fetch_population_data.assert_called_with("POPULN", "USA", 2020.0)


@patch('sspi_flask_app.api.resources.utilities.sspi_country_characteristics')
def test_find_population_edge_case_inputs(mock_country_characteristics):
    """Test find_population with edge case inputs."""
    
    mock_population_data = {"Value": 0}
    mock_country_characteristics.fetch_population_data.return_value = mock_population_data
    
    edge_cases = [
        ("", 2020),        # Empty country code
        ("USA", 0),        # Zero year
        ("USA", -1),       # Negative year
        ("USA", 9999),     # Future year
        ("XXX", 2020),     # Invalid country code
        ("123", 2020),     # Numeric country code
    ]
    
    for country_code, year in edge_cases:
        result = find_population(country_code, year)
        assert result == mock_population_data
        mock_country_characteristics.fetch_population_data.assert_called_with("POPULN", country_code, year)


@patch('sspi_flask_app.api.resources.utilities.sspi_country_characteristics')
def test_find_population_none_inputs(mock_country_characteristics):
    """Test find_population with None inputs."""
    
    mock_population_data = None
    mock_country_characteristics.fetch_population_data.return_value = mock_population_data
    
    # Test None country code
    result = find_population(None, 2020)
    assert result is None
    mock_country_characteristics.fetch_population_data.assert_called_with("POPULN", None, 2020)
    
    # Test None year
    result = find_population("USA", None)
    assert result is None
    mock_country_characteristics.fetch_population_data.assert_called_with("POPULN", "USA", None)
    
    # Test both None
    result = find_population(None, None)
    assert result is None
    mock_country_characteristics.fetch_population_data.assert_called_with("POPULN", None, None)


@patch('sspi_flask_app.api.resources.utilities.sspi_country_characteristics')
def test_find_population_case_sensitivity(mock_country_characteristics):
    """Test find_population with different case country codes."""
    
    mock_population_data = {"Value": 123456}
    mock_country_characteristics.fetch_population_data.return_value = mock_population_data
    
    case_variants = [
        "USA",  # Standard uppercase
        "usa",  # Lowercase
        "Usa",  # Mixed case
        "UsA"   # Mixed case
    ]
    
    for country_code in case_variants:
        result = find_population(country_code, 2020)
        assert result == mock_population_data
        # The function should pass the country code as-is (case preservation)
        mock_country_characteristics.fetch_population_data.assert_called_with("POPULN", country_code, 2020)


@patch('sspi_flask_app.api.resources.utilities.sspi_country_characteristics')
def test_find_population_special_country_codes(mock_country_characteristics):
    """Test find_population with special or non-standard country codes."""
    
    mock_population_data = {"Value": 123456}
    mock_country_characteristics.fetch_population_data.return_value = mock_population_data
    
    special_codes = [
        "XKX",   # Kosovo (non-ISO)
        "EU-28", # European Union grouping
        "OECD",  # Organization grouping
        "WLD",   # World
        "LDC",   # Least Developed Countries
    ]
    
    for country_code in special_codes:
        result = find_population(country_code, 2020)
        assert result == mock_population_data
        mock_country_characteristics.fetch_population_data.assert_called_with("POPULN", country_code, 2020)


@patch('sspi_flask_app.api.resources.utilities.sspi_country_characteristics')
def test_find_population_historical_years(mock_country_characteristics):
    """Test find_population with historical years."""
    
    historical_years = [1950, 1960, 1970, 1980, 1990]
    
    for year in historical_years:
        mock_population_data = {
            "CountryCode": "USA",
            "Year": year,
            "Value": 150000000 + (year - 1950) * 2000000,  # Simulated historical data
            "Unit": "People",
            "DatasetCode": "POPULN"
        }
        mock_country_characteristics.fetch_population_data.return_value = mock_population_data
        
        result = find_population("USA", year)
        
        assert result == mock_population_data
        mock_country_characteristics.fetch_population_data.assert_called_with("POPULN", "USA", year)


@patch('sspi_flask_app.api.resources.utilities.sspi_country_characteristics')
def test_find_population_return_value_passthrough(mock_country_characteristics):
    """Test that find_population returns exactly what the database returns."""
    
    # Test various return value types
    return_values = [
        {"Value": 123456, "Unit": "People"},
        [],  # Empty list
        {},  # Empty dict
        None,  # None
        {"Error": "No data found"},  # Error response
        {"Value": 0},  # Zero population
        {"Value": 1000000000000},  # Very large population
    ]
    
    for return_value in return_values:
        mock_country_characteristics.fetch_population_data.return_value = return_value
        
        result = find_population("USA", 2020)
        
        # Should return exactly what the database returns
        assert result is return_value
        mock_country_characteristics.fetch_population_data.assert_called_with("POPULN", "USA", 2020)


@patch('sspi_flask_app.api.resources.utilities.sspi_country_characteristics')
def test_find_population_multiple_calls_independence(mock_country_characteristics):
    """Test that multiple calls to find_population are independent."""
    
    # Set up different return values for different calls
    return_values = [
        {"CountryCode": "USA", "Value": 331000000},
        {"CountryCode": "CAN", "Value": 38000000},
        {"CountryCode": "GBR", "Value": 67000000}
    ]
    
    mock_country_characteristics.fetch_population_data.side_effect = return_values
    
    # Make multiple calls
    result1 = find_population("USA", 2020)
    result2 = find_population("CAN", 2020) 
    result3 = find_population("GBR", 2020)
    
    # Each call should get its respective return value
    assert result1 == return_values[0]
    assert result2 == return_values[1]
    assert result3 == return_values[2]
    
    # Verify all calls were made with correct parameters
    expected_calls = [
        (("POPULN", "USA", 2020),),
        (("POPULN", "CAN", 2020),),
        (("POPULN", "GBR", 2020),)
    ]
    
    actual_calls = mock_country_characteristics.fetch_population_data.call_args_list
    assert len(actual_calls) == 3
    
    for i, expected_call in enumerate(expected_calls):
        assert actual_calls[i].args == expected_call[0]


@patch('sspi_flask_app.api.resources.utilities.sspi_country_characteristics')
def test_find_population_function_signature(mock_country_characteristics):
    """Test that the function correctly maps its parameters to the database call."""
    
    mock_country_characteristics.fetch_population_data.return_value = {"Value": 123}
    
    # Call with specific parameters
    country = "TEST_COUNTRY"
    year = 2025
    
    find_population(country, year)
    
    # Verify the exact parameter mapping
    args, kwargs = mock_country_characteristics.fetch_population_data.call_args
    
    assert len(args) == 3, "Should pass exactly 3 arguments"
    assert args[0] == "POPULN", "First argument should be dataset code 'POPULN'"
    assert args[1] == country, "Second argument should be the country_code parameter"
    assert args[2] == year, "Third argument should be the year parameter"
    assert len(kwargs) == 0, "Should not pass any keyword arguments"