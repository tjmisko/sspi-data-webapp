"""
Unit tests for baseline reuse in custom scoring: change detection against the
default SSPI, restricted score-function validation, and filling unchanged
indicator rows from official scores.

No database writes. The default metadata, the baseline store and the dataset
fetch are all monkeypatched.
"""
import copy

import numpy as np
import pytest

import sspi_flask_app.api.resources.change_detection as cd
import sspi_flask_app.api.resources.fast_custom_scoring as fcs
from sspi_flask_app.api.resources.metadata_validator import (
    validate_custom_metadata,
)

GOOD_SF = "Score = goalpost(DS_A, 0, 100)"
BAD_SF = "Score = mean over conventions c in force where something prose"


def _indicator(code, dataset="DS_A", lower=0, upper=100, sf=None, weight=None):
    item = {
        "ItemType": "Indicator",
        "ItemCode": code,
        "IndicatorCode": code,
        "ItemName": code,
        "DatasetCodes": [dataset],
        "ScoreFunction": sf or f"Score = goalpost({dataset}, {lower}, {upper})",
        "LowerGoalpost": lower,
        "UpperGoalpost": upper,
        "CategoryCode": "CAT1",
    }
    if weight is not None:
        item["Weight"] = weight
    return item


def _metadata():
    return [
        {"ItemType": "SSPI", "ItemCode": "SSPI", "ItemName": "SSPI",
         "PillarCodes": ["PIL1"], "Children": ["PIL1"]},
        {"ItemType": "Pillar", "ItemCode": "PIL1", "ItemName": "P1",
         "CategoryCodes": ["CAT1", "CAT2"], "Children": ["CAT1", "CAT2"]},
        {"ItemType": "Category", "ItemCode": "CAT1", "ItemName": "C1",
         "PillarCode": "PIL1", "IndicatorCodes": ["AAAAAA", "BBBBBB"],
         "Children": ["AAAAAA", "BBBBBB"]},
        {"ItemType": "Category", "ItemCode": "CAT2", "ItemName": "C2",
         "PillarCode": "PIL1", "IndicatorCodes": ["CCCCCC"],
         "Children": ["CCCCCC"]},
        _indicator("AAAAAA", "DS_A"),
        _indicator("BBBBBB", "DS_B"),
        _indicator("CCCCCC", "DS_C"),
    ]


@pytest.fixture
def default_metadata(monkeypatch):
    """Install _metadata() as the default SSPI and reset detection caches."""
    cd.clear_default_caches()
    defaults = {
        i["ItemCode"]: i for i in _metadata() if i["ItemType"] == "Indicator"
    }
    monkeypatch.setattr(cd, "_load_default_indicators", lambda: defaults)
    yield defaults
    cd.clear_default_caches()


def _by_code(metadata, code):
    return next(i for i in metadata if i.get("ItemCode") == code)


# ---------------------------------------------------------------------------
# Change detection
# ---------------------------------------------------------------------------

def test_should_treat_every_indicator_as_unchanged_when_config_equals_default(
        default_metadata):
    result = cd.identify_modified_indicators(_metadata())
    assert result.modified_indicators == set()
    assert result.unchanged_indicators == {"AAAAAA", "BBBBBB", "CCCCCC"}


def test_should_mark_only_edited_indicator_changed_when_score_function_changes(
        default_metadata):
    meta = _metadata()
    _by_code(meta, "BBBBBB")["ScoreFunction"] = "Score = goalpost(DS_B, 0, 50)"
    result = cd.identify_modified_indicators(meta)
    assert result.modified_indicators == {"BBBBBB"}
    assert result.unchanged_indicators == {"AAAAAA", "CCCCCC"}


@pytest.mark.parametrize("field,value", [
    ("LowerGoalpost", 10),
    ("UpperGoalpost", 90),
])
def test_should_mark_only_edited_indicator_changed_when_goalpost_changes(
        default_metadata, field, value):
    meta = _metadata()
    _by_code(meta, "AAAAAA")[field] = value
    result = cd.identify_modified_indicators(meta)
    assert result.modified_indicators == {"AAAAAA"}


def test_should_mark_only_edited_indicator_changed_when_dataset_list_changes(
        default_metadata):
    meta = _metadata()
    _by_code(meta, "CCCCCC")["DatasetCodes"] = ["DS_C", "DS_X"]
    result = cd.identify_modified_indicators(meta)
    assert result.modified_indicators == {"CCCCCC"}


