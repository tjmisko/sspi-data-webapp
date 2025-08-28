import pytest
import inspect
from sspi_flask_app.api.resources.utilities import create_computed_series


def test_create_computed_series_single_computation():
    """Test creating a single computed series from existing datasets."""
    def multiply_values(DATASET_A, DATASET_B):
        return DATASET_A * DATASET_B
    
    indicator_documents = [
        {
            "IndicatorCode": "TEST_INDICATOR",
            "CountryCode": "USA",
            "Year": 2020,
            "Datasets": [
                {"DatasetCode": "DATASET_A", "CountryCode": "USA", "Year": 2020, "Value": 10},
                {"DatasetCode": "DATASET_B", "CountryCode": "USA", "Year": 2020, "Value": 5}
            ]
        }
    ]
    
    value_function_specification = [
        ("COMPUTED_PRODUCT", "Index", multiply_values)
    ]
    
    result = create_computed_series(indicator_documents, value_function_specification)
    
    assert len(result) == 1
    doc = result[0]
    assert len(doc["Datasets"]) == 3  # Original 2 + 1 computed
    
    computed_dataset = next(ds for ds in doc["Datasets"] if ds["DatasetCode"] == "COMPUTED_PRODUCT")
    assert computed_dataset["Value"] == 50  # 10 * 5
    assert computed_dataset["Unit"] == "Index"
    assert computed_dataset["Computed"] is True
    assert "ValueFunction" in computed_dataset


def test_create_computed_series_multiple_computations():
    """Test creating multiple computed series from existing datasets."""
    def add_values(DATASET_A, DATASET_B):
        return DATASET_A + DATASET_B
    
    def subtract_values(DATASET_A, DATASET_B):
        return DATASET_A - DATASET_B
    
    indicator_documents = [
        {
            "IndicatorCode": "TEST_INDICATOR", 
            "CountryCode": "USA",
            "Year": 2020,
            "Datasets": [
                {"DatasetCode": "DATASET_A", "CountryCode": "USA", "Year": 2020, "Value": 15},
                {"DatasetCode": "DATASET_B", "CountryCode": "USA", "Year": 2020, "Value": 8}
            ]
        }
    ]
    
    value_function_specification = [
        ("COMPUTED_SUM", "Total", add_values),
        ("COMPUTED_DIFF", "Difference", subtract_values)
    ]
    
    result = create_computed_series(indicator_documents, value_function_specification)
    
    assert len(result) == 1
    doc = result[0]
    assert len(doc["Datasets"]) == 4  # Original 2 + 2 computed
    
    sum_dataset = next(ds for ds in doc["Datasets"] if ds["DatasetCode"] == "COMPUTED_SUM")
    diff_dataset = next(ds for ds in doc["Datasets"] if ds["DatasetCode"] == "COMPUTED_DIFF")
    
    assert sum_dataset["Value"] == 23  # 15 + 8
    assert diff_dataset["Value"] == 7   # 15 - 8
    assert sum_dataset["Unit"] == "Total"
    assert diff_dataset["Unit"] == "Difference"


def test_create_computed_series_multiple_documents():
    """Test computing series across multiple indicator documents."""
    def ratio_values(DATASET_A, DATASET_B):
        return DATASET_A / DATASET_B
    
    indicator_documents = [
        {
            "IndicatorCode": "TEST_INDICATOR",
            "CountryCode": "USA", 
            "Year": 2020,
            "Datasets": [
                {"DatasetCode": "DATASET_A", "CountryCode": "USA", "Year": 2020, "Value": 20},
                {"DatasetCode": "DATASET_B", "CountryCode": "USA", "Year": 2020, "Value": 4}
            ]
        },
        {
            "IndicatorCode": "TEST_INDICATOR",
            "CountryCode": "CAN",
            "Year": 2020, 
            "Datasets": [
                {"DatasetCode": "DATASET_A", "CountryCode": "CAN", "Year": 2020, "Value": 30},
                {"DatasetCode": "DATASET_B", "CountryCode": "CAN", "Year": 2020, "Value": 6}
            ]
        }
    ]
    
    value_function_specification = [
        ("COMPUTED_RATIO", "Ratio", ratio_values)
    ]
    
    result = create_computed_series(indicator_documents, value_function_specification)
    
    assert len(result) == 2
    
    usa_doc = next(doc for doc in result if doc["CountryCode"] == "USA")
    can_doc = next(doc for doc in result if doc["CountryCode"] == "CAN")
    
    usa_ratio = next(ds for ds in usa_doc["Datasets"] if ds["DatasetCode"] == "COMPUTED_RATIO")
    can_ratio = next(ds for ds in can_doc["Datasets"] if ds["DatasetCode"] == "COMPUTED_RATIO")
    
    assert usa_ratio["Value"] == 5.0   # 20 / 4
    assert can_ratio["Value"] == 5.0   # 30 / 6


