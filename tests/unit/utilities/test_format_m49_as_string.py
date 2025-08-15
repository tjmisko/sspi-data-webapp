import pytest
from sspi_flask_app.api.resources.utilities import format_m49_as_string


def test_format_m49_as_string_three_digit_numbers():
    """Test formatting of numbers that are already 3 digits (100 and above)."""
    
    three_digit_cases = [
        (100, "100"),
        (123, "123"),
        (456, "456"),
        (789, "789"),
        (999, "999"),
        (840, "840"),  # USA M49 code
        (276, "276"),  # Germany M49 code
        (826, "826"),  # United Kingdom M49 code
    ]
    
    for input_val, expected in three_digit_cases:
        result = format_m49_as_string(input_val)
        assert result == expected, f"Failed for 3-digit input {input_val}"
        assert len(result) == 3, f"Result should be 3 digits for {input_val}"


def test_format_m49_as_string_two_digit_numbers():
    """Test formatting of 2-digit numbers (10-99) - should get one leading zero."""
    
    two_digit_cases = [
        (10, "010"),
        (15, "015"),
        (20, "020"),
        (50, "050"),
        (75, "075"),
        (99, "099"),
        (12, "012"),  # Algeria M49 code
        (32, "032"),  # Argentina M49 code
        (36, "036"),  # Australia M49 code
    ]
    
    for input_val, expected in two_digit_cases:
        result = format_m49_as_string(input_val)
        assert result == expected, f"Failed for 2-digit input {input_val}"
        assert len(result) == 3, f"Result should be 3 digits for {input_val}"


def test_format_m49_as_string_one_digit_numbers():
    """Test formatting of 1-digit numbers (0-9) - should get two leading zeros."""
    
    one_digit_cases = [
        (0, "000"),
        (1, "001"),
        (2, "002"),
        (5, "005"),
        (7, "007"),
        (9, "009"),
        (4, "004"),  # Afghanistan M49 code
        (8, "008"),  # Albania M49 code
    ]
    
    for input_val, expected in one_digit_cases:
        result = format_m49_as_string(input_val)
        assert result == expected, f"Failed for 1-digit input {input_val}"
        assert len(result) == 3, f"Result should be 3 digits for {input_val}"


def test_format_m49_as_string_large_numbers():
    """Test formatting of numbers larger than 999."""
    
    large_number_cases = [
        (1000, "1000"),
        (1234, "1234"),
        (9999, "9999"),
        (10000, "10000"),
    ]
    
    for input_val, expected in large_number_cases:
        result = format_m49_as_string(input_val)
        assert result == expected, f"Failed for large input {input_val}"
        # Note: Large numbers will be longer than 3 digits


def test_format_m49_as_string_string_inputs():
    """Test formatting with string inputs that can be converted to int."""
    
    string_cases = [
        ("100", "100"),
        ("50", "050"),
        ("5", "005"),
        ("0", "000"),
        ("999", "999"),
        ("840", "840"),  # USA as string
        ("076", "076"),  # Already formatted string
    ]
    
    for input_val, expected in string_cases:
        result = format_m49_as_string(input_val)
        assert result == expected, f"Failed for string input '{input_val}'"
        assert len(result) == 3 or int(input_val) >= 1000, f"Result length issue for '{input_val}'"


def test_format_m49_as_string_float_inputs():
    """Test formatting with float inputs (should be converted to int first)."""
    
    float_cases = [
        (100.0, "100"),
        (100.9, "100"),  # Should truncate decimal
        (50.0, "050"),
        (50.7, "050"),   # Should truncate decimal
        (5.0, "005"),
        (5.9, "005"),    # Should truncate decimal
        (0.0, "000"),
        (999.9, "999"),  # Should truncate decimal
    ]
    
    for input_val, expected in float_cases:
        result = format_m49_as_string(input_val)
        assert result == expected, f"Failed for float input {input_val}"


def test_format_m49_as_string_negative_numbers():
    """Test formatting with negative numbers."""
    
    # Negative numbers are converted to int, then formatted based on absolute comparisons
    # Since negative numbers are < 10 and < 100, they get "00" prefix
    negative_cases = [
        (-1, "00-1"),
        (-10, "00-10"),
        (-100, "00-100"),
        (-5, "00-5"),
    ]
    
    for input_val, expected in negative_cases:
        result = format_m49_as_string(input_val)
        assert result == expected, f"Failed for negative input {input_val}"


def test_format_m49_as_string_boundary_values():
    """Test formatting at boundary values."""
    
    boundary_cases = [
        (9, "009"),    # Just below 10
        (10, "010"),   # Exactly 10
        (99, "099"),   # Just below 100
        (100, "100"),  # Exactly 100
    ]
    
    for input_val, expected in boundary_cases:
        result = format_m49_as_string(input_val)
        assert result == expected, f"Failed for boundary value {input_val}"


