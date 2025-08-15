import pytest
from sspi_flask_app.api.resources.utilities import group_by_indicator


def test_group_by_indicator_single_country_single_year():
    """Test grouping with single country and single year."""
    datasets = [
        {"DatasetCode": "DATASET_A", "CountryCode": "USA", "Year": 2020, "Value": 100},
        {"DatasetCode": "DATASET_B", "CountryCode": "USA", "Year": 2020, "Value": 200}
    ]
    
    result = group_by_indicator(datasets, "TEST_INDICATOR")
    
    assert len(result) == 1
    indicator_doc = result[0]
    
    assert indicator_doc["IndicatorCode"] == "TEST_INDICATOR"
    assert indicator_doc["CountryCode"] == "USA"
    assert indicator_doc["Year"] == 2020
    assert len(indicator_doc["Datasets"]) == 2
    assert indicator_doc["Datasets"][0]["DatasetCode"] == "DATASET_A"
    assert indicator_doc["Datasets"][1]["DatasetCode"] == "DATASET_B"


def test_group_by_indicator_multiple_countries():
    """Test grouping with multiple countries for same year."""
    datasets = [
        {"DatasetCode": "DATASET_A", "CountryCode": "USA", "Year": 2020, "Value": 100},
        {"DatasetCode": "DATASET_B", "CountryCode": "USA", "Year": 2020, "Value": 200},
        {"DatasetCode": "DATASET_A", "CountryCode": "CAN", "Year": 2020, "Value": 150},
        {"DatasetCode": "DATASET_B", "CountryCode": "CAN", "Year": 2020, "Value": 250}
    ]
    
    result = group_by_indicator(datasets, "MULTI_COUNTRY_INDICATOR")
    
    assert len(result) == 2
    
    # Find USA and CAN documents
    usa_doc = next(doc for doc in result if doc["CountryCode"] == "USA")
    can_doc = next(doc for doc in result if doc["CountryCode"] == "CAN")
    
    assert usa_doc["IndicatorCode"] == "MULTI_COUNTRY_INDICATOR"
    assert can_doc["IndicatorCode"] == "MULTI_COUNTRY_INDICATOR"
    assert len(usa_doc["Datasets"]) == 2
    assert len(can_doc["Datasets"]) == 2


def test_group_by_indicator_multiple_years():
    """Test grouping with multiple years for same country."""
    datasets = [
        {"DatasetCode": "DATASET_A", "CountryCode": "USA", "Year": 2019, "Value": 90},
        {"DatasetCode": "DATASET_B", "CountryCode": "USA", "Year": 2019, "Value": 190},
        {"DatasetCode": "DATASET_A", "CountryCode": "USA", "Year": 2020, "Value": 100},
        {"DatasetCode": "DATASET_B", "CountryCode": "USA", "Year": 2020, "Value": 200}
    ]
    
    result = group_by_indicator(datasets, "MULTI_YEAR_INDICATOR")
    
    assert len(result) == 2
    
    # Find 2019 and 2020 documents
    doc_2019 = next(doc for doc in result if doc["Year"] == 2019)
    doc_2020 = next(doc for doc in result if doc["Year"] == 2020)
    
    assert doc_2019["CountryCode"] == "USA"
    assert doc_2020["CountryCode"] == "USA"
    assert len(doc_2019["Datasets"]) == 2
    assert len(doc_2020["Datasets"]) == 2


def test_group_by_indicator_complex_grouping():
    """Test grouping with multiple countries and years."""
    datasets = [
        {"DatasetCode": "DATASET_A", "CountryCode": "USA", "Year": 2019, "Value": 90},
        {"DatasetCode": "DATASET_B", "CountryCode": "USA", "Year": 2019, "Value": 190},
        {"DatasetCode": "DATASET_A", "CountryCode": "USA", "Year": 2020, "Value": 100},
        {"DatasetCode": "DATASET_B", "CountryCode": "USA", "Year": 2020, "Value": 200},
        {"DatasetCode": "DATASET_A", "CountryCode": "CAN", "Year": 2019, "Value": 95},
        {"DatasetCode": "DATASET_B", "CountryCode": "CAN", "Year": 2019, "Value": 195},
        {"DatasetCode": "DATASET_A", "CountryCode": "CAN", "Year": 2020, "Value": 105},
        {"DatasetCode": "DATASET_B", "CountryCode": "CAN", "Year": 2020, "Value": 205}
    ]
    
    result = group_by_indicator(datasets, "COMPLEX_INDICATOR")
    
    assert len(result) == 4  # 2 countries × 2 years
    
    # Check that all combinations are present
    combinations = {(doc["CountryCode"], doc["Year"]) for doc in result}
    expected_combinations = {("USA", 2019), ("USA", 2020), ("CAN", 2019), ("CAN", 2020)}
    assert combinations == expected_combinations
    
    # Check that each group has the correct number of datasets
    assert all(len(doc["Datasets"]) == 2 for doc in result)


