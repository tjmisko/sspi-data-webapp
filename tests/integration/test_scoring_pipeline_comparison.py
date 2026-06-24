"""
Scoring pipeline parity test (E1) — slow oracle vs fast engine.

This module is the *guardrail* for the custom-scoring weight work (Phase F).
It proves that the production fast engine
(:func:`score_custom_configuration_fast`) and the dormant slow reference
oracle (:func:`score_custom_configuration`) compute the **same** scores and
ranks at all four hierarchy levels (Indicator -> Category -> Pillar -> SSPI) in
the current *equal-weight* regime.

Why two engines?
- The fast engine (``fast_custom_scoring.py``) is the only pipeline wired into
  production; it builds a ``FastCustomSSPI`` score matrix and aggregates via a
  single matrix multiply.
- The slow engine (``custom_scoring.py``) is defined but unused by the live
  pipeline. It walks the hierarchy with plain Python means and a stable sort.
  We keep it as an independent *oracle*: if the two engines ever disagree on a
  fixture where they are constructed to agree, one of them has a bug.

F2 (weighted score matrix) replaces the fast engine's hard-coded ``1/n`` weights
with per-parent normalized weights. With equal weights the output MUST be
bit-for-bit what it is today, so this test must stay green after F2. Do NOT
"adjust" these equal-weight assertions to make a weighted change pass.

------------------------------------------------------------------------------
PARITY CONTRACT (the known, deliberate divergences between the two engines and
how this test pins them — F2 inherits this contract):

1. Imputation. The two engines impute missing data with *different* code
   (``impute_dataset`` vs ``impute_dataset_vectorized``). They agree on
   linear interpolation of an *interior* gap (identical formula) and on
   constant forward/backward fill, but they diverge on partial-children
   aggregation. Therefore every fixture here seeds data so that every indicator
   has a score at every (country, year) AFTER imputation. Concretely the main
   fixture seeds COMPLETE data (no gaps); a focused imputation case uses a
   single *interior* gap on a constant-valued series, where both engines fill
   the identical value.

2. Partial-children aggregation. The slow engine averages only the *present*
   children and renormalizes; the fast engine propagates NaN (a missing child
   makes the parent NaN, and NaN parents are dropped). Because (1) guarantees
   every child is present, this divergence never fires here. Do not rely on it.

3. Ranking tie-breaks. The fast engine ranks with ``np.argsort`` (NOT stable);
   the slow engine ranks with Python's stable ``sorted``. For *tied* scores the
   two engines may hand the tied countries different rank *numbers*. This test
   therefore pins ranking via the **rank -> score mapping**: for each
   (item, year) the score sitting at rank ``r`` must be identical across
   engines (tolerance ``1e-6``). Tied countries share a score, so this is
   invariant to which tied country won which adjacent rank. A dedicated tie
   case additionally asserts the tied countries occupy a contiguous rank pair
   in both engines and that every non-tied country's rank matches exactly.

4. The ``imputed`` / ``imputation_method`` fields are NOT part of the parity
   contract (the fast dict serializer hard-codes ``imputed=False``). Only
   ``score`` and ``rank`` are compared.

5. Both engines emit ``score`` on the 0-100 scale (indicator score * 100, then
   plain means up the hierarchy). Compared with absolute tolerance 1e-6.

NOTE: these tests need a live MongoDB. Importing the app / engines connects to
Mongo, and the fixtures seed and then delete rows in ``sspi_clean_api_data``
using a unique synthetic ``DatasetCode`` prefix so real collections are never
touched. Run with the dev Mongo up:

    pytest tests/integration/test_scoring_pipeline_comparison.py -v
"""
import collections

import pytest

from sspi_flask_app.models.database import sspi_clean_api_data
from sspi_flask_app.api.resources.custom_scoring import score_custom_configuration
from sspi_flask_app.api.resources.fast_custom_scoring import (
    score_custom_configuration_fast,
)


# =============================================================================
# Constants
# =============================================================================

SCORE_TOL = 1e-6
DS_PREFIX = "WGTPARITY_"  # synthetic dataset codes — never collide with real data
COUNTRIES = ["USA", "CAN", "MEX", "BRA"]
START_YEAR = 2000
END_YEAR = 2023
YEARS = list(range(START_YEAR, END_YEAR + 1))

