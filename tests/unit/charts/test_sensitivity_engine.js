/**
 * Pure-function unit tests for SensitivityEngine.
 *
 * Runs under plain Node (no DOM, no Chart.js, no Flask app, no Mongo):
 *     node tests/unit/charts/test_sensitivity_engine.js
 *
 * Covers the three propagation scenarios (goalpost / add / move), the
 * cross-pillar and same-pillar move cases, null (gap) propagation, the
 * n+1 / n-1 denominator edges, change-group derivation, and level ordering.
 */
const assert = require('assert');
const E = require('../../../sspi_flask_app/client/static/charts/panel/sensitivity-engine.js');

let passed = 0;
const tests = [];
function test(name, fn) {
    tests.push({ name, fn });
}
function approx(actual, expected, msg, tol = 1e-9) {
    if (actual === null || expected === null) {
        assert.strictEqual(actual, expected, msg);
        return;
    }
    assert.ok(Math.abs(actual - expected) <= tol, `${msg} (got ${actual}, want ${expected})`);
}
function approxSeries(actual, expected, msg) {
    assert.ok(Array.isArray(actual), `${msg}: actual is array`);
    assert.strictEqual(actual.length, expected.length, `${msg}: length`);
    for (let i = 0; i < expected.length; i++) {
        approx(actual[i], expected[i], `${msg}[${i}]`);
    }
}

// ---------------------------------------------------------------------------
// Shared synthetic metadata: SSPI -> {P1 -> [C1,C2], P2 -> [C3]}
// C1 = [I1, I2], C2 = [I3], C3 = [I4, I5]
// p = 2, m(P1) = 2, m(P2) = 1, n(C1) = 2
// ---------------------------------------------------------------------------
function baseMetadata() {
    return [
        { ItemType: 'SSPI', ItemCode: 'SSPI', ItemName: 'SSPI', PillarCodes: ['P1', 'P2'] },
        { ItemType: 'Pillar', ItemCode: 'P1', ItemName: 'Pillar One', CategoryCodes: ['C1', 'C2'] },
        { ItemType: 'Pillar', ItemCode: 'P2', ItemName: 'Pillar Two', CategoryCodes: ['C3'] },
        { ItemType: 'Category', ItemCode: 'C1', ItemName: 'Cat One', IndicatorCodes: ['I1', 'I2'] },
        { ItemType: 'Category', ItemCode: 'C2', ItemName: 'Cat Two', IndicatorCodes: ['I3'] },
        { ItemType: 'Category', ItemCode: 'C3', ItemName: 'Cat Three', IndicatorCodes: ['I4', 'I5'] },
        { ItemType: 'Indicator', ItemCode: 'I1', ItemName: 'Indicator One' },
        { ItemType: 'Indicator', ItemCode: 'I2', ItemName: 'Indicator Two' },
        { ItemType: 'Indicator', ItemCode: 'I3', ItemName: 'Indicator Three' },
        { ItemType: 'Indicator', ItemCode: 'I4', ItemName: 'Indicator Four' },
        { ItemType: 'Indicator', ItemCode: 'I5', ItemName: 'Indicator Five' }
    ];
}
// Helper: single-country score map.
function smap(arr) {
    return { AAA: arr };
}

// ---------------------------------------------------------------------------
test('should resolve ancestry and denominators from custom metadata', () => {
    const m = baseMetadata();
    assert.deepStrictEqual(E.resolveAncestry('I1', m), { indicatorCode: 'I1', categoryCode: 'C1', pillarCode: 'P1' });
    assert.strictEqual(E.countIndicatorsInCategory('C1', m), 2);
    assert.strictEqual(E.countCategoriesInPillar('P1', m), 2);
    assert.strictEqual(E.countCategoriesInPillar('P2', m), 1);
    assert.strictEqual(E.countPillars(m), 2);
});

