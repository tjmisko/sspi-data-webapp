"""
Unit tests for per-parent normalized weights in
FastCustomSSPI._build_score_matrix (F2).

Building a FastCustomSSPI does no Mongo I/O (it only reads the in-memory
metadata list), so these run offline. They cover:
- Equal-weight invariance: a weightless fixture reproduces the legacy
  ``(1/n_ind)/n_cat/n_pillar`` matrix exactly (the E1 parity guardrail).
- Custom weights at the category, pillar, and SSPI levels shift the matrix
  columns toward the heavier child and propagate as products.
- Defensive normalization by the actual sibling sum (weights that don't sum to
  1.0 are renormalized).
- Mixed and zero-sum sibling sets fall back to equal weighting.
"""
import numpy as np
import pytest

from sspi_flask_app.api.resources.fast_custom_scoring import FastCustomSSPI


# =============================================================================
# Fixtures: metadata builders
# =============================================================================

def _single_chain(weights=None):
    """SSPI -> P1 -> C1 -> [I1, I2]. weights: dict of code -> Weight."""
    weights = weights or {}
    items = [
        {"ItemType": "SSPI", "ItemCode": "SSPI", "ItemName": "SSPI",
         "Children": ["PILLR1"], "PillarCodes": ["PILLR1"]},
        {"ItemType": "Pillar", "ItemCode": "PILLR1", "ItemName": "P1",
         "Children": ["CATG01"], "CategoryCodes": ["CATG01"]},
        {"ItemType": "Category", "ItemCode": "CATG01", "ItemName": "C1",
         "Children": ["INDIC1", "INDIC2"], "IndicatorCodes": ["INDIC1", "INDIC2"]},
        {"ItemType": "Indicator", "ItemCode": "INDIC1", "ItemName": "I1",
         "Children": []},
        {"ItemType": "Indicator", "ItemCode": "INDIC2", "ItemName": "I2",
         "Children": []},
    ]
    for item in items:
        if item["ItemCode"] in weights:
            item["Weight"] = weights[item["ItemCode"]]
    return items


def _two_pillars(weights=None):
    """SSPI -> [P1, P2]; P1 -> C1 -> [I1, I2]; P2 -> C2 -> [I3]."""
    weights = weights or {}
    items = [
        {"ItemType": "SSPI", "ItemCode": "SSPI", "ItemName": "SSPI",
         "Children": ["PILLR1", "PILLR2"], "PillarCodes": ["PILLR1", "PILLR2"]},
        {"ItemType": "Pillar", "ItemCode": "PILLR1", "ItemName": "P1",
         "Children": ["CATG01"], "CategoryCodes": ["CATG01"]},
        {"ItemType": "Pillar", "ItemCode": "PILLR2", "ItemName": "P2",
         "Children": ["CATG02"], "CategoryCodes": ["CATG02"]},
        {"ItemType": "Category", "ItemCode": "CATG01", "ItemName": "C1",
         "Children": ["INDIC1", "INDIC2"], "IndicatorCodes": ["INDIC1", "INDIC2"]},
        {"ItemType": "Category", "ItemCode": "CATG02", "ItemName": "C2",
         "Children": ["INDIC3"], "IndicatorCodes": ["INDIC3"]},
        {"ItemType": "Indicator", "ItemCode": "INDIC1", "ItemName": "I1",
         "Children": []},
        {"ItemType": "Indicator", "ItemCode": "INDIC2", "ItemName": "I2",
         "Children": []},
        {"ItemType": "Indicator", "ItemCode": "INDIC3", "ItemName": "I3",
         "Children": []},
    ]
    for item in items:
        if item["ItemCode"] in weights:
            item["Weight"] = weights[item["ItemCode"]]
    return items


def _legacy_matrix(metadata):
    """Reconstruct the pre-F2 equal-weight matrix via the old 1/n chaining."""
    eng = FastCustomSSPI(metadata)
    n_ind = len(eng.indicator_codes)
    n_cat = len(eng.category_codes)
    n_pil = len(eng.pillar_codes)
    matrix = np.zeros((n_ind, n_cat + n_pil + 1))

    def children(item, *fields):
        for f in fields:
            v = item.get(f)
            if v:
                return v
        return []

    for ii, ind in enumerate(eng.indicator_codes):
        cat = eng._find_parent(ind, "Category")
        cat_children = children(cat, "IndicatorCodes", "Children")
        cat_w = 1.0 / len(cat_children)
        matrix[ii, eng.category_codes.index(cat["ItemCode"])] = cat_w
        pil = eng._find_parent(cat["ItemCode"], "Pillar")
        pil_children = children(pil, "CategoryCodes", "Children")
        pil_w = cat_w / len(pil_children)
        matrix[ii, n_cat + eng.pillar_codes.index(pil["ItemCode"])] = pil_w
        sspi = eng._find_parent(pil["ItemCode"], "SSPI")
        sspi_children = children(sspi, "PillarCodes", "Children")
        sspi_w = pil_w / len(sspi_children)
        matrix[ii, n_cat + n_pil] = sspi_w
    return matrix


def _col(eng, code):
    """Column index of a category/pillar/SSPI item in the score matrix."""
    return eng.item_codes.index(code)


def _row(eng, code):
    return eng.indicator_codes.index(code)


# =============================================================================
# Equal-weight invariance (the parity guardrail)
# =============================================================================

