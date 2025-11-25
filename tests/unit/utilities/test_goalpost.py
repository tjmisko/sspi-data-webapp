import pytest
import math
from sspi_flask_app.api.resources.utilities import goalpost


def test_goalpost_normal_range():
    """Test goalposting with values within the normal range."""
    
    # Value exactly in the middle should return 0.5
    assert goalpost(5, 0, 10) == 0.5
    
    # Value at 25% should return 0.25
    assert goalpost(2.5, 0, 10) == 0.25
    
    # Value at 75% should return 0.75
    assert goalpost(7.5, 0, 10) == 0.75


def test_goalpost_boundary_values():
    """Test goalposting with boundary values."""
    
    # Value at lower bound should return 0
    assert goalpost(0, 0, 10) == 0.0
    
    # Value at upper bound should return 1
    assert goalpost(10, 0, 10) == 1.0
    
    # Test with different bounds
    assert goalpost(50, 50, 100) == 0.0
    assert goalpost(100, 50, 100) == 1.0
    assert goalpost(75, 50, 100) == 0.5


def test_goalpost_values_below_lower_bound():
    """Test goalposting with values below the lower bound (should return 0)."""
    
    # Values below lower bound should be clamped to 0
    assert goalpost(-5, 0, 10) == 0.0
    assert goalpost(-100, 0, 10) == 0.0
    assert goalpost(0, 10, 20) == 0.0
    assert goalpost(5, 10, 20) == 0.0


def test_goalpost_values_above_upper_bound():
    """Test goalposting with values above the upper bound (should return 1)."""
    
    # Values above upper bound should be clamped to 1
    assert goalpost(15, 0, 10) == 1.0
    assert goalpost(100, 0, 10) == 1.0
    assert goalpost(25, 10, 20) == 1.0
    assert goalpost(1000, 10, 20) == 1.0


def test_goalpost_negative_ranges():
    """Test goalposting with negative value ranges."""
    
    # Range from negative to positive
    assert goalpost(-5, -10, 0) == 0.5
    assert goalpost(-10, -10, 0) == 0.0
    assert goalpost(0, -10, 0) == 1.0
    
    # Both bounds negative
    assert goalpost(-5, -10, -2) == 0.625  # (-5 - (-10)) / (-2 - (-10)) = 5/8
    assert goalpost(-10, -10, -2) == 0.0
    assert goalpost(-2, -10, -2) == 1.0


def test_goalpost_floating_point_values():
    """Test goalposting with floating point values."""
    
    # Test with float values
    assert goalpost(3.14, 0.0, 10.0) == pytest.approx(0.314, rel=1e-6)
    assert goalpost(2.5, 1.0, 4.0) == pytest.approx(0.5, rel=1e-6)
    assert goalpost(7.3, 2.1, 8.9) == pytest.approx(0.7647, rel=1e-3)


def test_goalpost_very_small_ranges():
    """Test goalposting with very small value ranges."""
    
    # Small range around zero
    result = goalpost(0.0005, 0.0, 0.001)
    assert result == pytest.approx(0.5, rel=1e-6)
    
    # Small range with larger base values
    result = goalpost(100.0005, 100.0, 100.001)
    assert result == pytest.approx(0.5, rel=1e-6)


def test_goalpost_large_ranges():
    """Test goalposting with very large value ranges."""
    
    # Large range
    result = goalpost(500000, 0, 1000000)
    assert result == pytest.approx(0.5, rel=1e-6)
    
    # Very large numbers
    result = goalpost(5e6, 0, 1e7)
    assert result == pytest.approx(0.5, rel=1e-6)


def test_goalpost_identical_bounds_handled_gracefully():
    """Test that identical upper and lower bounds are handled gracefully."""

    # When upper == lower, return 0.5 if value equals bounds, else clamp
    # Value above the single goalpost -> 1.0
    assert goalpost(5, 10, 10) == 0.0  # 5 < 10, so returns 0.0

    # Value equals the single goalpost -> 0.5
    assert goalpost(0, 0, 0) == 0.5
    assert goalpost(3.14, 3.14, 3.14) == 0.5

    # Value below the single goalpost -> 0.0
    assert goalpost(-5, 3.14, 3.14) == 0.0

    # Value above the single goalpost -> 1.0
    assert goalpost(15, 10, 10) == 1.0


