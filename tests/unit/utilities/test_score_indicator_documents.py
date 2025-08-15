import pytest
from sspi_flask_app.api.resources.utilities import score_indicator_documents


def test_score_indicator_documents_basic():
    """Test basic scoring with string unit."""
    documents = [
        {
            "IndicatorCode": "TEST_INDICATOR",
            "CountryCode": "USA",
            "Year": 2020,
            "Datasets": [
                {"DatasetCode": "DATASET_A", "Value": 100},
                {"DatasetCode": "DATASET_B", "Value": 200}
            ]
        }
    ]
    
    def score_function(DATASET_A, DATASET_B):
        return (DATASET_A + DATASET_B) / 2
    
    result = score_indicator_documents(documents, score_function, "Average")
    
    assert len(result) == 1
    assert result[0]["Score"] == 150.0  # (100 + 200) / 2
    assert result[0]["Unit"] == "Average"


def test_score_indicator_documents_callable_unit():
    """Test scoring with callable unit function."""
    documents = [
        {
            "IndicatorCode": "TEST_INDICATOR",
            "CountryCode": "USA",
            "Year": 2020,
            "Datasets": [
                {"DatasetCode": "DATASET_A", "Value": 100},
                {"DatasetCode": "DATASET_B", "Value": 200}
            ]
        }
    ]
    
    def score_function(DATASET_A, DATASET_B):
        return DATASET_A + DATASET_B
    
    def unit_function(DATASET_A, DATASET_B):
        if DATASET_A > DATASET_B:
            return "High A"
        else:
            return "High B"
    
    result = score_indicator_documents(documents, score_function, unit_function)
    
    assert len(result) == 1
    assert result[0]["Score"] == 300  # 100 + 200
    assert result[0]["Unit"] == "High B"  # 100 < 200


def test_score_indicator_documents_multiple_documents():
    """Test scoring multiple indicator documents."""
    documents = [
        {
            "IndicatorCode": "TEST_INDICATOR",
            "CountryCode": "USA",
            "Year": 2020,
            "Datasets": [
                {"DatasetCode": "DATASET_A", "Value": 100},
                {"DatasetCode": "DATASET_B", "Value": 200}
            ]
        },
        {
            "IndicatorCode": "TEST_INDICATOR",
            "CountryCode": "CAN",
            "Year": 2020,
            "Datasets": [
                {"DatasetCode": "DATASET_A", "Value": 150},
                {"DatasetCode": "DATASET_B", "Value": 250}
            ]
        }
    ]
    
    def score_function(DATASET_A, DATASET_B):
        return DATASET_A * DATASET_B
    
    result = score_indicator_documents(documents, score_function, "Product")
    
    assert len(result) == 2
    assert result[0]["Score"] == 20000  # 100 * 200
    assert result[1]["Score"] == 37500  # 150 * 250
    assert all(doc["Unit"] == "Product" for doc in result)


def test_score_indicator_documents_single_dataset():
    """Test scoring with single dataset per document."""
    documents = [
        {
            "IndicatorCode": "SINGLE_INDICATOR",
            "CountryCode": "USA",
            "Year": 2020,
            "Datasets": [
                {"DatasetCode": "SOLO_DATASET", "Value": 85.5}
            ]
        }
    ]
    
    def score_function(SOLO_DATASET):
        return SOLO_DATASET / 100
    
    result = score_indicator_documents(documents, score_function, "Normalized")
    
    assert len(result) == 1
    assert result[0]["Score"] == 0.855
    assert result[0]["Unit"] == "Normalized"


def test_score_indicator_documents_complex_scoring():
    """Test scoring with complex mathematical operations."""
    documents = [
        {
            "IndicatorCode": "COMPLEX_INDICATOR",
            "CountryCode": "USA",
            "Year": 2020,
            "Datasets": [
                {"DatasetCode": "GDP", "Value": 50000},
                {"DatasetCode": "POPULATION", "Value": 330},
                {"DatasetCode": "AREA", "Value": 9834}
            ]
        }
    ]
    
    def complex_score(GDP, POPULATION, AREA):
        gdp_per_capita = GDP / POPULATION
        density = POPULATION / AREA
        return gdp_per_capita * density ** 0.5
    
    result = score_indicator_documents(documents, complex_score, "Composite Index")
    
    assert len(result) == 1
    expected_score = (50000 / 330) * (330 / 9834) ** 0.5
    assert result[0]["Score"] == pytest.approx(expected_score, rel=1e-6)