# USA and CAN are seeded with IDENTICAL raw values for every dataset, so they
# tie at every hierarchy level and every year. This gives the tie-ranking case
# for free. MEX and BRA carry distinct values.
#
# raw value tables: dataset_suffix -> {country -> constant value across years}
RAW_VALUES = {
    "D1": {"USA": 80, "CAN": 80, "MEX": 60, "BRA": 40},  # plain   -> I1
    "D2": {"USA": 20, "CAN": 20, "MEX": 50, "BRA": 70},  # inverted-> I2
    "D3": {"USA": 60, "CAN": 60, "MEX": 40, "BRA": 90},  # custom a-> I3
    "D4": {"USA": 40, "CAN": 40, "MEX": 80, "BRA": 50},  # custom b-> I3
    "D5": {"USA": 70, "CAN": 70, "MEX": 30, "BRA": 60},  # plain   -> I4
    "D6": {"USA": 90, "CAN": 90, "MEX": 20, "BRA": 80},  # plain   -> I5
    "D7": {"USA": 30, "CAN": 30, "MEX": 60, "BRA": 20},  # inverted-> I6
    "D8": {"USA": 50, "CAN": 50, "MEX": 70, "BRA": 30},  # plain   -> I7
    "D9": {"USA": 40, "CAN": 40, "MEX": 50, "BRA": 90},  # plain   -> I8
}


def _ds(suffix: str) -> str:
    return f"{DS_PREFIX}{suffix}"


def _seed_docs(raw_values: dict, skip: set | None = None) -> list[dict]:
    """Build complete clean-data docs for the given raw-value tables.

    ``skip`` is a set of (dataset_code, country, year) tuples to omit (used to
    punch an interior gap for the imputation case).
    """
    skip = skip or set()
    docs = []
    for suffix, by_country in raw_values.items():
        ds_code = _ds(suffix)
        for country, value in by_country.items():
            for year in YEARS:
                if (ds_code, country, year) in skip:
                    continue
                docs.append({
                    "DatasetCode": ds_code,
                    "CountryCode": country,
                    "Year": year,
                    "Value": float(value),
                    "Unit": "Index",
                })
    return docs