test('should propagate dSSPI as dI over n*m*p when goalpost changes', () => {
    const m = baseMetadata();
    const group = { scenario: 'goalpost', indicatorCode: 'I1', categoryCode: 'C1', pillarCode: 'P1' };
    const context = {
        baselineByItem: {
            I1: smap([0.4, 0.4]),
            C1: smap([0.30, 0.30]),
            P1: smap([0.50, 0.50]),
            SSPI: smap([0.60, 0.60])
        },
        customIndicatorMap: smap([0.6, 0.6]) // dI = +0.2
    };
    const out = E.computeGroupSeries(group, m, context);
    // dC = 0.2/2 = 0.1 ; dP = 0.1/2 = 0.05 ; dSSPI = 0.05/2 = 0.025
    approxSeries(out.indicator.customMap.AAA, [0.6, 0.6], 'indicator custom');
    approxSeries(out.indicator.baselineMap.AAA, [0.4, 0.4], 'indicator baseline');
    approxSeries(out.category.customMap.AAA, [0.40, 0.40], 'category custom = baseline + dC');
    approxSeries(out.pillar.customMap.AAA, [0.55, 0.55], 'pillar custom = baseline + dP');
    approxSeries(out.sspi.customMap.AAA, [0.625, 0.625], 'sspi custom = baseline + dSSPI');
    // dSSPI hand-check == dI/(n*m*p)
    approx(out.sspi.customMap.AAA[0] - context.baselineByItem.SSPI.AAA[0], 0.2 / (2 * 2 * 2), 'dSSPI = dI/(n*m*p)');
});

test('should treat add-indicator as (I_new - C_baseline)/(n+1)', () => {
    const m = baseMetadata();
    // Custom C1 now contains the new indicator => n+1 = 3
    m.find((x) => x.ItemCode === 'C1').IndicatorCodes = ['I1', 'I2', 'INEW'];
    m.push({ ItemType: 'Indicator', ItemCode: 'INEW', ItemName: 'New One' });
    const group = { scenario: 'add', indicatorCode: 'INEW', categoryCode: 'C1', pillarCode: 'P1' };
    const context = {
        baselineByItem: {
            C1: smap([0.30, 0.30]),
            P1: smap([0.50, 0.50]),
            SSPI: smap([0.60, 0.60])
        },
        customIndicatorMap: smap([0.90, 0.90])
    };
    const out = E.computeGroupSeries(group, m, context);
    // dC = (0.9 - 0.3)/3 = 0.2 ; dP = 0.1 ; dSSPI = 0.05
    assert.strictEqual(out['added-indicator'].hasBaseline, false, 'new indicator has no baseline ghost');
    approxSeries(out['added-indicator'].customMap.AAA, [0.9, 0.9], 'new indicator custom line');
    approxSeries(out.category.customMap.AAA, [0.50, 0.50], 'category custom = baseline + dC');
    approxSeries(out.pillar.customMap.AAA, [0.60, 0.60], 'pillar custom = baseline + dP');
    approxSeries(out.sspi.customMap.AAA, [0.65, 0.65], 'sspi custom = baseline + dSSPI');
});

test('should propagate a cross-pillar move with two pillar deltas combined at SSPI', () => {
    const m = baseMetadata();
    // Custom reflects post-move: IX now in C1 (P1); removed from C3 (P2).
    m.find((x) => x.ItemCode === 'C1').IndicatorCodes = ['I1', 'I2', 'IX'];
    m.push({ ItemType: 'Indicator', ItemCode: 'IX', ItemName: 'Mover' });
    const group = {
        scenario: 'move',
        indicatorCode: 'IX',
        fromCategoryCode: 'C3', toCategoryCode: 'C1',
        fromPillarCode: 'P2', toPillarCode: 'P1'
    };
    const context = {
        baselineByItem: {
            IX: smap([0.50, 0.50]),
            C3: smap([0.40, 0.40]),   // losing category baseline
            C1: smap([0.30, 0.30]),   // gaining category baseline
            P2: smap([0.45, 0.45]),   // losing pillar baseline
            P1: smap([0.55, 0.55]),   // gaining pillar baseline
            SSPI: smap([0.60, 0.60])
        },
        customIndicatorMap: null
    };
    const out = E.computeGroupSeries(group, m, context);
    // n_from(custom C3) = 2 -> dC_from = (0.4 - 0.5)/2 = -0.05
    // n_to(custom C1)   = 3 -> dC_to   = (0.5 - 0.3)/3 = +0.0666667
    approxSeries(out['moved-indicator'].customMap.AAA, [0.5, 0.5], 'moved indicator unchanged');
    approxSeries(out['losing-category'].customMap.AAA, [0.35, 0.35], 'losing category custom');
    approxSeries(out['gaining-category'].customMap.AAA, [0.30 + 0.2 / 3, 0.30 + 0.2 / 3], 'gaining category custom');
    // m_from(P2) = 1 -> dP_from = -0.05 ; m_to(P1) = 2 -> dP_to = +0.0333333
    approxSeries(out['losing-pillar'].customMap.AAA, [0.45 - 0.05, 0.45 - 0.05], 'losing pillar custom');
    approxSeries(out['gaining-pillar'].customMap.AAA, [0.55 + (0.2 / 3) / 2, 0.55 + (0.2 / 3) / 2], 'gaining pillar custom');
    // dSSPI = (dP_from + dP_to)/p = (-0.05 + 0.0333333)/2
    const expectedDeltaSSPI = (-0.05 + (0.2 / 3) / 2) / 2;
    approx(out.sspi.customMap.AAA[0] - 0.60, expectedDeltaSSPI, 'dSSPI combines both pillar deltas');
});

