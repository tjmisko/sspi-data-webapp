import pytest
from sspi_flask_app.api.resources.utilities import string_to_float


def test_string_to_float_valid_numbers():
    """Test conversion of valid numeric strings."""
    
    valid_cases = [
        ("123", 123.0),
        ("123.45", 123.45),
        ("0", 0.0),
        ("0.0", 0.0),
        ("-123", -123.0),
        ("-123.45", -123.45),
        ("1.23e4", 12300.0),
        ("1.23E4", 12300.0),
        ("1.23e-4", 0.000123),
        ("-1.23e4", -12300.0),
        ("  123  ", 123.0),  # Whitespace should be handled by float()
        ("\t456\n", 456.0),
    ]
    
    for input_str, expected in valid_cases:
        result = string_to_float(input_str)
        assert isinstance(result, float), f"Should return float for '{input_str}'"
        assert result == expected, f"Failed for input '{input_str}'"


def test_string_to_float_invalid_strings():
    """Test handling of invalid non-numeric strings."""
    
    truly_invalid_cases = [
        "abc",
        "123abc",
        "abc123",
        "12.34.56",
        "not_a_number",
        "1.23.45",
        "12,345",  # Comma separator
        "$123",
        "123%",
        "1 2 3",
        "1+2",
        "hello world",
    ]
    
    for invalid_str in truly_invalid_cases:
        result = string_to_float(invalid_str)
        assert result == "NaN", f"Should return 'NaN' for invalid string '{invalid_str}'"
        assert isinstance(result, str), f"Should return string for invalid input '{invalid_str}'"
    
    # Test special cases that float() can actually convert
    special_cases = [
        ("NaN", float),  # float("NaN") returns float nan
        ("inf", float),
        ("infinity", float),
        ("-inf", float),
    ]
    
    for special_str, expected_type in special_cases:
        result = string_to_float(special_str)
        assert isinstance(result, expected_type), f"Should return {expected_type.__name__} for '{special_str}'"


def test_string_to_float_empty_inputs():
    """Test handling of empty or None-like inputs."""
    
    # These are falsy and should return "NaN"
    falsy_cases = [
        "",
        None,
        False,  # bool(False) is falsy
        0,      # 0 is also falsy in Python
    ]
    
    for empty_input in falsy_cases:
        result = string_to_float(empty_input)
        assert result == "NaN", f"Should return 'NaN' for falsy input {empty_input}"


def test_string_to_float_special_float_values():
    """Test conversion of special float value strings."""
    
    # Test actual string representations that float() can handle
    special_cases = [
        ("inf", float('inf')),
        ("-inf", float('-inf')),
        ("+inf", float('+inf')),
        ("infinity", float('infinity')),
        ("-infinity", float('-infinity')),
        ("+infinity", float('+infinity')),
    ]
    
    for input_str, expected in special_cases:
        result = string_to_float(input_str)
        assert isinstance(result, float), f"Should return float for '{input_str}'"
        if expected == float('inf'):
            assert result == float('inf'), f"Should return inf for '{input_str}'"
        elif expected == float('-inf'):
            assert result == float('-inf'), f"Should return -inf for '{input_str}'"


def test_string_to_float_nan_string():
    """Test that string 'nan' is handled correctly."""
    
    nan_cases = ["nan", "NaN", "NAN", "-nan", "+nan"]
    
    for nan_str in nan_cases:
        result = string_to_float(nan_str)
        assert isinstance(result, float), f"Should return float for '{nan_str}'"
        assert str(result).lower() == 'nan', f"Should return NaN for '{nan_str}'"


def test_string_to_float_numeric_types():
    """Test behavior with numeric types as input."""
    
    # Non-zero numeric types should convert successfully
    numeric_cases = [
        (123, 123.0),
        (123.45, 123.45),
        (-123, -123.0),
        (1.23e4, 12300.0),
    ]
    
    for input_num, expected in numeric_cases:
        result = string_to_float(input_num)
        assert isinstance(result, float), f"Should return float for numeric input {input_num}"
        assert result == expected, f"Failed for numeric input {input_num}"
    
    # Zero is falsy, so it returns "NaN"
    result_zero = string_to_float(0)
    assert result_zero == "NaN", "Zero should return 'NaN' as it's falsy"