def _build_metadata() -> list[dict]:
    """2 pillars x 2 categories x 2 indicators covering all score-fn shapes.

    Goalpost literals match LowerGoalpost/UpperGoalpost so the fast engine's
    simple-goalpost fast path (which reads the metadata goalposts, not the call
    literals) agrees with the slow engine's safe_eval of the literal call.
    """
    def plain(code, ds):
        return {
            "ItemType": "Indicator", "ItemCode": code, "ItemName": code,
            "IndicatorCode": code, "DatasetCodes": [_ds(ds)],
            "ScoreFunction": f"Score = goalpost({_ds(ds)}, 0, 100)",
            "LowerGoalpost": 0, "UpperGoalpost": 100, "Children": [],
        }

    def inverted(code, ds):
        return {
            "ItemType": "Indicator", "ItemCode": code, "ItemName": code,
            "IndicatorCode": code, "DatasetCodes": [_ds(ds)],
            "ScoreFunction": f"Score = goalpost(-{_ds(ds)}, -100, 0)",
            "LowerGoalpost": 0, "UpperGoalpost": 100, "Children": [],
        }

    def custom_avg(code, ds_a, ds_b):
        return {
            "ItemType": "Indicator", "ItemCode": code, "ItemName": code,
            "IndicatorCode": code, "DatasetCodes": [_ds(ds_a), _ds(ds_b)],
            "ScoreFunction": (
                f"Score = average(goalpost({_ds(ds_a)}, 0, 100), "
                f"goalpost({_ds(ds_b)}, 0, 100))"
            ),
            "LowerGoalpost": 0, "UpperGoalpost": 100, "Children": [],
        }

    return [
        {"ItemType": "SSPI", "ItemCode": "SSPI", "ItemName": "SSPI",
         "Children": ["PILLR1", "PILLR2"], "PillarCodes": ["PILLR1", "PILLR2"]},
        # Pillar 1
        {"ItemType": "Pillar", "ItemCode": "PILLR1", "ItemName": "Pillar 1",
         "PillarCode": "PILLR1", "Children": ["CATG01", "CATG02"],
         "CategoryCodes": ["CATG01", "CATG02"]},
        {"ItemType": "Category", "ItemCode": "CATG01", "ItemName": "Cat 1",
         "CategoryCode": "CATG01", "PillarCode": "PILLR1",
         "Children": ["INDIC1", "INDIC2"], "IndicatorCodes": ["INDIC1", "INDIC2"]},
        {"ItemType": "Category", "ItemCode": "CATG02", "ItemName": "Cat 2",
         "CategoryCode": "CATG02", "PillarCode": "PILLR1",
         "Children": ["INDIC3", "INDIC4"], "IndicatorCodes": ["INDIC3", "INDIC4"]},
        # Pillar 2
        {"ItemType": "Pillar", "ItemCode": "PILLR2", "ItemName": "Pillar 2",
         "PillarCode": "PILLR2", "Children": ["CATG03", "CATG04"],
         "CategoryCodes": ["CATG03", "CATG04"]},
        {"ItemType": "Category", "ItemCode": "CATG03", "ItemName": "Cat 3",
         "CategoryCode": "CATG03", "PillarCode": "PILLR2",
         "Children": ["INDIC5", "INDIC6"], "IndicatorCodes": ["INDIC5", "INDIC6"]},
        {"ItemType": "Category", "ItemCode": "CATG04", "ItemName": "Cat 4",
         "CategoryCode": "CATG04", "PillarCode": "PILLR2",
         "Children": ["INDIC7", "INDIC8"], "IndicatorCodes": ["INDIC7", "INDIC8"]},
        # Indicators — one of each score-function shape
        plain("INDIC1", "D1"),
        inverted("INDIC2", "D2"),
        custom_avg("INDIC3", "D3", "D4"),
        plain("INDIC4", "D5"),
        plain("INDIC5", "D6"),
        inverted("INDIC6", "D7"),
        plain("INDIC7", "D8"),
        plain("INDIC8", "D9"),
    ]


# Hierarchy bookkeeping used by assertions.
INDICATOR_CODES = [f"INDIC{i}" for i in range(1, 9)]
CATEGORY_CODES = ["CATG01", "CATG02", "CATG03", "CATG04"]
PILLAR_CODES = ["PILLR1", "PILLR2"]
ALL_LEVEL_CODES = {
    "Indicator": INDICATOR_CODES,
    "Category": CATEGORY_CODES,
    "Pillar": PILLAR_CODES,
    "SSPI": ["SSPI"],
}


# =============================================================================
# Comparison helpers
# =============================================================================

def _index_by_cell(docs: list[dict]) -> dict:
    return {(d["country_code"], d["year"]): d for d in docs}


def _rank_to_score(docs: list[dict]) -> dict:
    """Map (year) -> {rank -> score}. Used for tie-robust rank parity."""
    out = collections.defaultdict(dict)
    for d in docs:
        out[d["year"]][d["rank"]] = d["score"]
    return out


# =============================================================================
# Fixtures — seed, run both engines once, clean up, share the results
# =============================================================================

@pytest.fixture(scope="module")
def complete_results(app):
    """Seed COMPLETE synthetic data, run both engines, delete the seed.

    Scoped to the module so the (relatively expensive) scoring runs once. The
    seeded rows are deleted as soon as both engines have read them, minimizing
    the window in which test data lives in the shared collection.
    """
    metadata = _build_metadata()
    docs = _seed_docs(RAW_VALUES)
    seeded_codes = sorted({_ds(s) for s in RAW_VALUES})

    # Defensive: clear any stragglers from a previous aborted run.
    sspi_clean_api_data.delete_many({"DatasetCode": {"$in": seeded_codes}})
    try:
        sspi_clean_api_data.insert_many(docs)
        slow = score_custom_configuration(metadata, country_codes=list(COUNTRIES))
        fast = score_custom_configuration_fast(metadata, country_codes=list(COUNTRIES))
    finally:
        sspi_clean_api_data.delete_many({"DatasetCode": {"$in": seeded_codes}})

    return {"metadata": metadata, "slow": slow, "fast": fast}


