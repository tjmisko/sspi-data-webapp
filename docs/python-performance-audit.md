# Python Performance Audit

**Date:** 2026-06-26
**Scope:** ~30,000 LOC of production Python in `sspi_flask_app/`, `cli/`, `scripts/`, `connector/` (tests excluded).
**Method:** 14 parallel audit agents, each reading its assigned files in full and applying a shared checklist of *logic-preserving* optimizations (no behavior, output, ordering, or error-semantics changes). Findings deduplicated and prioritized below.

**Impact tags:** `HOT` = per web request / per country-year cell · `WARM` = per data-build or CLI run · `COLD` = rare/startup.

## Verified facts used throughout

- `MongoWrapper.find()` / `.aggregate()` return **materialized Python lists**, not cursors.
- `count_documents()` exists (`mongo_wrapper.py:45`).
- `sspi_metadata` accessors (`item_codes`, `dataset_codes`, `get_*_detail`, `country_group`, `get_goalposts`) each issue an **uncached** `find_one`/`find`.

---

## Tier 1 — HOT, high-confidence, drop-in (highest value)

Runs on user-facing requests; pure local edits.

**A. Stop counting by fetching every document**
- `client/routes.py:87` — `len(list(find(...)))` → `count_documents(same query)`
- `dashboard.py:2345-2350` — same; also drop the redundant `list()` (preserve empty→`None` branch)

**B. Drop `list()` around already-materialized `find()`/`aggregate()`**
- `dashboard.py:157, 441, 1059`
- `client/routes.py:72, 113, 140, 167`
- `delete.py:197` (COLD, admin)
- `sus/ghg/coalpw.py:126`, `sus/nrg/altnrg.py:142` (WARM — `list(x) + y` → `x + y`)

**C. `sorted(...)[0]` → `max(..., key=...)`** (stable sort ⇒ identical element)
- `dashboard.py:2230, 2265, 2300, 2336`
- `client/routes.py:79, 119, 146, 173`

**D. Linear `next()`/`index()` scan where a dict already exists → `dict.get`**
- `dashboard.py:2136` (`item_detail_map`; map already built at 2128)
- `finalize.py:333,350` (use `item_map`) — *Conf: Medium (duplicate ICodes)*
- `fast_custom_scoring.py:413,436` (category/pillar code→index maps in `__init__`)

**E. `x in list` membership inside loops → set**
- `coverage.py:96-97, 158-170, 192-199`
- `sspi.py:30,33` (item codes as set + `sum(1 for ...)`)
- `fast_custom_scoring.py:1067` (`ref_set`)
- `finalize.py:767-768, 788-789` (country groups as sets)

**F. `sum/any/all([listcomp])` → generator** (also restores short-circuit)
- `dashboard.py:1716-1718` (3 passes → single pass / `sum(1 for ...)`)
- `coverage.py:107-111`, `sspi.py:194,202,205,206`
- `utilities.py:353,396` (+ module const `_NUMERIC_TYPES = (int, float)`)
- > **DO NOT** touch `mongo_wrapper.py:137` `validate_documents_format` `all([...])`: a generator would short-circuit and skip validating later documents — behavior change.

**G. Eliminate repeated identical computation**
- `dashboard.py:1729,1732` — duplicate `sorted(list(set(...)))` → compute once
- `fast_custom_scoring.py:161` — `np.isnan(data)` 3× → `nan_mask` once
- `fast_custom_scoring.py:1182, 824` — re-indexed 3D arrays → hoist per-item 2D views + `nan_mat` (~80k cells/req)
- `fast_custom_scoring.py:554,558` — strip whitespace once
- `score_function_validator.py:776,784` — `set.difference(dict)` + only copy `env` when goalpost vars used
- `utilities.py:299-312` — `drop_none_or_na` O(n²) → single pass
- `utilities.py:419-428` — hoist `required_keys`, test dict directly
- `utilities.py:366` — hoist `inspect.getsource()` out of per-document loop

**H. Remove duplicate per-request DB round-trips**
- `fast_custom_scoring.py:1014` vs `1066` — `country_group()` called twice → fetch once
- `customize.py:1441-1455` — `get_line_data(config_hash)` full fetch twice → once — *Conf: Medium*

**I. Remove leftover debug `print()` in hot/loop paths** (changes stdout only)
- `dashboard.py:911` (prints whole `panel_data` per request), `1445, 1447, 1966`
- `mongo_wrapper.py:310-312` (per-item on bulk insert)

---

## Tier 2 — HOT/WARM, needs a small refactor or Medium confidence

**J. `sspi_metadata` recursion N+1 storms (biggest systemic DB cost)** — `sspi_metadata.py`
- `:1166` `get_active_schema_dataset_dependencies` — `find_one` per indicator (~50) + O(n²) list membership → one `$in` fetch + dict + `seen` set — *High*
- `:1114` `get_indicator_dependencies` — `item_codes()` (3 `find_one`) re-queried per node (~230) → thread code-set through recursion — *Medium*
- `:951,687` `get_dataset_dependencies`/`get_series_type` — up to 4 `find_one` per node → hoist sets into recursion — *Medium*
- `:711` `get_child_details` — 3 classification `find_one` + re-query → single `get_item_detail`, branch on `ItemType` — *Medium*
- `:795` `get_country_groups` — scans all `CountryGroup` docs vs precomputed `country_group_map()` — *Medium*
- `dashboard.py:575-577` — N+1 `find_one` for static ranks in nested loop → preload `rank_map {(ICode,CCode): Rank}` — *High*
- `dashboard.py:824` — `get_country_groups(cou)` per country → fetch once, build map — *High/Medium*
- `dashboard.py:2223-2301` — 3 `clean_api_data` queries → one `$in` — *Medium*
- `query_builder.py:127-141`, `utilities.py:903-908` — likely N+1 metadata; batch if accessor exists — *Medium*

