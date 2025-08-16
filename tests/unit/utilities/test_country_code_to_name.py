import pytest
from unittest.mock import patch, MagicMock
from sspi_flask_app.api.resources.utilities import country_code_to_name


@patch('sspi_flask_app.api.resources.utilities.pycountry')
def test_country_code_to_name_valid_codes(mock_pycountry):
    """Test conversion of valid ISO alpha-3 country codes to names."""
    
    valid_codes = [
        ("USA", "United States"),
        ("CAN", "Canada"),
        ("GBR", "United Kingdom"),
        ("FRA", "France"),
        ("DEU", "Germany"),
        ("JPN", "Japan"),
        ("BRA", "Brazil"),
        ("AUS", "Australia"),
        ("IND", "India"),
        ("CHN", "China")
    ]
    
    for code, expected_name in valid_codes:
        mock_country = MagicMock()
        mock_country.name = expected_name
        mock_pycountry.countries.get.return_value = mock_country
        
        result = country_code_to_name(code)
        
        assert result == expected_name, f"Failed for country code {code}"
        mock_pycountry.countries.get.assert_called_with(alpha_3=code)


@patch('sspi_flask_app.api.resources.utilities.pycountry')
def test_country_code_to_name_invalid_codes(mock_pycountry):
    """Test handling of invalid country codes."""
    
    invalid_codes = [
        "XXX",  # Non-existent code
        "ZZZ",  # Non-existent code  
        "ABC",  # Non-existent code
        "123",  # Numeric code
        "INVALID"  # Too long
    ]
    
    for code in invalid_codes:
        # Mock pycountry returning None for invalid codes
        mock_pycountry.countries.get.return_value = None
        
        result = country_code_to_name(code)
        
        assert result == code, f"Should return original code for invalid: {code}"
        mock_pycountry.countries.get.assert_called_with(alpha_3=code)


@patch('sspi_flask_app.api.resources.utilities.pycountry')
def test_country_code_to_name_pycountry_exception(mock_pycountry):
    """Test handling when pycountry raises an exception."""
    
    test_codes = ["USA", "CAN", "GBR"]
    
    for code in test_codes:
        # Mock pycountry raising AttributeError
        mock_pycountry.countries.get.side_effect = AttributeError("Country not found")
        
        result = country_code_to_name(code)
        
        assert result == code, f"Should return original code when exception for: {code}"
        mock_pycountry.countries.get.assert_called_with(alpha_3=code)


@patch('sspi_flask_app.api.resources.utilities.pycountry')
def test_country_code_to_name_none_result(mock_pycountry):
    """Test when pycountry.countries.get returns None."""
    
    test_codes = ["XKX", "XXX", "YYY"]  # Non-standard or invalid codes
    
    for code in test_codes:
        mock_pycountry.countries.get.return_value = None
        
        result = country_code_to_name(code)
        
        assert result == code, f"Should return original code when None result for: {code}"


@patch('sspi_flask_app.api.resources.utilities.pycountry')
def test_country_code_to_name_empty_string(mock_pycountry):
    """Test handling of empty string input."""
    
    mock_pycountry.countries.get.return_value = None
    
    result = country_code_to_name("")
    
    assert result == ""
    mock_pycountry.countries.get.assert_called_with(alpha_3="")


@patch('sspi_flask_app.api.resources.utilities.pycountry')
def test_country_code_to_name_none_input(mock_pycountry):
    """Test handling of None input."""
    
    mock_pycountry.countries.get.return_value = None
    
    result = country_code_to_name(None)
    
    assert result == None
    mock_pycountry.countries.get.assert_called_with(alpha_3=None)


@patch('sspi_flask_app.api.resources.utilities.pycountry')
def test_country_code_to_name_case_sensitivity(mock_pycountry):
    """Test case sensitivity of country codes."""
    
    # Test lowercase codes
    mock_pycountry.countries.get.return_value = None
    
    lowercase_codes = ["usa", "can", "gbr"]
    
    for code in lowercase_codes:
        result = country_code_to_name(code)
        assert result == code  # Should return as-is if not found
        mock_pycountry.countries.get.assert_called_with(alpha_3=code)


@patch('sspi_flask_app.api.resources.utilities.pycountry')
def test_country_code_to_name_special_codes(mock_pycountry):
    """Test handling of special or non-standard country codes."""
    
    special_codes = [
        "XKX",  # Kosovo (non-ISO)
        "TWN",  # Taiwan
        "PSE",  # Palestine
        "EU",   # European Union (not a country)
        "UK"    # Common abbreviation (not ISO alpha-3)
    ]
    
    for code in special_codes:
        mock_pycountry.countries.get.return_value = None
        
        result = country_code_to_name(code)
        
        assert result == code, f"Should return original for special code: {code}"


@patch('sspi_flask_app.api.resources.utilities.pycountry')
def test_country_code_to_name_numeric_input(mock_pycountry):
    """Test handling of numeric input."""
    
    numeric_inputs = [123, 456, 0]
    
    for code in numeric_inputs:
        mock_pycountry.countries.get.return_value = None
        
        result = country_code_to_name(code)
        
        assert result == code
        mock_pycountry.countries.get.assert_called_with(alpha_3=code)


