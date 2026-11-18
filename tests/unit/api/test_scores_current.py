"""A saved config counts as scored only against the current official baseline."""
import sspi_flask_app.api.resources.baseline_version as bv


def _has_scores(_hash):
    return True


def test_should_be_current_when_hash_exists_and_baseline_version_matches(monkeypatch):
    monkeypatch.setattr(bv, "get_baseline_version", lambda: "v2")
    config = {"scored_hash": "a" * 32, "scored_baseline_version": "v2"}
    assert bv.config_scores_are_current(config, _has_scores)


def test_should_be_stale_when_scored_against_an_older_baseline(monkeypatch):
    monkeypatch.setattr(bv, "get_baseline_version", lambda: "v2")
    config = {"scored_hash": "a" * 32, "scored_baseline_version": "v1"}
    assert not bv.config_scores_are_current(config, _has_scores)


def test_should_be_stale_when_scored_before_versions_were_recorded(monkeypatch):
    monkeypatch.setattr(bv, "get_baseline_version", lambda: "v2")
    assert not bv.config_scores_are_current({"scored_hash": "a" * 32}, _has_scores)


def test_should_be_unscored_when_no_scored_hash(monkeypatch):
    monkeypatch.setattr(bv, "get_baseline_version", lambda: "v2")
    assert not bv.config_scores_are_current({}, _has_scores)


def test_should_be_unscored_when_cached_rows_are_gone(monkeypatch):
    monkeypatch.setattr(bv, "get_baseline_version", lambda: "v2")
    config = {"scored_hash": "a" * 32, "scored_baseline_version": "v2"}
    assert not bv.config_scores_are_current(config, lambda _h: False)