def test_string_to_float_boolean_inputs():
    """Test behavior with boolean inputs."""
    
    # True is truthy, so it should try to convert
    result_true = string_to_float(True)
    assert result_true == 1.0, "True should convert to 1.0"
    
    # False is falsy, so it should return "NaN"
    result_false = string_to_float(False)
    assert result_false == "NaN", "False should return 'NaN'"


def test_string_to_float_very_large_numbers():
    """Test conversion of very large numbers."""
    
    large_cases = [
        ("1e100", 1e100),
        ("1.234567890123456789", 1.234567890123456789),
        ("-1e100", -1e100),
        ("999999999999999999999", 999999999999999999999.0),
    ]
    
    for input_str, expected in large_cases:
        result = string_to_float(input_str)
        assert isinstance(result, float), f"Should return float for large number '{input_str}'"
        assert result == expected, f"Failed for large number '{input_str}'"


def test_string_to_float_very_small_numbers():
    """Test conversion of very small numbers."""
    
    small_cases = [
        ("1e-100", 1e-100),
        ("1.234567890123456789e-50", 1.234567890123456789e-50),
        ("-1e-100", -1e-100),
        ("0.000000000000000001", 1e-18),
    ]
    
    for input_str, expected in small_cases:
        result = string_to_float(input_str)
        assert isinstance(result, float), f"Should return float for small number '{input_str}'"
        assert abs(result - expected) < 1e-200, f"Failed for small number '{input_str}'"


def test_string_to_float_edge_case_strings():
    """Test edge case string inputs."""
    
    edge_cases = [
        (".", "NaN"),
        ("-", "NaN"),
        ("+", "NaN"),
        ("e", "NaN"),
        ("E", "NaN"),
        ("e10", "NaN"),
        ("E10", "NaN"),
        ("10e", "NaN"),
        ("10E", "NaN"),
        ("--123", "NaN"),
        ("++123", "NaN"),
        ("12..34", "NaN"),
        ("1.2.3.4", "NaN"),
    ]
    
    for input_str, expected in edge_cases:
        result = string_to_float(input_str)
        assert result == expected, f"Failed for edge case '{input_str}'"


def test_string_to_float_return_type_consistency():
    """Test that return types are consistent."""
    
    # Valid conversions should return float
    valid_inputs = ["123", "0", "-45.67", "1e5"]
    for valid_input in valid_inputs:
        result = string_to_float(valid_input)
        assert isinstance(result, float), f"Valid input should return float: {valid_input}"
    
    # Invalid conversions should return string "NaN"
    invalid_inputs = ["abc", "", None, "not_a_number"]
    for invalid_input in invalid_inputs:
        result = string_to_float(invalid_input)
        assert result == "NaN", f"Invalid input should return 'NaN': {invalid_input}"
        assert isinstance(result, str), f"Invalid input should return string: {invalid_input}"


def test_string_to_float_whitespace_handling():
    """Test handling of various whitespace scenarios."""
    
    whitespace_cases = [
        ("   123   ", 123.0),
        ("\t456\t", 456.0),
        ("\n789\n", 789.0),
        ("  -123.45  ", -123.45),
        ("\t\n  0  \n\t", 0.0),
    ]
    
    for input_str, expected in whitespace_cases:
        result = string_to_float(input_str)
        assert isinstance(result, float), f"Should return float for whitespace input '{repr(input_str)}'"
        assert result == expected, f"Failed for whitespace input '{repr(input_str)}'"


