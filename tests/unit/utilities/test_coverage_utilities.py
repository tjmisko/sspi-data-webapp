import pytest
from unittest.mock import patch, MagicMock
from sspi_flask_app.api.resources.utilities import (
    check_raw_document_set_coverage, 
    reduce_dataset_list,
    deduplicate_dictionary_list
)


class TestCheckRawDocumentSetCoverage:
    """Test suite for check_raw_document_set_coverage function."""
    
    @patch('sspi_flask_app.api.resources.utilities.sspi_raw_api_data')
    @patch('sspi_flask_app.api.resources.utilities.sspi_metadata')
    def test_check_coverage_basic_functionality(self, mock_metadata, mock_raw_data):
        """Test basic coverage checking functionality."""
        
        # Mock source info for datasets
        mock_metadata.get_source_info.side_effect = [
            {"OrganizationCode": "WB", "QueryCode": "Q1"},
            {"OrganizationCode": "UN", "QueryCode": "Q2"},
            {"OrganizationCode": "OECD", "QueryCode": "Q3"}
        ]
        
        # Mock raw data availability
        mock_raw_data.raw_data_available.side_effect = [True, False, True]
        
        dataset_list = ["DS1", "DS2", "DS3"]
        uncollected, collected = check_raw_document_set_coverage(dataset_list)
        
        assert collected == ["DS1", "DS3"]  # Available datasets
        assert uncollected == ["DS2"]       # Unavailable dataset
        
        # Verify method calls
        assert mock_metadata.get_source_info.call_count == 3
        assert mock_raw_data.raw_data_available.call_count == 3
    
    @patch('sspi_flask_app.api.resources.utilities.sspi_raw_api_data')
    @patch('sspi_flask_app.api.resources.utilities.sspi_metadata')
    def test_check_coverage_all_collected(self, mock_metadata, mock_raw_data):
        """Test when all datasets are collected."""
        
        mock_metadata.get_source_info.side_effect = [
            {"OrganizationCode": "WB", "QueryCode": "Q1"},
            {"OrganizationCode": "UN", "QueryCode": "Q2"}
        ]
        mock_raw_data.raw_data_available.return_value = True
        
        dataset_list = ["DS1", "DS2"]
        uncollected, collected = check_raw_document_set_coverage(dataset_list)
        
        assert collected == ["DS1", "DS2"]
        assert uncollected == []
    
    @patch('sspi_flask_app.api.resources.utilities.sspi_raw_api_data')
    @patch('sspi_flask_app.api.resources.utilities.sspi_metadata')
    def test_check_coverage_none_collected(self, mock_metadata, mock_raw_data):
        """Test when no datasets are collected."""
        
        mock_metadata.get_source_info.side_effect = [
            {"OrganizationCode": "WB", "QueryCode": "Q1"},
            {"OrganizationCode": "UN", "QueryCode": "Q2"}
        ]
        mock_raw_data.raw_data_available.return_value = False
        
        dataset_list = ["DS1", "DS2"]
        uncollected, collected = check_raw_document_set_coverage(dataset_list)
        
        assert collected == []
        assert uncollected == ["DS1", "DS2"]
    
    @patch('sspi_flask_app.api.resources.utilities.sspi_raw_api_data')
    @patch('sspi_flask_app.api.resources.utilities.sspi_metadata')
    def test_check_coverage_empty_list(self, mock_metadata, mock_raw_data):
        """Test with empty dataset list."""
        
        uncollected, collected = check_raw_document_set_coverage([])
        
        assert collected == []
        assert uncollected == []
        mock_metadata.get_source_info.assert_not_called()
        mock_raw_data.raw_data_available.assert_not_called()
    
    @patch('sspi_flask_app.api.resources.utilities.sspi_raw_api_data')
    @patch('sspi_flask_app.api.resources.utilities.sspi_metadata')
    def test_check_coverage_single_dataset(self, mock_metadata, mock_raw_data):
        """Test with single dataset."""
        
        mock_metadata.get_source_info.return_value = {"OrganizationCode": "WB", "QueryCode": "Q1"}
        mock_raw_data.raw_data_available.return_value = True
        
        dataset_list = ["DS1"]
        uncollected, collected = check_raw_document_set_coverage(dataset_list)
        
        assert collected == ["DS1"]
        assert uncollected == []
    
    @patch('sspi_flask_app.api.resources.utilities.sspi_raw_api_data')
    @patch('sspi_flask_app.api.resources.utilities.sspi_metadata')
    def test_check_coverage_preserves_order(self, mock_metadata, mock_raw_data):
        """Test that order is preserved in results."""
        
        mock_metadata.get_source_info.side_effect = [
            {"OrganizationCode": "A"}, {"OrganizationCode": "B"}, 
            {"OrganizationCode": "C"}, {"OrganizationCode": "D"}
        ]
        mock_raw_data.raw_data_available.side_effect = [False, True, False, True]
        
        dataset_list = ["DS1", "DS2", "DS3", "DS4"]
        uncollected, collected = check_raw_document_set_coverage(dataset_list)
        
        assert collected == ["DS2", "DS4"]    # Preserves original order
        assert uncollected == ["DS1", "DS3"]  # Preserves original order
    
    @patch('sspi_flask_app.api.resources.utilities.sspi_raw_api_data')
    @patch('sspi_flask_app.api.resources.utilities.sspi_metadata')
    def test_check_coverage_realistic_scenario(self, mock_metadata, mock_raw_data):
        """Test with realistic SSPI dataset codes."""
        
        # Mock realistic source info
        source_infos = [
            {"OrganizationCode": "UNESCO", "QueryCode": "EDU_PRIMARY"},
            {"OrganizationCode": "WHO", "QueryCode": "HEALTH_OUTCOMES"},
            {"OrganizationCode": "WORLDBANK", "QueryCode": "ECONOMIC_FREEDOM"},
            {"OrganizationCode": "OECD", "QueryCode": "GOVERNANCE"}
        ]
        mock_metadata.get_source_info.side_effect = source_infos
        
        # Some datasets collected, some not
        mock_raw_data.raw_data_available.side_effect = [True, True, False, True]
        
        dataset_list = ["EDUACC", "HLTHOUT", "ECOFREE", "GOVEFF"]
        uncollected, collected = check_raw_document_set_coverage(dataset_list)
        
        assert collected == ["EDUACC", "HLTHOUT", "GOVEFF"]
        assert uncollected == ["ECOFREE"]


