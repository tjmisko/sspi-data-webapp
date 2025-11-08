import pytest
from sspi_flask_app.api.resources.utilities import lookup_database
from sspi_flask_app.models.errors import InvalidDatabaseError
from sspi_flask_app.models.database import (
    sspi_metadata,
    sspi_static_metadata,
    sspi_static_data_2018,
    sspi_raw_api_data,
    sspi_clean_api_data,
    sspi_indicator_data,
    sspi_incomplete_indicator_data,
    sspi_imputed_data,
    sspi_analysis,
    sspi_item_data,
    sspi_static_rank_data,
    sspi_static_radar_data,
    sspi_item_dynamic_line_data,
    sspi_indicator_dynamic_line_data,
    sspi_dynamic_matrix_data,
    sspi_panel_data,
)


def test_lookup_database_valid_databases():
    """Test that all valid database names return the correct database objects."""
    
    # Test all supported database names with their expected objects
    valid_databases = {
        "sspi_metadata": sspi_metadata,
        "sspi_static_metadata": sspi_static_metadata,
        "sspi_static_data_2018": sspi_static_data_2018,
        "sspi_raw_api_data": sspi_raw_api_data,
        "sspi_clean_api_data": sspi_clean_api_data,
        "sspi_indicator_data": sspi_indicator_data,
        "sspi_incomplete_indicator_data": sspi_incomplete_indicator_data,
        "sspi_imputed_data": sspi_imputed_data,
        "sspi_analysis": sspi_analysis,
        "sspi_item_data": sspi_item_data,
        "sspi_static_rank_data": sspi_static_rank_data,
        "sspi_static_radar_data": sspi_static_radar_data,
        "sspi_item_dynamic_line_data": sspi_item_dynamic_line_data,
        "sspi_indicator_dynamic_line_data": sspi_indicator_dynamic_line_data,
        "sspi_dynamic_matrix_data": sspi_dynamic_matrix_data,
        "sspi_panel_data": sspi_panel_data,
    }
    
    for db_name, expected_db in valid_databases.items():
        result = lookup_database(db_name)
        assert result is expected_db, f"Expected {expected_db} for {db_name}, got {result}"


def test_lookup_database_invalid_database_raises_error():
    """Test that invalid database names raise InvalidDatabaseError."""
    
    invalid_names = [
        "invalid_database",
        "sspi_nonexistent",
        "random_name",
        "",
        "SSPI_METADATA",  # case sensitive
        "sspi_metadata_typo",
        None,
        123,
    ]
    
    for invalid_name in invalid_names:
        with pytest.raises(InvalidDatabaseError):
            lookup_database(invalid_name)


def test_lookup_database_case_sensitivity():
    """Test that database lookup is case sensitive."""
    
    # Test that uppercase versions don't work
    case_variations = [
        "SSPI_METADATA",
        "Sspi_Metadata",
        "sspi_METADATA",
        "SSPI_MAIN_DATA_V3",
    ]
    
    for case_variant in case_variations:
        with pytest.raises(InvalidDatabaseError):
            lookup_database(case_variant)


def test_lookup_database_whitespace_handling():
    """Test that whitespace in database names is not handled gracefully."""
    
    whitespace_variations = [
        " sspi_metadata",
        "sspi_metadata ",
        " sspi_metadata ",
        "sspi_metadata\n",
        "sspi_metadata\t",
        "sspi metadata",  # space instead of underscore
    ]
    
    for whitespace_variant in whitespace_variations:
        with pytest.raises(InvalidDatabaseError):
            lookup_database(whitespace_variant)


def test_lookup_database_similar_names():
    """Test that similar but incorrect database names raise errors."""
    
    similar_names = [
        "sspi_meta_data",  # underscore instead of no space
        "sspi_metedata",   # typo
        "sspi_metdata",    # missing letter
        "sspi_raw_data",   # missing 'api'
        "sspi_clean_data", # missing 'api'
        "sspi_item_data_dynamic", # wrong order
        "sspi_data_item",  # wrong order
    ]
    
    for similar_name in similar_names:
        with pytest.raises(InvalidDatabaseError):
            lookup_database(similar_name)


def test_lookup_database_returns_same_instance():
    """Test that multiple calls to lookup_database return the same instance."""
    
    # Test that we get the same instance on multiple calls
    db1 = lookup_database("sspi_metadata")
    db2 = lookup_database("sspi_metadata")
    assert db1 is db2, "Multiple calls should return the same instance"
    
    # Test with another database
    db3 = lookup_database("sspi_raw_api_data")
    db4 = lookup_database("sspi_raw_api_data")
    assert db3 is db4, "Multiple calls should return the same instance"
    
    # Ensure different databases return different instances
    assert db1 is not db3, "Different databases should return different instances"


def test_lookup_database_all_imports_accessible():
    """Test that all imported database objects are accessible through lookup_database."""
    
    # Ensure we can access all the imported database objects
    all_databases = [
        "sspi_metadata",
        "sspi_static_metadata", 
        "sspi_static_data_2018",
        "sspi_raw_api_data",
        "sspi_clean_api_data",
        "sspi_indicator_data",
        "sspi_incomplete_indicator_data",
        "sspi_imputed_data",
        "sspi_analysis",
        "sspi_item_data",
        "sspi_static_rank_data",
        "sspi_static_radar_data",
        "sspi_item_dynamic_line_data",
        "sspi_indicator_dynamic_line_data",
        "sspi_dynamic_matrix_data",
        "sspi_panel_data",
    ]
    
    for db_name in all_databases:
        # Should not raise an exception
        result = lookup_database(db_name)
        assert result is not None, f"Database {db_name} should return a non-None object"