def test_create_computed_series_missing_dataset():
    """Test behavior when required dataset is missing for computation."""
    def multiply_values(DATASET_A, DATASET_B):
        return DATASET_A * DATASET_B
    
    indicator_documents = [
        {
            "IndicatorCode": "TEST_INDICATOR",
            "CountryCode": "USA",
            "Year": 2020,
            "Datasets": [
                {"DatasetCode": "DATASET_A", "CountryCode": "USA", "Year": 2020, "Value": 10}
                # Missing DATASET_B
            ]
        }
    ]
    
    value_function_specification = [
        ("COMPUTED_PRODUCT", "Index", multiply_values)
    ]
    
    result = create_computed_series(indicator_documents, value_function_specification)
    
    assert len(result) == 1
    doc = result[0]
    assert len(doc["Datasets"]) == 1  # Only original dataset, no computed dataset added
    assert not any(ds["DatasetCode"] == "COMPUTED_PRODUCT" for ds in doc["Datasets"])


def test_create_computed_series_non_numeric_values():
    """Test behavior when dataset values are non-numeric."""
    def add_values(DATASET_A, DATASET_B):
        return DATASET_A + DATASET_B
    
    indicator_documents = [
        {
            "IndicatorCode": "TEST_INDICATOR",
            "CountryCode": "USA",
            "Year": 2020,
            "Datasets": [
                {"DatasetCode": "DATASET_A", "CountryCode": "USA", "Year": 2020, "Value": "not_a_number"},
                {"DatasetCode": "DATASET_B", "CountryCode": "USA", "Year": 2020, "Value": 5}
            ]
        }
    ]
    
    value_function_specification = [
        ("COMPUTED_SUM", "Total", add_values)
    ]
    
    result = create_computed_series(indicator_documents, value_function_specification)
    
    assert len(result) == 1
    doc = result[0]
    assert len(doc["Datasets"]) == 2  # Only original datasets, no computed dataset added
    assert not any(ds["DatasetCode"] == "COMPUTED_SUM" for ds in doc["Datasets"])


def test_create_computed_series_none_values():
    """Test behavior when dataset values are None."""
    def multiply_values(DATASET_A, DATASET_B):
        return DATASET_A * DATASET_B
    
    indicator_documents = [
        {
            "IndicatorCode": "TEST_INDICATOR",
            "CountryCode": "USA",
            "Year": 2020,
            "Datasets": [
                {"DatasetCode": "DATASET_A", "CountryCode": "USA", "Year": 2020, "Value": None},
                {"DatasetCode": "DATASET_B", "CountryCode": "USA", "Year": 2020, "Value": 5}
            ]
        }
    ]
    
    value_function_specification = [
        ("COMPUTED_PRODUCT", "Index", multiply_values)
    ]
    
    result = create_computed_series(indicator_documents, value_function_specification)
    
    assert len(result) == 1
    doc = result[0]
    assert len(doc["Datasets"]) == 2  # Only original datasets, no computed dataset added
    assert not any(ds["DatasetCode"] == "COMPUTED_PRODUCT" for ds in doc["Datasets"])


def test_create_computed_series_missing_value_key():
    """Test behavior when dataset doesn't have Value key."""
    def add_values(DATASET_A, DATASET_B):
        return DATASET_A + DATASET_B
    
    indicator_documents = [
        {
            "IndicatorCode": "TEST_INDICATOR",
            "CountryCode": "USA", 
            "Year": 2020,
            "Datasets": [
                {"DatasetCode": "DATASET_A", "CountryCode": "USA", "Year": 2020},  # No Value key
                {"DatasetCode": "DATASET_B", "CountryCode": "USA", "Year": 2020, "Value": 5}
            ]
        }
    ]
    
    value_function_specification = [
        ("COMPUTED_SUM", "Total", add_values)
    ]
    
    result = create_computed_series(indicator_documents, value_function_specification)
    
    assert len(result) == 1
    doc = result[0]
    assert len(doc["Datasets"]) == 2  # Only original datasets, no computed dataset added
    assert not any(ds["DatasetCode"] == "COMPUTED_SUM" for ds in doc["Datasets"])


