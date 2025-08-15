import pytest
import pandas as pd
import json
from unittest.mock import patch, MagicMock
from sspi_flask_app.api.resources.utilities import jsonify_df


@pytest.fixture
def sample_dataframe():
    """Sample DataFrame for testing."""
    return pd.DataFrame({
        'Country': ['USA', 'CAN', 'GBR'],
        'Year': [2020, 2020, 2020],
        'Value': [100.0, 95.0, 90.0],
        'Score': [0.8, 0.75, 0.7]
    })


@patch('sspi_flask_app.api.resources.utilities.jsonify')
def test_jsonify_df_basic_functionality(mock_jsonify, sample_dataframe):
    """Test basic DataFrame to JSON conversion."""
    
    # Mock the jsonify function to return a simple response
    mock_response = MagicMock()
    mock_jsonify.return_value = mock_response
    
    result = jsonify_df(sample_dataframe)
    
    # Verify jsonify was called once
    mock_jsonify.assert_called_once()
    
    # Get the argument passed to jsonify
    args, kwargs = mock_jsonify.call_args
    jsonified_data = args[0]
    
    # Verify the structure
    assert isinstance(jsonified_data, list), "Should convert to list of records"
    assert len(jsonified_data) == 3, "Should have 3 records"
    
    # Verify the first record
    first_record = jsonified_data[0]
    expected_keys = {'Country', 'Year', 'Value', 'Score'}
    assert set(first_record.keys()) == expected_keys, "Should have all DataFrame columns"
    
    assert first_record['Country'] == 'USA'
    assert first_record['Year'] == 2020
    assert first_record['Value'] == 100.0
    assert first_record['Score'] == 0.8
    
    # Verify the result is what jsonify returned
    assert result == mock_response


@patch('sspi_flask_app.api.resources.utilities.jsonify')
def test_jsonify_df_empty_dataframe(mock_jsonify):
    """Test conversion of empty DataFrame."""
    
    empty_df = pd.DataFrame()
    mock_response = MagicMock()
    mock_jsonify.return_value = mock_response
    
    result = jsonify_df(empty_df)
    
    mock_jsonify.assert_called_once()
    args, kwargs = mock_jsonify.call_args
    jsonified_data = args[0]
    
    assert jsonified_data == [], "Empty DataFrame should convert to empty list"
    assert result == mock_response


@patch('sspi_flask_app.api.resources.utilities.jsonify')
def test_jsonify_df_single_row(mock_jsonify):
    """Test conversion of single-row DataFrame."""
    
    single_row_df = pd.DataFrame({
        'ID': [1],
        'Name': ['Test'],
        'Active': [True]
    })
    
    mock_response = MagicMock()
    mock_jsonify.return_value = mock_response
    
    result = jsonify_df(single_row_df)
    
    mock_jsonify.assert_called_once()
    args, kwargs = mock_jsonify.call_args
    jsonified_data = args[0]
    
    assert len(jsonified_data) == 1
    record = jsonified_data[0]
    assert record['ID'] == 1
    assert record['Name'] == 'Test'
    assert record['Active'] is True


@patch('sspi_flask_app.api.resources.utilities.jsonify')
def test_jsonify_df_single_column(mock_jsonify):
    """Test conversion of single-column DataFrame."""
    
    single_col_df = pd.DataFrame({
        'Values': [1, 2, 3, 4, 5]
    })
    
    mock_response = MagicMock()
    mock_jsonify.return_value = mock_response
    
    result = jsonify_df(single_col_df)
    
    mock_jsonify.assert_called_once()
    args, kwargs = mock_jsonify.call_args
    jsonified_data = args[0]
    
    assert len(jsonified_data) == 5
    for i, record in enumerate(jsonified_data):
        assert record['Values'] == i + 1


@patch('sspi_flask_app.api.resources.utilities.jsonify')
def test_jsonify_df_mixed_data_types(mock_jsonify):
    """Test conversion with mixed data types."""
    
    mixed_df = pd.DataFrame({
        'Integer': [1, 2, 3],
        'Float': [1.1, 2.2, 3.3],
        'String': ['A', 'B', 'C'],
        'Boolean': [True, False, True],
        'Null': [None, 'Value', None]
    })
    
    mock_response = MagicMock()
    mock_jsonify.return_value = mock_response
    
    result = jsonify_df(mixed_df)
    
    mock_jsonify.assert_called_once()
    args, kwargs = mock_jsonify.call_args
    jsonified_data = args[0]
    
    first_record = jsonified_data[0]
    assert first_record['Integer'] == 1
    assert first_record['Float'] == 1.1
    assert first_record['String'] == 'A'
    assert first_record['Boolean'] is True
    assert first_record['Null'] is None


