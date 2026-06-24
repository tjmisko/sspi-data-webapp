/**
 * SensitivityEngine
 *
 * Pure (DOM-free, Chart.js-free) helpers backing the custom-scoring
 * "Sensitivity" visualization. The engine turns a configuration's change log
 * into per-level baseline-vs-custom series using *linear ceteris-paribus
 * propagation* instead of re-scoring.
 *
 * Why linear propagation is exact (not an approximation): SSPI aggregation is
 * the (equal-weight) mean of child scores at every level above the indicator,
 * and the only nonlinearity -- goalpost clamping to [0, 1] -- is contained
 * entirely within indicator scoring. The fetched indicator series already
 * carry that clamping, so for every level above the indicator
 *     custom_series = baseline_series + propagated_delta
 * holds exactly, with no re-clamping required.
 *
 * The G1 (scaffold) portion below provides the generic series math and the
 * metadata/ancestry helpers. The G2 (buildout) portion adds change-group
 * derivation and the three-scenario propagation engine.
 *
 * This module is exposed as a browser global (for the asset bundle) and, when
 * loaded under Node, via module.exports so the pure functions can be
 * unit-tested without a DOM.
 */
const SensitivityEngine = {
    // ------------------------------------------------------------------
    // Weight lookup (pluggable denominator).
    //
    // v1 assumes equal weights, so a child's weight in its parent is 1/k where
    // k is the number of (custom) children. Phase 4's per-parent normalized
    // weights can replace this single lookup without touching propagation.
    // ------------------------------------------------------------------
    childWeight(childCount /*, parentCode, childCode */) {
        return childCount > 0 ? 1 / childCount : 0;
    },

    // ------------------------------------------------------------------
    // Element-wise series math. Every operation is null-safe: a null/undefined
    // operand at index i yields null at index i (a gap), never NaN.
    // ------------------------------------------------------------------
    _isNullish(value) {
        return value === null || value === undefined || (typeof value === 'number' && Number.isNaN(value));
    },

    subtractSeries(a, b) {
        if (!Array.isArray(a) || !Array.isArray(b)) {
            return null;
        }
        const length = Math.max(a.length, b.length);
        const out = new Array(length);
        for (let i = 0; i < length; i++) {
            const x = a[i];
            const y = b[i];
            out[i] = (this._isNullish(x) || this._isNullish(y)) ? null : x - y;
        }
        return out;
    },

    addSeries(a, b) {
        if (!Array.isArray(a) || !Array.isArray(b)) {
            return null;
        }
        const length = Math.max(a.length, b.length);
        const out = new Array(length);
        for (let i = 0; i < length; i++) {
            const x = a[i];
            const y = b[i];
            out[i] = (this._isNullish(x) || this._isNullish(y)) ? null : x + y;
        }
        return out;
    },

    scaleSeries(a, factor) {
        if (!Array.isArray(a)) {
            return null;
        }
        return a.map((x) => (this._isNullish(x) ? null : x * factor));
    },

    // ------------------------------------------------------------------
    // Per-country score maps. A panel payload's `data` is an array of country
    // datasets, each carrying a `score` (and/or `data`) array aligned to the
    // shared `labels`. These helpers reduce that to { CCode: number[] } maps so
    // that all propagation is per-country, per-label-index.
    // ------------------------------------------------------------------
    scoreMapFromPanel(panelData) {
        const map = {};
        if (!panelData || !Array.isArray(panelData.data)) {
            return map;
        }
        panelData.data.forEach((dataset) => {
            if (!dataset || !dataset.CCode) {
                return;
            }
            const series = dataset.score || dataset.data || [];
            map[dataset.CCode] = Array.isArray(series) ? series.slice() : [];
        });
        return map;
    },

    /** Element-wise subtract two per-country score maps (custom - baseline). */
    subtractMaps(customMap, baselineMap) {
        const out = {};
        const codes = new Set([...Object.keys(customMap || {}), ...Object.keys(baselineMap || {})]);
        codes.forEach((code) => {
            out[code] = this.subtractSeries(customMap?.[code] || null, baselineMap?.[code] || null);
        });
        return out;
    },

    /** Element-wise add two per-country score maps. */
    addMaps(baseMap, deltaMap) {
        const out = {};
        const codes = new Set([...Object.keys(baseMap || {}), ...Object.keys(deltaMap || {})]);
        codes.forEach((code) => {
            out[code] = this.addSeries(baseMap?.[code] || null, deltaMap?.[code] || null);
        });
        return out;
    },

    /** Scale every series in a per-country map by a scalar factor. */
    scaleMap(map, factor) {
        const out = {};
        Object.keys(map || {}).forEach((code) => {
            out[code] = this.scaleSeries(map[code], factor);
        });
        return out;
    },

    // ------------------------------------------------------------------
    // Metadata indexing + ancestry resolution.
    //
    // Configuration metadata is a flat list of item documents, each with an
    // `ItemType` (SSPI / Pillar / Category / Indicator) and `ItemCode`. Parent
    // -> child links live on the downward arrays (PillarCodes / CategoryCodes /
    // IndicatorCodes), falling back to a generic `Children` array. We resolve
    // an indicator's category and pillar by searching those downward links,
    // falling back to upward `CategoryCode` / `PillarCode` fields if present.
    // ------------------------------------------------------------------
    indexMetadata(metadata) {
        const items = Array.isArray(metadata) ? metadata : [];
        const byCode = {};
        const indicators = [];
        const categories = [];
        const pillars = [];
        let sspi = null;
        items.forEach((item) => {
            if (!item) {
                return;
            }
            if (item.ItemCode) {
                byCode[item.ItemCode] = item;
            }
            switch (item.ItemType) {
                case 'Indicator':
                    indicators.push(item);
                    break;
                case 'Category':
                    categories.push(item);
                    break;
                case 'Pillar':
                    pillars.push(item);
                    break;
                case 'SSPI':
                    sspi = item;
                    break;
                default:
                    break;
            }
        });
        return { byCode, indicators, categories, pillars, sspi, items };
    },

    childCodes(item) {
        if (!item) {
            return [];
        }
        switch (item.ItemType) {
            case 'SSPI':
                return item.PillarCodes || item.Children || [];
            case 'Pillar':
                return item.CategoryCodes || item.Children || [];
            case 'Category':
                return item.IndicatorCodes || item.Children || [];
            default:
                return [];
        }
    },

    resolveAncestry(indicatorCode, metadata) {
        const idx = this.indexMetadata(metadata);
        let categoryCode = null;
        let pillarCode = null;

        for (const category of idx.categories) {
            if (this.childCodes(category).includes(indicatorCode)) {
                categoryCode = category.ItemCode;
                break;
            }
        }
        if (categoryCode) {
            for (const pillar of idx.pillars) {
                if (this.childCodes(pillar).includes(categoryCode)) {
                    pillarCode = pillar.ItemCode;
                    break;
                }
            }
        }
        // Fallback to upward links carried on the indicator/category documents.
        const indicator = idx.byCode[indicatorCode];
        if (indicator) {
            categoryCode = categoryCode || indicator.CategoryCode || null;
            pillarCode = pillarCode || indicator.PillarCode || null;
        }
        if (!pillarCode && categoryCode) {
            const category = idx.byCode[categoryCode];
            if (category) {
                pillarCode = category.PillarCode || null;
            }
        }
        return { indicatorCode, categoryCode, pillarCode };
    },

    pillarOfCategory(categoryCode, metadata) {
        if (!categoryCode) {
            return null;
        }
        const idx = this.indexMetadata(metadata);
        for (const pillar of idx.pillars) {
            if (this.childCodes(pillar).includes(categoryCode)) {
                return pillar.ItemCode;
            }
        }
        const category = idx.byCode[categoryCode];
        return category ? (category.PillarCode || null) : null;
    },

    // ------------------------------------------------------------------
    // Child-count helpers (custom-side denominators). All counts come from the
    // *custom* metadata: the goalpost scenario uses the unchanged n; add uses
    // n+1 (the new indicator already lives in the custom category); move uses
    // n_from-1 and n_to+1 (A has already left/joined in the custom config).
    // ------------------------------------------------------------------
    countIndicatorsInCategory(categoryCode, metadata) {
        const idx = this.indexMetadata(metadata);
        const category = idx.byCode[categoryCode];
        if (category) {
            const codes = this.childCodes(category);
            if (codes.length) {
                return codes.length;
            }
        }
        return idx.indicators.filter(
            (indicator) => this.resolveAncestry(indicator.ItemCode, metadata).categoryCode === categoryCode
        ).length;
    },

    countCategoriesInPillar(pillarCode, metadata) {
        const idx = this.indexMetadata(metadata);
        const pillar = idx.byCode[pillarCode];
        if (pillar) {
            const codes = this.childCodes(pillar);
            if (codes.length) {
                return codes.length;
            }
        }
        return idx.categories.filter(
            (category) => this.pillarOfCategory(category.ItemCode, metadata) === pillarCode
        ).length;
    },

    countPillars(metadata) {
        const idx = this.indexMetadata(metadata);
        if (idx.sspi) {
            const codes = this.childCodes(idx.sspi);
            if (codes.length) {
                return codes.length;
            }
        }
        return idx.pillars.length;
    },

    // ==================================================================
    // G2 — change-group derivation, level building, and the three-scenario
    // linear-propagation engine.
    // ==================================================================
    SCENARIO: {
        GOALPOST: 'goalpost',
        ADD: 'add',
        MOVE: 'move',
        NO_EFFECT: 'no-effect',
        UNSUPPORTED: 'unsupported'
    },

    _itemName(itemCode, metadata) {
        const idx = this.indexMetadata(metadata);
        const item = idx.byCode[itemCode];
        return item && item.ItemName ? item.ItemName : itemCode;
    },

    /**
     * Map an action/sub-action type onto a sensitivity scenario. The vocabulary
     * mirrors the Changes tab: score-affecting edits (score function or dataset
     * membership) are the "goalpost" scenario; structural edits are move/add;
     * renames have no numeric effect; whole-category moves are out of v1 scope.
     */
    _classifyType(type) {
        if (!type) {
            return null;
        }
        if (type === 'move-indicator') {
            return this.SCENARIO.MOVE;
        }
        if (type === 'add-indicator' || type === 'create-indicator') {
            return this.SCENARIO.ADD;
        }
        if (type === 'set-score-function' || type === 'add-dataset' ||
            type === 'remove-dataset' || type === 'replace-datasets') {
            return this.SCENARIO.GOALPOST;
        }
        if (type === 'move-category') {
            return this.SCENARIO.UNSUPPORTED;
        }
        if (type.indexOf('set-') === 0 || type === 'rename' || type === 'ren') {
            return this.SCENARIO.NO_EFFECT;
        }
        return null;
    },

    /** Expand an action (including composite actions) into {type, delta} entries. */
    _flattenAction(action) {
        const out = [];
        if (!action) {
            return out;
        }
        const delta = action.delta || {};
        if (delta.type === 'composite' && Array.isArray(delta.subActions)) {
            delta.subActions.forEach((sub) => {
                out.push({ type: sub.type, delta: Object.assign({}, delta, sub) });
            });
            return out;
        }
        out.push({ type: action.type || delta.type, delta: delta });
        return out;
    },

    /**
     * Derive sensitivity change-groups from a configuration's actions[] log.
     * Returns one group per affected indicator (deduplicated), each classified
     * into a scenario and resolved against the *custom* metadata ancestry.
     * Rename / unsupported edits are dropped (no stacked view).
     */
    deriveChangeGroups(actions, metadata) {
        const list = Array.isArray(actions) ? actions : [];
        const groups = [];
        const seen = new Set();
        const push = (group) => {
            const key = `${group.scenario}:${group.indicatorCode || group.categoryCode || ''}`;
            if (seen.has(key)) {
                return;
            }
            seen.add(key);
            group.id = key;
            groups.push(group);
        };
        list.forEach((action) => {
            this._flattenAction(action).forEach(({ type, delta }) => {
                const scenario = this._classifyType(type);
                if (!scenario) {
                    return;
                }
                if (scenario === this.SCENARIO.GOALPOST) {
                    const indicatorCode = delta.indicatorCode;
                    if (!indicatorCode) {
                        return;
                    }
                    const ancestry = this.resolveAncestry(indicatorCode, metadata);
                    push({
                        scenario: scenario,
                        indicatorCode: indicatorCode,
                        categoryCode: ancestry.categoryCode,
                        pillarCode: ancestry.pillarCode,
                        label: `Score change — ${this._itemName(indicatorCode, metadata)} (${indicatorCode})`
                    });
                } else if (scenario === this.SCENARIO.ADD) {
                    const indicatorCode = delta.indicatorCode;
                    if (!indicatorCode) {
                        return;
                    }
                    const categoryCode = delta.parentCode ||
                        this.resolveAncestry(indicatorCode, metadata).categoryCode;
                    push({
                        scenario: scenario,
                        indicatorCode: indicatorCode,
                        categoryCode: categoryCode,
                        pillarCode: this.pillarOfCategory(categoryCode, metadata),
                        label: `New indicator — ${this._itemName(indicatorCode, metadata)} (${indicatorCode})`
                    });
                } else if (scenario === this.SCENARIO.MOVE) {
                    const indicatorCode = delta.indicatorCode;
                    if (!indicatorCode) {
                        return;
                    }
                    const fromCategoryCode = delta.fromParentCode;
                    const toCategoryCode = delta.toParentCode;
                    push({
                        scenario: scenario,
                        indicatorCode: indicatorCode,
                        fromCategoryCode: fromCategoryCode,
                        toCategoryCode: toCategoryCode,
                        fromPillarCode: this.pillarOfCategory(fromCategoryCode, metadata),
                        toPillarCode: this.pillarOfCategory(toCategoryCode, metadata),
                        label: `Moved indicator — ${this._itemName(indicatorCode, metadata)} (${indicatorCode})`
                    });
                }
            });
        });
        return groups;
    },

    /**
     * Build the ordered (smallest -> largest) list of levels a change-group
     * percolates through. move-indicator yields two category levels (losing +
     * gaining); a cross-pillar move yields two pillar levels.
     */
    buildLevelsForGroup(group, metadata) {
        if (!group) {
            return [];
        }
        const levels = [];
        const named = (itemCode, itemType, role, prefix) => ({
            itemCode: itemCode,
            itemType: itemType,
            role: role,
            title: `${prefix}: ${this._itemName(itemCode, metadata)} (${itemCode})`
        });
        const sspiLevel = { itemCode: 'SSPI', itemType: 'SSPI', role: 'sspi', title: 'SSPI' };

        if (group.scenario === this.SCENARIO.GOALPOST) {
            levels.push(named(group.indicatorCode, 'Indicator', 'indicator', 'Indicator'));
            if (group.categoryCode) {
                levels.push(named(group.categoryCode, 'Category', 'category', 'Category'));
            }
            if (group.pillarCode) {
                levels.push(named(group.pillarCode, 'Pillar', 'pillar', 'Pillar'));
            }
            levels.push(sspiLevel);
        } else if (group.scenario === this.SCENARIO.ADD) {
            levels.push(named(group.indicatorCode, 'Indicator', 'added-indicator', 'New Indicator'));
            if (group.categoryCode) {
                levels.push(named(group.categoryCode, 'Category', 'category', 'Category'));
            }
            if (group.pillarCode) {
                levels.push(named(group.pillarCode, 'Pillar', 'pillar', 'Pillar'));
            }
            levels.push(sspiLevel);
        } else if (group.scenario === this.SCENARIO.MOVE) {
            levels.push(named(group.indicatorCode, 'Indicator', 'moved-indicator', 'Indicator'));
            if (group.fromCategoryCode) {
                levels.push(named(group.fromCategoryCode, 'Category', 'losing-category', 'Losing Category'));
            }
            if (group.toCategoryCode) {
                levels.push(named(group.toCategoryCode, 'Category', 'gaining-category', 'Gaining Category'));
            }
            if (group.fromPillarCode && group.fromPillarCode === group.toPillarCode) {
                levels.push(named(group.fromPillarCode, 'Pillar', 'pillar', 'Pillar'));
            } else {
                if (group.fromPillarCode) {
                    levels.push(named(group.fromPillarCode, 'Pillar', 'losing-pillar', 'Losing Pillar'));
                }
                if (group.toPillarCode) {
                    levels.push(named(group.toPillarCode, 'Pillar', 'gaining-pillar', 'Gaining Pillar'));
                }
            }
            levels.push(sspiLevel);
        }
        return levels;
    },

    /** The indicator whose custom series must be fetched to measure the differential (null for move). */
    requiredCustomIndicator(group) {
        if (!group) {
            return null;
        }
        if (group.scenario === this.SCENARIO.GOALPOST || group.scenario === this.SCENARIO.ADD) {
            return group.indicatorCode;
        }
        return null;
    },

    /** Compose a level's custom map = baseline + delta, treating an absent country's delta as zero. */
    _composeLevel(baselineMap, deltaMap) {
        const base = baselineMap || {};
        const delta = deltaMap || {};
        const customMap = {};
        Object.keys(base).forEach((code) => {
            if (delta[code]) {
                customMap[code] = this.addSeries(base[code], delta[code]);
            } else {
                customMap[code] = Array.isArray(base[code]) ? base[code].slice() : null;
            }
        });
        Object.keys(delta).forEach((code) => {
            if (!(code in customMap)) {
                customMap[code] = delta[code];
            }
        });
        return { baselineMap: base, customMap: customMap, hasBaseline: true };
    },

    /**
     * Run the linear propagation for a change-group and return per-role
     * { baselineMap, customMap, hasBaseline, note } entries.
     *
     * context = { baselineByItem: { itemCode: scoreMap }, customIndicatorMap: scoreMap|null }
     *
     * Formula families (per-country, per-label-index, null-safe):
     *   A goalpost: dI = custom_I - baseline_I; dC = dI/n; dP = dC/m; dSSPI = dP/p
     *   B add:      dC = (I_new - C_baseline)/(n+1); dP = dC/m; dSSPI = dP/p
     *   C move:     dC_from = (C_from_baseline - A)/(n_from-1)
     *               dC_to   = (A - C_to_baseline)/(n_to+1)
     *               same pillar:  dP = (dC_from + dC_to)/m; dSSPI = dP/p
     *               cross pillar: dP_from = dC_from/m_from; dP_to = dC_to/m_to;
     *                             dSSPI = (dP_from + dP_to)/p
     * Denominators are CUSTOM-side counts; baseline category means come from the
     * baseline /panel/score series.
     */
    computeGroupSeries(group, metadata, context) {
        const baselineByItem = (context && context.baselineByItem) || {};
        const customIndicatorMap = (context && context.customIndicatorMap) || null;
        const out = {};
        const p = this.countPillars(metadata);

        if (group.scenario === this.SCENARIO.GOALPOST) {
            const baselineI = baselineByItem[group.indicatorCode] || {};
            const customI = customIndicatorMap || {};
            const deltaI = this.subtractMaps(customI, baselineI);
            const n = this.countIndicatorsInCategory(group.categoryCode, metadata);
            const m = this.countCategoriesInPillar(group.pillarCode, metadata);
            const deltaC = this.scaleMap(deltaI, this.childWeight(n));
            const deltaP = this.scaleMap(deltaC, this.childWeight(m));
            const deltaS = this.scaleMap(deltaP, this.childWeight(p));
            out.indicator = { baselineMap: baselineI, customMap: customI, hasBaseline: true };
            out.category = this._composeLevel(baselineByItem[group.categoryCode], deltaC);
            out.pillar = this._composeLevel(baselineByItem[group.pillarCode], deltaP);
            out.sspi = this._composeLevel(baselineByItem.SSPI, deltaS);
        } else if (group.scenario === this.SCENARIO.ADD) {
            const iNew = customIndicatorMap || {};
            const baselineC = baselineByItem[group.categoryCode] || {};
            const nPlus1 = this.countIndicatorsInCategory(group.categoryCode, metadata);
            const m = this.countCategoriesInPillar(group.pillarCode, metadata);
            const deltaC = this.scaleMap(this.subtractMaps(iNew, baselineC), this.childWeight(nPlus1));
            const deltaP = this.scaleMap(deltaC, this.childWeight(m));
            const deltaS = this.scaleMap(deltaP, this.childWeight(p));
            out['added-indicator'] = {
                baselineMap: null,
                customMap: iNew,
                hasBaseline: false,
                note: 'New indicator — no baseline to compare against.'
            };
            out.category = this._composeLevel(baselineC, deltaC);
            out.pillar = this._composeLevel(baselineByItem[group.pillarCode], deltaP);
            out.sspi = this._composeLevel(baselineByItem.SSPI, deltaS);
        } else if (group.scenario === this.SCENARIO.MOVE) {
            const aMap = baselineByItem[group.indicatorCode] || {};
            const baselineFrom = baselineByItem[group.fromCategoryCode] || {};
            const baselineTo = baselineByItem[group.toCategoryCode] || {};
            const nFrom = this.countIndicatorsInCategory(group.fromCategoryCode, metadata);
            const nTo = this.countIndicatorsInCategory(group.toCategoryCode, metadata);
            const deltaCfrom = this.scaleMap(this.subtractMaps(baselineFrom, aMap), this.childWeight(nFrom));
            const deltaCto = this.scaleMap(this.subtractMaps(aMap, baselineTo), this.childWeight(nTo));
            out['moved-indicator'] = {
                baselineMap: aMap,
                customMap: aMap,
                hasBaseline: true,
                note: 'Indicator score unchanged; the effect is structural.'
            };
            out['losing-category'] = this._composeLevel(baselineFrom, deltaCfrom);
            out['gaining-category'] = this._composeLevel(baselineTo, deltaCto);
            if (group.fromPillarCode && group.fromPillarCode === group.toPillarCode) {
                const m = this.countCategoriesInPillar(group.fromPillarCode, metadata);
                const deltaP = this.scaleMap(this.addMaps(deltaCfrom, deltaCto), this.childWeight(m));
                const deltaS = this.scaleMap(deltaP, this.childWeight(p));
                out.pillar = this._composeLevel(baselineByItem[group.fromPillarCode], deltaP);
                out.sspi = this._composeLevel(baselineByItem.SSPI, deltaS);
            } else {
                const mFrom = this.countCategoriesInPillar(group.fromPillarCode, metadata);
                const mTo = this.countCategoriesInPillar(group.toPillarCode, metadata);
                const deltaPfrom = this.scaleMap(deltaCfrom, this.childWeight(mFrom));
                const deltaPto = this.scaleMap(deltaCto, this.childWeight(mTo));
                const deltaS = this.scaleMap(this.addMaps(deltaPfrom, deltaPto), this.childWeight(p));
                out['losing-pillar'] = this._composeLevel(baselineByItem[group.fromPillarCode], deltaPfrom);
                out['gaining-pillar'] = this._composeLevel(baselineByItem[group.toPillarCode], deltaPto);
                out.sspi = this._composeLevel(baselineByItem.SSPI, deltaS);
            }
        }
        return out;
    }
};

// Node / test export (no-op in the browser, where `module` is undefined).
if (typeof module !== 'undefined' && module.exports) {
    module.exports = SensitivityEngine;
}