class TestEqualWeightInvariance:
    @pytest.mark.parametrize("builder", [_single_chain, _two_pillars])
    def test_no_weights_reproduces_legacy_matrix(self, builder):
        metadata = builder()
        eng = FastCustomSSPI(metadata)
        legacy = _legacy_matrix(metadata)
        assert np.allclose(eng.score_matrix, legacy), (
            f"\nnew:\n{eng.score_matrix}\nlegacy:\n{legacy}"
        )

    def test_columns_sum_to_one_per_parent(self):
        # Each parent column must sum to 1.0 across its indicator contributions
        # so aggregation (a weighted SUM) yields a proper average.
        eng = FastCustomSSPI(_two_pillars())
        col_sums = eng.score_matrix.sum(axis=0)
        # C1 has 2 indicators, C2 has 1, P1/P2 each cover their indicators,
        # SSPI covers all 3. Every column should sum to 1.0.
        assert np.allclose(col_sums, 1.0), col_sums


# =============================================================================
# Custom weights shift the matrix
# =============================================================================

class TestCustomWeights:
    def test_category_level_weights(self):
        eng = FastCustomSSPI(_single_chain({"INDIC1": 0.75, "INDIC2": 0.25}))
        c1 = _col(eng, "CATG01")
        assert eng.score_matrix[_row(eng, "INDIC1"), c1] == pytest.approx(0.75)
        assert eng.score_matrix[_row(eng, "INDIC2"), c1] == pytest.approx(0.25)
        # Heavier child dominates; column still sums to 1.0.
        assert eng.score_matrix[:, c1].sum() == pytest.approx(1.0)

    def test_category_weight_propagates_to_pillar_and_sspi(self):
        eng = FastCustomSSPI(_single_chain({"INDIC1": 0.75, "INDIC2": 0.25}))
        # C1 is the only category in P1, and P1 the only pillar, so the 0.75
        # propagates unchanged up to SSPI.
        for parent in ("CATG01", "PILLR1", "SSPI"):
            col = _col(eng, parent)
            assert eng.score_matrix[_row(eng, "INDIC1"), col] == pytest.approx(0.75)
            assert eng.score_matrix[_row(eng, "INDIC2"), col] == pytest.approx(0.25)

    def test_pillar_level_weights(self):
        eng = FastCustomSSPI(_two_pillars({"PILLR1": 0.8, "PILLR2": 0.2}))
        sspi = _col(eng, "SSPI")
        # I1 = cat(0.5) * (C1 in P1 = 1) * (P1 in SSPI = 0.8) = 0.4
        assert eng.score_matrix[_row(eng, "INDIC1"), sspi] == pytest.approx(0.4)
        assert eng.score_matrix[_row(eng, "INDIC2"), sspi] == pytest.approx(0.4)
        # I3 = cat(1) * (C2 in P2 = 1) * (P2 in SSPI = 0.2) = 0.2
        assert eng.score_matrix[_row(eng, "INDIC3"), sspi] == pytest.approx(0.2)
        # SSPI column still sums to 1.0 (0.4 + 0.4 + 0.2).
        assert eng.score_matrix[:, sspi].sum() == pytest.approx(1.0)

    def test_weights_renormalized_by_actual_sibling_sum(self):
        # Weights that do not sum to 1.0 are normalized by their actual sum.
        eng = FastCustomSSPI(_single_chain({"INDIC1": 0.6, "INDIC2": 0.2}))
        c1 = _col(eng, "CATG01")
        assert eng.score_matrix[_row(eng, "INDIC1"), c1] == pytest.approx(0.6 / 0.8)
        assert eng.score_matrix[_row(eng, "INDIC2"), c1] == pytest.approx(0.2 / 0.8)
        assert eng.score_matrix[:, c1].sum() == pytest.approx(1.0)


# =============================================================================
# Fallbacks: mixed and zero-sum sibling sets revert to equal weight
# =============================================================================

class TestWeightFallbacks:
    def test_mixed_weights_fall_back_to_equal(self):
        # Only one of two indicators carries a weight -> ambiguous -> equal.
        eng = FastCustomSSPI(_single_chain({"INDIC1": 0.75}))
        c1 = _col(eng, "CATG01")
        assert eng.score_matrix[_row(eng, "INDIC1"), c1] == pytest.approx(0.5)
        assert eng.score_matrix[_row(eng, "INDIC2"), c1] == pytest.approx(0.5)

    def test_zero_sum_weights_fall_back_to_equal(self):
        eng = FastCustomSSPI(_single_chain({"INDIC1": 0.0, "INDIC2": 0.0}))
        c1 = _col(eng, "CATG01")
        assert eng.score_matrix[_row(eng, "INDIC1"), c1] == pytest.approx(0.5)
        assert eng.score_matrix[_row(eng, "INDIC2"), c1] == pytest.approx(0.5)


# =============================================================================
# Aggregation direction: weighting shifts the parent score toward heavy child
# =============================================================================

class TestAggregationDirection:
    def _aggregate_one_cell(self, eng, ind_scores):
        # ind_scores: dict indicator_code -> score in [0, 1]; single cell.
        n = len(eng.indicator_codes)
        vec = np.zeros((n, 1, 1))
        for code, val in ind_scores.items():
            vec[_row(eng, code), 0, 0] = val
        return eng.aggregate(vec)

    def test_category_moves_toward_heavier_indicator(self):
        scores = {"INDIC1": 0.9, "INDIC2": 0.1}
        equal = FastCustomSSPI(_single_chain())
        weighted = FastCustomSSPI(_single_chain({"INDIC1": 0.75, "INDIC2": 0.25}))
        c1_equal = self._aggregate_one_cell(equal, scores)
        c1_weighted = self._aggregate_one_cell(weighted, scores)
        col = _col(equal, "CATG01")
        equal_val = c1_equal[col, 0, 0]
        weighted_val = c1_weighted[col, 0, 0]
        # Equal -> 0.5; weighting toward the high (0.9) indicator raises it.
        assert equal_val == pytest.approx(0.5)
        assert weighted_val == pytest.approx(0.75 * 0.9 + 0.25 * 0.1)
        assert weighted_val > equal_val
