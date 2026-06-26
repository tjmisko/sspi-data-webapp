"""
Regression tests for the custom-scoring cache write path.

These guard two bugs that produced ~600k duplicate/malformed rows in the
custom-scoring caches (see fix/custom-scoring-idempotent-store):

1. ``store_*`` returned ``len(int)`` (insert_many already returns a count),
   raising TypeError *after* a successful insert. The broad caller-side
   ``except`` swallowed it, so line data was never stored and item rows were
   re-inserted on every re-score -> duplicate accumulation.
2. Re-scoring did not clear prior rows first, so a re-store collided with the
   unique indexes (or, pre-index, silently duplicated). Stores are now an
   idempotent replace.

A third test pins root cause #2's structural guard: the line cache rejects
flat (item-shaped) documents.
"""
import pytest
from sspi_flask_app.models.database import sspidb
from sspi_flask_app.models.database.sspi_custom_item_data import SSPICustomItemData
from sspi_flask_app.models.database.sspi_custom_panel_data import SSPICustomPanelData
from sspi_flask_app.models.errors import InvalidDocumentFormatError


CONFIG_HASH = "a" * 32  # 32 lowercase hex chars, as the cache key requires


@pytest.fixture(scope="function")
def item_cache():
    """A SSPICustomItemData wrapper over an isolated test collection with the
    production unique index built, so a missing clear-before-store regression
    surfaces as a DuplicateKeyError."""
    collection = sspidb.sspi_test_custom_item_data
    collection.delete_many({})
    wrapper = SSPICustomItemData(collection)
    wrapper.create_indexes()
    yield wrapper
    collection.delete_many({})
    sspidb.drop_collection(collection)


@pytest.fixture(scope="function")
def panel_cache():
    """A SSPICustomPanelData wrapper over an isolated test collection with the
    production unique index built."""
    collection = sspidb.sspi_test_custom_panel_data
    collection.delete_many({})
    wrapper = SSPICustomPanelData(collection)
    wrapper.create_indexes()
    yield wrapper
    collection.delete_many({})
    sspidb.drop_collection(collection)


def _flat_scores():
    """Two valid flat score docs (store sets config_hash/created_at)."""
    return [
        {"item_code": "BIODIV", "item_type": "Indicator", "country_code": "USA", "year": 2020, "score": 0.75},
        {"item_code": "BIODIV", "item_type": "Indicator", "country_code": "CAN", "year": 2020, "score": 0.50},
    ]


def _line_docs():
    """Two valid line-chart docs (store sets config_hash/created_at/data)."""
    return [
        {"ICode": "SSPI", "IName": "Custom SSPI", "CCode": "USA", "CName": "United States",
         "CGroup": ["SSPI67"], "years": [2020, 2021], "score": [72.1, 73.5]},
        {"ICode": "SSPI", "IName": "Custom SSPI", "CCode": "CAN", "CName": "Canada",
         "CGroup": ["SSPI67"], "years": [2020, 2021], "score": [80.0, 81.2]},
    ]


# =============================================================================
# Root cause #1a: store_* must return an int count, not raise len(int)
# =============================================================================

def test_should_return_inserted_count_when_storing_flat_scores(item_cache):
    count = item_cache.store_scoring_results(CONFIG_HASH, _flat_scores())
    assert count == 2
    assert item_cache.count_documents({"config_hash": CONFIG_HASH}) == 2


def test_should_return_inserted_count_when_storing_line_data(panel_cache):
    count = panel_cache.store_line_data(CONFIG_HASH, _line_docs())
    assert count == 2
    assert panel_cache.count_documents({"config_hash": CONFIG_HASH}) == 2


# =============================================================================
# Root cause #1b: re-storing the same config_hash is an idempotent replace
# =============================================================================

def test_should_replace_not_duplicate_when_rescoring_flat_scores(item_cache):
    item_cache.store_scoring_results(CONFIG_HASH, _flat_scores())
    # A naive re-store without clear-before-insert would raise DuplicateKeyError
    # against unique_score_entry; the idempotent replace must succeed.
    count = item_cache.store_scoring_results(CONFIG_HASH, _flat_scores())
    assert count == 2
    assert item_cache.count_documents({"config_hash": CONFIG_HASH}) == 2


def test_should_replace_not_duplicate_when_rescoring_line_data(panel_cache):
    panel_cache.store_line_data(CONFIG_HASH, _line_docs())
    count = panel_cache.store_line_data(CONFIG_HASH, _line_docs())
    assert count == 2
    assert panel_cache.count_documents({"config_hash": CONFIG_HASH}) == 2


def test_should_not_evict_other_configs_when_rescoring(item_cache):
    """The replace must be scoped to its own config_hash."""
    other_hash = "b" * 32
    item_cache.store_scoring_results(other_hash, _flat_scores())
    item_cache.store_scoring_results(CONFIG_HASH, _flat_scores())
    item_cache.store_scoring_results(CONFIG_HASH, _flat_scores())  # re-score
    assert item_cache.count_documents({"config_hash": other_hash}) == 2


# =============================================================================
# Clear-after-validate: a bad replacement set must not wipe the good cache
# =============================================================================

def test_should_preserve_existing_cache_when_replacement_set_is_invalid(item_cache):
    item_cache.store_scoring_results(CONFIG_HASH, _flat_scores())
    bad = [{"item_code": "BIODIV", "item_type": "Indicator", "country_code": "USA"}]  # no year/score
    with pytest.raises(InvalidDocumentFormatError):
        item_cache.store_scoring_results(CONFIG_HASH, bad)
    # The original two rows survive because clear happens only after validation.
    assert item_cache.count_documents({"config_hash": CONFIG_HASH}) == 2


# =============================================================================
# Root cause #2: the line cache rejects flat (item-shaped) documents
# =============================================================================

def test_should_reject_flat_item_shaped_docs_in_line_cache(panel_cache):
    flat_shaped = [{"item_code": "BIODIV", "country_code": "USA", "year": 2020, "score": 0.5}]
    with pytest.raises(InvalidDocumentFormatError):
        panel_cache.store_line_data(CONFIG_HASH, flat_shaped)
    assert panel_cache.count_documents({"config_hash": CONFIG_HASH}) == 0