def test_create_computed_series_function_exception():
    """Test behavior when value function raises an exception."""
    def divide_by_zero(DATASET_A, DATASET_B):
        return DATASET_A / DATASET_B  # Will cause division by zero
    
    indicator_documents = [
        {
            "IndicatorCode": "TEST_INDICATOR",
            "CountryCode": "USA",
            "Year": 2020,
            "Datasets": [
                {"DatasetCode": "DATASET_A", "CountryCode": "USA", "Year": 2020, "Value": 10},
                {"DatasetCode": "DATASET_B", "CountryCode": "USA", "Year": 2020, "Value": 0}
            ]
        }
    ]
    
    value_function_specification = [
        ("COMPUTED_RATIO", "Ratio", divide_by_zero)
    ]
    
    result = create_computed_series(indicator_documents, value_function_specification)
    
    assert len(result) == 1
    doc = result[0]
    assert len(doc["Datasets"]) == 2  # Only original datasets, computed dataset not added due to exception


def test_create_computed_series_single_argument_function():
    """Test creating computed series with a single-argument function."""
    def square_value(DATASET_A):
        return DATASET_A ** 2
    
    indicator_documents = [
        {
            "IndicatorCode": "TEST_INDICATOR",
            "CountryCode": "USA",
            "Year": 2020,
            "Datasets": [
                {"DatasetCode": "DATASET_A", "CountryCode": "USA", "Year": 2020, "Value": 7}
            ]
        }
    ]
    
    value_function_specification = [
        ("COMPUTED_SQUARE", "Squared", square_value)
    ]
    
    result = create_computed_series(indicator_documents, value_function_specification)
    
    assert len(result) == 1
    doc = result[0]
    assert len(doc["Datasets"]) == 2  # Original 1 + 1 computed
    
    computed_dataset = next(ds for ds in doc["Datasets"] if ds["DatasetCode"] == "COMPUTED_SQUARE")
    assert computed_dataset["Value"] == 49  # 7^2
    assert computed_dataset["Unit"] == "Squared"


def test_create_computed_series_three_argument_function():
    """Test creating computed series with a three-argument function."""
    def weighted_average(DATASET_A, DATASET_B, DATASET_C):
        return (DATASET_A * 0.5) + (DATASET_B * 0.3) + (DATASET_C * 0.2)
    
    indicator_documents = [
        {
            "IndicatorCode": "TEST_INDICATOR",
            "CountryCode": "USA",
            "Year": 2020,
            "Datasets": [
                {"DatasetCode": "DATASET_A", "CountryCode": "USA", "Year": 2020, "Value": 10},
                {"DatasetCode": "DATASET_B", "CountryCode": "USA", "Year": 2020, "Value": 20},
                {"DatasetCode": "DATASET_C", "CountryCode": "USA", "Year": 2020, "Value": 30}
            ]
        }
    ]
    
    value_function_specification = [
        ("COMPUTED_WEIGHTED", "WeightedAvg", weighted_average)
    ]
    
    result = create_computed_series(indicator_documents, value_function_specification)
    
    assert len(result) == 1
    doc = result[0]
    assert len(doc["Datasets"]) == 4  # Original 3 + 1 computed
    
    computed_dataset = next(ds for ds in doc["Datasets"] if ds["DatasetCode"] == "COMPUTED_WEIGHTED")
    expected_value = (10 * 0.5) + (20 * 0.3) + (30 * 0.2)  # 5 + 6 + 6 = 17
    assert computed_dataset["Value"] == expected_value
    assert computed_dataset["Unit"] == "WeightedAvg"


def test_create_computed_series_empty_specification():
    """Test behavior with empty value function specification."""
    indicator_documents = [
        {
            "IndicatorCode": "TEST_INDICATOR",
            "CountryCode": "USA",
            "Year": 2020,
            "Datasets": [
                {"DatasetCode": "DATASET_A", "CountryCode": "USA", "Year": 2020, "Value": 10}
            ]
        }
    ]
    
    value_function_specification = []
    
    result = create_computed_series(indicator_documents, value_function_specification)
    
    assert len(result) == 1
    doc = result[0]
    assert len(doc["Datasets"]) == 1  # Only original dataset, no computed datasets


def test_create_computed_series_empty_documents():
    """Test behavior with empty indicator documents list."""
    def add_values(DATASET_A, DATASET_B):
        return DATASET_A + DATASET_B
    
    indicator_documents = []
    
    value_function_specification = [
        ("COMPUTED_SUM", "Total", add_values)
    ]
    
    result = create_computed_series(indicator_documents, value_function_specification)
    
    assert result == []