class TestDeduplicateDictionaryList:
    """Test suite for deduplicate_dictionary_list function."""
    
    def test_deduplicate_basic_functionality(self):
        """Test basic deduplication functionality."""
        
        dict_list = [
            {"a": 1, "b": 2},
            {"b": 2, "a": 1},  # Same as first, different order
            {"a": 3, "b": 4},
            {"a": 1, "b": 2},  # Duplicate of first
        ]
        
        result = deduplicate_dictionary_list(dict_list)
        
        assert len(result) == 2
        assert {"a": 1, "b": 2} in result
        assert {"a": 3, "b": 4} in result
    
    def test_deduplicate_empty_list(self):
        """Test deduplication with empty list."""
        
        result = deduplicate_dictionary_list([])
        
        assert result == []
    
    def test_deduplicate_single_dict(self):
        """Test deduplication with single dictionary."""
        
        dict_list = [{"key": "value"}]
        result = deduplicate_dictionary_list(dict_list)
        
        assert result == [{"key": "value"}]
    
    def test_deduplicate_no_duplicates(self):
        """Test deduplication when no duplicates exist."""
        
        dict_list = [
            {"a": 1},
            {"b": 2},
            {"c": 3}
        ]
        
        result = deduplicate_dictionary_list(dict_list)
        
        assert len(result) == 3
        assert result == dict_list
    
    def test_deduplicate_all_duplicates(self):
        """Test deduplication when all are duplicates."""
        
        dict_list = [
            {"x": 1, "y": 2},
            {"y": 2, "x": 1},  # Same content, different order
            {"x": 1, "y": 2},  # Exact duplicate
        ]
        
        result = deduplicate_dictionary_list(dict_list)
        
        assert len(result) == 1
        assert result == [{"x": 1, "y": 2}]
    
    def test_deduplicate_preserves_first_occurrence(self):
        """Test that first occurrence is preserved."""
        
        dict_list = [
            {"id": 1, "name": "first"},
            {"id": 2, "name": "second"},
            {"id": 1, "name": "first"},  # Duplicate
            {"id": 3, "name": "third"},
            {"id": 2, "name": "second"}, # Duplicate
        ]
        
        result = deduplicate_dictionary_list(dict_list)
        
        assert len(result) == 3
        # Should preserve order of first occurrences
        expected = [
            {"id": 1, "name": "first"},
            {"id": 2, "name": "second"},
            {"id": 3, "name": "third"}
        ]
        assert result == expected
    
    def test_deduplicate_different_key_orders(self):
        """Test that dictionaries with same content but different key order are considered equal."""
        
        dict_list = [
            {"a": 1, "b": 2, "c": 3},
            {"c": 3, "a": 1, "b": 2},  # Same content, different order
            {"b": 2, "c": 3, "a": 1},  # Same content, different order
        ]
        
        result = deduplicate_dictionary_list(dict_list)
        
        assert len(result) == 1
        assert result[0] == {"a": 1, "b": 2, "c": 3}
    
    def test_deduplicate_nested_structures(self):
        """Test deduplication with hashable nested structures."""
        
        # Use tuples instead of lists to make them hashable
        dict_list = [
            {"data": (1, 2, 3), "meta": "list_type"},
            {"meta": "list_type", "data": (1, 2, 3)},  # Same content, different order
            {"data": (1, 2, 4), "meta": "list_type"},  # Different content
        ]
        
        result = deduplicate_dictionary_list(dict_list)
        
        assert len(result) == 2
        assert {"data": (1, 2, 3), "meta": "list_type"} in result
        assert {"data": (1, 2, 4), "meta": "list_type"} in result
    
    def test_deduplicate_mixed_data_types(self):
        """Test deduplication with mixed data types."""
        
        dict_list = [
            {"int": 1, "str": "text", "bool": True, "none": None},
            {"bool": True, "int": 1, "none": None, "str": "text"},  # Same content
            {"int": 1, "str": "text", "bool": False, "none": None}, # Different bool
        ]
        
        result = deduplicate_dictionary_list(dict_list)
        
        assert len(result) == 2
    
    def test_deduplicate_empty_dictionaries(self):
        """Test deduplication with empty dictionaries."""
        
        dict_list = [{}, {}, {"a": 1}, {}]
        
        result = deduplicate_dictionary_list(dict_list)
        
        assert len(result) == 2
        assert {} in result
        assert {"a": 1} in result
    
    def test_deduplicate_large_dataset(self):
        """Test deduplication performance with larger dataset."""
        
        # Create dataset with many duplicates
        dict_list = []
        for i in range(100):
            dict_list.append({"group": i % 10, "value": i % 5})  # Many duplicates
        
        result = deduplicate_dictionary_list(dict_list)
        
        # Should have much fewer unique combinations
        assert len(result) < len(dict_list)
        assert len(result) <= 50  # At most 10 groups * 5 values


