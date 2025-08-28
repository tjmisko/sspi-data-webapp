import pytest
from sspi_flask_app.api.resources.utilities import generate_series_groups


@pytest.fixture
def sample_data():
    """Sample data for testing series grouping."""
    return [
        {
            "CountryCode": "USA",
            "Year": 2020,
            "Value": 100.0,
            "Score": 0.8,
            "IndicatorCode": "IND1",
            "Unit": "Percentage"
        },
        {
            "CountryCode": "CAN",
            "Year": 2020,
            "Value": 95.0,
            "Score": 0.75,
            "IndicatorCode": "IND1",
            "Unit": "Percentage"
        },
        {
            "CountryCode": "USA",
            "Year": 2021,
            "Value": 105.0,
            "Score": 0.85,
            "IndicatorCode": "IND1",
            "Unit": "Percentage"
        },
        {
            "CountryCode": "USA",
            "Year": 2020,
            "Value": 200.0,
            "Score": 0.9,
            "IndicatorCode": "IND2",
            "Unit": "Index"
        }
    ]


def test_generate_series_groups_basic_functionality(sample_data):
    """Test basic series grouping functionality."""
    
    result = generate_series_groups(sample_data)
    
    # Should group by non-excluded fields (IndicatorCode and Unit in this case)
    assert len(result) >= 1
    
    for group in result:
        # Each group should have required structure
        assert "Datasets" in group
        assert "Identifier" in group
        assert isinstance(group["Datasets"], dict)
        assert isinstance(group["Identifier"], dict)
        
        # Datasets should contain country-specific data
        for country_code, observations in group["Datasets"].items():
            assert isinstance(observations, list)
            for obs in observations:
                required_fields = ["entity_id", "time_id", "value_id", "score_id"]
                for field in required_fields:
                    assert field in obs


def test_generate_series_groups_custom_field_names():
    """Test series grouping with custom field names."""
    
    custom_data = [
        {
            "Nation": "USA",
            "Period": 2020,
            "Amount": 100.0,
            "Rating": 0.8,
            "Category": "Health"
        },
        {
            "Nation": "CAN",
            "Period": 2020,
            "Amount": 95.0,
            "Rating": 0.75,
            "Category": "Health"
        }
    ]
    
    result = generate_series_groups(
        data=custom_data,
        entity_id="Nation",
        value_id="Amount",
        time_id="Period",
        score_id="Rating"
    )
    
    assert len(result) == 1  # Should group by Category
    
    group = result[0]
    assert group["Identifier"]["Category"] == "Health"
    
    # Check that custom field names are used in datasets
    for country, observations in group["Datasets"].items():
        for obs in observations:
            assert obs["entity_id"] in ["USA", "CAN"]
            assert obs["time_id"] == 2020
            assert obs["value_id"] in [100.0, 95.0]
            assert obs["score_id"] in [0.8, 0.75]


def test_generate_series_groups_exclude_fields():
    """Test series grouping with excluded fields."""
    
    data_with_extra_fields = [
        {
            "CountryCode": "USA",
            "Year": 2020,
            "Value": 100.0,
            "Score": 0.8,
            "IndicatorCode": "IND1",
            "Unit": "Percentage",
            "Source": "WorldBank",
            "Notes": "Estimated"
        },
        {
            "CountryCode": "CAN",
            "Year": 2020,
            "Value": 95.0,
            "Score": 0.75,
            "IndicatorCode": "IND1",
            "Unit": "Percentage",
            "Source": "IMF",  # Different source
            "Notes": "Estimated"
        }
    ]
    
    # Exclude Source field from grouping
    result = generate_series_groups(
        data=data_with_extra_fields,
        exclude_fields=["Source"]
    )
    
    # Should group by IndicatorCode, Unit, and Notes (Source excluded)
    assert len(result) == 1
    
    group = result[0]
    assert "Source" not in group["Identifier"]  # Source should be excluded
    assert group["Identifier"]["IndicatorCode"] == "IND1"
    assert group["Identifier"]["Unit"] == "Percentage"
    assert group["Identifier"]["Notes"] == "Estimated"