@pytest.fixture(scope="module")
def gap_results(app):
    """A single-category fixture with one interior gap to exercise imputation.

    DatasetCode WGTPARITY_G1 is constant 50 for every country/year EXCEPT USA's
    year 2010 which is omitted. Both engines fill 2010 by linear interpolation
    between the (equal) neighbours -> 50, so parity is guaranteed. The second
    indicator uses a complete constant series so the category always has both
    children present.
    """
    gap_country, gap_year = "USA", 2010
    raw = {
        "G1": {c: 50 for c in COUNTRIES},
        "G2": {"USA": 70, "CAN": 70, "MEX": 30, "BRA": 90},
    }
    skip = {(_ds("G1"), gap_country, gap_year)}
    docs = _seed_docs(raw, skip=skip)
    seeded_codes = sorted({_ds(s) for s in raw})

    metadata = [
        {"ItemType": "SSPI", "ItemCode": "SSPI", "ItemName": "SSPI",
         "Children": ["GPILLR"], "PillarCodes": ["GPILLR"]},
        {"ItemType": "Pillar", "ItemCode": "GPILLR", "ItemName": "GP",
         "PillarCode": "GPILLR", "Children": ["GCATEG"],
         "CategoryCodes": ["GCATEG"]},
        {"ItemType": "Category", "ItemCode": "GCATEG", "ItemName": "GC",
         "CategoryCode": "GCATEG", "PillarCode": "GPILLR",
         "Children": ["GIND01", "GIND02"], "IndicatorCodes": ["GIND01", "GIND02"]},
        {"ItemType": "Indicator", "ItemCode": "GIND01", "ItemName": "GIND01",
         "IndicatorCode": "GIND01", "DatasetCodes": [_ds("G1")],
         "ScoreFunction": f"Score = goalpost({_ds('G1')}, 0, 100)",
         "LowerGoalpost": 0, "UpperGoalpost": 100, "Children": []},
        {"ItemType": "Indicator", "ItemCode": "GIND02", "ItemName": "GIND02",
         "IndicatorCode": "GIND02", "DatasetCodes": [_ds("G2")],
         "ScoreFunction": f"Score = goalpost({_ds('G2')}, 0, 100)",
         "LowerGoalpost": 0, "UpperGoalpost": 100, "Children": []},
    ]

    sspi_clean_api_data.delete_many({"DatasetCode": {"$in": seeded_codes}})
    try:
        sspi_clean_api_data.insert_many(docs)
        slow = score_custom_configuration(metadata, country_codes=list(COUNTRIES))
        fast = score_custom_configuration_fast(metadata, country_codes=list(COUNTRIES))
    finally:
        sspi_clean_api_data.delete_many({"DatasetCode": {"$in": seeded_codes}})

    return {
        "metadata": metadata, "slow": slow, "fast": fast,
        "gap_country": gap_country, "gap_year": gap_year,
    }


# =============================================================================
# Score parity at all four levels
# =============================================================================

class TestScoreParity:
    """Scores must match between engines at every hierarchy level."""

    def test_same_item_codes_returned(self, complete_results):
        slow, fast = complete_results["slow"], complete_results["fast"]
        assert set(slow.keys()) == set(fast.keys())
        # Sanity: all four levels present.
        for codes in ALL_LEVEL_CODES.values():
            for code in codes:
                assert code in slow, f"{code} missing from slow result"
                assert code in fast, f"{code} missing from fast result"

    def test_same_cells_per_item(self, complete_results):
        slow, fast = complete_results["slow"], complete_results["fast"]
        for code in slow:
            slow_cells = {(d["country_code"], d["year"]) for d in slow[code]}
            fast_cells = {(d["country_code"], d["year"]) for d in fast[code]}
            assert slow_cells == fast_cells, f"cell sets differ for {code}"

    @pytest.mark.parametrize("level", ["Indicator", "Category", "Pillar", "SSPI"])
    def test_scores_match_at_level(self, complete_results, level):
        slow, fast = complete_results["slow"], complete_results["fast"]
        for code in ALL_LEVEL_CODES[level]:
            slow_idx = _index_by_cell(slow[code])
            fast_idx = _index_by_cell(fast[code])
            assert set(slow_idx) == set(fast_idx), f"cells differ for {code}"
            for cell, sdoc in slow_idx.items():
                fdoc = fast_idx[cell]
                assert abs(sdoc["score"] - fdoc["score"]) <= SCORE_TOL, (
                    f"{level} {code} @ {cell}: "
                    f"slow={sdoc['score']} fast={fdoc['score']}"
                )

    def test_scores_within_0_100(self, complete_results):
        for engine in ("slow", "fast"):
            for code, docs in complete_results[engine].items():
                for d in docs:
                    assert -SCORE_TOL <= d["score"] <= 100 + SCORE_TOL, (
                        f"{engine} {code} score out of band: {d['score']}"
                    )


