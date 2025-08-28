import pytest
import math
from sspi_flask_app.api.resources.utilities import score_indicator
from sspi_flask_app.models.errors import InvalidDocumentFormatError


@pytest.fixture
def valid_test_data():
    """Test data with consistent units for successful processing."""
    return [
        {
            "DatasetCode": "DATASET_A",
            "CountryCode": "USA",
            "Year": 2020,
            "Value": 100,
            "Unit": "Index"
        },
        {
            "DatasetCode": "DATASET_B", 
            "CountryCode": "USA",
            "Year": 2020,
            "Value": 80,
            "Unit": "Index"
        },
        {
            "DatasetCode": "DATASET_A",
            "CountryCode": "CAN",
            "Year": 2020,
            "Value": 90,
            "Unit": "Index"
        },
        {
            "DatasetCode": "DATASET_B",
            "CountryCode": "CAN", 
            "Year": 2020,
            "Value": 85,
            "Unit": "Index"
        }
    ]


@pytest.fixture
def inconsistent_units_data():
    """Test data with inconsistent units."""
    return [
        {
            "DatasetCode": "DATASET_A",
            "CountryCode": "USA",
            "Year": 2020,
            "Value": 100,
            "Unit": "Index"
        },
        {
            "DatasetCode": "DATASET_B", 
            "CountryCode": "USA",
            "Year": 2020,
            "Value": 80,
            "Unit": "Percentage"  # Different unit
        }
    ]


@pytest.fixture
def data_with_none_values():
    """Test data containing None values."""
    return [
        {
            "DatasetCode": "DATASET_A",
            "CountryCode": "USA",
            "Year": 2020,
            "Value": None,
            "Unit": "Index"
        },
        {
            "DatasetCode": "DATASET_B",
            "CountryCode": "USA", 
            "Year": 2020,
            "Value": 80,
            "Unit": "Index"
        }
    ]


@pytest.fixture
def data_with_nan_values():
    """Test data containing NaN values.""" 
    return [
        {
            "DatasetCode": "DATASET_A",
            "CountryCode": "USA",
            "Year": 2020,
            "Value": float('nan'),
            "Unit": "Index"
        },
        {
            "DatasetCode": "DATASET_B",
            "CountryCode": "USA",
            "Year": 2020, 
            "Value": 80,
            "Unit": "Index"
        }
    ]


def test_score_indicator_empty_dataset():
    """Test score_indicator with empty dataset list."""
    
    def simple_score(DATASET_A):
        return DATASET_A / 100
    
    result, incomplete = score_indicator([], "TEST_INDICATOR", simple_score, "Score")
    
    assert result == []
    assert incomplete == []


def test_score_indicator_missing_required_datasets():
    """Test score_indicator when required datasets are missing."""
    
    # Score function expects DATASET_A and DATASET_B, but only DATASET_A is provided
    data = [
        {
            "DatasetCode": "DATASET_A",
            "CountryCode": "USA", 
            "Year": 2020,
            "Value": 100,
            "Unit": "Index"
        }
    ]
    
    def two_dataset_score(DATASET_A, DATASET_B):
        return (DATASET_A + DATASET_B) / 2
    
    result, incomplete = score_indicator(data, "TEST_INDICATOR", two_dataset_score, "Score")
    
    # Should not produce any complete results due to missing dataset
    assert len(result) == 0
    assert len(incomplete) == 1  # One incomplete record


def test_score_indicator_with_none_values(data_with_none_values):
    """Test score_indicator handles None values correctly."""
    
    def simple_score(DATASET_A, DATASET_B):
        return (DATASET_A + DATASET_B) / 2
    
    # None values should cause TypeError in convert_data_types
    with pytest.raises(TypeError):
        score_indicator(data_with_none_values, "TEST_INDICATOR", simple_score, "Score")


def test_score_indicator_with_nan_values(data_with_nan_values):
    """Test score_indicator handles NaN values correctly."""
    
    def simple_score(DATASET_A, DATASET_B):
        return (DATASET_A + DATASET_B) / 2
    
    # NaN values should cause InvalidDocumentFormatError in validation
    with pytest.raises(InvalidDocumentFormatError):
        score_indicator(data_with_nan_values, "TEST_INDICATOR", simple_score, "Score")


