import pytest
import math
from sspi_flask_app.api.resources.utilities import drop_none_or_na


def test_drop_none_or_na_no_null_values():
    """Test drop_none_or_na with documents that have no null values."""
    documents = [
        {"CountryCode": "USA", "Year": 2020, "Value": 100.0},
        {"CountryCode": "CAN", "Year": 2020, "Value": 85.5},
        {"CountryCode": "GBR", "Year": 2020, "Value": 90.2}
    ]
    
    clean_docs, dropped_docs = drop_none_or_na(documents)
    
    assert len(clean_docs) == 3
    assert len(dropped_docs) == 0
    assert clean_docs == documents


def test_drop_none_or_na_with_none_values():
    """Test drop_none_or_na with documents that have None values."""
    documents = [
        {"CountryCode": "USA", "Year": 2020, "Value": 100.0},
        {"CountryCode": "CAN", "Year": 2020, "Value": None},
        {"CountryCode": "GBR", "Year": 2020, "Value": 90.2},
        {"CountryCode": "FRA", "Year": 2020, "Value": None}
    ]
    
    clean_docs, dropped_docs = drop_none_or_na(documents)
    
    assert len(clean_docs) == 2
    assert len(dropped_docs) == 2
    
    # Check that correct documents were kept
    assert clean_docs[0]["CountryCode"] == "USA"
    assert clean_docs[1]["CountryCode"] == "GBR"
    
    # Check that correct documents were dropped
    assert dropped_docs[0]["CountryCode"] == "CAN"
    assert dropped_docs[1]["CountryCode"] == "FRA"
    assert dropped_docs[0]["Value"] is None
    assert dropped_docs[1]["Value"] is None


def test_drop_none_or_na_with_nan_values():
    """Test drop_none_or_na with documents that have NaN values."""
    documents = [
        {"CountryCode": "USA", "Year": 2020, "Value": 100.0},
        {"CountryCode": "CAN", "Year": 2020, "Value": float('nan')},
        {"CountryCode": "GBR", "Year": 2020, "Value": 90.2},
        {"CountryCode": "FRA", "Year": 2020, "Value": float('nan')}
    ]
    
    clean_docs, dropped_docs = drop_none_or_na(documents)
    
    assert len(clean_docs) == 2
    assert len(dropped_docs) == 2
    
    # Check that correct documents were kept
    assert clean_docs[0]["CountryCode"] == "USA"
    assert clean_docs[1]["CountryCode"] == "GBR"
    
    # Check that correct documents were dropped
    assert dropped_docs[0]["CountryCode"] == "CAN"
    assert dropped_docs[1]["CountryCode"] == "FRA"
    assert math.isnan(dropped_docs[0]["Value"])
    assert math.isnan(dropped_docs[1]["Value"])


def test_drop_none_or_na_mixed_none_and_nan():
    """Test drop_none_or_na with documents that have both None and NaN values."""
    documents = [
        {"CountryCode": "USA", "Year": 2020, "Value": 100.0},
        {"CountryCode": "CAN", "Year": 2020, "Value": None},
        {"CountryCode": "GBR", "Year": 2020, "Value": float('nan')},
        {"CountryCode": "FRA", "Year": 2020, "Value": 85.5},
        {"CountryCode": "DEU", "Year": 2020, "Value": None},
        {"CountryCode": "ITA", "Year": 2020, "Value": float('nan')}
    ]
    
    clean_docs, dropped_docs = drop_none_or_na(documents)
    
    assert len(clean_docs) == 2
    assert len(dropped_docs) == 4
    
    # Check that valid documents were kept
    clean_countries = {doc["CountryCode"] for doc in clean_docs}
    assert clean_countries == {"USA", "FRA"}
    
    # Check that invalid documents were dropped
    dropped_countries = {doc["CountryCode"] for doc in dropped_docs}
    assert dropped_countries == {"CAN", "GBR", "DEU", "ITA"}


def test_drop_none_or_na_empty_list():
    """Test drop_none_or_na with empty document list."""
    documents = []
    
    clean_docs, dropped_docs = drop_none_or_na(documents)
    
    assert clean_docs == []
    assert dropped_docs == []


def test_drop_none_or_na_all_none_values():
    """Test drop_none_or_na where all documents have None values."""
    documents = [
        {"CountryCode": "USA", "Year": 2020, "Value": None},
        {"CountryCode": "CAN", "Year": 2020, "Value": None},
        {"CountryCode": "GBR", "Year": 2020, "Value": None}
    ]
    
    clean_docs, dropped_docs = drop_none_or_na(documents)
    
    assert len(clean_docs) == 0
    assert len(dropped_docs) == 3
    assert dropped_docs == documents


def test_drop_none_or_na_all_nan_values():
    """Test drop_none_or_na where all documents have NaN values."""
    documents = [
        {"CountryCode": "USA", "Year": 2020, "Value": float('nan')},
        {"CountryCode": "CAN", "Year": 2020, "Value": float('nan')},
        {"CountryCode": "GBR", "Year": 2020, "Value": float('nan')}
    ]
    
    clean_docs, dropped_docs = drop_none_or_na(documents)
    
    assert len(clean_docs) == 0
    assert len(dropped_docs) == 3
    assert all(math.isnan(doc["Value"]) for doc in dropped_docs)