@patch('sspi_flask_app.api.resources.utilities.jsonify')
def test_jsonify_df_nan_values(mock_jsonify):
    """Test conversion with NaN values."""
    
    nan_df = pd.DataFrame({
        'A': [1, float('nan'), 3],
        'B': ['X', 'Y', 'Z']
    })
    
    mock_response = MagicMock()
    mock_jsonify.return_value = mock_response
    
    result = jsonify_df(nan_df)
    
    mock_jsonify.assert_called_once()
    args, kwargs = mock_jsonify.call_args
    jsonified_data = args[0]
    
    # pandas to_json converts NaN to null in JSON
    assert jsonified_data[0]['A'] == 1
    assert jsonified_data[1]['A'] is None  # NaN becomes null/None
    assert jsonified_data[2]['A'] == 3


@patch('sspi_flask_app.api.resources.utilities.jsonify')
def test_jsonify_df_datetime_columns(mock_jsonify):
    """Test conversion with datetime columns."""
    
    datetime_df = pd.DataFrame({
        'Date': pd.to_datetime(['2020-01-01', '2020-02-01', '2020-03-01']),
        'Value': [10, 20, 30]
    })
    
    mock_response = MagicMock()
    mock_jsonify.return_value = mock_response
    
    result = jsonify_df(datetime_df)
    
    mock_jsonify.assert_called_once()
    args, kwargs = mock_jsonify.call_args
    jsonified_data = args[0]
    
    # Dates should be converted to timestamps (milliseconds since epoch)
    first_record = jsonified_data[0]
    assert 'Date' in first_record
    assert 'Value' in first_record
    assert first_record['Value'] == 10


@patch('sspi_flask_app.api.resources.utilities.jsonify')
def test_jsonify_df_special_column_names(mock_jsonify):
    """Test conversion with special column names."""
    
    special_df = pd.DataFrame({
        'Column With Spaces': [1, 2],
        'Column-With-Dashes': [3, 4],
        'Column_With_Underscores': [5, 6],
        '123NumericStart': [7, 8],
        'åéîøü': [9, 10]  # Unicode characters
    })
    
    mock_response = MagicMock()
    mock_jsonify.return_value = mock_response
    
    result = jsonify_df(special_df)
    
    mock_jsonify.assert_called_once()
    args, kwargs = mock_jsonify.call_args
    jsonified_data = args[0]
    
    first_record = jsonified_data[0]
    assert first_record['Column With Spaces'] == 1
    assert first_record['Column-With-Dashes'] == 3
    assert first_record['Column_With_Underscores'] == 5
    assert first_record['123NumericStart'] == 7
    assert first_record['åéîøü'] == 9


@patch('sspi_flask_app.api.resources.utilities.jsonify')
def test_jsonify_df_large_dataframe(mock_jsonify):
    """Test conversion with a larger DataFrame."""
    
    # Create a larger DataFrame
    import numpy as np
    large_df = pd.DataFrame({
        'ID': range(100),
        'Random': np.random.rand(100),
        'Category': ['Cat' + str(i % 5) for i in range(100)]
    })
    
    mock_response = MagicMock()
    mock_jsonify.return_value = mock_response
    
    result = jsonify_df(large_df)
    
    mock_jsonify.assert_called_once()
    args, kwargs = mock_jsonify.call_args
    jsonified_data = args[0]
    
    assert len(jsonified_data) == 100
    assert all('ID' in record for record in jsonified_data)
    assert all('Random' in record for record in jsonified_data)
    assert all('Category' in record for record in jsonified_data)


@patch('sspi_flask_app.api.resources.utilities.jsonify')
def test_jsonify_df_index_handling(mock_jsonify):
    """Test that DataFrame index is not included in JSON output."""
    
    # Create DataFrame with custom index
    df_with_index = pd.DataFrame({
        'Value': [1, 2, 3]
    }, index=['A', 'B', 'C'])
    
    mock_response = MagicMock()
    mock_jsonify.return_value = mock_response
    
    result = jsonify_df(df_with_index)
    
    mock_jsonify.assert_called_once()
    args, kwargs = mock_jsonify.call_args
    jsonified_data = args[0]
    
    # Index should not be included (orient="records" excludes index)
    for record in jsonified_data:
        assert 'A' not in record  # Index values should not be keys
        assert 'B' not in record
        assert 'C' not in record
        assert 'Value' in record  # Only actual columns


@patch('sspi_flask_app.api.resources.utilities.jsonify')
def test_jsonify_df_conversion_chain(mock_jsonify):
    """Test the complete conversion chain: DataFrame -> JSON string -> dict -> Flask response."""
    
    test_df = pd.DataFrame({
        'A': [1, 2],
        'B': ['X', 'Y']
    })
    
    mock_response = MagicMock()
    mock_jsonify.return_value = mock_response
    
    result = jsonify_df(test_df)
    
    # Verify the conversion chain worked
    mock_jsonify.assert_called_once()
    args, kwargs = mock_jsonify.call_args
    parsed_data = args[0]
    
    # Should be the result of json.loads(str(df.to_json(orient="records")))
    expected_structure = [
        {'A': 1, 'B': 'X'},
        {'A': 2, 'B': 'Y'}
    ]
    
    assert parsed_data == expected_structure


