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
    }
};

// Node / test export (no-op in the browser, where `module` is undefined).
if (typeof module !== 'undefined' && module.exports) {
    module.exports = SensitivityEngine;
}
