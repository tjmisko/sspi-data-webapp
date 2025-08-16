import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock
from sspi_flask_app.api.resources.utilities import regression_imputation


@pytest.fixture
def sample_feature_data():
    """Sample feature data for testing."""
    return [
        {"FeatureCode": "FEAT1", "CountryCode": "USA", "Year": 2020, "Score": 0.8},
        {"FeatureCode": "FEAT2", "CountryCode": "USA", "Year": 2020, "Score": 0.6},
        {"FeatureCode": "FEAT1", "CountryCode": "CAN", "Year": 2020, "Score": 0.7},
        {"FeatureCode": "FEAT2", "CountryCode": "CAN", "Year": 2020, "Score": 0.9},
        {"FeatureCode": "FEAT1", "CountryCode": "GBR", "Year": 2020, "Score": 0.5},
        {"FeatureCode": "FEAT2", "CountryCode": "GBR", "Year": 2020, "Score": 0.4},
    ]


@pytest.fixture
def sample_outcome_data():
    """Sample outcome data for testing."""
    return [
        {"IndicatorCode": "TARGET", "CountryCode": "USA", "Year": 2020, "Score": 0.75},
        {"IndicatorCode": "TARGET", "CountryCode": "CAN", "Year": 2020, "Score": 0.85},
        {"IndicatorCode": "TARGET", "CountryCode": "GBR", "Year": 2020, "Score": 0.45},
    ]


@pytest.fixture
def sample_predictor_data():
    """Sample predictor data for testing (includes unknown targets)."""
    return [
        {"FeatureCode": "FEAT1", "CountryCode": "USA", "Year": 2021, "Score": 0.8},
        {"FeatureCode": "FEAT2", "CountryCode": "USA", "Year": 2021, "Score": 0.6},
        {"FeatureCode": "FEAT1", "CountryCode": "FRA", "Year": 2020, "Score": 0.6},
        {"FeatureCode": "FEAT2", "CountryCode": "FRA", "Year": 2020, "Score": 0.7},
        {"FeatureCode": "FEAT1", "CountryCode": "DEU", "Year": 2020, "Score": 0.9},
        {"FeatureCode": "FEAT2", "CountryCode": "DEU", "Year": 2020, "Score": 0.8},
    ]


def test_regression_imputation_basic_functionality(sample_feature_data, sample_outcome_data, sample_predictor_data):
    """Test basic regression imputation functionality."""
    
    result = regression_imputation(
        feature_list=sample_feature_data,
        outcome_list=sample_outcome_data,
        predictor_list=sample_predictor_data,
        target_indicator="TARGET",
        unit="Score",
        model_string="TARGET ~ FEAT1 + FEAT2",
        details="Linear regression imputation using FEAT1 and FEAT2",
        lg=0,
        ug=1
    )
    
    # Should return documents for all predictor countries/years
    assert len(result) == 3  # USA 2021, FRA 2020, DEU 2020
    
    # Check document structure
    for doc in result:
        required_fields = ["CountryCode", "Year", "Score", "IndicatorCode", "Imputed", 
                          "ImputationMethod", "ImputationRegessionModel", "ImputationDetails",
                          "ImputationDistance", "LowerGoalpost", "UpperGoalpost", "Unit", "Value"]
        for field in required_fields:
            assert field in doc, f"Missing field {field}"
        
        assert doc["IndicatorCode"] == "TARGET"
        assert doc["Imputed"] is True
        assert doc["ImputationMethod"] == "RegressionImputation"
        assert doc["ImputationRegessionModel"] == "TARGET ~ FEAT1 + FEAT2"
        assert doc["ImputationDetails"] == "Linear regression imputation using FEAT1 and FEAT2"
        assert doc["ImputationDistance"] == 0
        assert doc["LowerGoalpost"] == 0
        assert doc["UpperGoalpost"] == 1
        assert doc["Unit"] == "Score"
        
        # Score should be clipped between 0 and 1
        assert 0 <= doc["Score"] <= 1
        
        # Value should be calculated from score and goalposts
        expected_value = (1 - 0) * doc["Score"] + 0
        assert abs(doc["Value"] - expected_value) < 1e-10


