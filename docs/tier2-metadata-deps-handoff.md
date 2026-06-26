# Handoff: Tier 2 — `sspi_metadata` dependency-walker N+1 fix

**Date:** 2026-06-26
**Branch:** `perf/tier2-metadata-deps` (created off `main`; this doc is the only commit so far)
**Status:** Done — the three core walkers are refactored (query counts verified to
drop 33→12, 20→8, 2→1 on the 5-node test fixture with byte-identical output). The
branch then grew to cover **all of Tier 2** from the audit: `get_child_details` and
`get_country_groups` (the two optional smaller wins), the `dashboard.py` N+1 hotspots
(rank map, country-group map, characteristics `$in`), the `query_builder` source-info
batch, the `fast_custom_scoring` parent map + deferred stack (K/L), and the
`mongo_wrapper` quadratic flatten (M). `utilities.py:903` was evaluated and skipped
(the un-batchable `raw_data_available` is the dominant per-dataset query there, and the
existing tests assert the `get_source_info` call count). `tests/unit` reports 968 passed
/ 7 pre-existing errors throughout.
**Prereq context:** See `docs/python-performance-audit.md` (the full audit). Tier 1 is already
done and in draft PR #899 on branch `perf/tier1-hot-path-optimizations` — independent of this work.

---

## Goal (one sentence)

Eliminate the repeated, identical MongoDB round-trips that the recursive dependency
walkers in `sspi_flask_app/models/database/sspi_metadata.py` make at every tree node,
**without changing any public method signature or any returned value.**

---

## The problem

Every metadata accessor is an **uncached** Mongo query. One `find_one` each, every call:

```python
def pillar_codes(self):     return self.find_one({"DocumentType": "PillarCodes"})["Metadata"]    # 542
def category_codes(self):   return self.find_one({"DocumentType": "CategoryCodes"})["Metadata"]  # 548
def indicator_codes(self):  return self.find_one({"DocumentType": "IndicatorCodes"})["Metadata"] # 554
def dataset_codes(self):    return self.find_one({"DocumentType": "DatasetCodes"})...             # 656
def item_codes(self):       return ["SSPI"] + indicator_codes() + category_codes() + pillar_codes()  # 569 → 3 queries
```

`get_series_type` (687) classifies ONE code with up to **4** queries:

```python
def get_series_type(self, series_code):
    if series_code in self.dataset_codes():   # 1 query
        return "Dataset"
    elif series_code in self.item_codes():    # 3 queries
        return "Item"
    return None
```

`get_dataset_dependencies` (951) calls `get_series_type` (and `get_item_detail`, etc.)
at **every node, recursively**:

```python
def get_dataset_dependencies(self, series_code):
    series_type = self.get_series_type(series_code)         # ~4 queries PER NODE
    if series_type == "Item":
        children = self.get_item_detail(series_code)...      # +1 query
        for c in children:
            dataset_dependencies += self.get_dataset_dependencies(c)   # recurse
```

A full SSPI walk (~77 item nodes: 1 root → ~4 pillars → ~16 categories → ~57 indicators)
re-fetches the SAME global code lists hundreds of times → **~300–500 round-trips** for
data that is constant for the whole call.

Same shape in `get_indicator_dependencies` (1114): `item_code not in self.item_codes()`
(3 queries) **+** `get_item_detail` (1 query) at every node.

`get_active_schema_dataset_dependencies` (1145): a `get_indicator_detail` per active
indicator (~57 sequential queries) **+** an O(n²) `ds_code not in all_datasets` membership
against a growing **list**.

---

## Targets (exact, with current per-call query cost)

| Fn | Line | Issue | Confidence it's logic-preserving |
|---|---|---|---|
| `get_active_schema_dataset_dependencies` | 1166 | `get_indicator_detail` per indicator (N+1) **+** O(n²) `not in all_datasets` list | High |
| `get_indicator_dependencies` | 1114 | `item_codes()` (3 q) + `get_item_detail` (1 q) per recursion node | Medium (needs helper) |
| `get_dataset_dependencies` → `get_series_type` | 951 / 687 | up to 4 `find_one` per node | Medium (needs helper) |
| `get_child_details` | 711 | 3 classification `find_one` + re-query before the real query | Medium |
| `get_country_groups` | 795 | scans all `CountryGroup` docs vs precomputed `country_group_map()` | Medium |

---

## The fix pattern

The metadata is **immutable for the duration of one top-level call.** So fetch the code
sets / detail maps ONCE and thread them through an internal recursive helper. Keep the
public method as a thin wrapper so its signature and behavior are unchanged.

```python
def get_dataset_dependencies(self, series_code: str) -> list:
    # public signature unchanged — fetch invariants once, then recurse query-free
    dataset_set = set(self.dataset_codes())
    item_set = set(self.item_codes())
    return self._get_dataset_dependencies(series_code, dataset_set, item_set)

def _get_dataset_dependencies(self, series_code, dataset_set, item_set):
    if series_code in dataset_set:
        return [series_code]
    if series_code in item_set:
        children = self.get_item_detail(series_code).get("Children", [])
        if not children and series_code in item_set:  # was: in self.indicator_codes()
            children = self.get_indicator_detail(series_code).get("DatasetCodes", [])
        assert not any(c is None for c in children)
        deps = []
        for c in children:
            deps += self._get_dataset_dependencies(c, dataset_set, item_set)
        return deps
    return []
```