test('should combine both category deltas at the shared pillar for a same-pillar move', () => {
    const m = baseMetadata();
    // Move I3 from C2 to C1, both inside P1. Custom: C1 = [I1,I2,I3], C2 = [].
    m.find((x) => x.ItemCode === 'C1').IndicatorCodes = ['I1', 'I2', 'I3'];
    m.find((x) => x.ItemCode === 'C2').IndicatorCodes = [];
    const group = {
        scenario: 'move',
        indicatorCode: 'I3',
        fromCategoryCode: 'C2', toCategoryCode: 'C1',
        fromPillarCode: 'P1', toPillarCode: 'P1'
    };
    const context = {
        baselineByItem: {
            I3: smap([0.50]),
            C2: smap([0.40]),
            C1: smap([0.30]),
            P1: smap([0.55]),
            SSPI: smap([0.60])
        },
        customIndicatorMap: null
    };
    const out = E.computeGroupSeries(group, m, context);
    // single shared pillar level (no losing/gaining pillar split)
    assert.ok(out.pillar, 'same-pillar move yields one pillar level');
    assert.ok(!out['losing-pillar'] && !out['gaining-pillar'], 'no split pillar levels');
    // n_from(custom C2) = 0 -> childWeight(0) = 0 -> dC_from = 0 (last indicator left the category)
    // n_to(custom C1)   = 3 -> dC_to = (0.5 - 0.3)/3 = 0.0666667
    approxSeries(out['losing-category'].customMap.AAA, [0.40], 'losing category unchanged when emptied (weight 0)');
    // m(P1) = 2 -> dP = (dC_from + dC_to)/2 = (0 + 0.0666667)/2
    const dP = (0 + 0.2 / 3) / 2;
    approx(out.pillar.customMap.AAA[0] - 0.55, dP, 'shared pillar delta sums category deltas');
});

test('should propagate nulls as gaps, never NaN', () => {
    const m = baseMetadata();
    const group = { scenario: 'goalpost', indicatorCode: 'I1', categoryCode: 'C1', pillarCode: 'P1' };
    const context = {
        baselineByItem: {
            I1: smap([0.4, 0.4]),
            C1: smap([0.30, 0.30]),
            P1: smap([0.50, 0.50]),
            SSPI: smap([0.60, 0.60])
        },
        customIndicatorMap: smap([0.6, null]) // second year unknown
    };
    const out = E.computeGroupSeries(group, m, context);
    approx(out.sspi.customMap.AAA[0], 0.625, 'year 0 propagates');
    assert.strictEqual(out.sspi.customMap.AAA[1], null, 'year 1 is a gap, not NaN');
    assert.ok(!Number.isNaN(out.sspi.customMap.AAA[1]), 'never NaN');
});

test('should treat a country absent from the delta as unchanged (delta = 0)', () => {
    const m = baseMetadata();
    const group = { scenario: 'goalpost', indicatorCode: 'I1', categoryCode: 'C1', pillarCode: 'P1' };
    const context = {
        baselineByItem: {
            I1: { AAA: [0.4] },
            // category baseline has a second country BBB with no indicator delta
            C1: { AAA: [0.30], BBB: [0.70] },
            P1: { AAA: [0.50], BBB: [0.80] },
            SSPI: { AAA: [0.60], BBB: [0.90] }
        },
        customIndicatorMap: { AAA: [0.6] }
    };
    const out = E.computeGroupSeries(group, m, context);
    approxSeries(out.category.customMap.BBB, [0.70], 'BBB unchanged (no delta)');
    approxSeries(out.sspi.customMap.BBB, [0.90], 'BBB SSPI unchanged');
});