def test_format_m49_as_string_invalid_string_inputs():
    """Test that invalid string inputs raise appropriate errors."""
    
    invalid_strings = [
        "abc",
        "12.5abc",
        "not_a_number",
        "",
        "1.2.3",
        "NaN"
    ]
    
    for invalid_input in invalid_strings:
        with pytest.raises(ValueError):
            format_m49_as_string(invalid_input)


def test_format_m49_as_string_none_input():
    """Test that None input raises appropriate error."""
    
    with pytest.raises(TypeError):
        format_m49_as_string(None)


def test_format_m49_as_string_list_input():
    """Test that list input raises appropriate error."""
    
    with pytest.raises(TypeError):
        format_m49_as_string([1, 2, 3])


def test_format_m49_as_string_dict_input():
    """Test that dict input raises appropriate error."""
    
    with pytest.raises(TypeError):
        format_m49_as_string({"number": 123})


def test_format_m49_as_string_realistic_m49_codes():
    """Test with realistic M49 country codes."""
    
    realistic_m49_codes = [
        (4, "004"),     # Afghanistan
        (8, "008"),     # Albania  
        (12, "012"),    # Algeria
        (20, "020"),    # Andorra
        (24, "024"),    # Angola
        (32, "032"),    # Argentina
        (36, "036"),    # Australia
        (40, "040"),    # Austria
        (51, "051"),    # Armenia
        (56, "056"),    # Belgium
        (124, "124"),   # Canada
        (156, "156"),   # China
        (208, "208"),   # Denmark
        (276, "276"),   # Germany
        (380, "380"),   # Italy
        (392, "392"),   # Japan
        (484, "484"),   # Mexico
        (826, "826"),   # United Kingdom
        (840, "840"),   # United States
    ]
    
    for input_val, expected in realistic_m49_codes:
        result = format_m49_as_string(input_val)
        assert result == expected, f"Failed for M49 code {input_val}"
        assert len(result) == 3, f"M49 code should be 3 digits: {input_val}"


def test_format_m49_as_string_edge_case_zeros():
    """Test edge cases around zero values."""
    
    zero_cases = [
        (0, "000"),
        (0.0, "000"),
        ("0", "000"),
        ("00", "000"),
        ("000", "000"),
    ]
    
    for input_val, expected in zero_cases:
        result = format_m49_as_string(input_val)
        assert result == expected, f"Failed for zero case {input_val}"


def test_format_m49_as_string_scientific_notation():
    """Test with numbers in scientific notation."""
    
    scientific_cases = [
        (1e2, "100"),   # 100.0
        (1e1, "010"),   # 10.0
        (1e0, "001"),   # 1.0
        (5e1, "050"),   # 50.0
    ]
    
    for input_val, expected in scientific_cases:
        result = format_m49_as_string(input_val)
        assert result == expected, f"Failed for scientific notation {input_val}"


def test_format_m49_as_string_string_with_leading_zeros():
    """Test string inputs that already have leading zeros."""
    
    leading_zero_cases = [
        ("001", "001"),
        ("010", "010"), 
        ("100", "100"),
        ("050", "050"),
        ("005", "005"),
        ("0001", "001"),  # Extra leading zero should be truncated by int conversion
        ("0050", "050"),
        ("0100", "100"),
    ]
    
    for input_val, expected in leading_zero_cases:
        result = format_m49_as_string(input_val)
        assert result == expected, f"Failed for leading zero string '{input_val}'"


def test_format_m49_as_string_whitespace_strings():
    """Test string inputs with whitespace."""
    
    whitespace_cases = [
        (" 100 ", "100"),
        ("\t50\n", "050"),
        ("  5  ", "005"),
        (" 0 ", "000"),
    ]
    
    for input_val, expected in whitespace_cases:
        result = format_m49_as_string(input_val)
        assert result == expected, f"Failed for whitespace string '{input_val}'"


def test_format_m49_as_string_return_type():
    """Test that the function always returns a string."""
    
    test_inputs = [0, 5, 50, 500]
    
    for input_val in test_inputs:
        result = format_m49_as_string(input_val)
        assert isinstance(result, str), f"Result should be string for input {input_val}"


def test_format_m49_as_string_comprehensive_range():
    """Test a comprehensive range of values to ensure correct formatting."""
    
    # Test all values from 0 to 200 to ensure consistent behavior
    for i in range(201):
        result = format_m49_as_string(i)
        
        if i >= 100:
            expected = str(i)
        elif i >= 10:
            expected = "0" + str(i)
        else:
            expected = "00" + str(i)
        
        assert result == expected, f"Failed for comprehensive test value {i}"
        
        # All results should be at least 3 characters for valid M49 range
        if i < 1000:
            assert len(result) == 3, f"Length should be 3 for value {i}"