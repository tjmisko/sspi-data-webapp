from sspi_flask_app.api.resources.utilities import interpolate_linear


def test_interpolate_linear_single_gap():
    data = [
        {"CountryCode": "USA", "IndicatorCode": "GDP", "Year": 2000, "Value": 100},
        {"CountryCode": "USA", "IndicatorCode": "GDP", "Year": 2002, "Value": 200},
    ]
    interpolate_linear(data)
    years = sorted(d["Year"] for d in data)
    assert years == [2000, 2001, 2002]
    interpolated = [d for d in data if d.get("Imputed")]
    assert len(interpolated) == 1
    assert interpolated[0]["Year"] == 2001
    assert interpolated[0]["Value"] == 150
    assert interpolated[0]["ImputationMethod"] == "Linear Interpolation"


def test_interpolate_linear_multiple_gaps():
    data = [
        {"CountryCode": "USA", "IndicatorCode": "GDP", "Year": 2000, "Value": 100},
        {"CountryCode": "USA", "IndicatorCode": "GDP", "Year": 2003, "Value": 400},
    ]
    interpolate_linear(data)
    years = sorted(d["Year"] for d in data)
    assert years == [2000, 2001, 2002, 2003]
    values = {d["Year"]: d["Value"] for d in data}
    assert values[2001] == 200
    assert values[2002] == 300


def test_interpolate_linear_no_gap():
    data = [
        {"CountryCode": "USA", "IndicatorCode": "GDP", "Year": 2000, "Value": 100},
        {"CountryCode": "USA", "IndicatorCode": "GDP", "Year": 2001, "Value": 150},
        {"CountryCode": "USA", "IndicatorCode": "GDP", "Year": 2002, "Value": 200},
    ]
    before = len(data)
    interpolate_linear(data)
    assert len(data) == before  # no changes


def test_interpolate_linear_multiple_series():
    data = [
        {"CountryCode": "USA", "IndicatorCode": "GDP", "Year": 2000, "Value": 100},
        {"CountryCode": "USA", "IndicatorCode": "GDP", "Year": 2002, "Value": 200},
        {"CountryCode": "CAN", "IndicatorCode": "GDP", "Year": 2001, "Value": 90},
        {"CountryCode": "CAN", "IndicatorCode": "GDP", "Year": 2003, "Value": 110},
    ]
    interpolate_linear(data)
    usa = sorted([d for d in data if d["CountryCode"]
                 == "USA"], key=lambda x: x["Year"])
    can = sorted([d for d in data if d["CountryCode"]
                 == "CAN"], key=lambda x: x["Year"])
    assert [d["Year"] for d in usa] == [2000, 2001, 2002]
    assert [d["Year"] for d in can] == [2001, 2002, 2003]
    assert [d["Value"] for d in can if d.get("Imputed")] == [100]


def test_interpolate_linear_custom_series_key():
    data = [
        {"Country": "JPN", "Series": "POP", "Year": 1990, "Value": 120},
        {"Country": "JPN", "Series": "POP", "Year": 1992, "Value": 124},
    ]
    interpolate_linear(data, series_id=["Country", "Series"])
    years = sorted([d["Year"] for d in data])
    assert years == [1990, 1991, 1992]
    interpolated = [d for d in data if d.get("Imputed")]
    assert interpolated[0]["Value"] == 122
