import pytest
from sspi_flask_app.api.resources.utilities import impute_global_average


@pytest.fixture
def sample_ref_data():
    """Sample reference data for testing."""
    return [
        {"Value": 10.0, "Score": 0.8, "Unit": "Percentage"},
        {"Value": 15.0, "Score": 0.9, "Unit": "Percentage"},
        {"Value": 5.0, "Score": 0.7, "Unit": "Percentage"},
        {"Value": 20.0, "Score": 0.95, "Unit": "Percentage"},
    ]


def test_impute_global_average_basic_functionality(sample_ref_data):
    """Test basic global average imputation functionality."""
    
    result = impute_global_average(
        country_code="USA",
        start_year=2020,
        end_year=2022,
        item_type="Dataset",
        item_code="TEST_DATASET",
        ref_data=sample_ref_data
    )
    
    # Should return documents for each year in range
    assert len(result) == 3  # 2020, 2021, 2022
    
    # Calculate expected averages
    expected_mean_value = sum([x["Value"] for x in sample_ref_data]) / len(sample_ref_data)
    expected_mean_score = sum([x["Score"] for x in sample_ref_data]) / len(sample_ref_data)
    
    for i, doc in enumerate(result):
        expected_year = 2020 + i
        
        # Check document structure
        required_fields = ["CountryCode", "Value", "Score", "Year", "Unit", 
                          "Imputed", "ImputationMethod", "DatasetCode"]
        for field in required_fields:
            assert field in doc, f"Missing field {field}"
        
        # Check values
        assert doc["CountryCode"] == "USA"
        assert doc["Year"] == expected_year
        assert doc["Value"] == expected_mean_value
        assert doc["Score"] == expected_mean_score
        assert doc["Unit"] == "Percentage"
        assert doc["Imputed"] is True
        assert doc["ImputationMethod"] == "ImputeGlobalAverage"
        assert doc["DatasetCode"] == "TEST_DATASET"


def test_impute_global_average_indicator_type(sample_ref_data):
    """Test imputation with item_type='Indicator'."""
    
    result = impute_global_average(
        country_code="CAN",
        start_year=2021,
        end_year=2021,
        item_type="Indicator",
        item_code="TEST_INDICATOR",
        ref_data=sample_ref_data
    )
    
    assert len(result) == 1
    doc = result[0]
    
    # Should have IndicatorCode instead of DatasetCode
    assert "IndicatorCode" in doc
    assert "DatasetCode" not in doc
    assert doc["IndicatorCode"] == "TEST_INDICATOR"
    assert doc["CountryCode"] == "CAN"
    assert doc["Year"] == 2021


def test_impute_global_average_single_year():
    """Test imputation for a single year (start_year == end_year)."""
    
    ref_data = [
        {"Value": 100.0, "Score": 0.5, "Unit": "Index"},
        {"Value": 200.0, "Score": 0.7, "Unit": "Index"},
    ]
    
    result = impute_global_average(
        country_code="GBR",
        start_year=2023,
        end_year=2023,
        item_type="Dataset",
        item_code="SINGLE_YEAR",
        ref_data=ref_data
    )
    
    assert len(result) == 1
    doc = result[0]
    assert doc["Year"] == 2023
    assert doc["Value"] == 150.0  # (100 + 200) / 2
    assert doc["Score"] == 0.6    # (0.5 + 0.7) / 2


def test_impute_global_average_multiple_years():
    """Test imputation across multiple years."""
    
    ref_data = [
        {"Value": 50.0, "Score": 0.4, "Unit": "Points"},
        {"Value": 60.0, "Score": 0.6, "Unit": "Points"},
    ]
    
    result = impute_global_average(
        country_code="FRA",
        start_year=2015,
        end_year=2020,
        item_type="Indicator",
        item_code="MULTI_YEAR",
        ref_data=ref_data
    )
    
    assert len(result) == 6  # 2015-2020 inclusive
    
    expected_years = list(range(2015, 2021))
    actual_years = [doc["Year"] for doc in result]
    assert actual_years == expected_years
    
    # All documents should have same imputed values
    for doc in result:
        assert doc["Value"] == 55.0  # (50 + 60) / 2
        assert doc["Score"] == 0.5   # (0.4 + 0.6) / 2
        assert doc["CountryCode"] == "FRA"
        assert doc["IndicatorCode"] == "MULTI_YEAR"


