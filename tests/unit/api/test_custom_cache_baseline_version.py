"""
The custom result cache is keyed on (config hash, baseline version), so a
regenerated set of official scores never serves results built on the old ones.

All stores are mocked; nothing touches the database.
"""
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

import sspi_flask_app.api.resources.baseline_version as bv
import sspi_flask_app.api.resources.scoring_tasks as st
from sspi_flask_app.api.resources.metadata_validator import compute_config_hash

HASH = "a" * 32


@pytest.fixture(autouse=True)
def _reset_version_cache():
    bv.clear_baseline_version_cache()
    yield
    bv.clear_baseline_version_cache()


def test_should_change_cache_key_when_baseline_version_changes():
    assert bv.cache_key(HASH, "v1") != bv.cache_key(HASH, "v2")


def test_should_keep_cache_key_stable_when_inputs_are_unchanged():
    assert bv.cache_key(HASH, "v1") == bv.cache_key(HASH, "v1")


def test_should_return_32_hex_characters_when_building_a_cache_key():
    key = bv.cache_key(HASH, "v1")
    assert len(key) == 32 and set(key) <= set("0123456789abcdef")


def test_should_differ_per_config_when_baseline_version_is_shared():
    assert bv.cache_key("a" * 32, "v1") != bv.cache_key("b" * 32, "v1")


def _aggregate_returning(n, total):
    return MagicMock(return_value=[{"_id": None, "n": n, "total": total}])


def test_should_change_version_when_official_scores_change():
    with patch.object(bv.sspi_item_data, "aggregate", _aggregate_returning(10, 5.0)):
        before = bv.compute_baseline_version()
    with patch.object(bv.sspi_item_data, "aggregate", _aggregate_returning(10, 5.5)):
        after = bv.compute_baseline_version()
    assert before != after


def test_should_keep_version_when_official_scores_are_identical():
    with patch.object(bv.sspi_item_data, "aggregate", _aggregate_returning(10, 5.0)):
        assert bv.compute_baseline_version() == bv.compute_baseline_version()


def test_should_return_unknown_version_when_the_store_fails():
    with patch.object(bv.sspi_item_data, "aggregate",
                      side_effect=RuntimeError("down")):
        assert bv.compute_baseline_version() == bv.UNKNOWN_VERSION


def _metadata():
    return [
        {"ItemType": "SSPI", "ItemCode": "SSPI", "ItemName": "S",
         "PillarCodes": ["PIL"], "Children": ["PIL"]},
        {"ItemType": "Pillar", "ItemCode": "PIL", "ItemName": "P",
         "CategoryCodes": ["CAT"], "Children": ["CAT"]},
        {"ItemType": "Category", "ItemCode": "CAT", "ItemName": "C",
         "IndicatorCodes": ["AAAAAA"], "Children": ["AAAAAA"]},
        {"ItemType": "Indicator", "ItemCode": "AAAAAA", "ItemName": "A",
         "DatasetCodes": ["DS"], "ScoreFunction": "Score = goalpost(DS, 0, 1)"},
    ]


def _run_pipeline(version_at_run, cached_version):
    """Run the pipeline with a cache populated under `cached_version`."""
    metadata = _metadata()
    cached_key = bv.cache_key(compute_config_hash(metadata), cached_version)
    item_store = MagicMock()
    item_store.has_cached_results.side_effect = lambda key: key == cached_key
    item_store.get_cached_results.return_value = [{"x": 1}]
    panel_store = MagicMock()
    panel_store.has_line_data.return_value = True
    job = MagicMock()
    with patch.object(st, "identify_empty_datasets", return_value=SimpleNamespace(
            dropped_indicators=[], scorable_indicators=metadata[3:])), \
         patch.object(st, "changed_indicator_codes", return_value=set()), \
         patch.object(st, "validate_custom_metadata",
                      return_value=SimpleNamespace(valid=True, item_count=4)), \
         patch.object(st, "_abort_if_cancelled", return_value=False), \
         patch.object(st.sspi_metadata, "dataset_codes", return_value=["DS"]), \
         patch.object(st, "sspi_custom_item_data", item_store), \
         patch.object(st, "sspi_custom_panel_data", panel_store), \
         patch.object(st, "score_custom_configuration_fast",
                      side_effect=RuntimeError("scored-not-cached")), \
         patch.object(bv, "get_baseline_version", return_value=version_at_run):
        st.run_scoring_pipeline(job, metadata, [])
    return job


def test_should_hit_cache_when_baseline_version_matches():
    job = _run_pipeline(version_at_run="v1", cached_version="v1")
    job.emit_complete.assert_called_once()
    assert job.emit_complete.call_args.kwargs.get("cached") is True
    job.emit_error.assert_not_called()


def test_should_miss_cache_and_rescore_when_baseline_version_changed():
    job = _run_pipeline(version_at_run="v2", cached_version="v1")
    job.emit_complete.assert_not_called()
    job.emit_error.assert_called_once()
    assert "scored-not-cached" in job.emit_error.call_args.args[0]