test('should derive and classify change-groups, deduping by indicator', () => {
    const m = baseMetadata();
    const actions = [
        { type: 'set-score-function', delta: { type: 'set-score-function', indicatorCode: 'I1', to: 'Score = 1' } },
        { type: 'set-score-function', delta: { type: 'set-score-function', indicatorCode: 'I1', to: 'Score = 2' } }, // dup
        { type: 'move-indicator', delta: { type: 'move-indicator', indicatorCode: 'I4', fromParentCode: 'C3', toParentCode: 'C1' } },
        { type: 'add-indicator', delta: { type: 'add-indicator', indicatorCode: 'INEW', parentCode: 'C2' } },
        { type: 'set-indicator-name', delta: { type: 'set-indicator-name', indicatorCode: 'I2', from: 'a', to: 'b' } } // no-effect
    ];
    const groups = E.deriveChangeGroups(actions, m);
    assert.strictEqual(groups.length, 3, 'rename dropped + goalpost deduped');
    const byScenario = groups.reduce((acc, g) => { acc[g.scenario] = g; return acc; }, {});
    assert.ok(byScenario.goalpost && byScenario.goalpost.indicatorCode === 'I1', 'goalpost group');
    assert.ok(byScenario.move && byScenario.move.fromCategoryCode === 'C3' && byScenario.move.toCategoryCode === 'C1', 'move group');
    assert.strictEqual(byScenario.move.fromPillarCode, 'P2', 'move from-pillar resolved');
    assert.strictEqual(byScenario.move.toPillarCode, 'P1', 'move to-pillar resolved');
    assert.ok(byScenario.add && byScenario.add.categoryCode === 'C2', 'add group');
});

test('should expand composite actions into scenarios', () => {
    const m = baseMetadata();
    const actions = [
        {
            type: 'modify-indicator',
            delta: {
                type: 'composite',
                subActions: [
                    { type: 'set-indicator-name', indicatorCode: 'I1', to: 'Renamed' },
                    { type: 'add-dataset', indicatorCode: 'I1', datasetCode: 'DS1' }
                ]
            }
        }
    ];
    const groups = E.deriveChangeGroups(actions, m);
    assert.strictEqual(groups.length, 1, 'only the score-affecting sub-action surfaces');
    assert.strictEqual(groups[0].scenario, 'goalpost');
    assert.strictEqual(groups[0].indicatorCode, 'I1');
});

test('should build ordered levels for each scenario', () => {
    const m = baseMetadata();
    const goalpost = E.buildLevelsForGroup({ scenario: 'goalpost', indicatorCode: 'I1', categoryCode: 'C1', pillarCode: 'P1' }, m);
    assert.deepStrictEqual(goalpost.map((l) => l.role), ['indicator', 'category', 'pillar', 'sspi']);

    const crossMove = E.buildLevelsForGroup({
        scenario: 'move', indicatorCode: 'IX',
        fromCategoryCode: 'C3', toCategoryCode: 'C1', fromPillarCode: 'P2', toPillarCode: 'P1'
    }, m);
    assert.deepStrictEqual(crossMove.map((l) => l.role),
        ['moved-indicator', 'losing-category', 'gaining-category', 'losing-pillar', 'gaining-pillar', 'sspi']);

    const samePillarMove = E.buildLevelsForGroup({
        scenario: 'move', indicatorCode: 'I3',
        fromCategoryCode: 'C2', toCategoryCode: 'C1', fromPillarCode: 'P1', toPillarCode: 'P1'
    }, m);
    assert.deepStrictEqual(samePillarMove.map((l) => l.role),
        ['moved-indicator', 'losing-category', 'gaining-category', 'pillar', 'sspi']);

    const add = E.buildLevelsForGroup({ scenario: 'add', indicatorCode: 'INEW', categoryCode: 'C1', pillarCode: 'P1' }, m);
    assert.strictEqual(add[0].role, 'added-indicator');
});

// ---------------------------------------------------------------------------
let failed = 0;
tests.forEach(({ name, fn }) => {
    try {
        fn();
        passed += 1;
        console.log(`  ok   ${name}`);
    } catch (err) {
        failed += 1;
        console.error(`  FAIL ${name}\n       ${err.message}`);
    }
});
console.log(`\n${passed} passed, ${failed} failed`);
process.exit(failed === 0 ? 0 : 1);