def test_should_treat_indicator_moved_to_another_category_as_unchanged(
        default_metadata):
    meta = _metadata()
    _by_code(meta, "AAAAAA")["CategoryCode"] = "CAT2"
    _by_code(meta, "CAT1")["IndicatorCodes"] = ["BBBBBB"]
    _by_code(meta, "CAT1")["Children"] = ["BBBBBB"]
    _by_code(meta, "CAT2")["IndicatorCodes"] = ["CCCCCC", "AAAAAA"]
    _by_code(meta, "CAT2")["Children"] = ["CCCCCC", "AAAAAA"]
    result = cd.identify_modified_indicators(meta)
    assert result.modified_indicators == set()


def test_should_treat_weight_only_edit_as_unchanged(default_metadata):
    meta = _metadata()
    _by_code(meta, "AAAAAA")["Weight"] = 0.9
    result = cd.identify_modified_indicators(meta)
    assert result.modified_indicators == set()


def test_should_treat_new_indicator_code_as_changed(default_metadata):
    meta = _metadata() + [_indicator("NEWNEW", "DS_N")]
    result = cd.identify_modified_indicators(meta)
    assert result.modified_indicators == {"NEWNEW"}
    assert result.new_indicators == {"NEWNEW"}


def test_should_treat_whitespace_only_score_function_edit_as_unchanged(
        default_metadata):
    meta = _metadata()
    default = default_metadata["AAAAAA"]["ScoreFunction"]
    _by_code(meta, "AAAAAA")["ScoreFunction"] = (
        "  " + default.replace(" ", "   ") + "\n"
    )
    result = cd.identify_modified_indicators(meta)
    assert result.modified_indicators == set()


def test_should_treat_int_and_float_goalposts_as_equal(default_metadata):
    meta = _metadata()
    _by_code(meta, "AAAAAA")["LowerGoalpost"] = 0.0
    _by_code(meta, "AAAAAA")["UpperGoalpost"] = 100.0
    assert cd.identify_modified_indicators(meta).modified_indicators == set()


def test_should_skip_indicators_without_item_code_when_detecting(
        default_metadata):
    meta = _metadata() + [{"ItemType": "Indicator", "DatasetCodes": ["DS_Z"]}]
    result = cd.identify_modified_indicators(meta)
    assert result.modified_indicators == set()


def test_should_report_removed_indicators_when_config_drops_one(
        default_metadata):
    meta = [i for i in _metadata() if i.get("ItemCode") != "CCCCCC"]
    result = cd.identify_modified_indicators(meta)
    assert result.removed_indicators == {"CCCCCC"}
    assert result.modified_indicators == set()


def test_should_treat_all_as_changed_when_default_metadata_unavailable(
        monkeypatch, caplog):
    cd.clear_default_caches()
    monkeypatch.setattr(cd, "_load_default_indicators", lambda: {})
    with caplog.at_level("WARNING"):
        result = cd.identify_modified_indicators(_metadata())
    assert result.modified_indicators == {"AAAAAA", "BBBBBB", "CCCCCC"}
    assert result.unchanged_indicators == set()
    assert result.default_available is False
    assert "unavailable" in caplog.text
    cd.clear_default_caches()


def test_should_not_cache_empty_defaults_when_database_recovers(monkeypatch):
    cd.clear_default_caches()
    monkeypatch.setattr(cd, "_load_default_indicators", lambda: {})
    assert cd.get_default_indicator_signatures() == {}
    defaults = {"AAAAAA": _indicator("AAAAAA")}
    monkeypatch.setattr(cd, "_load_default_indicators", lambda: defaults)
    assert set(cd.get_default_indicator_signatures()) == {"AAAAAA"}
    cd.clear_default_caches()


def test_should_return_none_when_change_detection_raises(monkeypatch):
    def boom(_metadata):
        raise RuntimeError("db down")
    monkeypatch.setattr(cd, "identify_modified_indicators", boom)
    assert cd.changed_indicator_codes(_metadata()) is None


def test_should_ignore_non_dict_items_when_collecting_changed_codes(
        default_metadata):
    meta = _metadata() + ["junk", None]
    assert cd.changed_indicator_codes(meta) == set()


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def test_should_skip_score_function_validation_for_unchanged_indicators():
    meta = _metadata()
    _by_code(meta, "AAAAAA")["ScoreFunction"] = BAD_SF
    result = validate_custom_metadata(meta, score_function_codes=set())
    assert not [e for e in result.errors if e.field == "ScoreFunction"]


def test_should_report_invalid_score_function_when_indicator_is_in_changed_set():
    meta = _metadata()
    _by_code(meta, "AAAAAA")["ScoreFunction"] = BAD_SF
    result = validate_custom_metadata(meta, score_function_codes={"AAAAAA"})
    errors = [e for e in result.errors if e.field == "ScoreFunction"]
    assert [e.item_code for e in errors] == ["AAAAAA"]
    assert result.valid is False