def test_score_indicator_documents_missing_dataset():
    """Test scoring when required dataset is missing."""
    documents = [
        {
            "IndicatorCode": "MISSING_INDICATOR",
            "CountryCode": "USA",
            "Year": 2020,
            "Datasets": [
                {"DatasetCode": "DATASET_A", "Value": 100}
                # Missing DATASET_B
            ]
        }
    ]
    
    def score_function(DATASET_A, DATASET_B):
        return DATASET_A + DATASET_B
    
    result = score_indicator_documents(documents, score_function, "Sum")
    
    # Document should be skipped due to KeyError, no Score field added
    assert len(result) == 1
    assert "Score" not in result[0]
    assert "Unit" not in result[0]


def test_score_indicator_documents_non_numeric_values():
    """Test scoring when dataset values are non-numeric."""
    documents = [
        {
            "IndicatorCode": "NON_NUMERIC_INDICATOR",
            "CountryCode": "USA",
            "Year": 2020,
            "Datasets": [
                {"DatasetCode": "DATASET_A", "Value": "not_a_number"},
                {"DatasetCode": "DATASET_B", "Value": 200}
            ]
        }
    ]
    
    def score_function(DATASET_A, DATASET_B):
        return DATASET_A + DATASET_B
    
    result = score_indicator_documents(documents, score_function, "Sum")
    
    # Document should be skipped due to non-numeric value
    assert len(result) == 1
    assert "Score" not in result[0]
    assert "Unit" not in result[0]


def test_score_indicator_documents_none_values():
    """Test scoring when dataset values are None."""
    documents = [
        {
            "IndicatorCode": "NONE_INDICATOR",
            "CountryCode": "USA",
            "Year": 2020,
            "Datasets": [
                {"DatasetCode": "DATASET_A", "Value": None},
                {"DatasetCode": "DATASET_B", "Value": 200}
            ]
        }
    ]
    
    def score_function(DATASET_A, DATASET_B):
        return DATASET_A + DATASET_B
    
    result = score_indicator_documents(documents, score_function, "Sum")
    
    # Document should be skipped due to None value
    assert len(result) == 1
    assert "Score" not in result[0]


def test_score_indicator_documents_preserves_fields():
    """Test that scoring preserves existing document fields."""
    documents = [
        {
            "IndicatorCode": "PRESERVE_INDICATOR",
            "CountryCode": "USA",
            "Year": 2020,
            "ExistingField": "existing_value",
            "Metadata": {"source": "test"},
            "Datasets": [
                {"DatasetCode": "DATASET_A", "Value": 100}
            ]
        }
    ]
    
    def score_function(DATASET_A):
        return DATASET_A * 2
    
    result = score_indicator_documents(documents, score_function, "Doubled")
    
    assert len(result) == 1
    doc = result[0]
    
    # Check that new fields are added
    assert doc["Score"] == 200
    assert doc["Unit"] == "Doubled"
    
    # Check that existing fields are preserved
    assert doc["IndicatorCode"] == "PRESERVE_INDICATOR"
    assert doc["CountryCode"] == "USA"
    assert doc["Year"] == 2020
    assert doc["ExistingField"] == "existing_value"
    assert doc["Metadata"] == {"source": "test"}


def test_score_indicator_documents_empty_list():
    """Test scoring with empty document list."""
    documents = []
    
    def score_function(DATASET_A):
        return DATASET_A
    
    result = score_indicator_documents(documents, score_function, "Unit")
    
    assert result == []


def test_score_indicator_documents_mutates_in_place():
    """Test that the function mutates the original list."""
    documents = [
        {
            "IndicatorCode": "MUTATE_INDICATOR",
            "CountryCode": "USA",
            "Year": 2020,
            "Datasets": [
                {"DatasetCode": "DATASET_A", "Value": 100}
            ]
        }
    ]
    
    def score_function(DATASET_A):
        return DATASET_A / 2
    
    result = score_indicator_documents(documents, score_function, "Halved")
    
    # Should return the same list object
    assert result is documents
    # Original list should be modified
    assert documents[0]["Score"] == 50.0
    assert documents[0]["Unit"] == "Halved"


def test_score_indicator_documents_missing_value_field():
    """Test scoring when dataset missing Value field."""
    documents = [
        {
            "IndicatorCode": "MISSING_VALUE_INDICATOR",
            "CountryCode": "USA",
            "Year": 2020,
            "Datasets": [
                {"DatasetCode": "DATASET_A"},  # No Value field
                {"DatasetCode": "DATASET_B", "Value": 200}
            ]
        }
    ]
    
    def score_function(DATASET_A, DATASET_B):
        return DATASET_A + DATASET_B
    
    result = score_indicator_documents(documents, score_function, "Sum")
    
    # Document should be skipped due to None value from missing field
    assert len(result) == 1
    assert "Score" not in result[0]


