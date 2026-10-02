"""
Unit tests for ``SSPIMetadata.record_dataset_range``.

The method's only Mongo interaction is a single ``update_one`` on the
underlying collection, so these tests hand ``SSPIMetadata`` a fake collection
that records the call. Nothing touches a live database. They guard issue I-25:
the recorded range must be the true observed min/max of ``Value``, not a range
anchored at zero.
"""
import logging

import pytest

from sspi_flask_app.models.database.sspi_metadata import SSPIMetadata


DATASET_CODE = "WB_TESTDS"


class FakeCollection:
    """Minimal stand-in for a pymongo Collection that records update_one calls."""

    def __init__(self):
        self.name = "sspi_metadata_fake"
        self.update_one_calls = []

    def update_one(self, query, update, *args, **kwargs):
        self.update_one_calls.append((query, update))


@pytest.fixture
def fake_collection():
    return FakeCollection()


@pytest.fixture
def metadata(fake_collection):
    return SSPIMetadata(fake_collection)


def make_obs(value):
    return {
        "CountryCode": "USA",
        "DatasetCode": DATASET_CODE,
        "Description": "test",
        "Year": 2000,
        "Unit": "test",
        "Value": value,
    }


def recorded_range(fake_collection):
    assert len(fake_collection.update_one_calls) == 1
    _query, update = fake_collection.update_one_calls[0]
    set_fields = update["$set"]
    return set_fields["Metadata.Range.yMin"], set_fields["Metadata.Range.yMax"]


def test_should_record_true_min_when_all_values_are_positive(metadata, fake_collection):
    metadata.record_dataset_range([make_obs(v) for v in (12.5, 40.0, 87.25)], DATASET_CODE)
    y_min, y_max = recorded_range(fake_collection)
    assert y_min == 12.5
    assert y_max == 87.25


def test_should_record_true_max_when_all_values_are_negative(metadata, fake_collection):
    metadata.record_dataset_range([make_obs(v) for v in (-3.0, -0.5, -12.0)], DATASET_CODE)
    y_min, y_max = recorded_range(fake_collection)
    assert y_min == -12.0
    assert y_max == -0.5


def test_should_record_min_and_max_when_values_straddle_zero(metadata, fake_collection):
    metadata.record_dataset_range([make_obs(v) for v in (-2.5, 0.0, 7.0)], DATASET_CODE)
    y_min, y_max = recorded_range(fake_collection)
    assert y_min == -2.5
    assert y_max == 7.0


def test_should_record_equal_min_and_max_when_single_observation(metadata, fake_collection):
    metadata.record_dataset_range([make_obs(42.0)], DATASET_CODE)
    y_min, y_max = recorded_range(fake_collection)
    assert y_min == 42.0
    assert y_max == 42.0


def test_should_record_zero_range_when_all_values_are_zero(metadata, fake_collection):
    metadata.record_dataset_range([make_obs(0.0), make_obs(0)], DATASET_CODE)
    y_min, y_max = recorded_range(fake_collection)
    assert y_min == 0
    assert y_max == 0


def test_should_accept_int_values_when_mixed_with_floats(metadata, fake_collection):
    metadata.record_dataset_range([make_obs(3), make_obs(1.5), make_obs(9)], DATASET_CODE)
    y_min, y_max = recorded_range(fake_collection)
    assert y_min == 1.5
    assert y_max == 9


def test_should_target_dataset_detail_document_when_updating(metadata, fake_collection):
    metadata.record_dataset_range([make_obs(1.0)], DATASET_CODE)
    query, update = fake_collection.update_one_calls[0]
    assert query == {
        "DocumentType": "DatasetDetail",
        "Metadata.DatasetCode": DATASET_CODE,
    }
    assert set(update) == {"$set"}
    assert set(update["$set"]) == {"Metadata.Range.yMin", "Metadata.Range.yMax"}


def test_should_write_nothing_and_warn_when_dataset_is_empty(metadata, fake_collection, caplog):
    with caplog.at_level(logging.WARNING, logger="sspi_flask_app.models.database.sspi_metadata"):
        result = metadata.record_dataset_range([], DATASET_CODE)
    assert result is None
    assert fake_collection.update_one_calls == []
    warnings = [r for r in caplog.records if r.levelno == logging.WARNING]
    assert any(DATASET_CODE in r.getMessage() for r in warnings)


def test_should_raise_assertion_error_when_value_is_not_numeric(metadata, fake_collection):
    with pytest.raises(AssertionError):
        metadata.record_dataset_range([make_obs("12.5")], DATASET_CODE)
    assert fake_collection.update_one_calls == []


def test_should_raise_assertion_error_when_value_is_missing(metadata, fake_collection):
    with pytest.raises(AssertionError):
        metadata.record_dataset_range([{"CountryCode": "USA"}], DATASET_CODE)
    assert fake_collection.update_one_calls == []
