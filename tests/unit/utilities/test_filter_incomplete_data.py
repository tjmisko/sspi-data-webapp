import pytest
from sspi_flask_app.api.resources.utilities import filter_incomplete_data


def test_filter_incomplete_data_complete_documents():
    """Test filtering with complete documents that have all required fields."""
    documents = [
        {
            "IndicatorCode": "TEST_INDICATOR",
            "CountryCode": "USA",
            "Year": 2020,
            "Unit": "Index",
            "Score": 85.5,
            "Datasets": [{"DatasetCode": "DATASET_A", "Value": 100}]
        },
        {
            "IndicatorCode": "TEST_INDICATOR",
            "CountryCode": "CAN",
            "Year": 2020,
            "Unit": "Index",
            "Score": 92.3,
            "Datasets": [{"DatasetCode": "DATASET_A", "Value": 120}]
        }
    ]
    
    complete, incomplete = filter_incomplete_data(documents)
    
    assert len(complete) == 2
    assert len(incomplete) == 0
    assert complete == documents


def test_filter_incomplete_data_missing_required_fields():
    """Test filtering with documents missing required fields."""
    documents = [
        {
            "IndicatorCode": "TEST_INDICATOR",
            "CountryCode": "USA",
            "Year": 2020,
            "Unit": "Index",
            "Score": 85.5
            # Complete document
        },
        {
            "IndicatorCode": "TEST_INDICATOR",
            "CountryCode": "CAN",
            "Year": 2020,
            "Unit": "Index"
            # Missing Score field
        },
        {
            "IndicatorCode": "TEST_INDICATOR",
            "CountryCode": "GBR",
            "Year": 2020,
            "Score": 78.9
            # Missing Unit field
        },
        {
            "CountryCode": "FRA",
            "Year": 2020,
            "Unit": "Index",
            "Score": 88.1
            # Missing IndicatorCode field
        }
    ]
    
    complete, incomplete = filter_incomplete_data(documents)
    
    assert len(complete) == 1
    assert len(incomplete) == 3
    
    # Check that the complete document has all required fields
    assert complete[0]["CountryCode"] == "USA"
    assert complete[0]["Score"] == 85.5
    
    # Check that incomplete documents are correctly identified
    incomplete_countries = {doc["CountryCode"] for doc in incomplete}
    assert incomplete_countries == {"CAN", "GBR", "FRA"}


def test_filter_incomplete_data_empty_list():
    """Test filtering with empty document list."""
    documents = []
    
    complete, incomplete = filter_incomplete_data(documents)
    
    assert complete == []
    assert incomplete == []


def test_filter_incomplete_data_all_incomplete():
    """Test filtering where all documents are incomplete."""
    documents = [
        {
            "IndicatorCode": "TEST_INDICATOR",
            "CountryCode": "USA",
            "Year": 2020
            # Missing Unit and Score
        },
        {
            "CountryCode": "CAN",
            "Year": 2020,
            "Unit": "Index"
            # Missing IndicatorCode and Score
        }
    ]
    
    complete, incomplete = filter_incomplete_data(documents)
    
    assert len(complete) == 0
    assert len(incomplete) == 2
    assert incomplete == documents


def test_filter_incomplete_data_all_complete():
    """Test filtering where all documents are complete."""
    documents = [
        {
            "IndicatorCode": "TEST_INDICATOR_1",
            "CountryCode": "USA",
            "Year": 2020,
            "Unit": "Index",
            "Score": 85.5
        },
        {
            "IndicatorCode": "TEST_INDICATOR_2",
            "CountryCode": "CAN",
            "Year": 2021,
            "Unit": "Percentage",
            "Score": 92.3
        }
    ]
    
    complete, incomplete = filter_incomplete_data(documents)
    
    assert len(complete) == 2
    assert len(incomplete) == 0
    assert complete == documents