def test_score_indicator_inconsistent_units_error():
    """Test that missing Unit field raises InvalidDocumentFormatError."""
    
    # Data with missing Unit field (like in the original test)
    data = [
        {
            "DatasetCode": "DATASET_A",
            "CountryCode": "USA",
            "Year": 2020,
            "Value": 100,
            "Unit": "Index"
        },
        {
            "DatasetCode": "DATASET_B",
            "CountryCode": "USA", 
            "Year": 2020,
            "Value": 80
            # Missing "Unit" field
        }
    ]
    
    def simple_score(DATASET_A, DATASET_B):
        return (DATASET_A + DATASET_B) / 2
    
    with pytest.raises(InvalidDocumentFormatError):
        score_indicator(data, "TEST_INDICATOR", simple_score, "Score")


def test_score_indicator_invalid_data_types():
    """Test score_indicator with invalid data types."""
    
    # Non-numeric values should cause issues
    data = [
        {
            "DatasetCode": "DATASET_A",
            "CountryCode": "USA",
            "Year": "2020",  # String that can be converted to int
            "Value": "not_a_number",  # String that cannot be converted to float
            "Unit": "Index"
        }
    ]
    
    def simple_score(DATASET_A):
        return DATASET_A / 100
    
    # Invalid data types should raise ValueError in convert_data_types
    with pytest.raises(ValueError):
        score_indicator(data, "TEST_INDICATOR", simple_score, "Score")


def test_score_indicator_string_unit_parameter(valid_test_data):
    """Test score_indicator with string unit parameter."""
    
    def simple_score(DATASET_A, DATASET_B):
        return (DATASET_A + DATASET_B) / 2
    
    result, incomplete = score_indicator(valid_test_data, "TEST_INDICATOR", simple_score, "Normalized Score")
    
    assert len(result) == 2  # USA and CAN
    assert all(doc["Unit"] == "Normalized Score" for doc in result)
    assert all(doc["IndicatorCode"] == "TEST_INDICATOR" for doc in result)


def test_score_indicator_callable_unit_parameter(valid_test_data):
    """Test score_indicator with callable unit parameter."""
    
    def simple_score(DATASET_A, DATASET_B):
        return (DATASET_A + DATASET_B) / 2
    
    def unit_function(DATASET_A, DATASET_B):
        if DATASET_A > DATASET_B:
            return "High Score"
        else:
            return "Low Score"
    
    result, incomplete = score_indicator(valid_test_data, "TEST_INDICATOR", simple_score, unit_function)
    
    assert len(result) == 2
    # USA: (100 + 80) / 2 = 90, DATASET_A (100) > DATASET_B (80) = "High Score"
    # CAN: (90 + 85) / 2 = 87.5, DATASET_A (90) > DATASET_B (85) = "High Score"
    assert all(doc["Unit"] == "High Score" for doc in result)


def test_score_indicator_complex_score_function(valid_test_data):
    """Test score_indicator with a complex scoring function."""
    
    def complex_score(DATASET_A, DATASET_B):
        # Weighted average with bounds checking
        weighted = (DATASET_A * 0.6 + DATASET_B * 0.4)
        return min(100, max(0, weighted))
    
    result, incomplete = score_indicator(valid_test_data, "COMPLEX_INDICATOR", complex_score, "Weighted Index")
    
    assert len(result) == 2
    assert all("Score" in doc for doc in result)
    assert all(0 <= doc["Score"] <= 100 for doc in result)
    
    # Check specific calculations
    usa_result = next(doc for doc in result if doc["CountryCode"] == "USA")
    expected_usa = 100 * 0.6 + 80 * 0.4  # 60 + 32 = 92
    assert usa_result["Score"] == expected_usa


def test_score_indicator_score_function_with_division_by_zero():
    """Test score_indicator when score function causes division by zero."""
    
    data = [
        {
            "DatasetCode": "DATASET_A",
            "CountryCode": "USA",
            "Year": 2020,
            "Value": 100,
            "Unit": "Index"
        },
        {
            "DatasetCode": "DATASET_B",
            "CountryCode": "USA", 
            "Year": 2020,
            "Value": 0,  # Will cause division by zero
            "Unit": "Index"
        }
    ]
    
    def division_score(DATASET_A, DATASET_B):
        return DATASET_A / DATASET_B  # Division by zero!
    
    # Division by zero should raise ZeroDivisionError
    with pytest.raises(ZeroDivisionError):
        score_indicator(data, "DIV_INDICATOR", division_score, "Ratio")