def test_goalpost_inverted_bounds():
    """Test goalposting when upper bound is less than lower bound."""
    
    # When upper < lower, the formula still works mathematically
    result = goalpost(5, 10, 0)
    # (5 - 10) / (0 - 10) = -5 / -10 = 0.5
    # min(1, 0.5) = 0.5
    # max(0, 0.5) = 0.5
    assert result == 0.5
    
    # Test another case where result would be negative before max(0, ...)
    result = goalpost(15, 10, 0)
    # (15 - 10) / (0 - 10) = 5 / -10 = -0.5
    # min(1, -0.5) = -0.5
    # max(0, -0.5) = 0
    assert result == 0.0


def test_goalpost_edge_cases_precision():
    """Test goalposting edge cases that might have precision issues."""
    
    # Test values very close to bounds
    epsilon = 1e-15
    
    # Just above lower bound
    result = goalpost(epsilon, 0, 1)
    assert result == pytest.approx(epsilon, rel=1e-12)
    
    # Just below upper bound
    result = goalpost(1 - epsilon, 0, 1)
    assert result == pytest.approx(1 - epsilon, rel=1e-12)


def test_goalpost_mathematical_properties():
    """Test mathematical properties of the goalpost function."""
    
    # Monotonicity: if value1 < value2, then goalpost(value1) <= goalpost(value2)
    # (when bounds are normal, i.e., lower < upper)
    lower, upper = 0, 10
    for i in range(10):
        val1 = i
        val2 = i + 1
        result1 = goalpost(val1, lower, upper)
        result2 = goalpost(val2, lower, upper)
        assert result1 <= result2, f"Monotonicity violated: goalpost({val1}) = {result1} > goalpost({val2}) = {result2}"


def test_goalpost_linearity():
    """Test that goalpost function is linear within bounds."""
    
    lower, upper = 0, 10
    
    # Test that the function is linear between bounds
    # If we take two points within bounds, the midpoint should give the average result
    val1 = 2
    val2 = 8
    midpoint = (val1 + val2) / 2  # 5
    
    result1 = goalpost(val1, lower, upper)  # 0.2
    result2 = goalpost(val2, lower, upper)  # 0.8
    result_mid = goalpost(midpoint, lower, upper)  # 0.5
    expected_mid = (result1 + result2) / 2  # 0.5
    
    assert result_mid == pytest.approx(expected_mid, rel=1e-10)


def test_goalpost_special_numeric_values():
    """Test goalpost with special numeric values like infinity and NaN."""

    # Test with infinity
    result = goalpost(float('inf'), 0, 10)
    assert result == 1.0  # Should be clamped to 1

    result = goalpost(float('-inf'), 0, 10)
    assert result == 0.0  # Should be clamped to 0

    # Test with NaN - raises ValueError to indicate upstream data quality issue
    with pytest.raises(ValueError, match="NaN value"):
        goalpost(float('nan'), 0, 10)

    # Test bounds with NaN - raises ValueError
    with pytest.raises(ValueError, match="NaN goalpost bounds"):
        goalpost(5, float('nan'), 10)

    with pytest.raises(ValueError, match="NaN goalpost bounds"):
        goalpost(5, 0, float('nan'))

    # Test bounds with infinity
    result = goalpost(5, 0, float('inf'))
    assert result == 0.0  # (5-0)/(inf-0) = 0

    result = goalpost(5, float('-inf'), 10)
    assert result == 1.0  # (5-(-inf))/(10-(-inf)) = inf/inf = indeterminate, but gets clamped to 1


def test_goalpost_realistic_sspi_scenarios():
    """Test goalpost with realistic SSPI data scenarios."""
    
    # GDP per capita normalization (example values)
    gdp_value = 45000  # USD
    gdp_lower = 0      # Minimum possible
    gdp_upper = 100000 # Upper goalpost
    result = goalpost(gdp_value, gdp_lower, gdp_upper)
    assert result == 0.45
    
    # Life expectancy normalization
    life_exp = 75      # years
    life_lower = 20    # Lower goalpost
    life_upper = 85    # Upper goalpost  
    result = goalpost(life_exp, life_lower, life_upper)
    assert result == pytest.approx(0.846, rel=1e-2)  # (75-20)/(85-20) = 55/65
    
    # Percentage indicator (already 0-100, normalize to 0-1)
    percentage = 65.5  # %
    result = goalpost(percentage, 0, 100)
    assert result == 0.655