def test_filter_incomplete_data_preserves_extra_fields():
    """Test that filtering preserves extra fields beyond the required ones."""
    documents = [
        {
            "IndicatorCode": "TEST_INDICATOR",
            "CountryCode": "USA",
            "Year": 2020,
            "Unit": "Index",
            "Score": 85.5,
            "ExtraField": "extra_value",
            "Metadata": {"source": "test"},
            "Datasets": [{"DatasetCode": "DATASET_A", "Value": 100}]
        }
    ]
    
    complete, incomplete = filter_incomplete_data(documents)
    
    assert len(complete) == 1
    assert len(incomplete) == 0
    
    doc = complete[0]
    assert doc["ExtraField"] == "extra_value"
    assert doc["Metadata"] == {"source": "test"}
    assert doc["Datasets"] == [{"DatasetCode": "DATASET_A", "Value": 100}]


def test_filter_incomplete_data_none_values_allowed():
    """Test that None values in required fields still count as present."""
    documents = [
        {
            "IndicatorCode": "TEST_INDICATOR",
            "CountryCode": "USA",
            "Year": 2020,
            "Unit": None,  # None value but field is present
            "Score": None   # None value but field is present
        }
    ]
    
    complete, incomplete = filter_incomplete_data(documents)
    
    # Document should be considered complete because fields are present (even if None)
    assert len(complete) == 1
    assert len(incomplete) == 0


def test_filter_incomplete_data_zero_values_allowed():
    """Test that zero values in required fields are considered complete."""
    documents = [
        {
            "IndicatorCode": "TEST_INDICATOR",
            "CountryCode": "USA",
            "Year": 0,      # Zero year
            "Unit": "",     # Empty string unit
            "Score": 0.0    # Zero score
        }
    ]
    
    complete, incomplete = filter_incomplete_data(documents)
    
    # Document should be considered complete
    assert len(complete) == 1
    assert len(incomplete) == 0


def test_filter_incomplete_data_specific_missing_fields():
    """Test filtering with specific missing field scenarios."""
    
    # Test missing each required field individually
    test_cases = [
        {
            "missing_field": "IndicatorCode",
            "document": {
                "CountryCode": "USA",
                "Year": 2020,
                "Unit": "Index",
                "Score": 85.5
            }
        },
        {
            "missing_field": "CountryCode",
            "document": {
                "IndicatorCode": "TEST_INDICATOR",
                "Year": 2020,
                "Unit": "Index",
                "Score": 85.5
            }
        },
        {
            "missing_field": "Year",
            "document": {
                "IndicatorCode": "TEST_INDICATOR",
                "CountryCode": "USA",
                "Unit": "Index",
                "Score": 85.5
            }
        },
        {
            "missing_field": "Unit",
            "document": {
                "IndicatorCode": "TEST_INDICATOR",
                "CountryCode": "USA",
                "Year": 2020,
                "Score": 85.5
            }
        },
        {
            "missing_field": "Score",
            "document": {
                "IndicatorCode": "TEST_INDICATOR",
                "CountryCode": "USA",
                "Year": 2020,
                "Unit": "Index"
            }
        }
    ]
    
    for test_case in test_cases:
        complete, incomplete = filter_incomplete_data([test_case["document"]])
        
        assert len(complete) == 0, f"Document missing {test_case['missing_field']} should be incomplete"
        assert len(incomplete) == 1, f"Document missing {test_case['missing_field']} should be in incomplete list"


