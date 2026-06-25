"""Regression tests for the query input sanitizer (audit finding F6).

The sanitizer previously iterated ``enumerate(dict)``, so it inspected field
names instead of user values and never actually filtered anything. These tests
lock in that VALUES are validated and that NoSQL operator objects are rejected.
"""
import pytest

from sspi_flask_app.api.resources.validators import validate_data_query
from sspi_flask_app.models.errors import InvalidQueryError


def _base_query(**overrides):
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


def test_accepts_clean_values():
    query = _base_query(
        SeriesCodes=["BIODIV", "REDLST"], CountryGroup="SSPI67", Year=["2018"]
    )
    assert validate_data_query(query) is query


def test_rejects_operator_object_scalar():
    """A dict value like {"$ne": null} must be rejected, not silently passed."""
    with pytest.raises(InvalidQueryError):
        validate_data_query(_base_query(CountryGroup={"$ne": None}))


def test_rejects_operator_object_inside_list():
    with pytest.raises(InvalidQueryError):
        validate_data_query(_base_query(CountryCode=[{"$ne": None}]))


def test_rejects_unsafe_characters():
    with pytest.raises(InvalidQueryError):
        validate_data_query(_base_query(CountryGroup="a;b|c"))


def test_rejects_regex_metacharacters():
    """Regex metacharacters previously reached a Mongo $regex unfiltered."""
    with pytest.raises(InvalidQueryError):
        validate_data_query(_base_query(CountryGroup=".*"))


def test_rejects_too_many_parameters():
    with pytest.raises(InvalidQueryError):
        validate_data_query({f"k{i}": "v" for i in range(201)})