def test_generate_series_groups_multiple_series():
    """Test grouping data with multiple distinct series."""
    
    multi_series_data = [
        # Series 1: Health indicators in percentage
        {
            "CountryCode": "USA",
            "Year": 2020,
            "Value": 85.0,
            "Score": 0.85,
            "Category": "Health",
            "Unit": "Percentage"
        },
        {
            "CountryCode": "CAN",
            "Year": 2020,
            "Value": 90.0,
            "Score": 0.9,
            "Category": "Health",
            "Unit": "Percentage"
        },
        # Series 2: Education indicators in index
        {
            "CountryCode": "USA",
            "Year": 2020,
            "Value": 7.5,
            "Score": 0.75,
            "Category": "Education",
            "Unit": "Index"
        },
        {
            "CountryCode": "CAN",
            "Year": 2020,
            "Value": 8.0,
            "Score": 0.8,
            "Category": "Education",
            "Unit": "Index"
        }
    ]
    
    result = generate_series_groups(multi_series_data)
    
    # Should create 2 groups (Health/Percentage and Education/Index)
    assert len(result) == 2
    
    # Find health and education groups
    health_group = next((g for g in result if g["Identifier"]["Category"] == "Health"), None)
    education_group = next((g for g in result if g["Identifier"]["Category"] == "Education"), None)
    
    assert health_group is not None
    assert education_group is not None
    
    assert health_group["Identifier"]["Unit"] == "Percentage"
    assert education_group["Identifier"]["Unit"] == "Index"
    
    # Both groups should have USA and CAN data
    assert "USA" in health_group["Datasets"]
    assert "CAN" in health_group["Datasets"]
    assert "USA" in education_group["Datasets"]
    assert "CAN" in education_group["Datasets"]


def test_generate_series_groups_empty_data():
    """Test series grouping with empty data."""
    
    result = generate_series_groups([])
    
    assert result == []


def test_generate_series_groups_single_observation():
    """Test series grouping with single observation."""
    
    single_data = [
        {
            "CountryCode": "USA",
            "Year": 2020,
            "Value": 100.0,
            "Score": 0.8,
            "Type": "Test"
        }
    ]
    
    result = generate_series_groups(single_data)
    
    assert len(result) == 1
    
    group = result[0]
    assert group["Identifier"]["Type"] == "Test"
    assert "USA" in group["Datasets"]
    assert len(group["Datasets"]["USA"]) == 1
    
    obs = group["Datasets"]["USA"][0]
    assert obs["entity_id"] == "USA"
    assert obs["time_id"] == 2020
    assert obs["value_id"] == 100.0
    assert obs["score_id"] == 0.8


def test_generate_series_groups_list_values_excluded():
    """Test that list values are excluded from grouping identifiers."""
    
    data_with_lists = [
        {
            "CountryCode": "USA",
            "Year": 2020,
            "Value": 100.0,
            "Score": 0.8,
            "Type": "Test",
            "Sources": ["WorldBank", "IMF"],  # List value
            "Tags": ["economic", "social"]    # List value
        },
        {
            "CountryCode": "CAN", 
            "Year": 2020,
            "Value": 95.0,
            "Score": 0.75,
            "Type": "Test",
            "Sources": ["OECD"],              # Different list
            "Tags": ["economic"]              # Different list
        }
    ]
    
    result = generate_series_groups(data_with_lists)
    
    # Should group only by Type (lists excluded)
    assert len(result) == 1
    
    group = result[0]
    assert group["Identifier"]["Type"] == "Test"
    assert "Sources" not in group["Identifier"]
    assert "Tags" not in group["Identifier"]


def test_generate_series_groups_missing_default_fields():
    """Test behavior when default field names are missing."""
    
    data_missing_defaults = [
        {
            "Nation": "USA",
            "Period": 2020,
            "Category": "Health"
            # Missing CountryCode, Year, Value, Score
        }
    ]
    
    # Should raise KeyError when required entity_id field is missing
    with pytest.raises(KeyError):
        generate_series_groups(data_missing_defaults)


def test_generate_series_groups_duplicate_observations():
    """Test grouping with duplicate observations."""
    
    duplicate_data = [
        {
            "CountryCode": "USA",
            "Year": 2020,
            "Value": 100.0,
            "Score": 0.8,
            "Type": "Test"
        },
        {
            "CountryCode": "USA",
            "Year": 2020,
            "Value": 100.0,
            "Score": 0.8,
            "Type": "Test"
        }
    ]
    
    result = generate_series_groups(duplicate_data)
    
    assert len(result) == 1
    
    group = result[0]
    assert "USA" in group["Datasets"]
    # Should have both observations even if duplicate
    assert len(group["Datasets"]["USA"]) == 2


def test_generate_series_groups_multiple_years_same_country():
    """Test grouping with multiple years for same country."""
    
    multi_year_data = [
        {
            "CountryCode": "USA",
            "Year": 2020,
            "Value": 100.0,
            "Score": 0.8,
            "Type": "Economic"
        },
        {
            "CountryCode": "USA",
            "Year": 2021,
            "Value": 105.0,
            "Score": 0.85,
            "Type": "Economic"
        },
        {
            "CountryCode": "USA",
            "Year": 2022,
            "Value": 110.0,
            "Score": 0.9,
            "Type": "Economic"
        }
    ]
    
    result = generate_series_groups(multi_year_data)
    
    assert len(result) == 1
    
    group = result[0]
    assert group["Identifier"]["Type"] == "Economic"
    assert "USA" in group["Datasets"]
    assert len(group["Datasets"]["USA"]) == 3
    
    # Check that all years are present
    years = [obs["time_id"] for obs in group["Datasets"]["USA"]]
    assert sorted(years) == [2020, 2021, 2022]