def test_filter_incomplete_data_mixed_scenarios():
    """Test filtering with a mix of complete and incomplete documents."""
    documents = [
        # Complete document
        {
            "IndicatorCode": "INDICATOR_1",
            "CountryCode": "USA",
            "Year": 2020,
            "Unit": "Index",
            "Score": 85.5
        },
        # Missing Score
        {
            "IndicatorCode": "INDICATOR_2",
            "CountryCode": "CAN",
            "Year": 2020,
            "Unit": "Index"
        },
        # Complete document
        {
            "IndicatorCode": "INDICATOR_3",
            "CountryCode": "GBR",
            "Year": 2021,
            "Unit": "Percentage",
            "Score": 92.1
        },
        # Missing multiple fields
        {
            "CountryCode": "FRA",
            "Year": 2020
        },
        # Complete document with extra fields
        {
            "IndicatorCode": "INDICATOR_5",
            "CountryCode": "DEU",
            "Year": 2019,
            "Unit": "Ratio",
            "Score": 78.3,
            "ExtraField": "extra"
        }
    ]
    
    complete, incomplete = filter_incomplete_data(documents)
    
    assert len(complete) == 3
    assert len(incomplete) == 2
    
    # Check complete documents
    complete_countries = {doc["CountryCode"] for doc in complete}
    assert complete_countries == {"USA", "GBR", "DEU"}
    
    # Check incomplete documents
    incomplete_countries = {doc["CountryCode"] for doc in incomplete}
    assert incomplete_countries == {"CAN", "FRA"}


def test_filter_incomplete_data_does_not_mutate_original():
    """Test that filtering does not mutate the original document list."""
    original_documents = [
        {
            "IndicatorCode": "TEST_INDICATOR",
            "CountryCode": "USA",
            "Year": 2020,
            "Unit": "Index",
            "Score": 85.5
        },
        {
            "IndicatorCode": "TEST_INDICATOR",
            "CountryCode": "CAN",
            "Year": 2020,
            "Unit": "Index"
            # Missing Score - incomplete
        }
    ]
    
    # Create a copy to compare later
    original_copy = [doc.copy() for doc in original_documents]
    
    complete, incomplete = filter_incomplete_data(original_documents)
    
    # Original list should remain unchanged
    assert original_documents == original_copy
    assert len(original_documents) == 2


def test_filter_incomplete_data_different_data_types():
    """Test filtering with different data types in required fields."""
    documents = [
        {
            "IndicatorCode": "TEST_INDICATOR",
            "CountryCode": "USA",
            "Year": "2020",      # String year
            "Unit": 123,         # Numeric unit
            "Score": "85.5"      # String score
        },
        {
            "IndicatorCode": 456,        # Numeric indicator code
            "CountryCode": "CAN",
            "Year": 2020.0,      # Float year
            "Unit": "Index",
            "Score": 92.3
        }
    ]
    
    complete, incomplete = filter_incomplete_data(documents)
    
    # Both should be considered complete regardless of data types
    assert len(complete) == 2
    assert len(incomplete) == 0


def test_filter_incomplete_data_case_sensitivity():
    """Test that field names are case sensitive."""
    documents = [
        {
            "indicatorcode": "TEST_INDICATOR",  # lowercase
            "CountryCode": "USA",
            "Year": 2020,
            "Unit": "Index",
            "Score": 85.5
        }
    ]
    
    complete, incomplete = filter_incomplete_data(documents)
    
    # Should be incomplete due to case mismatch
    assert len(complete) == 0
    assert len(incomplete) == 1


def test_filter_incomplete_data_large_dataset():
    """Test filtering with a large number of documents."""
    documents = []
    
    # Create 1000 documents, half complete and half incomplete
    for i in range(1000):
        if i % 2 == 0:
            # Complete document
            documents.append({
                "IndicatorCode": f"INDICATOR_{i}",
                "CountryCode": f"COUNTRY_{i}",
                "Year": 2020 + (i % 5),
                "Unit": "Index",
                "Score": i * 0.1
            })
        else:
            # Incomplete document (missing Score)
            documents.append({
                "IndicatorCode": f"INDICATOR_{i}",
                "CountryCode": f"COUNTRY_{i}",
                "Year": 2020 + (i % 5),
                "Unit": "Index"
            })
    
    complete, incomplete = filter_incomplete_data(documents)
    
    assert len(complete) == 500
    assert len(incomplete) == 500
    assert len(complete) + len(incomplete) == 1000