def test_regression_imputation_score_clipping():
    """Test that predicted scores are properly clipped to [0, 1] range."""
    
    # Create extreme feature data that might predict outside [0, 1]
    extreme_features = [
        {"FeatureCode": "FEAT1", "CountryCode": "LOW", "Year": 2020, "Score": 0.0},
        {"FeatureCode": "FEAT1", "CountryCode": "HIGH", "Year": 2020, "Score": 1.0},
    ]
    
    extreme_outcomes = [
        {"IndicatorCode": "TARGET", "CountryCode": "LOW", "Year": 2020, "Score": 0.0},
        {"IndicatorCode": "TARGET", "CountryCode": "HIGH", "Year": 2020, "Score": 1.0},
    ]
    
    # Predictor with very extreme values
    extreme_predictors = [
        {"FeatureCode": "FEAT1", "CountryCode": "EXTREME", "Year": 2021, "Score": 10.0},  # Very high
    ]
    
    result = regression_imputation(
        feature_list=extreme_features,
        outcome_list=extreme_outcomes,
        predictor_list=extreme_predictors,
        target_indicator="TARGET",
        unit="Score",
        model_string="TARGET ~ FEAT1",
        details="Test clipping",
        lg=0,
        ug=1
    )
    
    # Score should still be clipped to [0, 1]
    assert 0 <= result[0]["Score"] <= 1


def test_regression_imputation_custom_goalposts():
    """Test regression imputation with custom goalpost values."""
    
    feature_data = [
        {"FeatureCode": "FEAT1", "CountryCode": "USA", "Year": 2020, "Score": 0.5},
    ]
    
    outcome_data = [
        {"IndicatorCode": "TARGET", "CountryCode": "USA", "Year": 2020, "Score": 0.5},
    ]
    
    predictor_data = [
        {"FeatureCode": "FEAT1", "CountryCode": "CAN", "Year": 2020, "Score": 0.7},
    ]
    
    lg, ug = 10, 100  # Custom goalpost range
    
    result = regression_imputation(
        feature_list=feature_data,
        outcome_list=outcome_data,
        predictor_list=predictor_data,
        target_indicator="TARGET",
        unit="Custom Unit",
        model_string="TARGET ~ FEAT1",
        details="Custom goalpost test",
        lg=lg,
        ug=ug
    )
    
    assert result[0]["LowerGoalpost"] == lg
    assert result[0]["UpperGoalpost"] == ug
    assert result[0]["Unit"] == "Custom Unit"
    
    # Value should be calculated using custom goalposts
    score = result[0]["Score"]
    expected_value = (ug - lg) * score + lg
    assert abs(result[0]["Value"] - expected_value) < 1e-10


def test_regression_imputation_multiple_features():
    """Test regression with multiple feature codes."""
    
    multi_features = [
        {"FeatureCode": "FEAT1", "CountryCode": "USA", "Year": 2020, "Score": 0.8},
        {"FeatureCode": "FEAT2", "CountryCode": "USA", "Year": 2020, "Score": 0.6},
        {"FeatureCode": "FEAT3", "CountryCode": "USA", "Year": 2020, "Score": 0.4},
        {"FeatureCode": "FEAT1", "CountryCode": "CAN", "Year": 2020, "Score": 0.7},
        {"FeatureCode": "FEAT2", "CountryCode": "CAN", "Year": 2020, "Score": 0.9},
        {"FeatureCode": "FEAT3", "CountryCode": "CAN", "Year": 2020, "Score": 0.5},
    ]
    
    multi_outcomes = [
        {"IndicatorCode": "TARGET", "CountryCode": "USA", "Year": 2020, "Score": 0.6},
        {"IndicatorCode": "TARGET", "CountryCode": "CAN", "Year": 2020, "Score": 0.7},
    ]
    
    multi_predictors = [
        {"FeatureCode": "FEAT1", "CountryCode": "GBR", "Year": 2020, "Score": 0.5},
        {"FeatureCode": "FEAT2", "CountryCode": "GBR", "Year": 2020, "Score": 0.8},
        {"FeatureCode": "FEAT3", "CountryCode": "GBR", "Year": 2020, "Score": 0.3},
    ]
    
    result = regression_imputation(
        feature_list=multi_features,
        outcome_list=multi_outcomes,
        predictor_list=multi_predictors,
        target_indicator="TARGET",
        unit="Score",
        model_string="TARGET ~ FEAT1 + FEAT2 + FEAT3",
        details="Multiple features test"
    )
    
    assert len(result) == 1
    assert result[0]["CountryCode"] == "GBR"
    assert 0 <= result[0]["Score"] <= 1