**K.** `fast_custom_scoring._find_parent` — 3 full metadata scans per indicator → precompute parent map in `__init__` — *Medium*
**L.** `fast_custom_scoring.py:643` — needless `np.array(dataset_stack)` copy on simple-goalpost path — *Medium*
**M.** `mongo_wrapper.py:90-91` — `sum([...], [])` quadratic flatten → nested comprehension — *High*

---

## Tier 3 — WARM (data-build / ETL / CLI), batchable cleanups

- **WID (`datasource/wid.py:79-84,108`):** `filter_wid_csv` re-parses each country's full data+metadata CSV per `(variable, percentile)` — **dominant WID ETL cost**. Parse each country CSV once, reuse — *Medium, caller-level*. (All 77 `wid/` wrappers are otherwise clean.)
- `datasource/wid.py:90` — debug log eagerly computes `sorted(unique().tolist())` even when DEBUG off → guard — *High*
- `datasource/unsdg.py:59` — `any([isinstance,...])` → `isinstance(v, (str, float, int))` — *High*
- `datasource/unsdg.py:112-131` — `type(v) in [list]` → tuple; drop `.keys()` — *High*
- `datasource/unfao.py:33` — `any([...])` → generator — *High*
- `datasource/taxfoundation.py:40` — `.map(lambda x: int(x))` → `.astype(int)` — *High*
- `datasource/epi.py:46` — row-by-row `re.search` → `str.extract` — *Medium*; `:52-53` drop `.index.tolist()` — *High*
- `datasource/prisonstudies.py:125,135` — `df.apply(axis=1)` for append → `itertuples` — *Medium*
- **UNSDG cleaners (13 files):** delete redundant `DatasetCode` re-assignment loop (`filter_sdg` already sets it). **EXCLUDE** `unsdg_intrnt.py`, `unsdg_fampln.py` (loop is load-bearing there) — *High*
- **Dataset tail:** `unfao_crbnav/frstav` `range(1990,2000)` rebuilt per iter; `sorted(all_years)` per country; sipri `skip_regions`/`skip_countries` → `frozenset`; `unodc_pripop` double full-frame mask; `vdem`/`itu` redundant `str(df.to_json())` — *High; do NOT swap to `to_dict` (NaN handling)*
- **Compute sus/ms:** `txrdst`/`ginipt` duplicate `get_goalposts()`; `watman.py:165` rescan → `defaultdict`; `senior.py:134` `datetime.now()` in loop; `biodiv`/`stcons` `set([listcomp])`; `airpol`/`recycl` `ref_data`; `fdepth` `any([...])` — *High*
- `cli/utilities.py:24,36` — hoist regex to module-level `compile` (per-line/per-token on streams) — *High*
- `cli/commands/collect.py:41-45` — `.get()` once instead of double lookup — *High*
- `validators.py:26-27` — hoist `_SAFE_RE = re.compile(...)` — *High*
- `save.py:48` — hoist `list_collection_names()` out of loop — *High*
- `sspi_raw_api_data.py:146` — hoist `obs.update(kwargs)` out of fragment loop — *High*
- `connector/SSPIDatabaseConnector.py` — `.env` loaded twice per construction — *High*

---

## Tier 4 — COLD / dead code to delete (free)

- `customize.py:1452` — dead `scored_items` set comp
- `fast_custom_scoring.py:76` — unused `dataset_to_idx`; `flatten_to_documents` never called
- `dashboard.py:2086-2094` — dead `multi_index`/`df` build; `1968/1971` duplicate `order_map_literal`
- `coverage.py:260-262` — dead `child_details` (N `get_item_detail` calls thrown away) — *Medium*

---

## Do-NOT-touch guardrails (flagged by agents)

1. `mongo_wrapper.py:137` `all([...])` — must stay a list (short-circuit would skip validating later docs).
2. UNSDG/WB `parse_json()` round-trips — load-bearing (convert `insert_many`'s in-place ObjectIds to JSON).
3. `df.to_json()` → don't swap to `to_dict()` (NaN→null handling differs, changes which rows drop).
4. `fast_custom_scoring.py:223-240` imputation inner loop — vectorizing relies on a live view of imputed data; a refactor, not logic-preserving.

---

## Bonus — real bugs surfaced (not performance; out of audit scope)

- `coverage.py:292` — references `sspi_clean_api_data` which is **not imported** in the module → latent `NameError` in that branch.
- `unsdg_socassist.py:28` — early `return parse_json(...)` makes lines 29-33 unreachable → cleaner **never writes** to `sspi_clean_api_data` nor records its range.
- `who_cstunt.py` / `who_fampln.py` — early `return` → remaining code is dead.
- Several CLI commands (`coverage`/`metadata`/`extrapolate`/`interpolate`) — `echo_pretty` blocks after `raise` are unreachable dead code.
- `api/core/load.py` — `json.loads(request.get_json())` double-decode (correctness smell).

---

## Files confirmed clean (no findings)

All 77 `wid/` wrappers; all `wb/` wrappers; most `pg/` & `outcome/` (thin wrappers, several fully commented out); ~18 `sus/`/`ms/` compute files; `iea`/`ilo`/`who`/`fpi`/`epi`/`uis` tails; many models (`rank`, `usermodel`, `utils`, `errors`, `custom_item/panel/user_data`, `clean/indicator/imputed/item` data); datasource `fpi`/`fsi`/`iea`/`ilo`/`imf`/`itu`/`sipri`/`uis`/`vdem`/`wef`/`who`/`worldbank`.