def test_create_computed_series_preserves_metadata():
    """Test that computed series preserves all required metadata fields."""
    def simple_addition(DATASET_A, DATASET_B):
        return DATASET_A + DATASET_B
    
    indicator_documents = [
        {
            "IndicatorCode": "TEST_INDICATOR",
            "CountryCode": "USA",
            "Year": 2020,
            "Datasets": [
                {"DatasetCode": "DATASET_A", "CountryCode": "USA", "Year": 2020, "Value": 15},
                {"DatasetCode": "DATASET_B", "CountryCode": "USA", "Year": 2020, "Value": 25}
            ]
        }
    ]
    
    value_function_specification = [
        ("COMPUTED_SUM", "Total", simple_addition)
    ]
    
    result = create_computed_series(indicator_documents, value_function_specification)
    
    computed_dataset = next(ds for ds in result[0]["Datasets"] if ds["DatasetCode"] == "COMPUTED_SUM")
    
    # Check all required fields are present
    assert computed_dataset["DatasetCode"] == "COMPUTED_SUM"
    assert computed_dataset["CountryCode"] == "USA"
    assert computed_dataset["Year"] == 2020
    assert computed_dataset["Value"] == 40
    assert computed_dataset["Unit"] == "Total"
    assert computed_dataset["Computed"] is True
    assert "ValueFunction" in computed_dataset
    assert isinstance(computed_dataset["ValueFunction"], str)
    assert len(computed_dataset["ValueFunction"]) > 0


def test_create_computed_series_value_function_source():
    """Test that the ValueFunction field contains the actual function source code."""
    def multiply_by_constant(DATASET_A):
        constant = 2.5
        return DATASET_A * constant
    
    indicator_documents = [
        {
            "IndicatorCode": "TEST_INDICATOR",
            "CountryCode": "USA",
            "Year": 2020,
            "Datasets": [
                {"DatasetCode": "DATASET_A", "CountryCode": "USA", "Year": 2020, "Value": 8}
            ]
        }
    ]
    
    value_function_specification = [
        ("COMPUTED_SCALED", "Scaled", multiply_by_constant)
    ]
    
    result = create_computed_series(indicator_documents, value_function_specification)
    
    computed_dataset = next(ds for ds in result[0]["Datasets"] if ds["DatasetCode"] == "COMPUTED_SCALED")
    
    # Check that ValueFunction contains the source code
    assert "constant = 2.5" in computed_dataset["ValueFunction"]
    assert "DATASET_A * constant" in computed_dataset["ValueFunction"]
    assert computed_dataset["Value"] == 20.0  # 8 * 2.5


def test_create_computed_series_float_and_int_values():
    """Test that function works with both float and int values."""
    def complex_calculation(DATASET_A, DATASET_B):
        return (DATASET_A * 1.5) + (DATASET_B / 2.0)
    
    indicator_documents = [
        {
            "IndicatorCode": "TEST_INDICATOR",
            "CountryCode": "USA",
            "Year": 2020,
            "Datasets": [
                {"DatasetCode": "DATASET_A", "CountryCode": "USA", "Year": 2020, "Value": 10},      # int
                {"DatasetCode": "DATASET_B", "CountryCode": "USA", "Year": 2020, "Value": 5.5}     # float
            ]
        }
    ]
    
    value_function_specification = [
        ("COMPUTED_COMPLEX", "Complex", complex_calculation)
    ]
    
    result = create_computed_series(indicator_documents, value_function_specification)
    
    computed_dataset = next(ds for ds in result[0]["Datasets"] if ds["DatasetCode"] == "COMPUTED_COMPLEX")
    expected_value = (10 * 1.5) + (5.5 / 2.0)  # 15 + 2.75 = 17.75
    assert computed_dataset["Value"] == expected_value


def test_create_computed_series_mutates_original_list():
    """Test that the function mutates the original indicator documents list."""
    def double_value(DATASET_A):
        return DATASET_A * 2
    
    original_documents = [
        {
            "IndicatorCode": "TEST_INDICATOR", 
            "CountryCode": "USA",
            "Year": 2020,
            "Datasets": [
                {"DatasetCode": "DATASET_A", "CountryCode": "USA", "Year": 2020, "Value": 5}
            ]
        }
    ]
    
    value_function_specification = [
        ("COMPUTED_DOUBLE", "Doubled", double_value)
    ]
    
    result = create_computed_series(original_documents, value_function_specification)
    
    # The function should return the same object and mutate the original
    assert result is original_documents
    assert len(original_documents[0]["Datasets"]) == 2
    assert any(ds["DatasetCode"] == "COMPUTED_DOUBLE" for ds in original_documents[0]["Datasets"])