def test_regression_imputation_multiple_years():
    """Test regression imputation across multiple years."""
    
    multi_year_features = [
        {"FeatureCode": "FEAT1", "CountryCode": "USA", "Year": 2019, "Score": 0.7},
        {"FeatureCode": "FEAT1", "CountryCode": "USA", "Year": 2020, "Score": 0.8},
        {"FeatureCode": "FEAT1", "CountryCode": "CAN", "Year": 2019, "Score": 0.6},
        {"FeatureCode": "FEAT1", "CountryCode": "CAN", "Year": 2020, "Score": 0.7},
    ]
    
    multi_year_outcomes = [
        {"IndicatorCode": "TARGET", "CountryCode": "USA", "Year": 2019, "Score": 0.65},
        {"IndicatorCode": "TARGET", "CountryCode": "USA", "Year": 2020, "Score": 0.75},
        {"IndicatorCode": "TARGET", "CountryCode": "CAN", "Year": 2019, "Score": 0.55},
        {"IndicatorCode": "TARGET", "CountryCode": "CAN", "Year": 2020, "Score": 0.65},
    ]
    
    multi_year_predictors = [
        {"FeatureCode": "FEAT1", "CountryCode": "GBR", "Year": 2019, "Score": 0.5},
        {"FeatureCode": "FEAT1", "CountryCode": "GBR", "Year": 2020, "Score": 0.6},
        {"FeatureCode": "FEAT1", "CountryCode": "FRA", "Year": 2021, "Score": 0.9},
    ]
    
    result = regression_imputation(
        feature_list=multi_year_features,
        outcome_list=multi_year_outcomes,
        predictor_list=multi_year_predictors,
        target_indicator="TARGET",
        unit="Score",
        model_string="TARGET ~ FEAT1",
        details="Multi-year test"
    )
    
    assert len(result) == 3  # GBR 2019, GBR 2020, FRA 2021
    
    # Check that years are preserved correctly
    countries_years = [(doc["CountryCode"], doc["Year"]) for doc in result]
    expected = [("GBR", 2019), ("GBR", 2020), ("FRA", 2021)]
    for expected_cy in expected:
        assert expected_cy in countries_years


def test_regression_imputation_missing_features_in_predictors():
    """Test behavior when predictor data is missing some features."""
    
    features = [
        {"FeatureCode": "FEAT1", "CountryCode": "USA", "Year": 2020, "Score": 0.8},
        {"FeatureCode": "FEAT2", "CountryCode": "USA", "Year": 2020, "Score": 0.6},
    ]
    
    outcomes = [
        {"IndicatorCode": "TARGET", "CountryCode": "USA", "Year": 2020, "Score": 0.7},
    ]
    
    # Predictor missing FEAT2
    incomplete_predictors = [
        {"FeatureCode": "FEAT1", "CountryCode": "CAN", "Year": 2020, "Score": 0.5},
        # Missing FEAT2 for CAN
    ]
    
    # Should raise ValueError due to NaN in prediction data
    with pytest.raises(ValueError) as exc_info:
        regression_imputation(
            feature_list=features,
            outcome_list=outcomes,
            predictor_list=incomplete_predictors,
            target_indicator="TARGET",
            unit="Score",
            model_string="TARGET ~ FEAT1 + FEAT2",
            details="Missing features test"
        )
    
    assert "NaN" in str(exc_info.value)