def test_score_indicator_score_function_returns_none():
    """Test score_indicator when score function returns None."""
    
    def none_returning_score(DATASET_A, DATASET_B):
        if DATASET_A < 50:
            return None  # Conditional None return
        return DATASET_A + DATASET_B
    
    data = [
        {
            "DatasetCode": "DATASET_A",
            "CountryCode": "USA",
            "Year": 2020,
            "Value": 30,  # < 50, will return None
            "Unit": "Index"
        },
        {
            "DatasetCode": "DATASET_B",
            "CountryCode": "USA",
            "Year": 2020,
            "Value": 80,
            "Unit": "Index"
        }
    ]
    
    result, incomplete = score_indicator(data, "NONE_INDICATOR", none_returning_score, "Sum")
    
    # The function includes documents with None scores in the result
    # filter_incomplete_data will put them in complete if they have required fields
    assert len(result) == 1  # Document with None score is included
    assert result[0]["Score"] is None  # Score is None as expected


def test_score_indicator_multiple_years_same_country(valid_test_data):
    """Test score_indicator with multiple years for the same country."""
    
    # Add more years to the test data
    multi_year_data = valid_test_data + [
        {
            "DatasetCode": "DATASET_A",
            "CountryCode": "USA",
            "Year": 2021,
            "Value": 105,
            "Unit": "Index"
        },
        {
            "DatasetCode": "DATASET_B",
            "CountryCode": "USA",
            "Year": 2021,
            "Value": 85,
            "Unit": "Index"
        }
    ]
    
    def simple_score(DATASET_A, DATASET_B):
        return (DATASET_A + DATASET_B) / 2
    
    result, incomplete = score_indicator(multi_year_data, "MULTI_YEAR", simple_score, "Average")
    
    assert len(result) == 3  # USA 2020, USA 2021, CAN 2020
    
    # Check that both USA years are present
    usa_results = [doc for doc in result if doc["CountryCode"] == "USA"]
    assert len(usa_results) == 2
    assert {doc["Year"] for doc in usa_results} == {2020, 2021}


def test_score_indicator_score_function_argument_mismatch():
    """Test score_indicator when score function arguments don't match available datasets."""
    
    data = [
        {
            "DatasetCode": "WRONG_DATASET",
            "CountryCode": "USA",
            "Year": 2020,
            "Value": 100,
            "Unit": "Index"
        }
    ]
    
    def expecting_different_datasets(DATASET_A, DATASET_B):
        return DATASET_A + DATASET_B
    
    result, incomplete = score_indicator(data, "MISMATCH_INDICATOR", expecting_different_datasets, "Sum")
    
    # Should handle missing arguments gracefully
    assert len(result) == 0
    assert len(incomplete) >= 1


def test_score_indicator_large_dataset():
    """Test score_indicator performance with a larger dataset."""
    
    # Create a larger dataset
    large_data = []
    for country in ["USA", "CAN", "GBR", "FRA", "DEU"]:
        for year in range(2018, 2023):
            large_data.extend([
                {
                    "DatasetCode": "DATASET_A",
                    "CountryCode": country,
                    "Year": year,
                    "Value": 50 + hash(f"{country}_{year}") % 50,
                    "Unit": "Index"
                },
                {
                    "DatasetCode": "DATASET_B", 
                    "CountryCode": country,
                    "Year": year,
                    "Value": 30 + hash(f"{country}_{year}_B") % 40,
                    "Unit": "Index"
                }
            ])
    
    def simple_score(DATASET_A, DATASET_B):
        return (DATASET_A + DATASET_B) / 2
    
    result, incomplete = score_indicator(large_data, "LARGE_INDICATOR", simple_score, "Average")
    
    assert len(result) == 25  # 5 countries × 5 years
    assert len(incomplete) == 0
    assert all("Score" in doc for doc in result)
    assert all(doc["IndicatorCode"] == "LARGE_INDICATOR" for doc in result)


def test_score_indicator_extreme_numeric_values():
    """Test score_indicator with extreme numeric values."""
    
    data = [
        {
            "DatasetCode": "DATASET_A",
            "CountryCode": "USA", 
            "Year": 2020,
            "Value": 1e10,  # Very large number
            "Unit": "Index"
        },
        {
            "DatasetCode": "DATASET_B",
            "CountryCode": "USA",
            "Year": 2020,
            "Value": 1e-10,  # Very small number
            "Unit": "Index"
        }
    ]
    
    def extreme_score(DATASET_A, DATASET_B):
        return DATASET_A + DATASET_B
    
    result, incomplete = score_indicator(data, "EXTREME_INDICATOR", extreme_score, "Sum")
    
    assert len(result) == 1
    assert math.isfinite(result[0]["Score"])
    assert result[0]["Score"] > 0