class TestReduceDatasetList:
    """Test suite for reduce_dataset_list function."""
    
    @patch('sspi_flask_app.api.resources.utilities.sspi_metadata')
    def test_reduce_dataset_list_basic_functionality(self, mock_metadata):
        """Test basic dataset list reduction."""
        
        # Mock source info where some datasets share sources
        mock_metadata.get_source_info.side_effect = [
            {"OrganizationCode": "WB", "QueryCode": "Q1"},  # DS1
            {"OrganizationCode": "WB", "QueryCode": "Q1"},  # DS2 - same source as DS1
            {"OrganizationCode": "UN", "QueryCode": "Q2"},  # DS3
            {"OrganizationCode": "WB", "QueryCode": "Q1"},  # DS4 - same source as DS1/DS2
        ]
        
        dataset_list = ["DS1", "DS2", "DS3", "DS4"]
        result = reduce_dataset_list(dataset_list)
        
        # Should keep first occurrence of each unique source
        assert len(result) == 2
        assert "DS1" in result  # First occurrence of WB/Q1
        assert "DS3" in result  # Unique UN/Q2
        assert "DS2" not in result  # Duplicate source
        assert "DS4" not in result  # Duplicate source
    
    @patch('sspi_flask_app.api.resources.utilities.sspi_metadata')
    def test_reduce_dataset_list_no_duplicates(self, mock_metadata):
        """Test reduction when no source duplicates exist."""
        
        mock_metadata.get_source_info.side_effect = [
            {"OrganizationCode": "WB", "QueryCode": "Q1"},
            {"OrganizationCode": "UN", "QueryCode": "Q2"},
            {"OrganizationCode": "OECD", "QueryCode": "Q3"},
        ]
        
        dataset_list = ["DS1", "DS2", "DS3"]
        result = reduce_dataset_list(dataset_list)
        
        # Should keep all datasets (no duplicates)
        assert len(result) == 3
        assert result == ["DS1", "DS2", "DS3"]
    
    @patch('sspi_flask_app.api.resources.utilities.sspi_metadata')
    def test_reduce_dataset_list_all_same_source(self, mock_metadata):
        """Test reduction when all datasets have same source."""
        
        same_source = {"OrganizationCode": "WB", "QueryCode": "Q1"}
        mock_metadata.get_source_info.return_value = same_source
        
        dataset_list = ["DS1", "DS2", "DS3", "DS4"]
        result = reduce_dataset_list(dataset_list)
        
        # Should keep only first dataset
        assert len(result) == 1
        assert result == ["DS1"]
    
    @patch('sspi_flask_app.api.resources.utilities.sspi_metadata')
    def test_reduce_dataset_list_empty_list(self, mock_metadata):
        """Test reduction with empty dataset list."""
        
        result = reduce_dataset_list([])
        
        assert result == []
        mock_metadata.get_source_info.assert_not_called()
    
    @patch('sspi_flask_app.api.resources.utilities.sspi_metadata')
    def test_reduce_dataset_list_single_dataset(self, mock_metadata):
        """Test reduction with single dataset."""
        
        mock_metadata.get_source_info.return_value = {"OrganizationCode": "WB", "QueryCode": "Q1"}
        
        dataset_list = ["DS1"]
        result = reduce_dataset_list(dataset_list)
        
        assert result == ["DS1"]
    
    @patch('sspi_flask_app.api.resources.utilities.sspi_metadata')
    def test_reduce_dataset_list_preserves_order(self, mock_metadata):
        """Test that reduction preserves order of first occurrences."""
        
        mock_metadata.get_source_info.side_effect = [
            {"OrganizationCode": "C", "QueryCode": "Q3"},  # DS1
            {"OrganizationCode": "A", "QueryCode": "Q1"},  # DS2
            {"OrganizationCode": "B", "QueryCode": "Q2"},  # DS3
            {"OrganizationCode": "A", "QueryCode": "Q1"},  # DS4 - duplicate
            {"OrganizationCode": "C", "QueryCode": "Q3"},  # DS5 - duplicate
        ]
        
        dataset_list = ["DS1", "DS2", "DS3", "DS4", "DS5"]
        result = reduce_dataset_list(dataset_list)
        
        # Should preserve order of first occurrences
        assert result == ["DS1", "DS2", "DS3"]
    
    @patch('sspi_flask_app.api.resources.utilities.sspi_metadata')
    def test_reduce_dataset_list_complex_source_info(self, mock_metadata):
        """Test reduction with complex source information."""
        
        mock_metadata.get_source_info.side_effect = [
            {
                "OrganizationCode": "UNESCO",
                "QueryCode": "EDU_PRIMARY",
                "Region": "Global",
                "DataType": "Enrollment"
            },
            {
                "OrganizationCode": "UNESCO", 
                "QueryCode": "EDU_PRIMARY",
                "Region": "Global",
                "DataType": "Enrollment"
            },  # Exact duplicate
            {
                "OrganizationCode": "UNESCO",
                "QueryCode": "EDU_PRIMARY", 
                "Region": "Regional",  # Different region
                "DataType": "Enrollment"
            },
            {
                "OrganizationCode": "WHO",
                "QueryCode": "HEALTH_BASIC",
                "Region": "Global",
                "DataType": "Coverage"
            }
        ]
        
        dataset_list = ["EDU_PRIM_GLOB", "EDU_PRIM_DUP", "EDU_PRIM_REG", "HLTH_BASIC"]
        result = reduce_dataset_list(dataset_list)
        
        # Should keep 3 unique sources (duplicate removed)
        assert len(result) == 3
        assert "EDU_PRIM_GLOB" in result
        assert "EDU_PRIM_REG" in result  # Different region
        assert "HLTH_BASIC" in result
        assert "EDU_PRIM_DUP" not in result  # Duplicate
    
    @patch('sspi_flask_app.api.resources.utilities.sspi_metadata')
    def test_reduce_dataset_list_realistic_scenario(self, mock_metadata):
        """Test with realistic SSPI dataset scenario."""
        
        # Realistic scenario where multiple dataset codes map to same raw source
        mock_metadata.get_source_info.side_effect = [
            {"OrganizationCode": "WORLDBANK", "QueryCode": "WDI_EDUCATION"},     # EDUACC_PRIM
            {"OrganizationCode": "WORLDBANK", "QueryCode": "WDI_EDUCATION"},     # EDUACC_SEC (same source)
            {"OrganizationCode": "UNESCO", "QueryCode": "UIS_EDUCATION"},        # EDUQUAL
            {"OrganizationCode": "WHO", "QueryCode": "GHO_HEALTH"},              # HLTHOUT
            {"OrganizationCode": "WHO", "QueryCode": "GHO_HEALTH"},              # HLTHEXP (same source)
            {"OrganizationCode": "OECD", "QueryCode": "GOVERNANCE"},             # GOVEFF
        ]
        
        dataset_list = ["EDUACC_PRIM", "EDUACC_SEC", "EDUQUAL", "HLTHOUT", "HLTHEXP", "GOVEFF"]
        result = reduce_dataset_list(dataset_list)
        
        # Should reduce to 4 unique sources
        expected_kept = ["EDUACC_PRIM", "EDUQUAL", "HLTHOUT", "GOVEFF"]
        assert len(result) == 4
        assert result == expected_kept
        
        # Duplicates should be removed
        assert "EDUACC_SEC" not in result   # Same source as EDUACC_PRIM
        assert "HLTHEXP" not in result      # Same source as HLTHOUT