def test_string_to_float_list_dict_inputs():
    """Test behavior with list and dict inputs."""
    
    # These should raise TypeError/ValueError when float() is called on them
    complex_inputs = [
        [1, 2, 3],
        {"key": "value"},
        (1, 2, 3),
        set([1, 2, 3]),
    ]
    
    for complex_input in complex_inputs:
        # These are truthy, so they'll attempt conversion and should raise an exception
        # The function should catch ValueError but not TypeError
        with pytest.raises(TypeError):
            string_to_float(complex_input)


def test_string_to_float_unicode_strings():
    """Test handling of unicode and special character strings."""
    
    # Test cases where Python's float() can actually handle unicode
    convertible_unicode = [
        ("１２３", 123.0),  # Full-width digits - Python can convert these!
    ]
    
    for input_str, expected in convertible_unicode:
        result = string_to_float(input_str)
        assert isinstance(result, float), f"Should convert unicode digits: '{input_str}'"
        assert result == expected, f"Failed for convertible unicode input '{input_str}'"
    
    # Test cases that should return "NaN"
    non_convertible_unicode = [
        ("①②③", "NaN"),    # Circle numbers
        ("½", "NaN"),       # Fraction symbol
        ("π", "NaN"),       # Greek pi
        ("∞", "NaN"),       # Infinity symbol
        ("−123", "NaN"),    # Unicode minus sign (different from ASCII -)
        ("123°", "NaN"),    # Degree symbol
    ]
    
    for input_str, expected in non_convertible_unicode:
        result = string_to_float(input_str)
        assert result == expected, f"Failed for unicode input '{input_str}'"


def test_string_to_float_realistic_data_scenarios():
    """Test with realistic data scenarios."""
    
    realistic_cases = [
        # CSV data scenarios
        ("85.2", 85.2),
        ("", "NaN"),
        ("NULL", "NaN"),
        ("n/a", "NaN"),
        ("N/A", "NaN"),
        ("-", "NaN"),
        ("--", "NaN"),
        
        # Survey response scenarios
        ("4.5", 4.5),
        ("No response", "NaN"),
        ("Refused", "NaN"),
        ("Don't know", "NaN"),
        
        # Economic data scenarios  
        ("1234567.89", 1234567.89),
        ("1.23E+06", 1230000.0),
        ("-456.78", -456.78),
        ("0.00", 0.0),
        
        # Percentage scenarios
        ("95.6%", "NaN"),  # Contains % symbol
        ("95.6", 95.6),    # Clean percentage
    ]
    
    for input_data, expected in realistic_cases:
        result = string_to_float(input_data)
        if isinstance(expected, float):
            assert isinstance(result, float), f"Should return float for '{input_data}'"
            assert result == expected, f"Failed for realistic input '{input_data}'"
        else:
            assert result == expected, f"Failed for realistic input '{input_data}'"
            assert isinstance(result, str), f"Should return string for '{input_data}'"


def test_string_to_float_filter_pattern():
    """Test the documented usage pattern for filtering non-numeric values."""
    
    mixed_data = ["123", "456.78", "invalid", "", "789", None, "abc123"]
    
    # Filter to get only numeric values using type checking
    numeric_values = []
    for item in mixed_data:
        converted = string_to_float(item)
        if isinstance(converted, float):
            numeric_values.append(converted)
    
    expected_numeric = [123.0, 456.78, 789.0]
    assert numeric_values == expected_numeric, "Filter pattern should extract only valid numeric values"


def test_string_to_float_performance_edge_cases():
    """Test edge cases that might affect performance."""
    
    # Very long strings
    very_long_number = "1" + "0" * 1000
    result = string_to_float(very_long_number)
    assert isinstance(result, float), "Should handle very long numeric strings"
    
    # Very long invalid string
    very_long_invalid = "a" * 1000
    result = string_to_float(very_long_invalid)
    assert result == "NaN", "Should return 'NaN' for very long invalid strings"
    
    # String with many decimal places
    many_decimals = "1." + "1" * 100
    result = string_to_float(many_decimals)
    assert isinstance(result, float), "Should handle strings with many decimal places"