def test_regression_imputation_empty_inputs():
    """Test regression imputation with empty input lists."""
    
    # Test with empty feature list
    with pytest.raises((ValueError, KeyError, IndexError)):
        regression_imputation(
            feature_list=[],
            outcome_list=[{"IndicatorCode": "TARGET", "CountryCode": "USA", "Year": 2020, "Score": 0.5}],
            predictor_list=[{"FeatureCode": "FEAT1", "CountryCode": "CAN", "Year": 2020, "Score": 0.5}],
            target_indicator="TARGET",
            unit="Score",
            model_string="TARGET ~ FEAT1",
            details="Empty features test"
        )
    
    # Test with empty outcome list
    with pytest.raises((ValueError, KeyError, IndexError)):
        regression_imputation(
            feature_list=[{"FeatureCode": "FEAT1", "CountryCode": "USA", "Year": 2020, "Score": 0.5}],
            outcome_list=[],
            predictor_list=[{"FeatureCode": "FEAT1", "CountryCode": "CAN", "Year": 2020, "Score": 0.5}],
            target_indicator="TARGET",
            unit="Score",
            model_string="TARGET ~ FEAT1",
            details="Empty outcomes test"
        )


def test_regression_imputation_single_data_point():
    """Test regression with minimal data (single training point)."""
    
    single_feature = [
        {"FeatureCode": "FEAT1", "CountryCode": "USA", "Year": 2020, "Score": 0.8},
    ]
    
    single_outcome = [
        {"IndicatorCode": "TARGET", "CountryCode": "USA", "Year": 2020, "Score": 0.7},
    ]
    
    single_predictor = [
        {"FeatureCode": "FEAT1", "CountryCode": "CAN", "Year": 2020, "Score": 0.6},
    ]
    
    # This might work or fail depending on sklearn's handling of single points
    try:
        result = regression_imputation(
            feature_list=single_feature,
            outcome_list=single_outcome,
            predictor_list=single_predictor,
            target_indicator="TARGET",
            unit="Score",
            model_string="TARGET ~ FEAT1",
            details="Single point test"
        )
        
        assert len(result) == 1
        assert result[0]["CountryCode"] == "CAN"
        
    except (ValueError, np.linalg.LinAlgError):
        # Expected for insufficient data points
        pass


def test_regression_imputation_duplicate_country_year_predictors():
    """Test behavior with duplicate country-year combinations in predictors."""
    
    features = [
        {"FeatureCode": "FEAT1", "CountryCode": "USA", "Year": 2020, "Score": 0.8},
        {"FeatureCode": "FEAT1", "CountryCode": "CAN", "Year": 2020, "Score": 0.6},
    ]
    
    outcomes = [
        {"IndicatorCode": "TARGET", "CountryCode": "USA", "Year": 2020, "Score": 0.75},
        {"IndicatorCode": "TARGET", "CountryCode": "CAN", "Year": 2020, "Score": 0.65},
    ]
    
    duplicate_predictors = [
        {"FeatureCode": "FEAT1", "CountryCode": "GBR", "Year": 2020, "Score": 0.5},
        {"FeatureCode": "FEAT1", "CountryCode": "GBR", "Year": 2020, "Score": 0.7},  # Duplicate
    ]
    
    result = regression_imputation(
        feature_list=features,
        outcome_list=outcomes,
        predictor_list=duplicate_predictors,
        target_indicator="TARGET",
        unit="Score",
        model_string="TARGET ~ FEAT1",
        details="Duplicate predictors test"
    )
    
    # Should handle duplicates (likely by taking last value or aggregating)
    assert len(result) == 1
    assert result[0]["CountryCode"] == "GBR"


def test_regression_imputation_wrong_target_indicator():
    """Test regression with mismatched target indicator."""
    
    features = [
        {"FeatureCode": "FEAT1", "CountryCode": "USA", "Year": 2020, "Score": 0.8},
    ]
    
    # Outcome has different indicator code than target
    wrong_outcomes = [
        {"IndicatorCode": "WRONG_TARGET", "CountryCode": "USA", "Year": 2020, "Score": 0.7},
    ]
    
    predictors = [
        {"FeatureCode": "FEAT1", "CountryCode": "CAN", "Year": 2020, "Score": 0.6},
    ]
    
    # Should fail or return empty results due to missing target column
    with pytest.raises((KeyError, ValueError)):
        regression_imputation(
            feature_list=features,
            outcome_list=wrong_outcomes,
            predictor_list=predictors,
            target_indicator="TARGET",  # This doesn't match WRONG_TARGET
            unit="Score",
            model_string="TARGET ~ FEAT1",
            details="Wrong target test"
        )