def test_generate_series_groups_complex_identifiers():
    """Test grouping with complex identifier combinations."""
    
    complex_data = [
        {
            "CountryCode": "USA",
            "Year": 2020,
            "Value": 100.0,
            "Score": 0.8,
            "Sector": "Health",
            "SubSector": "Primary",
            "DataSource": "WHO",
            "Methodology": "Survey"
        },
        {
            "CountryCode": "CAN",
            "Year": 2020,
            "Value": 95.0,
            "Score": 0.75,
            "Sector": "Health",
            "SubSector": "Primary",
            "DataSource": "WHO",
            "Methodology": "Survey"
        },
        {
            "CountryCode": "USA",
            "Year": 2020,
            "Value": 80.0,
            "Score": 0.7,
            "Sector": "Health",
            "SubSector": "Secondary",  # Different sub-sector
            "DataSource": "WHO",
            "Methodology": "Survey"
        }
    ]
    
    result = generate_series_groups(complex_data)
    
    # Should create 2 groups (Primary vs Secondary)
    assert len(result) == 2
    
    primary_group = next((g for g in result if g["Identifier"]["SubSector"] == "Primary"), None)
    secondary_group = next((g for g in result if g["Identifier"]["SubSector"] == "Secondary"), None)
    
    assert primary_group is not None
    assert secondary_group is not None
    
    # Primary group should have both USA and CAN
    assert "USA" in primary_group["Datasets"]
    assert "CAN" in primary_group["Datasets"]
    
    # Secondary group should have only USA
    assert "USA" in secondary_group["Datasets"]
    assert "CAN" not in secondary_group["Datasets"]


def test_generate_series_groups_none_values():
    """Test grouping with None values in identifiers."""
    
    none_data = [
        {
            "CountryCode": "USA",
            "Year": 2020,
            "Value": 100.0,
            "Score": 0.8,
            "Category": None,
            "Type": "Test"
        },
        {
            "CountryCode": "CAN",
            "Year": 2020,
            "Value": 95.0,
            "Score": 0.75,
            "Category": None,
            "Type": "Test"
        }
    ]
    
    result = generate_series_groups(none_data)
    
    assert len(result) == 1
    
    group = result[0]
    assert group["Identifier"]["Category"] is None
    assert group["Identifier"]["Type"] == "Test"


def test_generate_series_groups_numeric_identifiers():
    """Test grouping with numeric identifier values."""
    
    numeric_data = [
        {
            "CountryCode": "USA",
            "Year": 2020,
            "Value": 100.0,
            "Score": 0.8,
            "Priority": 1,
            "Level": 5.5
        },
        {
            "CountryCode": "CAN",
            "Year": 2020,
            "Value": 95.0,
            "Score": 0.75,
            "Priority": 1,
            "Level": 5.5
        }
    ]
    
    result = generate_series_groups(numeric_data)
    
    assert len(result) == 1
    
    group = result[0]
    assert group["Identifier"]["Priority"] == 1
    assert group["Identifier"]["Level"] == 5.5


def test_generate_series_groups_empty_string_values():
    """Test grouping with empty string values."""
    
    empty_string_data = [
        {
            "CountryCode": "USA",
            "Year": 2020,
            "Value": 100.0,
            "Score": 0.8,
            "Category": "",
            "Notes": "Valid"
        },
        {
            "CountryCode": "CAN",
            "Year": 2020,
            "Value": 95.0,
            "Score": 0.75,
            "Category": "",
            "Notes": "Valid"
        }
    ]
    
    result = generate_series_groups(empty_string_data)
    
    assert len(result) == 1
    
    group = result[0]
    assert group["Identifier"]["Category"] == ""
    assert group["Identifier"]["Notes"] == "Valid"


def test_generate_series_groups_field_order_consistency():
    """Test that field order in identifiers is consistent."""
    
    order_data = [
        {
            "CountryCode": "USA",
            "Year": 2020,
            "Value": 100.0,
            "Score": 0.8,
            "Z_Last": "z",
            "A_First": "a",
            "M_Middle": "m"
        }
    ]
    
    result = generate_series_groups(order_data)
    
    assert len(result) == 1
    
    group = result[0]
    # Check that all expected fields are present
    assert group["Identifier"]["A_First"] == "a"
    assert group["Identifier"]["M_Middle"] == "m"
    assert group["Identifier"]["Z_Last"] == "z"


