"""
Startup must not fail when a cache collection written by older code blocks
its unique index; the cache is repaired instead (it is recomputable).
"""
from unittest.mock import MagicMock

import pytest
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError, OperationFailure, ServerSelectionTimeoutError

from sspi_flask_app.models.database.cache_index import create_unique_cache_index

KEYS = [("config_hash", 1), ("ICode", 1)]


def _collection(first_error=None):
    collection = MagicMock()
    collection.name = "sspi_custom_panel_data"
    collection.create_index.side_effect = [first_error, None] if first_error else [None]
    return collection


def test_should_create_index_once_when_cache_has_no_conflicts():
    collection = _collection()
    create_unique_cache_index(collection, KEYS, name="unique_line_entry")
    collection.create_index.assert_called_once_with(KEYS, unique=True, name="unique_line_entry")
    collection.delete_many.assert_not_called()


def test_should_clear_cache_and_retry_when_duplicate_rows_block_the_index():
    collection = _collection(DuplicateKeyError("E11000 duplicate key"))
    create_unique_cache_index(collection, KEYS, name="unique_line_entry")
    collection.delete_many.assert_called_once_with({})
    assert collection.create_index.call_count == 2


@pytest.mark.parametrize("code", [85, 86])
def test_should_drop_old_index_and_retry_when_index_options_conflict(code):
    collection = _collection(OperationFailure("index conflict", code=code))
    create_unique_cache_index(collection, KEYS, name="unique_line_entry")
    collection.drop_index.assert_called_once_with("unique_line_entry")
    collection.delete_many.assert_not_called()
    assert collection.create_index.call_count == 2


def test_should_raise_when_failure_is_not_an_index_conflict():
    collection = _collection(OperationFailure("not authorized", code=13))
    with pytest.raises(OperationFailure):
        create_unique_cache_index(collection, KEYS, name="unique_line_entry")
    collection.delete_many.assert_not_called()


@pytest.fixture
def scratch_collection():
    client = MongoClient("localhost", 27017, serverSelectionTimeoutMS=2000)
    try:
        client.admin.command("ping")
    except ServerSelectionTimeoutError:
        pytest.skip("local MongoDB not available")
    collection = client["sspi_test_cache_index"]["panel_cache"]
    collection.drop()
    yield collection
    client.drop_database("sspi_test_cache_index")
    client.close()


def test_should_build_unique_index_when_real_collection_holds_duplicates(scratch_collection):
    scratch_collection.insert_many([
        {"config_hash": "a", "ICode": "SSPI"},
        {"config_hash": "a", "ICode": "SSPI"},
    ])
    create_unique_cache_index(scratch_collection, KEYS, name="unique_line_entry")
    info = scratch_collection.index_information()
    assert info["unique_line_entry"].get("unique") is True
    assert scratch_collection.count_documents({}) == 0


def test_should_keep_rows_when_real_collection_has_no_duplicates(scratch_collection):
    scratch_collection.insert_many([
        {"config_hash": "a", "ICode": "SSPI"},
        {"config_hash": "b", "ICode": "SSPI"},
    ])
    create_unique_cache_index(scratch_collection, KEYS, name="unique_line_entry")
    assert scratch_collection.count_documents({}) == 2


def test_should_replace_old_non_unique_index_when_name_collides(scratch_collection):
    scratch_collection.create_index(KEYS, name="unique_line_entry")
    create_unique_cache_index(scratch_collection, KEYS, name="unique_line_entry")
    assert scratch_collection.index_information()["unique_line_entry"].get("unique") is True