def test_impute_global_average_inconsistent_units():
    """Test that inconsistent units raise an error."""
    
    inconsistent_ref_data = [
        {"Value": 10.0, "Score": 0.8, "Unit": "Percentage"},
        {"Value": 15.0, "Score": 0.9, "Unit": "Index"},  # Different unit
        {"Value": 5.0, "Score": 0.7, "Unit": "Percentage"},
    ]
    
    with pytest.raises(ValueError) as exc_info:
        impute_global_average(
            country_code="DEU",
            start_year=2020,
            end_year=2021,
            item_type="Dataset",
            item_code="INCONSISTENT",
            ref_data=inconsistent_ref_data
        )
    
    assert "Units are not consistent" in str(exc_info.value)


def test_impute_global_average_invalid_item_type():
    """Test that invalid item_type raises an error."""
    
    ref_data = [
        {"Value": 10.0, "Score": 0.8, "Unit": "Percentage"},
    ]
    
    invalid_types = ["DataSet", "INDICATOR", "item", "data", "indicator", "Category", ""]
    
    for invalid_type in invalid_types:
        with pytest.raises(ValueError) as exc_info:
            impute_global_average(
                country_code="JPN",
                start_year=2020,
                end_year=2020,
                item_type=invalid_type,
                item_code="INVALID_TYPE",
                ref_data=ref_data
            )
        
        assert "item_type must be either 'Dataset' or 'Indicator'" in str(exc_info.value)


def test_impute_global_average_empty_ref_data():
    """Test behavior with empty reference data."""
    
    with pytest.raises(ZeroDivisionError):
        impute_global_average(
            country_code="BRA",
            start_year=2020,
            end_year=2020,
            item_type="Dataset",
            item_code="EMPTY_REF",
            ref_data=[]
        )


def test_impute_global_average_single_ref_point():
    """Test imputation with single reference data point."""
    
    single_ref_data = [
        {"Value": 42.0, "Score": 0.75, "Unit": "Score"}
    ]
    
    result = impute_global_average(
        country_code="IND",
        start_year=2019,
        end_year=2021,
        item_type="Indicator",
        item_code="SINGLE_REF",
        ref_data=single_ref_data
    )
    
    assert len(result) == 3  # 2019, 2020, 2021
    
    for doc in result:
        assert doc["Value"] == 42.0
        assert doc["Score"] == 0.75
        assert doc["Unit"] == "Score"


def test_impute_global_average_extreme_values():
    """Test imputation with extreme reference values."""
    
    extreme_ref_data = [
        {"Value": 0.0, "Score": 0.0, "Unit": "Scale"},
        {"Value": 1000000.0, "Score": 1.0, "Unit": "Scale"},
        {"Value": -500.0, "Score": 0.2, "Unit": "Scale"},
    ]
    
    result = impute_global_average(
        country_code="CHN",
        start_year=2020,
        end_year=2020,
        item_type="Dataset",
        item_code="EXTREME",
        ref_data=extreme_ref_data
    )
    
    doc = result[0]
    expected_mean_value = (0.0 + 1000000.0 + (-500.0)) / 3
    expected_mean_score = (0.0 + 1.0 + 0.2) / 3
    
    assert abs(doc["Value"] - expected_mean_value) < 1e-10
    assert abs(doc["Score"] - expected_mean_score) < 1e-10


def test_impute_global_average_floating_point_precision():
    """Test that floating point calculations are handled correctly."""
    
    precision_ref_data = [
        {"Value": 1.0/3.0, "Score": 1.0/7.0, "Unit": "Ratio"},
        {"Value": 2.0/3.0, "Score": 2.0/7.0, "Unit": "Ratio"},
        {"Value": 1.0, "Score": 3.0/7.0, "Unit": "Ratio"},
    ]
    
    result = impute_global_average(
        country_code="RUS",
        start_year=2020,
        end_year=2020,
        item_type="Indicator",
        item_code="PRECISION",
        ref_data=precision_ref_data
    )
    
    doc = result[0]
    expected_mean_value = (1.0/3.0 + 2.0/3.0 + 1.0) / 3
    expected_mean_score = (1.0/7.0 + 2.0/7.0 + 3.0/7.0) / 3
    
    assert abs(doc["Value"] - expected_mean_value) < 1e-15
    assert abs(doc["Score"] - expected_mean_score) < 1e-15


