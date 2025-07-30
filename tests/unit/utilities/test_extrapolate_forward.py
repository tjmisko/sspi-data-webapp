from sspi_flask_app.api.resources.utilities import extrapolate_forward
from copy import deepcopy


def test_extrapolate_forward_single_series():
    data = [
        {"CountryCode": "USA", "IndicatorCode": "GDP", "Year": 2000, "Value": 100}
    ]
    extrapolate_forward(data, 2003)
    years = sorted(d['Year'] for d in data)
    assert years == [2000, 2001, 2002, 2003]
    imputed = [d for d in data if d.get("Imputed")]
    assert len(imputed) == 3
    assert all(d["ImputationMethod"] ==
               "Forward Extrapolation" for d in imputed)
    assert all("ImputationDistance" in d for d in imputed)


def test_no_forward_extrapolation_needed():
    data = [
        {"CountryCode": "USA", "IndicatorCode": "GDP", "Year": 2000, "Value": 100}
    ]
    extrapolate_forward(data, 2000)
    assert len(data) == 1  # No new years added


def test_forward_multiple_series():
    data = [
        {"CountryCode": "USA", "IndicatorCode": "GDP", "Year": 2000, "Value": 100},
        {"CountryCode": "CAN", "IndicatorCode": "GDP", "Year": 2001, "Value": 90}
    ]
    extrapolate_forward(data, 2003)
    usa_years = sorted([d["Year"] for d in data if d["CountryCode"] == "USA"])
    can_years = sorted([d["Year"] for d in data if d["CountryCode"] == "CAN"])
    assert usa_years == [2000, 2001, 2002, 2003]
    assert can_years == [2001, 2002, 2003]


def test_forward_custom_series_key():
    data = [
        {"Country": "FRA", "Series": "POP", "Year": 2010, "Value": 66}
    ]
    extrapolate_forward(data, 2012, series_id=["Country", "Series"])
    years = sorted([d["Year"] for d in data])
    assert years == [2010, 2011, 2012]


def test_extrapolate_forward_impute_only():
    data = [
        {"CountryCode": "USA", "IndicatorCode": "GDP", "Year": 2000, "Value": 10},
        {"CountryCode": "USA", "IndicatorCode": "GDP", "Year": 2002, "Value": 30}
    ]
    result = extrapolate_forward(deepcopy(data), 2004, impute_only=True)
    assert all(doc["Imputed"] is True for doc in result)
    assert sorted(doc["Year"] for doc in result) == [2003, 2004]
    assert len(result) == 2
    assert all(doc["ImputationMethod"] == "Forward Extrapolation" for doc in result)

def test_extrapolate_forward_full_series():
    data = [
        {"CountryCode": "USA", "IndicatorCode": "GDP", "Year": 2000, "Value": 10},
        {"CountryCode": "USA", "IndicatorCode": "GDP", "Year": 2001, "Value": 10},
        {"CountryCode": "USA", "IndicatorCode": "GDP", "Year": 2002, "Value": 30}
    ]
    result = extrapolate_forward(deepcopy(data), 2002, impute_only=True)
    assert len(result) == 0
