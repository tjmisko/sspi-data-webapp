import pytest
from unittest.mock import patch
from sspi_flask_app.api.resources.utilities import slice_dataset, filter_imputations


class TestSliceDataset:
    """Test suite for slice_dataset function."""
    
    @pytest.fixture
    def sample_scored_documents(self):
        """Sample documents in the format output by score_indicator."""
        return [
            {
                "IndicatorCode": "IND1",
                "CountryCode": "USA",
                "Year": 2020,
                "Score": 0.8,
                "Datasets": [
                    {
                        "DatasetCode": "DS1",
                        "CountryCode": "USA",
                        "Year": 2020,
                        "Value": 100.0,
                        "Unit": "Percentage"
                    },
                    {
                        "DatasetCode": "DS2",
                        "CountryCode": "USA",
                        "Year": 2020,
                        "Value": 85.0,
                        "Unit": "Index"
                    }
                ]
            },
            {
                "IndicatorCode": "IND1",
                "CountryCode": "CAN",
                "Year": 2020,
                "Score": 0.75,
                "Datasets": [
                    {
                        "DatasetCode": "DS1",
                        "CountryCode": "CAN",
                        "Year": 2020,
                        "Value": 95.0,
                        "Unit": "Percentage"
                    },
                    {
                        "DatasetCode": "DS3",
                        "CountryCode": "CAN",
                        "Year": 2020,
                        "Value": 70.0,
                        "Unit": "Score"
                    }
                ]
            }
        ]
    
    @patch('builtins.print')
    def test_slice_dataset_single_code_string(self, mock_print, sample_scored_documents):
        """Test slicing with a single dataset code as string."""
        
        result = slice_dataset(sample_scored_documents, "DS1")
        
        # Should return 2 datasets (one from each country)
        assert len(result) == 2
        
        # Both should have DatasetCode "DS1"
        assert all(ds["DatasetCode"] == "DS1" for ds in result)
        
        # Check specific values
        usa_dataset = next(ds for ds in result if ds["CountryCode"] == "USA")
        can_dataset = next(ds for ds in result if ds["CountryCode"] == "CAN")
        
        assert usa_dataset["Value"] == 100.0
        assert can_dataset["Value"] == 95.0
        
    
    @patch('builtins.print')
    def test_slice_dataset_list_of_codes(self, mock_print, sample_scored_documents):
        """Test slicing with a list of dataset codes."""
        
        result = slice_dataset(sample_scored_documents, ["DS1", "DS2"])
        
        # Should return 3 datasets (DS1 from both countries, DS2 from USA)
        assert len(result) == 3
        
        # Check that we have the right dataset codes
        dataset_codes = [ds["DatasetCode"] for ds in result]
        assert "DS1" in dataset_codes
        assert "DS2" in dataset_codes
        assert dataset_codes.count("DS1") == 2  # From both countries
        assert dataset_codes.count("DS2") == 1  # Only from USA
    
    @patch('builtins.print')
    def test_slice_dataset_nonexistent_code(self, mock_print, sample_scored_documents):
        """Test slicing with a dataset code that doesn't exist."""
        
        result = slice_dataset(sample_scored_documents, "NONEXISTENT")
        
        assert result == []
    
    @patch('builtins.print')
    def test_slice_dataset_empty_list(self, mock_print):
        """Test slicing with empty document list."""
        
        result = slice_dataset([], "DS1")
        
        assert result == []
        mock_print.assert_not_called()
    
    @patch('builtins.print')
    def test_slice_dataset_empty_dataset_codes(self, mock_print, sample_scored_documents):
        """Test slicing with empty dataset codes list."""
        
        result = slice_dataset(sample_scored_documents, [])
        
        assert result == []
    
    @patch('builtins.print')
    def test_slice_dataset_documents_without_datasets(self, mock_print):
        """Test slicing documents that don't have Datasets field."""
        
        docs_without_datasets = [
            {
                "IndicatorCode": "IND1",
                "CountryCode": "USA",
                "Year": 2020,
                "Score": 0.8
                # No Datasets field
            }
        ]
        
        result = slice_dataset(docs_without_datasets, "DS1")
        
        assert result == []
    
    @patch('builtins.print')
    def test_slice_dataset_documents_with_empty_datasets(self, mock_print):
        """Test slicing documents with empty Datasets list."""
        
        docs_with_empty_datasets = [
            {
                "IndicatorCode": "IND1",
                "CountryCode": "USA",
                "Year": 2020,
                "Score": 0.8,
                "Datasets": []
            }
        ]
        
        result = slice_dataset(docs_with_empty_datasets, "DS1")
        
        assert result == []
    
    @patch('builtins.print')
    def test_slice_dataset_datasets_without_code(self, mock_print):
        """Test slicing when datasets don't have DatasetCode field."""
        
        docs_without_codes = [
            {
                "IndicatorCode": "IND1",
                "CountryCode": "USA",
                "Year": 2020,
                "Score": 0.8,
                "Datasets": [
                    {
                        "CountryCode": "USA",
                        "Year": 2020,
                        "Value": 100.0
                        # No DatasetCode field
                    }
                ]
            }
        ]
        
        result = slice_dataset(docs_without_codes, "DS1")
        
        assert result == []
    
    @patch('builtins.print')
    def test_slice_dataset_mixed_valid_invalid(self, mock_print):
        """Test slicing with mix of valid and invalid documents."""
        
        mixed_docs = [
            {
                "IndicatorCode": "IND1",
                "CountryCode": "USA",
                "Year": 2020,
                "Datasets": [
                    {"DatasetCode": "DS1", "Value": 100.0}
                ]
            },
            {
                "IndicatorCode": "IND2",
                "CountryCode": "CAN",
                "Year": 2020,
                "Datasets": []  # Empty datasets
            },
            {
                "IndicatorCode": "IND3",
                "CountryCode": "GBR",
                "Year": 2020
                # No Datasets field
            }
        ]
        
        result = slice_dataset(mixed_docs, "DS1")
        
        assert len(result) == 1
        assert result[0]["DatasetCode"] == "DS1"
        assert result[0]["Value"] == 100.0
    
    @patch('builtins.print')
    def test_slice_dataset_case_sensitivity(self, mock_print, sample_scored_documents):
        """Test case sensitivity of dataset codes."""
        
        result = slice_dataset(sample_scored_documents, "ds1")  # lowercase
        
        # Should not match "DS1" (case sensitive)
        assert result == []
    
    @patch('builtins.print')
    def test_slice_dataset_preserves_dataset_structure(self, mock_print, sample_scored_documents):
        """Test that returned datasets preserve their structure."""
        
        result = slice_dataset(sample_scored_documents, "DS2")
        
        assert len(result) == 1
        dataset = result[0]
        
        # Should preserve all fields from original dataset
        expected_fields = {"DatasetCode", "CountryCode", "Year", "Value", "Unit"}
        assert set(dataset.keys()) == expected_fields
        
        assert dataset["DatasetCode"] == "DS2"
        assert dataset["CountryCode"] == "USA"
        assert dataset["Year"] == 2020
        assert dataset["Value"] == 85.0
        assert dataset["Unit"] == "Index"
    
    @patch('builtins.print')
    def test_slice_dataset_realistic_scenario(self, mock_print):
        """Test with realistic SSPI indicator scoring output."""
        
        realistic_docs = [
            {
                "IndicatorCode": "EDUACC",
                "CountryCode": "USA",
                "Year": 2020,
                "Score": 0.852,
                "Unit": "SSPI Score",
                "Datasets": [
                    {
                        "DatasetCode": "UNESC_PRIM",
                        "CountryCode": "USA",
                        "Year": 2020,
                        "Value": 95.2,
                        "Unit": "Percentage",
                        "Source": "UNESCO"
                    },
                    {
                        "DatasetCode": "UNESC_SEC",
                        "CountryCode": "USA",
                        "Year": 2020,
                        "Value": 87.5,
                        "Unit": "Percentage",
                        "Source": "UNESCO"
                    }
                ]
            },
            {
                "IndicatorCode": "EDUACC",
                "CountryCode": "CAN",
                "Year": 2020,
                "Score": 0.891,
                "Unit": "SSPI Score",
                "Datasets": [
                    {
                        "DatasetCode": "UNESC_PRIM",
                        "CountryCode": "CAN",
                        "Year": 2020,
                        "Value": 98.1,
                        "Unit": "Percentage",
                        "Source": "UNESCO"
                    }
                ]
            }
        ]
        
        # Extract primary education datasets
        result = slice_dataset(realistic_docs, "UNESC_PRIM")
        
        assert len(result) == 2
        usa_data = next(ds for ds in result if ds["CountryCode"] == "USA")
        can_data = next(ds for ds in result if ds["CountryCode"] == "CAN")
        
        assert usa_data["Value"] == 95.2
        assert can_data["Value"] == 98.1
        assert all(ds["Source"] == "UNESCO" for ds in result)


