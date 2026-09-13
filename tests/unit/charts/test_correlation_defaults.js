/**
 * Pure-function unit tests for CorrelationDefaults.
 *
 * Runs under plain Node (no DOM, no Chart.js, no Flask app, no Mongo):
 *     node tests/unit/charts/test_correlation_defaults.js
 */
const assert = require('assert');
const Defaults = require('../../../sspi_flask_app/client/static/js/correlation-defaults.js');

const tests = [];
function test(name, fn) {
    tests.push({ name, fn });
}

function seriesOptions(datasetCodes) {
    return {
        Index: [{ code: 'SSPI', name: 'SSPI', type: 'SSPI' }],
        Pillars: [{ code: 'SUS', name: 'Sustainability', type: 'Pillar' }],
        Categories: [],
        Indicators: [],
        Datasets: datasetCodes.map(code => ({ code, name: code, type: 'Dataset' }))
    };
}

test('should start with SSPI against GDP per capita when every candidate is offered', () => {
    const pairs = Defaults.candidatePairs(seriesOptions(['WB_GDP_PERCAP_CURPRICE_USD', 'FPI_HDI', 'WB_GINIPT']));
    assert.deepStrictEqual(pairs[0], ['SSPI', 'WB_GDP_PERCAP_CURPRICE_USD']);
    assert.strictEqual(pairs.length, 4);
});

test('should skip pairs whose dataset is not offered when options are filtered to series with data', () => {
    const pairs = Defaults.candidatePairs(seriesOptions(['FPI_HDI']));
    assert.deepStrictEqual(pairs, [['SSPI', 'FPI_HDI'], ['SSPI', 'SUS']]);
});

test('should fall back to SSPI against a pillar when no outcome dataset is offered', () => {
    const pairs = Defaults.candidatePairs(seriesOptions([]));
    assert.deepStrictEqual(pairs, [['SSPI', 'SUS']]);
});

test('should keep every candidate when series options are missing or malformed', () => {
    assert.strictEqual(Defaults.candidatePairs(null).length, Defaults.CANDIDATE_PAIRS.length);
    assert.strictEqual(Defaults.candidatePairs({ Datasets: 'nope' }).length, Defaults.CANDIDATE_PAIRS.length);
    assert.strictEqual(Defaults.candidatePairs({ Datasets: [null, { code: 5 }] }).length, Defaults.CANDIDATE_PAIRS.length);
});

test('should not mutate the candidate list when filtering', () => {
    const before = JSON.stringify(Defaults.CANDIDATE_PAIRS);
    const pairs = Defaults.candidatePairs(seriesOptions([]));
    pairs[0][1] = 'CHANGED';
    assert.strictEqual(JSON.stringify(Defaults.CANDIDATE_PAIRS), before);
});

test('should classify no common countries as an empty result', () => {
    assert.strictEqual(Defaults.isEmptyResult(400, { error: 'No common countries between SSPI and X' }), true);
});

test('should classify an unknown series as an empty result', () => {
    assert.strictEqual(Defaults.isEmptyResult(404, { error: 'Series X not found' }), true);
    assert.strictEqual(Defaults.isEmptyResult(404, null), true);
});

test('should classify a successful response without rows as an empty result', () => {
    assert.strictEqual(Defaults.isEmptyResult(200, { data: [] }), true);
    assert.strictEqual(Defaults.isEmptyResult(200, {}), true);
    assert.strictEqual(Defaults.isEmptyResult(200, null), true);
});

test('should not classify a successful response with rows as empty', () => {
    assert.strictEqual(Defaults.isEmptyResult(200, { data: [{ CCode: 'USA' }] }), false);
});

test('should not classify server errors or other bad requests as empty', () => {
    assert.strictEqual(Defaults.isEmptyResult(500, { error: 'boom' }), false);
    assert.strictEqual(Defaults.isEmptyResult(500, null), false);
    assert.strictEqual(Defaults.isEmptyResult(400, { error: 'Bad series code' }), false);
});

test('should name both series and avoid the word failed when describing an empty pair', () => {
    const message = Defaults.emptyStateMessage('SSPI', 'WB_MURDER');
    assert.ok(message.includes('SSPI'));
    assert.ok(message.includes('WB_MURDER'));
    assert.ok(!/failed/i.test(message));
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
