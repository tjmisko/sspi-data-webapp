import pytest
from unittest.mock import patch, MagicMock
from sspi_flask_app.api.resources.utilities import score_indicator


class TestScoreIndicator:
    """Test suite for score_indicator function."""
    
    @pytest.fixture
    def sample_dataset_documents(self):
        """Sample dataset documents for scoring."""
        return [
            {
                "DatasetCode": "DS1",
                "CountryCode": "USA",
                "Year": "2020",
                "Value": "100.0",
                "Unit": "Percentage"
            },
            {
                "DatasetCode": "DS2", 
                "CountryCode": "USA",
                "Year": "2020",
                "Value": "85.0",
                "Unit": "Index"
            },
            {
                "DatasetCode": "DS1",
                "CountryCode": "CAN",
                "Year": "2020", 
                "Value": "95.0",
                "Unit": "Percentage"
            }
        ]
    
    @pytest.fixture
    def sample_score_function(self):
        """Simple score function for testing."""
        def score_func(ds1, ds2=None):
            if ds2 is None:
                return ds1 / 100.0
            return (ds1 + ds2) / 200.0
        return score_func
    
    @patch('sspi_flask_app.api.resources.utilities.filter_incomplete_data')
    @patch('sspi_flask_app.api.resources.utilities.score_indicator_documents')
    @patch('sspi_flask_app.api.resources.utilities.group_by_indicator')
    @patch('sspi_flask_app.api.resources.utilities.drop_none_or_na')
    @patch('sspi_flask_app.api.resources.utilities.sspi_clean_api_data')
    @patch('sspi_flask_app.api.resources.utilities.convert_data_types')
    def test_score_indicator_basic_functionality(
        self, mock_convert, mock_validate, mock_drop, mock_group, 
        mock_score_docs, mock_filter, sample_dataset_documents, sample_score_function
    ):
        """Test basic score_indicator functionality."""
        
        # Setup mocks
        converted_docs = [{"Year": 2020, "Value": 100.0}]
        mock_convert.return_value = converted_docs
        mock_validate.validate_dataset_list.return_value = None
        
        cleaned_docs = ([{"Year": 2020, "Value": 100.0}], [])
        mock_drop.return_value = cleaned_docs
        
        grouped_docs = [{"IndicatorCode": "IND1", "Datasets": []}]
        mock_group.return_value = grouped_docs
        
        scored_docs = [{"IndicatorCode": "IND1", "Score": 0.8}]
        mock_score_docs.return_value = scored_docs
        
        filtered_docs = ([{"IndicatorCode": "IND1", "Score": 0.8}], [])
        mock_filter.return_value = filtered_docs
        
        # Execute
        result = score_indicator(
            sample_dataset_documents, 
            "IND1", 
            sample_score_function, 
            "SSPI Score"
        )
        
        # Verify
        assert result == filtered_docs
        
        # Verify function call chain
        mock_convert.assert_called_once_with(sample_dataset_documents)
        mock_validate.validate_dataset_list.assert_called_once_with(converted_docs)
        mock_drop.assert_called_once_with(converted_docs)
        mock_group.assert_called_once_with(cleaned_docs[0], "IND1")
        mock_score_docs.assert_called_once_with(grouped_docs, sample_score_function, "SSPI Score")
        mock_filter.assert_called_once_with(scored_docs)
    
    @patch('sspi_flask_app.api.resources.utilities.filter_incomplete_data')
    @patch('sspi_flask_app.api.resources.utilities.score_indicator_documents')
    @patch('sspi_flask_app.api.resources.utilities.group_by_indicator')
    @patch('sspi_flask_app.api.resources.utilities.drop_none_or_na')
    @patch('sspi_flask_app.api.resources.utilities.sspi_clean_api_data')
    @patch('sspi_flask_app.api.resources.utilities.convert_data_types')
    def test_score_indicator_with_callable_unit(
        self, mock_convert, mock_validate, mock_drop, mock_group,
        mock_score_docs, mock_filter, sample_dataset_documents
    ):
        """Test score_indicator with callable unit function."""
        
        # Setup mocks
        mock_convert.return_value = sample_dataset_documents
        mock_validate.validate_dataset_list.return_value = None
        mock_drop.return_value = (sample_dataset_documents, [])
        mock_group.return_value = [{"IndicatorCode": "IND1"}]
        mock_score_docs.return_value = [{"Score": 0.8}]
        mock_filter.return_value = ([{"Score": 0.8}], [])
        
        # Callable unit function
        def unit_func(ds1, ds2=None):
            return "Dynamic Unit"
        
        def score_func(ds1, ds2=None):
            return 0.8
        
        # Execute
        result = score_indicator(
            sample_dataset_documents,
            "IND1", 
            score_func,
            unit_func
        )
        
        # Verify unit function is passed through
        mock_score_docs.assert_called_once_with(
            [{"IndicatorCode": "IND1"}], 
            score_func, 
            unit_func
        )
    
    @patch('sspi_flask_app.api.resources.utilities.filter_incomplete_data')
    @patch('sspi_flask_app.api.resources.utilities.score_indicator_documents')
    @patch('sspi_flask_app.api.resources.utilities.group_by_indicator')
    @patch('sspi_flask_app.api.resources.utilities.drop_none_or_na')
    @patch('sspi_flask_app.api.resources.utilities.sspi_clean_api_data')
    @patch('sspi_flask_app.api.resources.utilities.convert_data_types')
    def test_score_indicator_with_empty_dataset_list(
        self, mock_convert, mock_validate, mock_drop, mock_group,
        mock_score_docs, mock_filter, sample_score_function
    ):
        """Test score_indicator with empty dataset list."""
        
        # Setup mocks for empty processing
        mock_convert.return_value = []
        mock_validate.validate_dataset_list.return_value = None
        mock_drop.return_value = ([], [])
        mock_group.return_value = []
        mock_score_docs.return_value = []
        mock_filter.return_value = ([], [])
        
        # Execute
        result = score_indicator([], "IND1", sample_score_function, "Unit")
        
        # Should handle empty list gracefully
        assert result == ([], [])
        
        # All functions should still be called
        mock_convert.assert_called_once_with([])
        mock_validate.validate_dataset_list.assert_called_once_with([])
    
    @patch('sspi_flask_app.api.resources.utilities.filter_incomplete_data')
    @patch('sspi_flask_app.api.resources.utilities.score_indicator_documents')
    @patch('sspi_flask_app.api.resources.utilities.group_by_indicator')
    @patch('sspi_flask_app.api.resources.utilities.drop_none_or_na')
    @patch('sspi_flask_app.api.resources.utilities.sspi_clean_api_data')
    @patch('sspi_flask_app.api.resources.utilities.convert_data_types')
    def test_score_indicator_realistic_scenario(
        self, mock_convert, mock_validate, mock_drop, mock_group,
        mock_score_docs, mock_filter
    ):
        """Test score_indicator with realistic SSPI data."""
        
        # Realistic dataset documents
        realistic_datasets = [
            {
                "DatasetCode": "UNESC_PRIM",
                "CountryCode": "USA",
                "Year": "2020",
                "Value": "95.2",
                "Unit": "Percentage"
            },
            {
                "DatasetCode": "UNESC_SEC", 
                "CountryCode": "USA",
                "Year": "2020",
                "Value": "87.5",
                "Unit": "Percentage"
            }
        ]
        
        # Setup realistic processing chain
        converted = [
            {"DatasetCode": "UNESC_PRIM", "Year": 2020, "Value": 95.2},
            {"DatasetCode": "UNESC_SEC", "Year": 2020, "Value": 87.5}
        ]
        mock_convert.return_value = converted
        mock_validate.validate_dataset_list.return_value = None
        mock_drop.return_value = (converted, [])
        
        grouped = [
            {
                "IndicatorCode": "EDUACC",
                "CountryCode": "USA", 
                "Year": 2020,
                "Datasets": [
                    {"DatasetCode": "UNESC_PRIM", "Value": 95.2},
                    {"DatasetCode": "UNESC_SEC", "Value": 87.5}
                ]
            }
        ]
        mock_group.return_value = grouped
        
        scored = [
            {
                "IndicatorCode": "EDUACC",
                "CountryCode": "USA",
                "Year": 2020, 
                "Score": 0.852,
                "Unit": "SSPI Score",
                "Datasets": [
                    {"DatasetCode": "UNESC_PRIM", "Value": 95.2},
                    {"DatasetCode": "UNESC_SEC", "Value": 87.5}
                ]
            }
        ]
        mock_score_docs.return_value = scored
        mock_filter.return_value = (scored, [])
        
        # Realistic score function (average of primary and secondary education)
        def education_score(unesc_prim, unesc_sec):
            return (unesc_prim + unesc_sec) / 200.0
        
        # Execute
        result = score_indicator(
            realistic_datasets,
            "EDUACC",
            education_score,
            "SSPI Score"
        )
        
        # Verify result
        assert result == (scored, [])
        
        # Verify score function is passed correctly
        mock_score_docs.assert_called_once_with(grouped, education_score, "SSPI Score")
    
    @patch('sspi_flask_app.api.resources.utilities.filter_incomplete_data')
    @patch('sspi_flask_app.api.resources.utilities.score_indicator_documents')
    @patch('sspi_flask_app.api.resources.utilities.group_by_indicator')
    @patch('sspi_flask_app.api.resources.utilities.drop_none_or_na')
    @patch('sspi_flask_app.api.resources.utilities.sspi_clean_api_data')
    @patch('sspi_flask_app.api.resources.utilities.convert_data_types')
    def test_score_indicator_with_data_cleaning(
        self, mock_convert, mock_validate, mock_drop, mock_group,
        mock_score_docs, mock_filter, sample_score_function
    ):
        """Test score_indicator handles data cleaning properly."""
        
        # Setup mocks to simulate data cleaning
        mock_convert.return_value = [{"Year": 2020, "Value": 100.0}]
        mock_validate.validate_dataset_list.return_value = None
        
        # Simulate some data being dropped
        cleaned_data = [{"Year": 2020, "Value": 100.0}]
        dropped_data = [{"Year": 2020, "Value": None}]  # None values dropped
        mock_drop.return_value = (cleaned_data, dropped_data)
        
        mock_group.return_value = [{"IndicatorCode": "IND1"}]
        mock_score_docs.return_value = [{"Score": 0.8}]
        mock_filter.return_value = ([{"Score": 0.8}], [])
        
        # Execute
        result = score_indicator(
            [{"Value": "100.0"}, {"Value": None}],
            "IND1",
            sample_score_function,
            "Unit"
        )
        
        # Verify cleaned data is used for grouping (not original)
        mock_group.assert_called_once_with(cleaned_data, "IND1")
    
    @patch('sspi_flask_app.api.resources.utilities.filter_incomplete_data')
    @patch('sspi_flask_app.api.resources.utilities.score_indicator_documents')
    @patch('sspi_flask_app.api.resources.utilities.group_by_indicator')
    @patch('sspi_flask_app.api.resources.utilities.drop_none_or_na')
    @patch('sspi_flask_app.api.resources.utilities.sspi_clean_api_data')
    @patch('sspi_flask_app.api.resources.utilities.convert_data_types')
    def test_score_indicator_validation_integration(
        self, mock_convert, mock_validate, mock_drop, mock_group,
        mock_score_docs, mock_filter, sample_dataset_documents, sample_score_function
    ):
        """Test that dataset validation is properly integrated."""
        
        # Setup mocks
        mock_convert.return_value = sample_dataset_documents
        mock_validate.validate_dataset_list.return_value = None  # Validation passes
        mock_drop.return_value = (sample_dataset_documents, [])
        mock_group.return_value = [{"IndicatorCode": "IND1"}]
        mock_score_docs.return_value = [{"Score": 0.8}]
        mock_filter.return_value = ([{"Score": 0.8}], [])
        
        # Execute
        score_indicator(
            sample_dataset_documents,
            "IND1", 
            sample_score_function,
            "Unit"
        )
        
        # Verify validation is called with converted data
        mock_validate.validate_dataset_list.assert_called_once_with(sample_dataset_documents)
    
    @patch('sspi_flask_app.api.resources.utilities.filter_incomplete_data')
    @patch('sspi_flask_app.api.resources.utilities.score_indicator_documents')
    @patch('sspi_flask_app.api.resources.utilities.group_by_indicator')
    @patch('sspi_flask_app.api.resources.utilities.drop_none_or_na')
    @patch('sspi_flask_app.api.resources.utilities.sspi_clean_api_data')
    @patch('sspi_flask_app.api.resources.utilities.convert_data_types')
    def test_score_indicator_error_propagation(
        self, mock_convert, mock_validate, mock_drop, mock_group,
        mock_score_docs, mock_filter, sample_score_function
    ):
        """Test that errors from sub-functions are properly propagated."""
        
        # Test validation error
        mock_convert.return_value = []
        mock_validate.validate_dataset_list.side_effect = ValueError("Invalid dataset")
        
        with pytest.raises(ValueError, match="Invalid dataset"):
            score_indicator([], "IND1", sample_score_function, "Unit")
        
        # Test conversion error  
        mock_validate.validate_dataset_list.side_effect = None
        mock_convert.side_effect = TypeError("Conversion failed")
        
        with pytest.raises(TypeError, match="Conversion failed"):
            score_indicator([], "IND1", sample_score_function, "Unit")
    
    @patch('sspi_flask_app.api.resources.utilities.filter_incomplete_data')
    @patch('sspi_flask_app.api.resources.utilities.score_indicator_documents')
    @patch('sspi_flask_app.api.resources.utilities.group_by_indicator')
    @patch('sspi_flask_app.api.resources.utilities.drop_none_or_na')
    @patch('sspi_flask_app.api.resources.utilities.sspi_clean_api_data')
    @patch('sspi_flask_app.api.resources.utilities.convert_data_types')
    def test_score_indicator_different_indicator_codes(
        self, mock_convert, mock_validate, mock_drop, mock_group,
        mock_score_docs, mock_filter, sample_dataset_documents, sample_score_function
    ):
        """Test score_indicator with different indicator codes."""
        
        # Setup mocks
        mock_convert.return_value = sample_dataset_documents
        mock_validate.validate_dataset_list.return_value = None
        mock_drop.return_value = (sample_dataset_documents, [])
        mock_group.return_value = [{"IndicatorCode": "CUSTOM_IND"}]
        mock_score_docs.return_value = [{"Score": 0.8}]
        mock_filter.return_value = ([{"Score": 0.8}], [])
        
        # Test with different indicator codes
        indicator_codes = ["EDUACC", "HLTHOUT", "GOVEFF", "ECOFREE", "CUSTOM123"]
        
        for indicator_code in indicator_codes:
            score_indicator(
                sample_dataset_documents,
                indicator_code,
                sample_score_function,
                "Unit"
            )
            
            # Verify correct indicator code is passed to grouping
            mock_group.assert_called_with(sample_dataset_documents, indicator_code)
    
    @patch('sspi_flask_app.api.resources.utilities.filter_incomplete_data')
    @patch('sspi_flask_app.api.resources.utilities.score_indicator_documents') 
    @patch('sspi_flask_app.api.resources.utilities.group_by_indicator')
    @patch('sspi_flask_app.api.resources.utilities.drop_none_or_na')
    @patch('sspi_flask_app.api.resources.utilities.sspi_clean_api_data')
    @patch('sspi_flask_app.api.resources.utilities.convert_data_types')
    def test_score_indicator_complex_score_functions(
        self, mock_convert, mock_validate, mock_drop, mock_group,
        mock_score_docs, mock_filter, sample_dataset_documents
    ):
        """Test score_indicator with complex score functions."""
        
        # Setup mocks
        mock_convert.return_value = sample_dataset_documents
        mock_validate.validate_dataset_list.return_value = None
        mock_drop.return_value = (sample_dataset_documents, [])
        mock_group.return_value = [{"IndicatorCode": "IND1"}]
        mock_score_docs.return_value = [{"Score": 0.8}]
        mock_filter.return_value = ([{"Score": 0.8}], [])
        
        # Complex score function with multiple parameters
        def complex_score_func(primary_ed, secondary_ed, tertiary_ed, literacy_rate):
            weights = [0.3, 0.3, 0.25, 0.15]
            values = [primary_ed, secondary_ed, tertiary_ed, literacy_rate]
            return sum(w * v for w, v in zip(weights, values)) / 100.0
        
        # Execute with complex function
        score_indicator(
            sample_dataset_documents,
            "COMPLEX_IND",
            complex_score_func,
            "Weighted Score"
        )
        
        # Verify complex function is passed through
        mock_score_docs.assert_called_once_with(
            [{"IndicatorCode": "IND1"}],
            complex_score_func,
            "Weighted Score"
        )
    
    @patch('sspi_flask_app.api.resources.utilities.filter_incomplete_data')
    @patch('sspi_flask_app.api.resources.utilities.score_indicator_documents')
    @patch('sspi_flask_app.api.resources.utilities.group_by_indicator')
    @patch('sspi_flask_app.api.resources.utilities.drop_none_or_na')
    @patch('sspi_flask_app.api.resources.utilities.sspi_clean_api_data')
    @patch('sspi_flask_app.api.resources.utilities.convert_data_types')
    def test_score_indicator_return_value_structure(
        self, mock_convert, mock_validate, mock_drop, mock_group,
        mock_score_docs, mock_filter, sample_dataset_documents, sample_score_function
    ):
        """Test that score_indicator returns the correct structure."""
        
        # Setup mocks
        mock_convert.return_value = sample_dataset_documents
        mock_validate.validate_dataset_list.return_value = None
        mock_drop.return_value = (sample_dataset_documents, [])
        mock_group.return_value = [{"IndicatorCode": "IND1"}]
        mock_score_docs.return_value = [{"Score": 0.8}]
        
        # Mock filter_incomplete_data to return tuple
        complete_data = [{"IndicatorCode": "IND1", "Score": 0.8, "Unit": "Score"}]
        incomplete_data = [{"IndicatorCode": "IND1", "CountryCode": "USA"}] 
        mock_filter.return_value = (complete_data, incomplete_data)
        
        # Execute
        result = score_indicator(
            sample_dataset_documents,
            "IND1",
            sample_score_function,
            "Score"
        )
        
        # Verify return value is exactly what filter_incomplete_data returns
        assert result == (complete_data, incomplete_data)
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], list)  # Complete data
        assert isinstance(result[1], list)  # Incomplete data
    
    @patch('sspi_flask_app.api.resources.utilities.filter_incomplete_data')
    @patch('sspi_flask_app.api.resources.utilities.score_indicator_documents')
    @patch('sspi_flask_app.api.resources.utilities.group_by_indicator')
    @patch('sspi_flask_app.api.resources.utilities.drop_none_or_na')
    @patch('sspi_flask_app.api.resources.utilities.sspi_clean_api_data')
    @patch('sspi_flask_app.api.resources.utilities.convert_data_types')
    def test_score_indicator_execution_order(
        self, mock_convert, mock_validate, mock_drop, mock_group,
        mock_score_docs, mock_filter, sample_dataset_documents, sample_score_function
    ):
        """Test that score_indicator executes functions in correct order."""
        
        # Use side_effect to track call order
        call_order = []
        
        def track_convert(data):
            call_order.append('convert')
            return data
        
        def track_validate(data):
            call_order.append('validate')
            
        def track_drop(data):
            call_order.append('drop')
            return (data, [])
        
        def track_group(data, code):
            call_order.append('group')
            return [{"IndicatorCode": code}]
        
        def track_score(data, func, unit):
            call_order.append('score')
            return [{"Score": 0.8}]
        
        def track_filter(data):
            call_order.append('filter')
            return (data, [])
        
        # Setup side effects
        mock_convert.side_effect = track_convert
        mock_validate.validate_dataset_list.side_effect = track_validate
        mock_drop.side_effect = track_drop
        mock_group.side_effect = track_group
        mock_score_docs.side_effect = track_score
        mock_filter.side_effect = track_filter
        
        # Execute
        score_indicator(
            sample_dataset_documents,
            "IND1",
            sample_score_function,
            "Unit"
        )
        
        # Verify execution order
        expected_order = ['convert', 'validate', 'drop', 'group', 'score', 'filter']
        assert call_order == expected_order