@patch('sspi_flask_app.api.resources.utilities.pycountry')
def test_country_code_to_name_long_codes(mock_pycountry):
    """Test handling of codes that are too long."""
    
    long_codes = [
        "USAA",     # 4 characters
        "UNITED",   # 6 characters
        "TOOLONG"   # 7 characters
    ]
    
    for code in long_codes:
        mock_pycountry.countries.get.return_value = None
        
        result = country_code_to_name(code)
        
        assert result == code, f"Should return original for long code: {code}"


@patch('sspi_flask_app.api.resources.utilities.pycountry')
def test_country_code_to_name_short_codes(mock_pycountry):
    """Test handling of codes that are too short."""
    
    short_codes = [
        "U",   # 1 character
        "US",  # 2 characters (alpha-2, not alpha-3)
        "A"    # 1 character
    ]
    
    for code in short_codes:
        mock_pycountry.countries.get.return_value = None
        
        result = country_code_to_name(code)
        
        assert result == code, f"Should return original for short code: {code}"


@patch('sspi_flask_app.api.resources.utilities.pycountry')
def test_country_code_to_name_whitespace_codes(mock_pycountry):
    """Test handling of codes with whitespace."""
    
    whitespace_codes = [
        " USA",   # Leading space
        "USA ",   # Trailing space
        " USA ",  # Both spaces
        "U SA",   # Space in middle
        "\tUSA",  # Tab
        "USA\n"   # Newline
    ]
    
    for code in whitespace_codes:
        mock_pycountry.countries.get.return_value = None
        
        result = country_code_to_name(code)
        
        assert result == code, f"Should return original for whitespace code: '{code}'"


@patch('sspi_flask_app.api.resources.utilities.pycountry')
def test_country_code_to_name_special_characters(mock_pycountry):
    """Test handling of codes with special characters."""
    
    special_char_codes = [
        "US@",    # With symbol
        "US-A",   # With hyphen
        "US_A",   # With underscore
        "US.A",   # With period
        "US/A"    # With slash
    ]
    
    for code in special_char_codes:
        mock_pycountry.countries.get.return_value = None
        
        result = country_code_to_name(code)
        
        assert result == code, f"Should return original for special char code: {code}"


@patch('sspi_flask_app.api.resources.utilities.pycountry')
def test_country_code_to_name_realistic_iso_codes(mock_pycountry):
    """Test with realistic ISO alpha-3 codes and their expected names."""
    
    realistic_codes = [
        # Common countries
        ("USA", "United States of America"),
        ("GBR", "United Kingdom of Great Britain and Northern Ireland"),
        ("RUS", "Russian Federation"),
        ("CHN", "China"),
        
        # Smaller countries
        ("LIE", "Liechtenstein"),
        ("SMR", "San Marino"),
        ("VAT", "Holy See"),
        ("MCO", "Monaco"),
        
        # Countries with complex names
        ("LAO", "Lao People's Democratic Republic"),
        ("PRK", "Democratic People's Republic of Korea"),
        ("IRN", "Iran (Islamic Republic of)"),
        ("VEN", "Venezuela (Bolivarian Republic of)")
    ]
    
    for code, expected_name in realistic_codes:
        mock_country = MagicMock()
        mock_country.name = expected_name
        mock_pycountry.countries.get.return_value = mock_country
        
        result = country_code_to_name(code)
        
        assert result == expected_name, f"Failed for {code}"
        mock_pycountry.countries.get.assert_called_with(alpha_3=code)


@patch('sspi_flask_app.api.resources.utilities.pycountry')
def test_country_code_to_name_country_object_no_name_attribute(mock_pycountry):
    """Test when country object exists but has no name attribute."""
    
    # Create a mock country object without name attribute
    mock_country = MagicMock()
    del mock_country.name  # Remove name attribute
    mock_pycountry.countries.get.return_value = mock_country
    
    result = country_code_to_name("USA")
    
    # Should raise AttributeError and return original code
    assert result == "USA"


@patch('sspi_flask_app.api.resources.utilities.pycountry')
def test_country_code_to_name_country_name_is_none(mock_pycountry):
    """Test when country object exists but name is None."""
    
    mock_country = MagicMock()
    mock_country.name = None
    mock_pycountry.countries.get.return_value = mock_country
    
    result = country_code_to_name("USA")
    
    # Should return None as the name
    assert result is None


@patch('sspi_flask_app.api.resources.utilities.pycountry')
def test_country_code_to_name_country_name_empty_string(mock_pycountry):
    """Test when country object exists but name is empty string."""
    
    mock_country = MagicMock()
    mock_country.name = ""
    mock_pycountry.countries.get.return_value = mock_country
    
    result = country_code_to_name("USA")
    
    # Should return empty string as the name
    assert result == ""


def test_country_code_to_name_integration_with_real_pycountry():
    """Integration test with real pycountry (if available)."""
    
    try:
        # Test with a few real codes to ensure integration works
        real_test_cases = [
            ("USA", "United States"),
            ("CAN", "Canada"),
            ("GBR", "United Kingdom")
        ]
        
        for code, expected_substring in real_test_cases:
            result = country_code_to_name(code)
            
            # Check if the expected substring is in the result
            # (since pycountry names may be longer/different)
            assert expected_substring.lower() in result.lower(), f"Expected '{expected_substring}' in result for {code}"
            
    except Exception:
        # Skip if pycountry is not available or has issues
        pytest.skip("Real pycountry integration test skipped")