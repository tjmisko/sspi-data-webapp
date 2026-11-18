/**
 * Pure-function unit tests for PanelSummaryStats.
 *
 * Runs under plain Node (no DOM, no Chart.js, no Flask app, no Mongo):
 *     node tests/unit/charts/test_panel_summary_stats.js
 */
const assert = require('assert');
const Stats = require('../../../sspi_flask_app/client/static/js/panel-summary-stats.js');

const tests = [];
function test(name, fn) {
    tests.push({ name, fn });
}
function approx(actual, expected, message, tolerance = 1e-9) {
    assert.ok(Math.abs(actual - expected) <= tolerance, `${message} (got ${actual}, want ${expected})`);
}

// 2000..2023 -> 24 values; value for year y is (y - 2000) / 100
function linearSeries() {
    return Array.from({ length: 24 }, (_, index) => index / 100);
}

test('should include the selected end year when the range ends at the last year', () => {
    const stats = Stats.compute(linearSeries(), 2000, 2023);
    assert.strictEqual(stats.count, 24);
    assert.strictEqual(stats.lastYear, 2023);
    approx(stats.maximum, 0.23, 'maximum is the 2023 value');
    assert.strictEqual(stats.maximumYear, 2023);
    approx(stats.average, 0.115, 'average covers 2000-2023');
});

test('should include both ends when the range is a single year', () => {
    const stats = Stats.compute(linearSeries(), 2010, 2010);
    assert.strictEqual(stats.count, 1);
    assert.strictEqual(stats.firstYear, 2010);
    assert.strictEqual(stats.lastYear, 2010);
    approx(stats.average, 0.10, 'single year average');
    approx(stats.change, 0, 'no change within one year');
});

test('should include the end year when the range sits inside the panel', () => {
    const stats = Stats.compute(linearSeries(), 2005, 2015);
    assert.strictEqual(stats.count, 11);
    assert.strictEqual(stats.firstYear, 2005);
    assert.strictEqual(stats.lastYear, 2015);
    approx(stats.change, (0.15 - 0.05) / 0.05 * 100, 'percent change 2005-2015');
});

test('should skip missing values when the series has gaps', () => {
    const series = linearSeries();
    series[0] = null;
    series[5] = undefined;
    series[23] = NaN;
    const stats = Stats.compute(series, 2000, 2023);
    assert.strictEqual(stats.count, 21);
    assert.strictEqual(stats.firstYear, 2001);
    assert.strictEqual(stats.lastYear, 2022);
    approx(stats.minimum, 0.01, 'minimum ignores null');
    assert.strictEqual(stats.minimumYear, 2001);
});

test('should return null when no value is observed in the range', () => {
    const series = new Array(24).fill(null);
    assert.strictEqual(Stats.compute(series, 2000, 2023), null);
    assert.strictEqual(Stats.compute([], 2000, 2023), null);
    assert.strictEqual(Stats.compute(undefined, 2000, 2023), null);
});

test('should return null when the start year is after the end year', () => {
    assert.strictEqual(Stats.compute(linearSeries(), 2020, 2010), null);
});

test('should clamp the range when years fall outside the series', () => {
    const stats = Stats.compute(linearSeries(), 1990, 2030);
    assert.strictEqual(stats.count, 24);
    assert.strictEqual(stats.firstYear, 2000);
    assert.strictEqual(stats.lastYear, 2023);
});

test('should accept year inputs given as strings', () => {
    const stats = Stats.compute(linearSeries(), '2000', '2023');
    assert.strictEqual(stats.count, 24);
});

test('should report null change when the first observed value is zero', () => {
    const stats = Stats.compute(linearSeries(), 2000, 2003);
    assert.strictEqual(stats.change, null);
});

test('should report the first year of a tied extreme when values repeat', () => {
    const series = [0.5, 0.2, 0.9, 0.2, 0.9];
    const stats = Stats.compute(series, 2000, 2004);
    assert.strictEqual(stats.minimumYear, 2001);
    assert.strictEqual(stats.maximumYear, 2002);
});

test('should keep the sign of change when values are negative', () => {
    const stats = Stats.compute([-2, -1], 2000, 2001);
    approx(stats.change, 50, 'rising from -2 to -1 is a positive change');
});

let failed = 0;
for (const { name, fn } of tests) {
    try {
        fn();
        console.log(`  ok   ${name}`);
    } catch (error) {
        failed++;
        console.log(`  FAIL ${name}\n       ${error.message}`);
    }
}
console.log(`\n${tests.length - failed} passed, ${failed} failed`);
process.exit(failed ? 1 : 0);