def test_should_validate_every_score_function_when_codes_is_none():
    meta = _metadata()
    _by_code(meta, "AAAAAA")["ScoreFunction"] = BAD_SF
    result = validate_custom_metadata(meta)
    assert any(e.field == "ScoreFunction" for e in result.errors)


def test_should_still_fail_structural_validation_on_unchanged_items():
    meta = _metadata()
    # Category CAT1 claims an indicator that does not exist.
    _by_code(meta, "CAT1")["IndicatorCodes"] = ["AAAAAA", "ZZZZZZ"]
    _by_code(meta, "CAT1")["Children"] = ["AAAAAA", "ZZZZZZ"]
    result = validate_custom_metadata(meta, score_function_codes=set())
    assert result.valid is False


def test_should_still_validate_goalpost_types_on_unchanged_indicators():
    meta = _metadata()
    _by_code(meta, "AAAAAA")["LowerGoalpost"] = "zero"
    result = validate_custom_metadata(meta, score_function_codes=set())
    assert any(e.field == "LowerGoalpost" for e in result.errors)


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------

COUNTRIES = ["USA", "CAN", "MEX"]
START, END = 2018, 2020


@pytest.fixture
def stubbed_scoring(monkeypatch):
    """Stub metadata/dataset/baseline fetches; record what was fetched."""
    calls = {"datasets": [], "baseline": []}
    monkeypatch.setattr(
        fcs.sspi_metadata, "country_group", lambda _g: list(COUNTRIES)
    )

    def fake_datasets(codes, countries, start, end):
        calls["datasets"].append(sorted(codes))
        n_years = end - start + 1
        return {
            c: np.full((len(countries), n_years), 50.0) for c in codes
        }
    monkeypatch.setattr(fcs, "fetch_all_datasets_aggregated", fake_datasets)

    baseline_values = {
        "AAAAAA": np.array([[0.1, 0.2, 0.3], [0.4, 0.5, 0.6],
                            [0.7, 0.8, 0.9]]),
        "CCCCCC": np.array([[0.9, 0.8, 0.7], [0.6, 0.5, 0.4],
                            [0.3, 0.2, 0.1]]),
    }

    def fake_baseline(codes, countries, start, end):
        calls["baseline"].append(list(codes))
        nan = np.full((len(countries), end - start + 1), np.nan)
        return {c: baseline_values.get(c, nan).copy() for c in codes}
    monkeypatch.setattr(fcs, "fetch_baseline_indicator_scores", fake_baseline)
    return calls, baseline_values


def _score(meta, modified, **kw):
    return fcs.score_custom_configuration_fast(
        meta, modified_indicators=modified, country_codes=COUNTRIES,
        start_year=START, end_year=END, **kw
    )


def _grid(docs):
    out = np.full((len(COUNTRIES), END - START + 1), np.nan)
    # Output docs are on the 0-100 scale; convert back to 0-1 for comparison.
    for d in docs:
        out[COUNTRIES.index(d["country_code"]), d["year"] - START] = (
            d["score"] / 100
        )
    return out


def test_should_fill_unchanged_indicators_from_baseline_and_compute_changed(
        stubbed_scoring):
    calls, baseline = stubbed_scoring
    result = _score(_metadata(), {"BBBBBB"})
    # Only the changed indicator's dataset is fetched from raw data.
    assert calls["datasets"] == [["DS_B"]]
    assert calls["baseline"] == [["AAAAAA", "CCCCCC"]]
    np.testing.assert_allclose(
        _grid(result["AAAAAA"]), baseline["AAAAAA"], rtol=1e-12
    )
    np.testing.assert_allclose(
        _grid(result["CCCCCC"]), baseline["CCCCCC"], rtol=1e-12
    )
    # Computed: goalpost(50, 0, 100) = 0.5 everywhere.
    np.testing.assert_allclose(_grid(result["BBBBBB"]), 0.5)


def test_should_aggregate_over_mixed_baseline_and_computed_rows(stubbed_scoring):
    _, baseline = stubbed_scoring
    result = _score(_metadata(), {"BBBBBB"})
    cat1 = _grid(result["CAT1"])
    expected = (baseline["AAAAAA"] + 0.5) / 2
    np.testing.assert_allclose(cat1, expected)