def test_regression_imputation_value_calculation_various_goalposts():
    """Test Value calculation with various goalpost combinations."""
    
    feature_data = [
        {"FeatureCode": "FEAT1", "CountryCode": "USA", "Year": 2020, "Score": 0.5},
    ]
    
    outcome_data = [
        {"IndicatorCode": "TARGET", "CountryCode": "USA", "Year": 2020, "Score": 0.5},
    ]
    
    predictor_data = [
        {"FeatureCode": "FEAT1", "CountryCode": "TEST", "Year": 2020, "Score": 0.5},
    ]
    
    goalpost_test_cases = [
        (0, 1),      # Standard [0, 1]
        (0, 10),     # Scale to [0, 10]
        (-5, 5),     # Symmetric around 0
        (100, 200),  # Large positive range
        (-1, 0),     # Negative range
    ]
    
    for lg, ug in goalpost_test_cases:
        result = regression_imputation(
            feature_list=feature_data,
            outcome_list=outcome_data,
            predictor_list=predictor_data,
            target_indicator="TARGET",
            unit="Test Unit",
            model_string="TARGET ~ FEAT1",
            details=f"Goalpost test {lg}-{ug}",
            lg=lg,
            ug=ug
        )
        
        score = result[0]["Score"]
        expected_value = (ug - lg) * score + lg
        actual_value = result[0]["Value"]
        
        assert abs(actual_value - expected_value) < 1e-10, f"Value calculation failed for goalposts {lg}-{ug}"
        assert result[0]["LowerGoalpost"] == lg
        assert result[0]["UpperGoalpost"] == ug


def test_regression_imputation_metadata_fields():
    """Test that all metadata fields are correctly set."""
    
    features = [
        {"FeatureCode": "FEAT1", "CountryCode": "USA", "Year": 2020, "Score": 0.8},
        {"FeatureCode": "FEAT1", "CountryCode": "CAN", "Year": 2020, "Score": 0.6},
    ]
    
    outcomes = [
        {"IndicatorCode": "CUSTOM_TARGET", "CountryCode": "USA", "Year": 2020, "Score": 0.75},
        {"IndicatorCode": "CUSTOM_TARGET", "CountryCode": "CAN", "Year": 2020, "Score": 0.65},
    ]
    
    predictors = [
        {"FeatureCode": "FEAT1", "CountryCode": "GBR", "Year": 2021, "Score": 0.7},
    ]
    
    custom_metadata = {
        "target_indicator": "CUSTOM_TARGET",
        "unit": "Custom Units",
        "model_string": "CUSTOM_TARGET ~ FEAT1 + intercept",
        "details": "Detailed description of the custom regression model and methodology"
    }
    
    result = regression_imputation(
        feature_list=features,
        outcome_list=outcomes,
        predictor_list=predictors,
        target_indicator=custom_metadata["target_indicator"],
        unit=custom_metadata["unit"],
        model_string=custom_metadata["model_string"],
        details=custom_metadata["details"],
        lg=5,
        ug=15
    )
    
    doc = result[0]
    assert doc["IndicatorCode"] == custom_metadata["target_indicator"]
    assert doc["Unit"] == custom_metadata["unit"]
    assert doc["ImputationRegessionModel"] == custom_metadata["model_string"]
    assert doc["ImputationDetails"] == custom_metadata["details"]
    assert doc["Imputed"] is True
    assert doc["ImputationMethod"] == "RegressionImputation"
    assert doc["ImputationDistance"] == 0