# =============================================================================
# Indicator-level score-function shape checks (anchors the parity to truth)
# =============================================================================

class TestScoreFunctionShapes:
    """Pin the actual computed values for each score-function shape so a parity
    bug that corrupts *both* engines identically is still caught."""

    def _cell(self, docs_by_code, code, country, year=END_YEAR):
        for d in docs_by_code[code]:
            if d["country_code"] == country and d["year"] == year:
                return d
        raise AssertionError(f"no {code} doc for {country}/{year}")

    def test_plain_goalpost(self, complete_results):
        # INDIC1 = goalpost(D1, 0, 100); D1[MEX]=60 -> score 60.
        for engine in ("slow", "fast"):
            d = self._cell(complete_results[engine], "INDIC1", "MEX")
            assert abs(d["score"] - 60.0) <= SCORE_TOL

    def test_inverted_goalpost(self, complete_results):
        # INDIC2 = goalpost(-D2, -100, 0); D2[BRA]=70 -> 100-70 = 30.
        for engine in ("slow", "fast"):
            d = self._cell(complete_results[engine], "INDIC2", "BRA")
            assert abs(d["score"] - 30.0) <= SCORE_TOL

    def test_custom_average_function(self, complete_results):
        # INDIC3 = average(goalpost(D3,0,100), goalpost(D4,0,100));
        # MEX: (40 + 80)/2 = 60.
        for engine in ("slow", "fast"):
            d = self._cell(complete_results[engine], "INDIC3", "MEX")
            assert abs(d["score"] - 60.0) <= SCORE_TOL

    def test_aggregation_is_plain_mean_equal_weight(self, complete_results):
        # CATG01 = mean(INDIC1, INDIC2). BRA: I1=40, I2(inv D2=70)->30; mean=35.
        for engine in ("slow", "fast"):
            d = self._cell(complete_results[engine], "CATG01", "BRA")
            assert abs(d["score"] - 35.0) <= SCORE_TOL


# =============================================================================
# Rank parity (tie-robust contract)
# =============================================================================

class TestRankParity:
    """Ranks order countries by score; the rank->score mapping must be
    identical across engines (robust to tie-break differences)."""

    @pytest.mark.parametrize("level", ["Indicator", "Category", "Pillar", "SSPI"])
    def test_rank_to_score_mapping_matches(self, complete_results, level):
        slow, fast = complete_results["slow"], complete_results["fast"]
        for code in ALL_LEVEL_CODES[level]:
            slow_map = _rank_to_score(slow[code])
            fast_map = _rank_to_score(fast[code])
            assert set(slow_map) == set(fast_map), f"years differ for {code}"
            for year, srank in slow_map.items():
                frank = fast_map[year]
                assert set(srank) == set(frank), (
                    f"rank set differs for {code} {year}"
                )
                for rank, score in srank.items():
                    assert abs(score - frank[rank]) <= SCORE_TOL, (
                        f"{code} {year} rank {rank}: "
                        f"slow={score} fast={frank[rank]}"
                    )

    def test_ranks_are_a_permutation_of_1_to_n(self, complete_results):
        # Every country is present after imputation, so every (item, year)
        # assigns the ranks 1..n_countries exactly once.
        n = len(COUNTRIES)
        for engine in ("slow", "fast"):
            for code, docs in complete_results[engine].items():
                by_year = collections.defaultdict(list)
                for d in docs:
                    by_year[d["year"]].append(d["rank"])
                for year, ranks in by_year.items():
                    assert sorted(ranks) == list(range(1, n + 1)), (
                        f"{engine} {code} {year} ranks not 1..{n}: {sorted(ranks)}"
                    )