class TestFilterImputations:
    """Test suite for filter_imputations function."""
    
    @pytest.fixture
    def sample_documents_with_imputations(self):
        """Sample documents with and without imputations."""
        return [
            {
                "IndicatorCode": "IND1",
                "CountryCode": "USA",
                "Year": 2020,
                "Score": 0.8,
                "Datasets": [
                    {
                        "DatasetCode": "DS1",
                        "Value": 100.0,
                        "Imputed": False
                    },
                    {
                        "DatasetCode": "DS2",
                        "Value": 85.0,
                        "Imputed": True  # This document has imputation
                    }
                ]
            },
            {
                "IndicatorCode": "IND1",
                "CountryCode": "CAN",
                "Year": 2020,
                "Score": 0.75,
                "Datasets": [
                    {
                        "DatasetCode": "DS1",
                        "Value": 95.0,
                        "Imputed": False
                    },
                    {
                        "DatasetCode": "DS2",
                        "Value": 80.0,
                        "Imputed": False
                    }
                ]
            },
            {
                "IndicatorCode": "IND1",
                "CountryCode": "GBR",
                "Year": 2020,
                "Score": 0.7,
                "Datasets": [
                    {
                        "DatasetCode": "DS1",
                        "Value": 90.0,
                        "Imputed": True  # This document has imputation
                    }
                ]
            }
        ]
    
    def test_filter_imputations_basic_functionality(self, sample_documents_with_imputations):
        """Test basic filtering of documents with imputations."""
        
        result = filter_imputations(sample_documents_with_imputations)
        
        # Should return 2 documents (USA and GBR have imputations)
        assert len(result) == 2
        
        country_codes = [doc["CountryCode"] for doc in result]
        assert "USA" in country_codes  # Has one imputed dataset
        assert "GBR" in country_codes  # Has one imputed dataset
        assert "CAN" not in country_codes  # No imputed datasets
    
    def test_filter_imputations_no_imputations(self):
        """Test filtering when no documents have imputations."""
        
        docs_without_imputations = [
            {
                "IndicatorCode": "IND1",
                "CountryCode": "USA",
                "Year": 2020,
                "Datasets": [
                    {"DatasetCode": "DS1", "Imputed": False},
                    {"DatasetCode": "DS2", "Imputed": False}
                ]
            }
        ]
        
        result = filter_imputations(docs_without_imputations)
        
        assert result == []
    
    def test_filter_imputations_all_have_imputations(self):
        """Test filtering when all documents have imputations."""
        
        docs_with_imputations = [
            {
                "CountryCode": "USA",
                "Datasets": [{"DatasetCode": "DS1", "Imputed": True}]
            },
            {
                "CountryCode": "CAN",
                "Datasets": [{"DatasetCode": "DS2", "Imputed": True}]
            }
        ]
        
        result = filter_imputations(docs_with_imputations)
        
        assert len(result) == 2
        assert result == docs_with_imputations
    
    def test_filter_imputations_empty_list(self):
        """Test filtering with empty document list."""
        
        result = filter_imputations([])
        
        assert result == []
    
    def test_filter_imputations_documents_without_datasets(self):
        """Test filtering documents without Datasets field."""
        
        docs_without_datasets = [
            {
                "IndicatorCode": "IND1",
                "CountryCode": "USA",
                "Year": 2020,
                "Score": 0.8
                # No Datasets field
            }
        ]
        
        result = filter_imputations(docs_without_datasets)
        
        assert result == []
    
    def test_filter_imputations_documents_with_empty_datasets(self):
        """Test filtering documents with empty Datasets list."""
        
        docs_with_empty_datasets = [
            {
                "IndicatorCode": "IND1",
                "CountryCode": "USA",
                "Year": 2020,
                "Score": 0.8,
                "Datasets": []
            }
        ]
        
        result = filter_imputations(docs_with_empty_datasets)
        
        assert result == []
    
    def test_filter_imputations_datasets_without_imputed_field(self):
        """Test filtering when datasets don't have Imputed field."""
        
        docs_without_imputed_field = [
            {
                "CountryCode": "USA",
                "Datasets": [
                    {
                        "DatasetCode": "DS1",
                        "Value": 100.0
                        # No Imputed field
                    }
                ]
            }
        ]
        
        result = filter_imputations(docs_without_imputed_field)
        
        # Should not include documents where Imputed field is missing (defaults to False)
        assert result == []
    
    def test_filter_imputations_mixed_imputed_values(self):
        """Test filtering with various Imputed field values."""
        
        mixed_docs = [
            {
                "CountryCode": "A",
                "Datasets": [{"Imputed": True}]  # Explicit True
            },
            {
                "CountryCode": "B", 
                "Datasets": [{"Imputed": False}]  # Explicit False
            },
            {
                "CountryCode": "C",
                "Datasets": [{"Imputed": 1}]  # Truthy value
            },
            {
                "CountryCode": "D",
                "Datasets": [{"Imputed": 0}]  # Falsy value
            },
            {
                "CountryCode": "E",
                "Datasets": [{"Imputed": "yes"}]  # Truthy string
            },
            {
                "CountryCode": "F",
                "Datasets": [{"Imputed": ""}]  # Falsy string
            },
            {
                "CountryCode": "G",
                "Datasets": [{}]  # Missing Imputed field
            }
        ]
        
        result = filter_imputations(mixed_docs)
        
        # Should include documents with truthy Imputed values
        country_codes = [doc["CountryCode"] for doc in result]
        assert "A" in country_codes  # True
        assert "C" in country_codes  # 1
        assert "E" in country_codes  # "yes"
        
        assert "B" not in country_codes  # False
        assert "D" not in country_codes  # 0
        assert "F" not in country_codes  # ""
        assert "G" not in country_codes  # Missing field
    
    def test_filter_imputations_multiple_datasets_mixed(self):
        """Test filtering with multiple datasets, some imputed, some not."""
        
        mixed_datasets_doc = [
            {
                "CountryCode": "USA",
                "Datasets": [
                    {"DatasetCode": "DS1", "Imputed": False},
                    {"DatasetCode": "DS2", "Imputed": True},   # Has imputation
                    {"DatasetCode": "DS3", "Imputed": False}
                ]
            }
        ]
        
        result = filter_imputations(mixed_datasets_doc)
        
        # Should include the document because at least one dataset is imputed
        assert len(result) == 1
        assert result[0]["CountryCode"] == "USA"
    
    def test_filter_imputations_preserves_document_structure(self, sample_documents_with_imputations):
        """Test that filtered documents preserve their original structure."""
        
        result = filter_imputations(sample_documents_with_imputations)
        
        # Find the USA document (should be included)
        usa_doc = next(doc for doc in result if doc["CountryCode"] == "USA")
        
        # Should preserve all original fields
        expected_fields = {"IndicatorCode", "CountryCode", "Year", "Score", "Datasets"}
        assert set(usa_doc.keys()) == expected_fields
        
        # Should preserve all datasets (both imputed and non-imputed)
        assert len(usa_doc["Datasets"]) == 2
        assert usa_doc["IndicatorCode"] == "IND1"
        assert usa_doc["Score"] == 0.8
    
    def test_filter_imputations_realistic_scenario(self):
        """Test with realistic SSPI indicator data with imputations."""
        
        realistic_docs = [
            {
                "IndicatorCode": "EDUACC",
                "CountryCode": "USA",
                "Year": 2020,
                "Score": 0.852,
                "Datasets": [
                    {
                        "DatasetCode": "UNESC_PRIM",
                        "Value": 95.2,
                        "Imputed": False,
                        "ImputationMethod": None
                    },
                    {
                        "DatasetCode": "UNESC_SEC",
                        "Value": 87.5,
                        "Imputed": False,
                        "ImputationMethod": None
                    }
                ]
            },
            {
                "IndicatorCode": "EDUACC",
                "CountryCode": "SOM",  # Somalia - likely to have imputed data
                "Year": 2020,
                "Score": 0.234,
                "Datasets": [
                    {
                        "DatasetCode": "UNESC_PRIM",
                        "Value": 45.0,
                        "Imputed": True,
                        "ImputationMethod": "Linear Interpolation",
                        "ImputationDistance": 2
                    }
                ]
            },
            {
                "IndicatorCode": "EDUACC",
                "CountryCode": "CAN",
                "Year": 2020,
                "Score": 0.891,
                "Datasets": [
                    {
                        "DatasetCode": "UNESC_PRIM",
                        "Value": 98.1,
                        "Imputed": False,
                        "ImputationMethod": None
                    }
                ]
            }
        ]
        
        result = filter_imputations(realistic_docs)
        
        # Should only include Somalia (has imputed data)
        assert len(result) == 1
        assert result[0]["CountryCode"] == "SOM"
        
        # Verify imputation metadata is preserved
        som_dataset = result[0]["Datasets"][0]
        assert som_dataset["Imputed"] is True
        assert som_dataset["ImputationMethod"] == "Linear Interpolation"
        assert som_dataset["ImputationDistance"] == 2
    
    def test_filter_imputations_performance_large_dataset(self):
        """Test performance with larger dataset."""
        
        # Create large dataset with mix of imputed and non-imputed
        large_docs = []
        for i in range(1000):
            doc = {
                "CountryCode": f"CTR{i}",
                "Datasets": [
                    {
                        "DatasetCode": "DS1",
                        "Imputed": i % 3 == 0  # Every third document has imputation
                    }
                ]
            }
            large_docs.append(doc)
        
        result = filter_imputations(large_docs)
        
        # Should include roughly 1/3 of documents
        expected_count = len([i for i in range(1000) if i % 3 == 0])
        assert len(result) == expected_count
        
        # Verify all returned documents have imputations
        for doc in result:
            assert any(ds.get("Imputed", False) for ds in doc["Datasets"])