def test_impute_global_average_reverse_year_range():
    """Test behavior when start_year > end_year."""
    
    ref_data = [
        {"Value": 10.0, "Score": 0.5, "Unit": "Test"}
    ]
    
    # Should return empty list for reverse range
    result = impute_global_average(
        country_code="AUS",
        start_year=2022,
        end_year=2020,  # Earlier than start_year
        item_type="Dataset",
        item_code="REVERSE",
        ref_data=ref_data
    )
    
    assert len(result) == 0


def test_impute_global_average_zero_values():
    """Test imputation with zero values in reference data."""
    
    zero_ref_data = [
        {"Value": 0.0, "Score": 0.0, "Unit": "Zero"},
        {"Value": 0.0, "Score": 0.0, "Unit": "Zero"},
        {"Value": 0.0, "Score": 0.0, "Unit": "Zero"},
    ]
    
    result = impute_global_average(
        country_code="NOR",
        start_year=2021,
        end_year=2022,
        item_type="Indicator",
        item_code="ZEROS",
        ref_data=zero_ref_data
    )
    
    assert len(result) == 2
    
    for doc in result:
        assert doc["Value"] == 0.0
        assert doc["Score"] == 0.0


def test_impute_global_average_negative_values():
    """Test imputation with negative values in reference data."""
    
    negative_ref_data = [
        {"Value": -10.0, "Score": 0.3, "Unit": "Negative"},
        {"Value": -5.0, "Score": 0.4, "Unit": "Negative"},
        {"Value": -15.0, "Score": 0.2, "Unit": "Negative"},
    ]
    
    result = impute_global_average(
        country_code="SWE",
        start_year=2020,
        end_year=2020,
        item_type="Dataset",
        item_code="NEGATIVE",
        ref_data=negative_ref_data
    )
    
    doc = result[0]
    assert doc["Value"] == -10.0  # (-10 + -5 + -15) / 3
    assert doc["Score"] == 0.3    # (0.3 + 0.4 + 0.2) / 3


def test_impute_global_average_large_year_range():
    """Test imputation across a large year range."""
    
    ref_data = [
        {"Value": 100.0, "Score": 0.8, "Unit": "Large"}
    ]
    
    result = impute_global_average(
        country_code="MEX",
        start_year=2000,
        end_year=2023,  # 24 years
        item_type="Indicator",
        item_code="LARGE_RANGE",
        ref_data=ref_data
    )
    
    assert len(result) == 24  # 2000-2023 inclusive
    
    # Check first and last years
    assert result[0]["Year"] == 2000
    assert result[-1]["Year"] == 2023
    
    # All should have same imputed values
    for doc in result:
        assert doc["Value"] == 100.0
        assert doc["Score"] == 0.8


def test_impute_global_average_special_country_codes():
    """Test imputation with special country codes."""
    
    ref_data = [
        {"Value": 50.0, "Score": 0.5, "Unit": "Special"}
    ]
    
    special_codes = ["XKX", "EU-28", "OECD", "WLD", "LDC"]
    
    for country_code in special_codes:
        result = impute_global_average(
            country_code=country_code,
            start_year=2020,
            end_year=2020,
            item_type="Dataset",
            item_code="SPECIAL",
            ref_data=ref_data
        )
        
        assert len(result) == 1
        assert result[0]["CountryCode"] == country_code


