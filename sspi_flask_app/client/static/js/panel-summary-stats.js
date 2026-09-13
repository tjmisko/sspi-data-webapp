/**
 * PanelSummaryStats - summary statistics for the active country box on
 * panel charts (Average, Change, Minimum, Maximum).
 *
 * Pure functions with no DOM or Chart.js dependency, so they run under Node:
 *     node tests/unit/charts/test_panel_summary_stats.js
 *
 * Series are indexed by year offset from firstYear (index 0 is firstYear).
 * The selected year range is inclusive at both ends, and missing values
 * (null, undefined, NaN) are skipped rather than counted as zero.
 */
const PanelSummaryStats = {
    isObservedValue(value) {
        return typeof value === 'number' && Number.isFinite(value);
    },

    /**
     * Pairs of {year, value} for every observed value between startYear and
     * endYear inclusive.
     */
    observationsInRange(series, startYear, endYear, firstYear = 2000) {
        if (!Array.isArray(series)) return [];
        const start = Number(startYear);
        const end = Number(endYear);
        if (!Number.isFinite(start) || !Number.isFinite(end)) return [];
        if (start > end) return [];
        const startIndex = Math.max(0, start - firstYear);
        const endIndexInclusive = Math.min(series.length - 1, end - firstYear);
        const observations = [];
        for (let index = startIndex; index <= endIndexInclusive; index++) {
            const value = series[index];
            if (!this.isObservedValue(value)) continue;
            observations.push({ year: firstYear + index, value: value });
        }
        return observations;
    },

    /**
     * Returns null when no value is observed in the range. Change is the
     * percent change from the first to the last observed value, and is null
     * when the first observed value is zero.
     */
    compute(series, startYear, endYear, firstYear = 2000) {
        const observations = this.observationsInRange(series, startYear, endYear, firstYear);
        if (observations.length === 0) return null;
        const first = observations[0];
        const last = observations[observations.length - 1];
        let minimum = first;
        let maximum = first;
        let total = 0;
        for (const observation of observations) {
            total += observation.value;
            if (observation.value < minimum.value) minimum = observation;
            if (observation.value > maximum.value) maximum = observation;
        }
        const change = first.value === 0
            ? null
            : (last.value - first.value) / Math.abs(first.value) * 100;
        return {
            count: observations.length,
            firstYear: first.year,
            lastYear: last.year,
            average: total / observations.length,
            change: change,
            minimum: minimum.value,
            minimumYear: minimum.year,
            maximum: maximum.value,
            maximumYear: maximum.year
        };
    }
};

// Node / test export (no-op in the browser, where module is undefined).
if (typeof module !== 'undefined' && module.exports) {
    module.exports = PanelSummaryStats;
}