class TestCoverageUtilitiesIntegration:
    """Integration tests for coverage utilities working together."""
    
    @patch('sspi_flask_app.api.resources.utilities.sspi_raw_api_data')
    @patch('sspi_flask_app.api.resources.utilities.sspi_metadata')
    def test_coverage_and_reduction_workflow(self, mock_metadata, mock_raw_data):
        """Test typical workflow: reduce dataset list, then check coverage."""
        
        # Step 1: Mock source info for reduction
        mock_metadata.get_source_info.side_effect = [
            {"OrganizationCode": "WB", "QueryCode": "Q1"},  # DS1
            {"OrganizationCode": "WB", "QueryCode": "Q1"},  # DS2 - duplicate
            {"OrganizationCode": "UN", "QueryCode": "Q2"},  # DS3
            {"OrganizationCode": "WB", "QueryCode": "Q1"},  # For coverage check of DS1
            {"OrganizationCode": "UN", "QueryCode": "Q2"},  # For coverage check of DS3
        ]
        
        # Step 2: Mock raw data availability
        mock_raw_data.raw_data_available.side_effect = [True, False]  # DS1 available, DS3 not
        
        original_list = ["DS1", "DS2", "DS3"]
        
        # Reduce dataset list first
        reduced_list = reduce_dataset_list(original_list)
        assert reduced_list == ["DS1", "DS3"]  # DS2 removed as duplicate
        
        # Then check coverage of reduced list
        uncollected, collected = check_raw_document_set_coverage(reduced_list)
        
        assert collected == ["DS1"]
        assert uncollected == ["DS3"]
    
    def test_deduplication_edge_cases(self):
        """Test edge cases in dictionary deduplication."""
        
        # Test with unhashable values - should raise TypeError
        dict_list = [
            {"data": [1, 2], "nested": {"key": "value"}},
            {"nested": {"key": "value"}, "data": [1, 2]},  # Same content
            {"data": [1, 3], "nested": {"key": "value"}},  # Different list
        ]
        
        # Function doesn't handle unhashable types, should raise TypeError
        with pytest.raises(TypeError):
            deduplicate_dictionary_list(dict_list)