def test_impute_global_average_mixed_data_types():
    """Test that function handles mixed numeric types in reference data."""
    
    mixed_ref_data = [
        {"Value": 10, "Score": 0.8, "Unit": "Mixed"},      # int
        {"Value": 15.5, "Score": 0.9, "Unit": "Mixed"},    # float
        {"Value": 5.0, "Score": 0.7, "Unit": "Mixed"},     # float
    ]
    
    result = impute_global_average(
        country_code="ESP",
        start_year=2020,
        end_year=2020,
        item_type="Indicator",
        item_code="MIXED",
        ref_data=mixed_ref_data
    )
    
    doc = result[0]
    expected_mean_value = (10 + 15.5 + 5.0) / 3
    expected_mean_score = (0.8 + 0.9 + 0.7) / 3
    
    assert abs(doc["Value"] - expected_mean_value) < 1e-10
    assert abs(doc["Score"] - expected_mean_score) < 1e-10


def test_impute_global_average_unit_preservation():
    """Test that the unit from reference data is preserved."""
    
    ref_data = [
        {"Value": 25.0, "Score": 0.6, "Unit": "CustomUnit"},
        {"Value": 35.0, "Score": 0.8, "Unit": "CustomUnit"},
    ]
    
    result = impute_global_average(
        country_code="ITA",
        start_year=2019,
        end_year=2021,
        item_type="Dataset",
        item_code="UNIT_TEST",
        ref_data=ref_data
    )
    
    for doc in result:
        assert doc["Unit"] == "CustomUnit"


def test_impute_global_average_metadata_consistency():
    """Test that imputation metadata is consistent across all documents."""
    
    ref_data = [
        {"Value": 75.0, "Score": 0.85, "Unit": "Metadata"}
    ]
    
    result = impute_global_average(
        country_code="POL",
        start_year=2018,
        end_year=2022,
        item_type="Indicator",
        item_code="METADATA",
        ref_data=ref_data
    )
    
    for doc in result:
        assert doc["Imputed"] is True
        assert doc["ImputationMethod"] == "ImputeGlobalAverage"
        assert doc["CountryCode"] == "POL"
        assert doc["IndicatorCode"] == "METADATA"
        assert "DatasetCode" not in doc  # Should not exist for Indicator type


def test_impute_global_average_ref_data_with_missing_fields():
    """Test behavior when reference data is missing required fields."""
    
    # Missing Value field
    incomplete_ref_data = [
        {"Score": 0.8, "Unit": "Incomplete"},
        {"Value": 10.0, "Score": 0.7, "Unit": "Incomplete"},
    ]
    
    with pytest.raises(KeyError):
        impute_global_average(
            country_code="TUR",
            start_year=2020,
            end_year=2020,
            item_type="Dataset",
            item_code="INCOMPLETE",
            ref_data=incomplete_ref_data
        )


def test_impute_global_average_realistic_scenario():
    """Test imputation with realistic SSPI-like data."""
    
    # Realistic reference data for education access indicator
    realistic_ref_data = [
        {"Value": 85.2, "Score": 0.852, "Unit": "Percentage"},  # High-income country
        {"Value": 92.8, "Score": 0.928, "Unit": "Percentage"},  # Nordic country
        {"Value": 78.5, "Score": 0.785, "Unit": "Percentage"},  # Middle-income country
        {"Value": 95.1, "Score": 0.951, "Unit": "Percentage"},  # Best performer
        {"Value": 73.9, "Score": 0.739, "Unit": "Percentage"},  # Lower performer
    ]
    
    result = impute_global_average(
        country_code="LKA",  # Sri Lanka
        start_year=2020,
        end_year=2023,
        item_type="Indicator",
        item_code="EDUACC",  # Education Access
        ref_data=realistic_ref_data
    )
    
    assert len(result) == 4  # 2020-2023
    
    # Calculate expected averages
    expected_value = sum([x["Value"] for x in realistic_ref_data]) / len(realistic_ref_data)
    expected_score = sum([x["Score"] for x in realistic_ref_data]) / len(realistic_ref_data)
    
    for doc in result:
        assert doc["CountryCode"] == "LKA"
        assert doc["IndicatorCode"] == "EDUACC"
        assert doc["Unit"] == "Percentage"
        assert abs(doc["Value"] - expected_value) < 1e-10
        assert abs(doc["Score"] - expected_score) < 1e-10
        assert doc["Imputed"] is True
        assert doc["ImputationMethod"] == "ImputeGlobalAverage"
        assert 2020 <= doc["Year"] <= 2023