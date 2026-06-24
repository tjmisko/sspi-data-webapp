"""
Unit tests for the per-child Weight data model in the metadata hasher (F1).

These are pure-function tests (no Flask app / Mongo) covering:
- Weight participates in CONFIG_HASH_FIELDS / SCORING_RELEVANT_FIELDS.
- Two configs differing only by a Weight hash differently.
- Identical configs hash identically (deterministic).
- A weightless config is byte-identical in canonical form to pre-F1 (no
  injected Weight default) -> its config hash is unchanged by F1.
- canonicalize_value preserves fractional weights like 0.5 / 0.25.
"""
import copy

from sspi_flask_app.api.resources.metadata_validator import (
    CONFIG_HASH_FIELDS,
    SCORING_RELEVANT_FIELDS,
    canonicalize_item,
    canonicalize_value,
    compute_config_hash,
    compute_indicator_hash,
)


def _metadata(weight_i1=None, weight_i2=None):
    """Minimal 1-pillar / 1-category / 2-indicator structure.

    Optional weights are attached to the two indicators only when provided.
    """
    i1 = {
        "ItemType": "Indicator", "ItemCode": "INDIC1", "ItemName": "I1",
        "IndicatorCode": "INDIC1", "DatasetCodes": ["DS_ONE"],
        "ScoreFunction": "Score = goalpost(DS_ONE, 0, 100)", "Children": [],
        "TreeIndex": [0, 0, 0, 0],
    }
    i2 = {
        "ItemType": "Indicator", "ItemCode": "INDIC2", "ItemName": "I2",
        "IndicatorCode": "INDIC2", "DatasetCodes": ["DS_TWO"],
        "ScoreFunction": "Score = goalpost(DS_TWO, 0, 100)", "Children": [],
        "TreeIndex": [0, 0, 0, 1],
    }
    if weight_i1 is not None:
        i1["Weight"] = weight_i1
    if weight_i2 is not None:
        i2["Weight"] = weight_i2
    return [
        {"ItemType": "SSPI", "ItemCode": "SSPI", "ItemName": "SSPI",
         "Children": ["PILLR1"], "PillarCodes": ["PILLR1"], "TreeIndex": [0]},
        {"ItemType": "Pillar", "ItemCode": "PILLR1", "ItemName": "P1",
         "PillarCode": "PILLR1", "Children": ["CATG01"],
         "CategoryCodes": ["CATG01"], "TreeIndex": [0, 0]},
        {"ItemType": "Category", "ItemCode": "CATG01", "ItemName": "C1",
         "CategoryCode": "CATG01", "PillarCode": "PILLR1",
         "Children": ["INDIC1", "INDIC2"],
         "IndicatorCodes": ["INDIC1", "INDIC2"], "TreeIndex": [0, 0, 0]},
        i1, i2,
    ]


def test_weight_in_field_allowlists():
    assert "Weight" in CONFIG_HASH_FIELDS
    assert "Weight" in SCORING_RELEVANT_FIELDS


def test_config_hash_differs_when_only_a_weight_differs():
    a = _metadata(weight_i1=0.75, weight_i2=0.25)
    b = _metadata(weight_i1=0.5, weight_i2=0.5)
    assert compute_config_hash(a) != compute_config_hash(b)


def test_config_hash_is_deterministic_for_identical_structures():
    a = _metadata(weight_i1=0.6, weight_i2=0.4)
    b = copy.deepcopy(a)
    assert compute_config_hash(a) == compute_config_hash(b)


def test_weightless_config_hash_unchanged_by_weight_field():
    # Adding a Weight to even one sibling must change the hash relative to the
    # weightless baseline; the weightless baseline must not gain an injected
    # default.
    weightless = _metadata()
    weighted = _metadata(weight_i1=0.5, weight_i2=0.5)
    assert compute_config_hash(weightless) != compute_config_hash(weighted)
    # Canonical form of a weightless indicator carries no Weight key.
    canon = canonicalize_item(weightless[-1])
    assert "Weight" not in canon


def test_canonicalize_preserves_fractional_weights():
    assert canonicalize_value(0.5) == 0.5
    assert canonicalize_value(0.25) == 0.25
    # A whole-number weight collapses to int (1.0 -> 1) but stays equal.
    assert canonicalize_value(1.0) == 1
    canon = canonicalize_item({"ItemCode": "INDIC1", "ItemType": "Indicator",
                               "Weight": 0.5})
    assert canon["Weight"] == 0.5


def test_indicator_hash_changes_with_weight():
    base = {"ItemCode": "INDIC1", "DatasetCodes": ["DS_ONE"],
            "ScoreFunction": "Score = goalpost(DS_ONE, 0, 100)"}
    weighted = dict(base, Weight=0.7)
    assert compute_indicator_hash(base) != compute_indicator_hash(weighted)
    # Same weight -> same hash.
    assert compute_indicator_hash(dict(base, Weight=0.7)) == \
        compute_indicator_hash(weighted)