def test_drop_none_or_na_preserves_other_fields():
    """Test that drop_none_or_na preserves all other fields in documents."""
    documents = [
        {
            "CountryCode": "USA",
            "Year": 2020,
            "Value": 100.0,
            "DatasetCode": "TEST_DATA",
            "Unit": "Index",
            "Metadata": {"source": "test"}
        },
        {
            "CountryCode": "CAN",
            "Year": 2020,
            "Value": None,
            "DatasetCode": "TEST_DATA",
            "Unit": "Index",
            "Metadata": {"source": "test"}
        }
    ]
    
    clean_docs, dropped_docs = drop_none_or_na(documents)
    
    assert len(clean_docs) == 1
    assert len(dropped_docs) == 1
    
    # Check that all fields are preserved in clean documents
    clean_doc = clean_docs[0]
    assert clean_doc["CountryCode"] == "USA"
    assert clean_doc["DatasetCode"] == "TEST_DATA"
    assert clean_doc["Unit"] == "Index"
    assert clean_doc["Metadata"] == {"source": "test"}
    
    # Check that all fields are preserved in dropped documents
    dropped_doc = dropped_docs[0]
    assert dropped_doc["CountryCode"] == "CAN"
    assert dropped_doc["DatasetCode"] == "TEST_DATA"
    assert dropped_doc["Unit"] == "Index"
    assert dropped_doc["Metadata"] == {"source": "test"}


def test_drop_none_or_na_does_not_mutate_original():
    """Test that drop_none_or_na does not mutate the original list."""
    original_documents = [
        {"CountryCode": "USA", "Year": 2020, "Value": 100.0},
        {"CountryCode": "CAN", "Year": 2020, "Value": None},
        {"CountryCode": "GBR", "Year": 2020, "Value": 90.2}
    ]
    
    # Create a copy to compare later
    original_copy = original_documents.copy()
    
    clean_docs, dropped_docs = drop_none_or_na(original_documents)
    
    # Original list should remain unchanged
    assert original_documents == original_copy
    assert len(original_documents) == 3


def test_drop_none_or_na_zero_values_kept():
    """Test that zero values are not dropped (only None and NaN)."""
    documents = [
        {"CountryCode": "USA", "Year": 2020, "Value": 0.0},
        {"CountryCode": "CAN", "Year": 2020, "Value": 0},
        {"CountryCode": "GBR", "Year": 2020, "Value": -0.0},
        {"CountryCode": "FRA", "Year": 2020, "Value": None},
        {"CountryCode": "DEU", "Year": 2020, "Value": float('nan')}
    ]
    
    clean_docs, dropped_docs = drop_none_or_na(documents)
    
    assert len(clean_docs) == 3  # Zero values should be kept
    assert len(dropped_docs) == 2  # Only None and NaN should be dropped
    
    # Check that zero values are preserved
    clean_countries = {doc["CountryCode"] for doc in clean_docs}
    assert clean_countries == {"USA", "CAN", "GBR"}


def test_drop_none_or_na_negative_infinity_kept():
    """Test that negative infinity values are not dropped."""
    documents = [
        {"CountryCode": "USA", "Year": 2020, "Value": float('inf')},
        {"CountryCode": "CAN", "Year": 2020, "Value": float('-inf')},
        {"CountryCode": "GBR", "Year": 2020, "Value": None},
        {"CountryCode": "FRA", "Year": 2020, "Value": float('nan')}
    ]
    
    clean_docs, dropped_docs = drop_none_or_na(documents)
    
    assert len(clean_docs) == 2  # Infinity values should be kept
    assert len(dropped_docs) == 2  # Only None and NaN should be dropped
    
    # Check that infinity values are preserved
    clean_countries = {doc["CountryCode"] for doc in clean_docs}
    assert clean_countries == {"USA", "CAN"}
    assert clean_docs[0]["Value"] == float('inf')
    assert clean_docs[1]["Value"] == float('-inf')


def test_drop_none_or_na_duplicate_documents():
    """Test drop_none_or_na with duplicate documents containing None/NaN."""
    documents = [
        {"CountryCode": "USA", "Year": 2020, "Value": 100.0},
        {"CountryCode": "USA", "Year": 2020, "Value": None},
        {"CountryCode": "USA", "Year": 2020, "Value": None},  # Duplicate
        {"CountryCode": "CAN", "Year": 2020, "Value": 85.5}
    ]
    
    clean_docs, dropped_docs = drop_none_or_na(documents)
    
    assert len(clean_docs) == 2
    assert len(dropped_docs) == 2
    
    # Both None documents should be in dropped list
    assert all(doc["Value"] is None for doc in dropped_docs)


def test_drop_none_or_na_missing_value_field():
    """Test drop_none_or_na when Value field is missing."""
    documents = [
        {"CountryCode": "USA", "Year": 2020}  # No Value field
    ]
    
    with pytest.raises(KeyError):
        drop_none_or_na(documents)


def test_drop_none_or_na_complex_data_types():
    """Test drop_none_or_na with various data types in Value field."""
    documents = [
        {"CountryCode": "USA", "Year": 2020, "Value": 100},  # int
        {"CountryCode": "CAN", "Year": 2020, "Value": 85.5},  # float
        {"CountryCode": "GBR", "Year": 2020, "Value": None},  # None
        {"CountryCode": "FRA", "Year": 2020, "Value": float('nan')},  # NaN
        {"CountryCode": "DEU", "Year": 2020, "Value": 1e10},  # Scientific notation
        {"CountryCode": "ITA", "Year": 2020, "Value": -999.99}  # Negative
    ]
    
    clean_docs, dropped_docs = drop_none_or_na(documents)
    
    assert len(clean_docs) == 4
    assert len(dropped_docs) == 2
    
    # Check that various numeric types are preserved
    clean_values = [doc["Value"] for doc in clean_docs]
    assert 100 in clean_values  # int
    assert 85.5 in clean_values  # float
    assert 1e10 in clean_values  # scientific notation
    assert -999.99 in clean_values  # negative