def test_group_by_indicator_empty_list():
    """Test grouping with empty dataset list."""
    datasets = []
    
    result = group_by_indicator(datasets, "EMPTY_INDICATOR")
    
    assert result == []


def test_group_by_indicator_single_dataset():
    """Test grouping with single dataset document."""
    datasets = [
        {"DatasetCode": "SINGLE_DATASET", "CountryCode": "USA", "Year": 2020, "Value": 100}
    ]
    
    result = group_by_indicator(datasets, "SINGLE_INDICATOR")
    
    assert len(result) == 1
    indicator_doc = result[0]
    
    assert indicator_doc["IndicatorCode"] == "SINGLE_INDICATOR"
    assert indicator_doc["CountryCode"] == "USA"
    assert indicator_doc["Year"] == 2020
    assert len(indicator_doc["Datasets"]) == 1
    assert indicator_doc["Datasets"][0]["DatasetCode"] == "SINGLE_DATASET"


def test_group_by_indicator_preserves_dataset_fields():
    """Test that grouping preserves all fields from original dataset documents."""
    datasets = [
        {
            "DatasetCode": "DATASET_A",
            "CountryCode": "USA",
            "Year": 2020,
            "Value": 100,
            "Unit": "Index",
            "Metadata": {"source": "test"},
            "Notes": "Test data"
        }
    ]
    
    result = group_by_indicator(datasets, "PRESERVE_FIELDS_INDICATOR")
    
    assert len(result) == 1
    dataset_in_group = result[0]["Datasets"][0]
    
    assert dataset_in_group["DatasetCode"] == "DATASET_A"
    assert dataset_in_group["CountryCode"] == "USA"
    assert dataset_in_group["Year"] == 2020
    assert dataset_in_group["Value"] == 100
    assert dataset_in_group["Unit"] == "Index"
    assert dataset_in_group["Metadata"] == {"source": "test"}
    assert dataset_in_group["Notes"] == "Test data"


def test_group_by_indicator_duplicate_datasets():
    """Test grouping with duplicate dataset documents."""
    datasets = [
        {"DatasetCode": "DATASET_A", "CountryCode": "USA", "Year": 2020, "Value": 100},
        {"DatasetCode": "DATASET_A", "CountryCode": "USA", "Year": 2020, "Value": 100},  # Duplicate
        {"DatasetCode": "DATASET_B", "CountryCode": "USA", "Year": 2020, "Value": 200}
    ]
    
    result = group_by_indicator(datasets, "DUPLICATE_INDICATOR")
    
    assert len(result) == 1
    indicator_doc = result[0]
    
    assert len(indicator_doc["Datasets"]) == 3  # Duplicates are preserved
    assert indicator_doc["Datasets"][0]["DatasetCode"] == "DATASET_A"
    assert indicator_doc["Datasets"][1]["DatasetCode"] == "DATASET_A"
    assert indicator_doc["Datasets"][2]["DatasetCode"] == "DATASET_B"


def test_group_by_indicator_different_dataset_same_group():
    """Test that datasets with same CountryCode_Year get grouped together."""
    datasets = [
        {"DatasetCode": "GDP", "CountryCode": "USA", "Year": 2020, "Value": 100},
        {"DatasetCode": "POPULATION", "CountryCode": "USA", "Year": 2020, "Value": 330},
        {"DatasetCode": "UNEMPLOYMENT", "CountryCode": "USA", "Year": 2020, "Value": 5.5}
    ]
    
    result = group_by_indicator(datasets, "ECONOMIC_INDICATOR")
    
    assert len(result) == 1
    indicator_doc = result[0]
    
    assert indicator_doc["CountryCode"] == "USA"
    assert indicator_doc["Year"] == 2020
    assert len(indicator_doc["Datasets"]) == 3
    
    dataset_codes = {ds["DatasetCode"] for ds in indicator_doc["Datasets"]}
    assert dataset_codes == {"GDP", "POPULATION", "UNEMPLOYMENT"}


def test_group_by_indicator_missing_required_fields():
    """Test grouping when required fields are missing."""
    
    # Missing CountryCode
    datasets_missing_country = [
        {"DatasetCode": "DATASET_A", "Year": 2020, "Value": 100}
    ]
    
    with pytest.raises(KeyError):
        group_by_indicator(datasets_missing_country, "MISSING_COUNTRY")
    
    # Missing Year
    datasets_missing_year = [
        {"DatasetCode": "DATASET_A", "CountryCode": "USA", "Value": 100}
    ]
    
    with pytest.raises(KeyError):
        group_by_indicator(datasets_missing_year, "MISSING_YEAR")


