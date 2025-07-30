from sspi_flask_app.api.resources.utilities import extrapolate_backward
from copy import deepcopy


def test_extrapolate_backward_single_series():
    data = [
        {"CountryCode": "USA", "IndicatorCode": "GDP", "Year": 2000, "Value": 100}
    ]
    extrapolated_data = extrapolate_backward(data, 1997)
    years = sorted(d['Year'] for d in extrapolated_data)
    assert years == [1997, 1998, 1999, 2000]
    imputed = [d for d in extrapolated_data if d.get("Imputed")]
    assert len(imputed) == 3
    assert all(d["ImputationMethod"] == "Backward Extrapolation" for d in imputed)
    assert all("ImputationDistance" in d for d in imputed)


def test_no_extrapolation_needed():
    data = [
        {"CountryCode": "USA", "IndicatorCode": "GDP", "Year": 1990, "Value": 50}
    ]
    extrapolated_data = extrapolate_backward(data, 1990)
    assert len(extrapolated_data) == 1  # No new years added


def test_multiple_series():
    data = [
        {"CountryCode": "USA", "IndicatorCode": "GDP", "Year": 2000, "Value": 100},
        {"CountryCode": "CAN", "IndicatorCode": "GDP", "Year": 1999, "Value": 90}
    ]
    extrapolated_data = extrapolate_backward(data, 1997)
    usa_years = sorted([d["Year"] for d in extrapolated_data if d["CountryCode"] == "USA"])
    can_years = sorted([d["Year"] for d in extrapolated_data if d["CountryCode"] == "CAN"])
    assert usa_years == [1997, 1998, 1999, 2000]
    assert can_years == [1997, 1998, 1999]


def test_custom_series_key():
    data = [
        {"Country": "FRA", "Series": "POP", "Year": 2010, "Value": 66}
    ]
    extrapolated_data = extrapolate_backward(data, 2008, series_id=["Country", "Series"])
    years = sorted([d["Year"] for d in extrapolated_data])
    assert years == [2008, 2009, 2010]


def test_extrapolate_backward_impute_only():
    data = [
        {"CountryCode": "USA", "IndicatorCode": "GDP", "Year": 2000, "Value": 10},
        {"CountryCode": "USA", "IndicatorCode": "GDP", "Year": 2002, "Value": 30}
    ]
    result = extrapolate_backward(data, 1998, impute_only=True)
    assert all(doc["Imputed"] is True for doc in result)
    assert sorted(doc["Year"] for doc in result) == [1998, 1999]
    assert len(result) == 2
    assert all(doc["IndicatorCode"] == "GDP" for doc in result)
    assert all(doc["ImputationMethod"] == "Backward Extrapolation" for doc in result)