@patch('sspi_flask_app.api.resources.utilities.jsonify')
def test_jsonify_df_with_multiindex_columns(mock_jsonify):
    """Test conversion with MultiIndex columns."""
    
    # Create DataFrame with MultiIndex columns
    arrays = [['A', 'A', 'B', 'B'], ['X', 'Y', 'X', 'Y']]
    columns = pd.MultiIndex.from_arrays(arrays)
    multi_df = pd.DataFrame([[1, 2, 3, 4], [5, 6, 7, 8]], columns=columns)
    
    mock_response = MagicMock()
    mock_jsonify.return_value = mock_response
    
    result = jsonify_df(multi_df)
    
    mock_jsonify.assert_called_once()
    args, kwargs = mock_jsonify.call_args
    jsonified_data = args[0]
    
    # MultiIndex columns should be flattened in some way
    assert len(jsonified_data) == 2
    first_record = jsonified_data[0]
    assert len(first_record) == 4  # Should have 4 columns


def test_jsonify_df_invalid_input():
    """Test behavior with invalid input (not a DataFrame)."""
    
    invalid_inputs = [
        "not a dataframe",
        123,
        ['list', 'of', 'values'],
        {'dict': 'value'},
        None
    ]
    
    for invalid_input in invalid_inputs:
        with pytest.raises(AttributeError):
            # Should fail when trying to call .to_json() on non-DataFrame
            jsonify_df(invalid_input)


@patch('sspi_flask_app.api.resources.utilities.jsonify')
def test_jsonify_df_realistic_sspi_scenario(mock_jsonify):
    """Test with realistic SSPI-like DataFrame structure."""
    
    sspi_df = pd.DataFrame({
        'CountryCode': ['USA', 'CAN', 'GBR', 'FRA'],
        'CountryName': ['United States', 'Canada', 'United Kingdom', 'France'],
        'Year': [2020, 2020, 2020, 2020],
        'IndicatorCode': ['EDUACC', 'EDUACC', 'EDUACC', 'EDUACC'],
        'IndicatorName': ['Education Access'] * 4,
        'Value': [95.2, 98.1, 94.7, 96.8],
        'Score': [0.952, 0.981, 0.947, 0.968],
        'Unit': ['Percentage'] * 4,
        'DataSource': ['UNESCO'] * 4
    })
    
    mock_response = MagicMock()
    mock_jsonify.return_value = mock_response
    
    result = jsonify_df(sspi_df)
    
    mock_jsonify.assert_called_once()
    args, kwargs = mock_jsonify.call_args
    jsonified_data = args[0]
    
    assert len(jsonified_data) == 4
    
    usa_record = jsonified_data[0]
    expected_fields = {
        'CountryCode', 'CountryName', 'Year', 'IndicatorCode', 
        'IndicatorName', 'Value', 'Score', 'Unit', 'DataSource'
    }
    assert set(usa_record.keys()) == expected_fields
    
    assert usa_record['CountryCode'] == 'USA'
    assert usa_record['CountryName'] == 'United States'
    assert usa_record['Year'] == 2020
    assert usa_record['Value'] == 95.2
    assert usa_record['Score'] == 0.952


@patch('sspi_flask_app.api.resources.utilities.json')
@patch('sspi_flask_app.api.resources.utilities.jsonify')
def test_jsonify_df_json_parsing_error_handling(mock_jsonify, mock_json):
    """Test error handling in JSON parsing step."""
    
    test_df = pd.DataFrame({'A': [1, 2]})
    
    # Mock json.loads to raise an error
    mock_json.loads.side_effect = json.JSONDecodeError("Invalid JSON", "doc", 0)
    
    with pytest.raises(json.JSONDecodeError):
        jsonify_df(test_df)


@patch('sspi_flask_app.api.resources.utilities.jsonify')
def test_jsonify_df_preserves_data_precision(mock_jsonify):
    """Test that numeric precision is preserved through conversion."""
    
    precision_df = pd.DataFrame({
        'HighPrecision': [1.123456789123456789, 2.987654321987654321],
        'Scientific': [1.23e-15, 4.56e10],
        'Integer': [1234567890123456789, 9876543210987654321]
    })
    
    mock_response = MagicMock()
    mock_jsonify.return_value = mock_response
    
    result = jsonify_df(precision_df)
    
    mock_jsonify.assert_called_once()
    args, kwargs = mock_jsonify.call_args
    jsonified_data = args[0]
    
    # Check that values are preserved (within JSON precision limits)
    first_record = jsonified_data[0]
    assert 'HighPrecision' in first_record
    assert 'Scientific' in first_record
    assert 'Integer' in first_record