def test_generate_series_groups_id_field_exclusion():
    """Test that _id field is properly excluded."""
    
    id_data = [
        {
            "_id": "ObjectId123",
            "CountryCode": "USA",
            "Year": 2020,
            "Value": 100.0,
            "Score": 0.8,
            "Type": "Test"
        }
    ]
    
    result = generate_series_groups(id_data)
    
    assert len(result) == 1
    
    group = result[0]
    assert "_id" not in group["Identifier"]
    assert group["Identifier"]["Type"] == "Test"


def test_generate_series_groups_large_dataset():
    """Test grouping with a larger dataset to verify performance."""
    
    large_data = []
    countries = ["USA", "CAN", "GBR", "FRA", "DEU"]
    years = list(range(2000, 2024))
    categories = ["Health", "Education", "Environment"]
    
    for country in countries:
        for year in years:
            for category in categories:
                large_data.append({
                    "CountryCode": country,
                    "Year": year,
                    "Value": 50.0 + hash(f"{country}{year}{category}") % 50,
                    "Score": 0.5 + (hash(f"{country}{year}{category}") % 50) / 100,
                    "Category": category,
                    "Unit": "Index"
                })
    
    result = generate_series_groups(large_data)
    
    # Should create 3 groups (one for each category)
    assert len(result) == 3
    
    for group in result:
        assert group["Identifier"]["Category"] in categories
        assert group["Identifier"]["Unit"] == "Index"
        
        # Each group should have data for all countries
        assert len(group["Datasets"]) == 5  # 5 countries
        
        # Each country should have data for all years
        for country_data in group["Datasets"].values():
            assert len(country_data) == 24  # 24 years


def test_generate_series_groups_realistic_sspi_scenario():
    """Test grouping with realistic SSPI-like data structure."""
    
    sspi_data = [
        # Education Access - Primary
        {
            "CountryCode": "USA",
            "Year": 2020,
            "Value": 95.2,
            "Score": 0.952,
            "IndicatorCode": "EDUACC",
            "PillarCode": "SUS",
            "CategoryCode": "EDU",
            "Unit": "Percentage",
            "DataSource": "UNESCO",
            "Level": "Primary"
        },
        {
            "CountryCode": "FRA",
            "Year": 2020,
            "Value": 98.1,
            "Score": 0.981,
            "IndicatorCode": "EDUACC",
            "PillarCode": "SUS",
            "CategoryCode": "EDU",
            "Unit": "Percentage",
            "DataSource": "UNESCO",
            "Level": "Primary"
        },
        # Education Access - Secondary (different level)
        {
            "CountryCode": "USA",
            "Year": 2020,
            "Value": 87.5,
            "Score": 0.875,
            "IndicatorCode": "EDUACC",
            "PillarCode": "SUS",
            "CategoryCode": "EDU",
            "Unit": "Percentage",
            "DataSource": "UNESCO",
            "Level": "Secondary"
        },
        # Health Outcomes (different indicator)
        {
            "CountryCode": "USA",
            "Year": 2020,
            "Value": 78.9,
            "Score": 0.789,
            "IndicatorCode": "HLTHOUT",
            "PillarCode": "SUS",
            "CategoryCode": "HLT",
            "Unit": "Index",
            "DataSource": "WHO",
            "Level": "National"
        }
    ]
    
    result = generate_series_groups(sspi_data)
    
    # Should create groups based on all distinguishing fields
    # Different combinations: EDUACC+Primary, EDUACC+Secondary, HLTHOUT+National
    assert len(result) == 3
    
    # Find specific groups
    edu_primary = next((g for g in result 
                       if g["Identifier"]["IndicatorCode"] == "EDUACC" 
                       and g["Identifier"]["Level"] == "Primary"), None)
    
    edu_secondary = next((g for g in result 
                         if g["Identifier"]["IndicatorCode"] == "EDUACC" 
                         and g["Identifier"]["Level"] == "Secondary"), None)
    
    health = next((g for g in result 
                  if g["Identifier"]["IndicatorCode"] == "HLTHOUT"), None)
    
    assert edu_primary is not None
    assert edu_secondary is not None
    assert health is not None
    
    # Education primary should have both USA and FRA
    assert "USA" in edu_primary["Datasets"]
    assert "FRA" in edu_primary["Datasets"]
    
    # Education secondary should have only USA
    assert "USA" in edu_secondary["Datasets"]
    assert "FRA" not in edu_secondary["Datasets"]
    
    # Health should have only USA
    assert "USA" in health["Datasets"]
    assert "FRA" not in health["Datasets"]
    
    # Verify identifier fields are correctly preserved
    assert edu_primary["Identifier"]["PillarCode"] == "SUS"
    assert edu_primary["Identifier"]["CategoryCode"] == "EDU"
    assert edu_primary["Identifier"]["DataSource"] == "UNESCO"
    assert health["Identifier"]["CategoryCode"] == "HLT"
    assert health["Identifier"]["DataSource"] == "WHO"