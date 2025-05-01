from sspi_flask_app.api.resources.utilities import extrapolate_backward


def test_extrapolate_backward_single_series():
    data = [
        {"CountryCode": "USA", "IndicatorCode": "GDP", "Year": 2000, "Value": 100}
    ]
    extrapolate_backward(data, 1997)
    years = sorted(d['Year'] for d in data)
    assert years == [1997, 1998, 1999, 2000]
    imputed = [d for d in data if d.get("Imputed")]
    assert len(imputed) == 3
    assert all(d["ImputationMethod"] == "Backward Extrapolation" for d in imputed)
    assert all("ImputationDistance" in d for d in imputed)


def test_no_extrapolation_needed():
    data = [
        {"CountryCode": "USA", "IndicatorCode": "GDP", "Year": 1990, "Value": 50}
    ]
    extrapolate_backward(data, 1990)
    assert len(data) == 1  # No new years added


def test_multiple_series():
    data = [
        {"CountryCode": "USA", "IndicatorCode": "GDP", "Year": 2000, "Value": 100},
        {"CountryCode": "CAN", "IndicatorCode": "GDP", "Year": 1999, "Value": 90}
    ]
    extrapolate_backward(data, 1997)
    usa_years = sorted([d["Year"] for d in data if d["CountryCode"] == "USA"])
    can_years = sorted([d["Year"] for d in data if d["CountryCode"] == "CAN"])
    assert usa_years == [1997, 1998, 1999, 2000]
    assert can_years == [1997, 1998, 1999]


def test_custom_series_key():
    data = [
        {"Country": "FRA", "Series": "POP", "Year": 2010, "Value": 66}
    ]
    extrapolate_backward(data, 2008, series_id=["Country", "Series"])
    years = sorted([d["Year"] for d in data])
    assert years == [2008, 2009, 2010]
