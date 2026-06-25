"""Regression tests for year-range bounds in build_mongo_query (findings F2/F12).

An unbounded YearRange (e.g. 0..2_000_000_000) previously expanded into billions
of integers via range() before any DB call, OOM-killing the worker; non-numeric
year input raised an uncaught 500. These must now be clean InvalidQueryError.
"""
import pytest

from sspi_flask_app.api.resources.query_builder import build_mongo_query
from sspi_flask_app.models.errors import InvalidQueryError


def _year_query(**overrides):
    query = {
        "SeriesCodes": [],
        "CountryCode": [],
        "CountryGroup": None,
        "Year": [],
        "TimePeriod": [],
        "YearRangeStart": None,
        "YearRangeEnd": None,
    }
    query.update(overrides)
    return query


def test_valid_year_range_expands():
    mongo_query = build_mongo_query(
        _year_query(YearRangeStart="2000", YearRangeEnd="2005"), database=None
    )
    assert set(mongo_query["Year"]["$in"]) == {2000, 2001, 2002, 2003, 2004, 2005}


def test_rejects_unbounded_year_range():
    with pytest.raises(InvalidQueryError):
        build_mongo_query(
            _year_query(YearRangeStart="0", YearRangeEnd="2000000000"), database=None
        )


def test_rejects_reversed_year_range():
    with pytest.raises(InvalidQueryError):
        build_mongo_query(
            _year_query(YearRangeStart="2020", YearRangeEnd="2000"), database=None
        )


def test_rejects_nonnumeric_year():
    with pytest.raises(InvalidQueryError):
        build_mongo_query(_year_query(Year=["abc"]), database=None)


def test_rejects_nonnumeric_year_range():
    with pytest.raises(InvalidQueryError):
        build_mongo_query(
            _year_query(YearRangeStart="x", YearRangeEnd="y"), database=None
        )