class TestTieRankingContract:
    """USA and CAN are seeded identically, so they tie at every level. Pin the
    explicit tie contract that F2 must preserve."""

    def test_usa_can_tie_at_sspi(self, complete_results):
        for engine in ("slow", "fast"):
            sspi = _index_by_cell(complete_results[engine]["SSPI"])
            for year in YEARS:
                usa = sspi[("USA", year)]["score"]
                can = sspi[("CAN", year)]["score"]
                assert abs(usa - can) <= SCORE_TOL, (
                    f"{engine} USA/CAN not tied @ {year}: {usa} vs {can}"
                )

    def test_tied_pair_occupies_contiguous_ranks(self, complete_results):
        # In both engines the two tied countries must take an adjacent rank
        # pair {k, k+1}, and the non-tied countries must get identical ranks.
        for code in ["SSPI", "PILLR1", "PILLR2", "CATG01"]:
            for engine in ("slow", "fast"):
                idx = _index_by_cell(complete_results[engine][code])
                for year in YEARS:
                    usa_rank = idx[("USA", year)]["rank"]
                    can_rank = idx[("CAN", year)]["rank"]
                    assert abs(usa_rank - can_rank) == 1, (
                        f"{engine} {code} {year}: USA/CAN ranks not adjacent "
                        f"({usa_rank}, {can_rank})"
                    )

    def test_non_tied_country_ranks_match_exactly(self, complete_results):
        # MEX and BRA are distinct from the tied pair and from each other at the
        # SSPI level, so their exact rank numbers must match across engines.
        slow = _index_by_cell(complete_results["slow"]["SSPI"])
        fast = _index_by_cell(complete_results["fast"]["SSPI"])
        for year in YEARS:
            for country in ("MEX", "BRA"):
                assert slow[(country, year)]["rank"] == fast[(country, year)]["rank"], (
                    f"SSPI {country} {year} rank differs: "
                    f"slow={slow[(country, year)]['rank']} "
                    f"fast={fast[(country, year)]['rank']}"
                )


# =============================================================================
# Imputation parity (interior gap)
# =============================================================================

class TestImputationParity:
    """A single interior gap must be filled identically by both engines, and
    the gapped indicator must still score at the gap year."""

    def test_gap_indicator_scored_at_gap_year(self, gap_results):
        gc, gy = gap_results["gap_country"], gap_results["gap_year"]
        for engine in ("slow", "fast"):
            cells = {
                (d["country_code"], d["year"]) for d in gap_results[engine]["GIND01"]
            }
            assert (gc, gy) in cells, f"{engine} missing imputed cell {(gc, gy)}"

    def test_gap_value_is_constant_fill(self, gap_results):
        gc, gy = gap_results["gap_country"], gap_results["gap_year"]
        # Constant series of 50 -> goalpost(50,0,100) = 50.
        for engine in ("slow", "fast"):
            doc = next(
                d for d in gap_results[engine]["GIND01"]
                if d["country_code"] == gc and d["year"] == gy
            )
            assert abs(doc["score"] - 50.0) <= SCORE_TOL

    def test_full_parity_with_gap(self, gap_results):
        slow, fast = gap_results["slow"], gap_results["fast"]
        assert set(slow.keys()) == set(fast.keys())
        for code in slow:
            slow_idx = _index_by_cell(slow[code])
            fast_idx = _index_by_cell(fast[code])
            assert set(slow_idx) == set(fast_idx), f"cells differ for {code}"
            for cell, sdoc in slow_idx.items():
                fdoc = fast_idx[cell]
                assert abs(sdoc["score"] - fdoc["score"]) <= SCORE_TOL, (
                    f"{code} @ {cell}: slow={sdoc['score']} fast={fdoc['score']}"
                )