def test_score_indicator_documents_different_dataset_orders():
    """Test that scoring works regardless of dataset order in the document."""
    documents = [
        {
            "IndicatorCode": "ORDER_INDICATOR",
            "CountryCode": "USA",
            "Year": 2020,
            "Datasets": [
                {"DatasetCode": "DATASET_B", "Value": 200},  # B before A
                {"DatasetCode": "DATASET_A", "Value": 100}
            ]
        }
    ]
    
    def score_function(DATASET_A, DATASET_B):
        return DATASET_A - DATASET_B  # Order matters for subtraction
    
    result = score_indicator_documents(documents, score_function, "Difference")
    
    assert len(result) == 1
    assert result[0]["Score"] == -100  # 100 - 200 = -100


def test_score_indicator_documents_zero_values():
    """Test scoring with zero values."""
    documents = [
        {
            "IndicatorCode": "ZERO_INDICATOR",
            "CountryCode": "USA",
            "Year": 2020,
            "Datasets": [
                {"DatasetCode": "DATASET_A", "Value": 0},
                {"DatasetCode": "DATASET_B", "Value": 100}
            ]
        }
    ]
    
    def score_function(DATASET_A, DATASET_B):
        return DATASET_A + DATASET_B
    
    result = score_indicator_documents(documents, score_function, "Sum")
    
    assert len(result) == 1
    assert result[0]["Score"] == 100  # 0 + 100


def test_score_indicator_documents_negative_values():
    """Test scoring with negative values."""
    documents = [
        {
            "IndicatorCode": "NEGATIVE_INDICATOR",
            "CountryCode": "USA",
            "Year": 2020,
            "Datasets": [
                {"DatasetCode": "DATASET_A", "Value": -50},
                {"DatasetCode": "DATASET_B", "Value": 150}
            ]
        }
    ]
    
    def score_function(DATASET_A, DATASET_B):
        return DATASET_A + DATASET_B
    
    result = score_indicator_documents(documents, score_function, "Sum")
    
    assert len(result) == 1
    assert result[0]["Score"] == 100  # -50 + 150


def test_score_indicator_documents_float_values():
    """Test scoring with floating point values."""
    documents = [
        {
            "IndicatorCode": "FLOAT_INDICATOR",
            "CountryCode": "USA",
            "Year": 2020,
            "Datasets": [
                {"DatasetCode": "DATASET_A", "Value": 33.33},
                {"DatasetCode": "DATASET_B", "Value": 66.67}
            ]
        }
    ]
    
    def score_function(DATASET_A, DATASET_B):
        return DATASET_A + DATASET_B
    
    result = score_indicator_documents(documents, score_function, "Sum")
    
    assert len(result) == 1
    assert result[0]["Score"] == pytest.approx(100.0, rel=1e-6)


def test_score_indicator_documents_very_large_numbers():
    """Test scoring with very large numbers."""
    documents = [
        {
            "IndicatorCode": "LARGE_INDICATOR",
            "CountryCode": "USA",
            "Year": 2020,
            "Datasets": [
                {"DatasetCode": "DATASET_A", "Value": 1e15},
                {"DatasetCode": "DATASET_B", "Value": 2e15}
            ]
        }
    ]
    
    def score_function(DATASET_A, DATASET_B):
        return DATASET_A + DATASET_B
    
    result = score_indicator_documents(documents, score_function, "Sum")
    
    assert len(result) == 1
    assert result[0]["Score"] == 3e15


def test_score_indicator_documents_extra_datasets():
    """Test scoring when document has more datasets than function needs."""
    documents = [
        {
            "IndicatorCode": "EXTRA_INDICATOR",
            "CountryCode": "USA",
            "Year": 2020,
            "Datasets": [
                {"DatasetCode": "DATASET_A", "Value": 100},
                {"DatasetCode": "DATASET_B", "Value": 200},
                {"DatasetCode": "DATASET_C", "Value": 300}  # Extra dataset
            ]
        }
    ]
    
    def score_function(DATASET_A, DATASET_B):  # Only uses A and B
        return DATASET_A + DATASET_B
    
    result = score_indicator_documents(documents, score_function, "Sum")
    
    assert len(result) == 1
    assert result[0]["Score"] == 300  # Should ignore DATASET_C