def test_should_not_fetch_raw_datasets_when_nothing_changed(stubbed_scoring):
    calls, baseline = stubbed_scoring
    result = _score(_metadata(), set())
    assert calls["datasets"] == []
    # BBBBBB has no baseline row in the stub -> all NaN -> dropped, as today.
    assert "BBBBBB" not in result
    np.testing.assert_allclose(
        _grid(result["AAAAAA"]), baseline["AAAAAA"], rtol=1e-12
    )


def test_should_compute_every_indicator_when_modified_set_is_none(
        stubbed_scoring):
    calls, _ = stubbed_scoring
    result = _score(_metadata(), None)
    assert calls["baseline"] == []
    assert calls["datasets"] == [["DS_A", "DS_B", "DS_C"]]
    np.testing.assert_allclose(_grid(result["AAAAAA"]), 0.5)


def test_should_use_supplied_default_scores_instead_of_store(
        stubbed_scoring):
    calls, _ = stubbed_scoring
    default_scores = {
        "AAAAAA": [{"CountryCode": "USA", "Year": 2018, "Score": 0.25},
                   {"CountryCode": "ZZZ", "Year": 2018, "Score": 0.99},
                   {"CountryCode": "CAN", "Year": 1999, "Score": 0.99}],
        "CCCCCC": [],
    }
    result = _score(_metadata(), {"BBBBBB"}, default_scores=default_scores)
    assert calls["baseline"] == []
    grid = _grid(result["AAAAAA"])
    assert grid[0, 0] == 0.25
    assert np.isnan(grid[1:]).all()


def test_should_leave_nan_when_baseline_missing_for_country_year(monkeypatch):
    class FakeStore:
        def find(self, query, projection=None):
            assert query["ItemCode"]["$in"] == ["AAAAAA"]
            return iter([
                {"ItemCode": "AAAAAA", "CountryCode": "CAN", "Year": 2019,
                 "Score": 0.42},
                {"ItemCode": "AAAAAA", "CountryCode": "CAN", "Year": 2030,
                 "Score": 0.1},
                {"ItemCode": "AAAAAA", "CountryCode": "XXX", "Year": 2019,
                 "Score": 0.1},
                {"ItemCode": "AAAAAA", "CountryCode": "USA", "Year": 2019,
                 "Score": None},
            ])
    monkeypatch.setattr(fcs, "sspi_item_data", FakeStore())
    arrays = fcs.fetch_baseline_indicator_scores(
        ["AAAAAA"], COUNTRIES, START, END
    )
    grid = arrays["AAAAAA"]
    assert grid[1, 1] == 0.42
    assert np.isnan(grid).sum() == grid.size - 1


# ---------------------------------------------------------------------------
# Builder-saved shape: goalposts live in the ScoreFunction, fields are None
# ---------------------------------------------------------------------------

def _as_saved_by_builder(metadata):
    """The builder saves LowerGoalpost/UpperGoalpost as None and the
    ScoreFunction without the YAML trailing newline."""
    saved = copy.deepcopy(metadata)
    for item in saved:
        if item.get("ItemType") == "Indicator":
            item["LowerGoalpost"] = None
            item["UpperGoalpost"] = None
            item["ScoreFunction"] = item["ScoreFunction"].rstrip("\n")
    return saved


def test_should_treat_indicators_as_unchanged_when_builder_saved_goalposts_as_none(
        default_metadata):
    result = cd.identify_modified_indicators(_as_saved_by_builder(_metadata()))
    assert result.modified_indicators == set()
    assert result.unchanged_indicators == {"AAAAAA", "BBBBBB", "CCCCCC"}


def test_should_mark_changed_when_builder_saved_config_edits_the_score_function(
        default_metadata):
    meta = _as_saved_by_builder(_metadata())
    _by_code(meta, "BBBBBB")["ScoreFunction"] = "Score = goalpost(DS_B, 10, 100)"
    result = cd.identify_modified_indicators(meta)
    assert result.modified_indicators == {"BBBBBB"}


def test_should_mark_changed_when_an_explicit_goalpost_differs_from_default(
        default_metadata):
    meta = _metadata()
    _by_code(meta, "CCCCCC")["UpperGoalpost"] = 90
    result = cd.identify_modified_indicators(meta)
    assert result.modified_indicators == {"CCCCCC"}


def test_should_inherit_only_the_unset_goalpost_when_one_is_explicit(
        default_metadata):
    meta = _metadata()
    _by_code(meta, "AAAAAA")["LowerGoalpost"] = None
    _by_code(meta, "AAAAAA")["UpperGoalpost"] = 80
    result = cd.identify_modified_indicators(meta)
    assert result.modified_indicators == {"AAAAAA"}