@patch('sspi_flask_app.api.resources.utilities.LinearRegression')
@patch('sspi_flask_app.api.resources.utilities.pd')
def test_regression_imputation_sklearn_integration(mock_pd, mock_lr):
    """Test integration with sklearn LinearRegression (mocked)."""
    
    # Mock pandas operations
    mock_dataframe = MagicMock()
    mock_dataframe.pivot_table.return_value.sort_index.return_value = mock_dataframe
    mock_dataframe.join.return_value.dropna.return_value = mock_dataframe
    mock_dataframe.drop.return_value = MagicMock()  # X_train
    mock_dataframe.__getitem__.return_value = MagicMock()  # y_train
    mock_dataframe.reset_index.return_value.rename.return_value.__getitem__.return_value.to_dict.return_value = [
        {"CountryCode": "TEST", "Year": 2020, "Score": 0.5}
    ]
    mock_pd.DataFrame.from_records.return_value = mock_dataframe
    
    # Mock sklearn LinearRegression
    mock_model = MagicMock()
    mock_model.predict.return_value = np.array([0.7])
    mock_lr.return_value.fit.return_value = mock_model
    
    # Call the function
    result = regression_imputation(
        feature_list=[{"FeatureCode": "FEAT1", "CountryCode": "USA", "Year": 2020, "Score": 0.8}],
        outcome_list=[{"IndicatorCode": "TARGET", "CountryCode": "USA", "Year": 2020, "Score": 0.7}],
        predictor_list=[{"FeatureCode": "FEAT1", "CountryCode": "TEST", "Year": 2020, "Score": 0.6}],
        target_indicator="TARGET",
        unit="Score",
        model_string="TARGET ~ FEAT1",
        details="Mock test"
    )
    
    # Verify sklearn was called
    mock_lr.assert_called_once_with(fit_intercept=True)
    mock_lr.return_value.fit.assert_called_once()


def test_regression_imputation_realistic_scenario():
    """Test regression imputation with realistic SSPI-like data."""
    
    # Realistic feature data (education and health indicators)
    realistic_features = [
        {"FeatureCode": "EDUCAT", "CountryCode": "USA", "Year": 2020, "Score": 0.85},
        {"FeatureCode": "HEALTH", "CountryCode": "USA", "Year": 2020, "Score": 0.78},
        {"FeatureCode": "EDUCAT", "CountryCode": "FRA", "Year": 2020, "Score": 0.82},
        {"FeatureCode": "HEALTH", "CountryCode": "FRA", "Year": 2020, "Score": 0.89},
        {"FeatureCode": "EDUCAT", "CountryCode": "BRA", "Year": 2020, "Score": 0.65},
        {"FeatureCode": "HEALTH", "CountryCode": "BRA", "Year": 2020, "Score": 0.72},
    ]
    
    # Realistic outcome data (social protection indicator)
    realistic_outcomes = [
        {"IndicatorCode": "SOCPRT", "CountryCode": "USA", "Year": 2020, "Score": 0.81},
        {"IndicatorCode": "SOCPRT", "CountryCode": "FRA", "Year": 2020, "Score": 0.85},
        {"IndicatorCode": "SOCPRT", "CountryCode": "BRA", "Year": 2020, "Score": 0.68},
    ]
    
    # Predictors for countries with missing social protection data
    realistic_predictors = [
        {"FeatureCode": "EDUCAT", "CountryCode": "IND", "Year": 2020, "Score": 0.55},
        {"FeatureCode": "HEALTH", "CountryCode": "IND", "Year": 2020, "Score": 0.62},
        {"FeatureCode": "EDUCAT", "CountryCode": "CHN", "Year": 2020, "Score": 0.73},
        {"FeatureCode": "HEALTH", "CountryCode": "CHN", "Year": 2020, "Score": 0.76},
    ]
    
    result = regression_imputation(
        feature_list=realistic_features,
        outcome_list=realistic_outcomes,
        predictor_list=realistic_predictors,
        target_indicator="SOCPRT",
        unit="SSPI Score",
        model_string="SOCPRT ~ EDUCAT + HEALTH + epsilon",
        details="Regression imputation for Social Protection using Education and Health indicators",
        lg=0,
        ug=1
    )
    
    assert len(result) == 2  # IND and CHN
    
    for doc in result:
        assert doc["IndicatorCode"] == "SOCPRT"
        assert doc["Unit"] == "SSPI Score"
        assert 0 <= doc["Score"] <= 1
        assert doc["CountryCode"] in ["IND", "CHN"]
        assert doc["Year"] == 2020
        
        # Should be reasonable predictions based on input patterns
        # Countries with lower education/health should have lower social protection scores
        if doc["CountryCode"] == "IND":
            # IND has lower features, should predict lower score
            assert doc["Score"] < 0.8  # Reasonable upper bound
        elif doc["CountryCode"] == "CHN":
            # CHN has higher features, should predict higher score
            assert doc["Score"] > 0.6  # Reasonable lower bound