Apply the same shape to `get_indicator_dependencies` (thread `item_set` + an
`item_detail_map`). For `get_active_schema_dataset_dependencies`: replace the per-indicator
`get_indicator_detail` loop with ONE `self.find({"DocumentType": "IndicatorDetail",
"Metadata.IndicatorCode": {"$in": active_indicator_codes}})` → build a
`{code: Metadata}` dict, iterate `active_indicator_codes` in order reading from the dict;
and make `all_datasets` membership use a parallel `set` while keeping the **list** for the
ordered output. For `get_child_details` (711) and `get_country_groups` (795), see the
audit report's Tier 2 section — both are independent, smaller wins; do them only if cheap.

> ⚠️ Subtle equivalence point: in the original, `series_code in self.indicator_codes()`
> tests membership against the indicator-codes list specifically, NOT all item codes.
> If you collapse it to `item_set`, confirm that branch only matters when `Children` is
> empty AND the code is an indicator — verify against `test_get_dataset_dependencies.py`
> before assuming `item_set` is a safe substitute. If unsure, thread a separate
> `indicator_set`.

---

## Why it's logic-preserving

Within a single call, the metadata documents do not change, so reading `dataset_codes()` /
`item_codes()` once and reusing the result yields the **same** classification and the
**same** recursion as re-reading them per node. The `in list` → `in set` swap preserves
membership semantics over unique codes. Outputs (and their order, for the dependency lists)
are identical.

## Why it was NOT in Tier 1

The public signature `get_dataset_dependencies(series_code)` has no place to carry the
precomputed sets, so you must add a private recursive helper (or a request-scoped cache).
That's a small **refactor**, which is the exact line Tier 1 (pure local line-edits) did not
cross. It's still safe — it just needs the helper.

---

## Public API must stay stable — external callers

Do **not** change these signatures; they're called from:

- `get_dataset_dependencies`: `api/resources/query_builder.py:128`, `api/core/delete.py:148,157`,
  `api/core/dataset.py:64,122` (+ unit test below)
- `get_indicator_dependencies`: `api/core/delete.py:158`, `api/core/sspi/__init__.py:119,146`
- `get_active_schema_dataset_dependencies`: `api/core/dashboard.py:1005`
- `get_series_type`: `api/core/query.py:123`
- `get_child_details`: `api/core/dashboard.py:1335`

---

## Definition of done

1. `get_dataset_dependencies`, `get_indicator_dependencies`,
   `get_active_schema_dataset_dependencies` return **byte-identical** results to `main` for
   the same inputs (lists in the same order).
2. Public signatures unchanged; all callers above untouched.
3. Per-call Mongo round-trips drop from O(nodes) to a small constant (rough check: count
   `find`/`find_one` calls, e.g. monkeypatch or log, for `get_dataset_dependencies("SSPI")`).
4. `pytest tests/unit/models/test_get_dataset_dependencies.py` passes (this is the safety
   net — it asserts exact dependency lists for UNSDG_*, BIODIV, REDLST, ECO, SUS, SSPI).
5. Whole `tests/unit` suite: same pass count as `main`. NOTE: `main` currently has **7
   pre-existing errors** in `tests/unit/security/test_*_bp.py` — a local-Mongo
   `DuplicateKeyError` on the `unique_score_entry` index, NOT related to this work. Confirm
   your count matches `main`'s (968 passed, 7 errors at time of writing).
6. Atomic commits, conventional messages (`perf:` / `refactor:`).

## How to verify

```bash
python -m py_compile sspi_flask_app/models/database/sspi_metadata.py
pytest tests/unit/models/test_get_dataset_dependencies.py -q     # primary safety net
pytest tests/unit -q                                             # full unit sweep
```

To prove the query reduction, temporarily wrap `find`/`find_one` with a counter (or use
`caplog`) around `get_dataset_dependencies("SSPI")` before vs after.

## Guardrails (do NOT touch — from the audit)

- `mongo_wrapper.py:137` `validate_documents_format` `all([...])` must stay a **list**
  (generator would short-circuit and skip validating later docs).
- Don't add a process-wide metadata cache without an invalidation story — scope any cache
  to the single call (helper-threading is simplest and safest).
- Keep `get_series_type`'s `None` return for unknown codes, and `get_item_detail`'s
  `{"Error": ...}` / empty-children fallbacks.

## Out of scope

`get_country_groups` (795) and `get_child_details` (711) are listed as optional smaller
wins; the core deliverable is the three dependency walkers. The Tier 1 PR (#899) and the
two non-perf bugs (`coverage.py:292` latent `NameError`; `unsdg_socassist.py` early return)
are tracked separately in `docs/python-performance-audit.md`.
