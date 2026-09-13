/**
 * CorrelationDefaults - choose the series pair the regressions page opens
 * with, and classify failed loads as empty data or errors.
 *
 * Pure functions with no DOM dependency, so they run under Node:
 *     node tests/unit/charts/test_correlation_defaults.js
 */
const CorrelationDefaults = {
    /**
     * Pairs tried in order when the URL names no series. SSPI against an
     * outcome comes first; the last pair compares the index with one of its
     * own pillars, which has data whenever the index does.
     */
    CANDIDATE_PAIRS: [
        ['SSPI', 'WB_GDP_PERCAP_CURPRICE_USD'],
        ['SSPI', 'FPI_HDI'],
        ['SSPI', 'WB_GINIPT'],
        ['SSPI', 'SUS']
    ],

    /** Every series code offered by /api/v1/series-options. */
    availableCodes(seriesOptions) {
        const codes = new Set();
        if (!seriesOptions || typeof seriesOptions !== 'object') return codes;
        Object.values(seriesOptions).forEach(group => {
            if (!Array.isArray(group)) return;
            group.forEach(option => {
                if (option && typeof option.code === 'string' && option.code) {
                    codes.add(option.code);
                }
            });
        });
        return codes;
    },

    /**
     * Candidate pairs whose two series are both offered. When the options are
     * unknown, every candidate is kept so the page can still try to load.
     */
    candidatePairs(seriesOptions, candidates = this.CANDIDATE_PAIRS) {
        const codes = this.availableCodes(seriesOptions);
        const pairs = candidates.map(pair => [pair[0], pair[1]]);
        if (codes.size === 0) return pairs;
        return pairs.filter(pair => codes.has(pair[0]) && codes.has(pair[1]));
    },

    /**
     * True when a load came back without usable data for the pair (unknown
     * series, no countries in common, or an empty data list), as opposed to a
     * server or network failure.
     */
    isEmptyResult(status, payload) {
        if (status === 404) return true;
        const message = payload && typeof payload.error === 'string' ? payload.error : '';
        if (status === 400 && /no common countries/i.test(message)) return true;
        if (status >= 200 && status < 300) {
            return !payload || !Array.isArray(payload.data) || payload.data.length === 0;
        }
        return false;
    },

    emptyStateMessage(seriesX, seriesY) {
        return 'No overlapping data for ' + seriesX + ' and ' + seriesY +
            '. Choose another pair of series.';
    },

    errorStateMessage(seriesX, seriesY) {
        return 'Could not load data for ' + seriesX + ' and ' + seriesY +
            '. Try again or choose another pair of series.';
    }
};

// Node / test export (no-op in the browser, where module is undefined).
if (typeof module !== 'undefined' && module.exports) {
    module.exports = CorrelationDefaults;
}