def test_group_by_indicator_different_data_types():
    """Test grouping with different data types for Year field."""
    datasets = [
        {"DatasetCode": "DATASET_A", "CountryCode": "USA", "Year": 2020, "Value": 100},  # int
        {"DatasetCode": "DATASET_B", "CountryCode": "USA", "Year": "2020", "Value": 200},  # string
        {"DatasetCode": "DATASET_C", "CountryCode": "USA", "Year": 2020.0, "Value": 300}  # float
    ]
    
    result = group_by_indicator(datasets, "MIXED_TYPES_INDICATOR")
    
    # String conversion in document_id means:
    # - int 2020 -> "USA_2020"
    # - string "2020" -> "USA_2020"  
    # - float 2020.0 -> "USA_2020.0"
    # So int and string will group together, float separately
    assert len(result) == 2  # int/string together, float separate
    
    # Check the actual groupings based on observed behavior
    # One group should have the int/string years (2 datasets)
    # One group should have the float year (1 dataset)
    dataset_counts = [len(doc["Datasets"]) for doc in result]
    dataset_counts.sort()
    assert dataset_counts == [1, 2], f"Expected [1, 2] datasets, got {dataset_counts}"


def test_group_by_indicator_very_large_dataset():
    """Test grouping with a large number of datasets."""
    datasets = []
    
    # Create datasets for 5 countries, 3 years, 4 datasets each
    countries = ["USA", "CAN", "GBR", "FRA", "DEU"]
    years = [2018, 2019, 2020]
    dataset_codes = ["DATASET_A", "DATASET_B", "DATASET_C", "DATASET_D"]
    
    for country in countries:
        for year in years:
            for dataset_code in dataset_codes:
                datasets.append({
                    "DatasetCode": dataset_code,
                    "CountryCode": country,
                    "Year": year,
                    "Value": 100
                })
    
    result = group_by_indicator(datasets, "LARGE_INDICATOR")
    
    assert len(result) == 15  # 5 countries × 3 years
    assert all(len(doc["Datasets"]) == 4 for doc in result)  # 4 datasets per group
    assert all(doc["IndicatorCode"] == "LARGE_INDICATOR" for doc in result)


def test_group_by_indicator_special_country_codes():
    """Test grouping with special country codes and characters."""
    datasets = [
        {"DatasetCode": "DATASET_A", "CountryCode": "USA", "Year": 2020, "Value": 100},
        {"DatasetCode": "DATASET_B", "CountryCode": "EU-28", "Year": 2020, "Value": 200},
        {"DatasetCode": "DATASET_C", "CountryCode": "XK", "Year": 2020, "Value": 300},  # Kosovo
        {"DatasetCode": "DATASET_D", "CountryCode": "TWN", "Year": 2020, "Value": 400}  # Taiwan
    ]
    
    result = group_by_indicator(datasets, "SPECIAL_COUNTRIES_INDICATOR")
    
    assert len(result) == 4  # Each country should get its own group
    
    country_codes = {doc["CountryCode"] for doc in result}
    assert country_codes == {"USA", "EU-28", "XK", "TWN"}


def test_group_by_indicator_negative_years():
    """Test grouping with negative year values."""
    datasets = [
        {"DatasetCode": "DATASET_A", "CountryCode": "HIST", "Year": -100, "Value": 50},
        {"DatasetCode": "DATASET_B", "CountryCode": "HIST", "Year": -100, "Value": 60},
        {"DatasetCode": "DATASET_A", "CountryCode": "HIST", "Year": -50, "Value": 70}
    ]
    
    result = group_by_indicator(datasets, "HISTORICAL_INDICATOR")
    
    assert len(result) == 2  # Two different years: -100 and -50
    
    years = {doc["Year"] for doc in result}
    assert years == {-100, -50}
    
    # Year -100 should have 2 datasets, year -50 should have 1
    year_neg100_doc = next(doc for doc in result if doc["Year"] == -100)
    year_neg50_doc = next(doc for doc in result if doc["Year"] == -50)
    
    assert len(year_neg100_doc["Datasets"]) == 2
    assert len(year_neg50_doc["Datasets"]) == 1


def test_group_by_indicator_document_id_uniqueness():
    """Test that document IDs are correctly formed and unique."""
    datasets = [
        {"DatasetCode": "DATASET_A", "CountryCode": "US_A", "Year": 2020, "Value": 100},
        {"DatasetCode": "DATASET_B", "CountryCode": "USA", "Year": 2_020, "Value": 200},  # Underscore in year
    ]
    
    result = group_by_indicator(datasets, "ID_TEST_INDICATOR")
    
    # These should create different groups due to different document IDs
    assert len(result) == 2
    
    # Check that the document IDs would be "US_A_2020" and "USA_2_020" 
    country_codes = {doc["CountryCode"] for doc in result}
    assert "US_A" in country_codes
    assert "USA" in country_codes