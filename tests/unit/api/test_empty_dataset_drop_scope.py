"""
identify_empty_datasets must only drop indicators that are eligible
(changed/new). Unchanged indicators reuse official scores, so empty raw
datasets (e.g. TRNETW) must never remove them.

The clean-data store is mocked; nothing touches the database.
"""
from unittest.mock import patch

import sspi_flask_app.models.database as db
from sspi_flask_app.api.resources.custom_scoring import identify_empty_datasets


def _indicator(code, dataset):
    return {
        "ItemType": "Indicator", "ItemCode": code, "ItemName": code,
        "DatasetCodes": [dataset],
    }


def _metadata():
    return [_indicator("AAAAAA", "DS_FULL"), _indicator("TRNETW", "DS_EMPTY")]


def _run(droppable_codes):
    with patch.object(db.sspi_clean_api_data, "aggregate",
                      return_value=[{"_id": "DS_FULL"}]):
        return identify_empty_datasets(
            _metadata(), droppable_codes=droppable_codes
        )


def test_should_drop_empty_indicator_when_all_indicators_are_droppable():
    result = _run(droppable_codes=None)
    assert [d["code"] for d in result.dropped_indicators] == ["TRNETW"]


def test_should_keep_unchanged_indicator_when_its_datasets_are_empty():
    result = _run(droppable_codes={"AAAAAA"})
    assert result.dropped_indicators == []
    assert {i["ItemCode"] for i in result.scorable_indicators} == {
        "AAAAAA", "TRNETW"}


def test_should_drop_changed_indicator_when_its_datasets_are_empty():
    result = _run(droppable_codes={"TRNETW"})
    assert [d["code"] for d in result.dropped_indicators] == ["TRNETW"]
    assert [i["ItemCode"] for i in result.scorable_indicators] == ["AAAAAA"]


def test_should_keep_everything_when_no_indicator_is_droppable():
    result = _run(droppable_codes=set())
    assert result.dropped_indicators == []
    assert len(result.scorable_indicators) == 2
