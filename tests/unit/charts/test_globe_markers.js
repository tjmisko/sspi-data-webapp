/**
 * Pure-function unit tests for GlobeMarkers.
 *
 * Runs under plain Node (no DOM, no globe.gl, no Flask app, no Mongo):
 *     node tests/unit/charts/test_globe_markers.js
 */
const assert = require('assert');
const Markers = require('../../../sspi_flask_app/client/static/js/globe-markers.js');

const tests = [];
function test(name, fn) {
    tests.push({ name, fn });
}

function polygonFeature(code) {
    return {
        type: 'Feature',
        properties: { CCode: code, CName: code, SSPI: [0.5] },
        bbox: [0, 0, 1, 1],
        geometry: { type: 'Polygon', coordinates: [[[0, 0], [1, 0], [1, 1], [0, 0]]] }
    };
}

test('should add a Singapore fallback marker when the features omit SGP', () => {
    const prepared = Markers.prepare([polygonFeature('USA'), polygonFeature('FRA')]);
    assert.strictEqual(prepared.polygonFeatures.length, 2);
    assert.strictEqual(prepared.markerFeatures.length, 1);
    const marker = prepared.markerFeatures[0];
    assert.strictEqual(marker.properties.CCode, 'SGP');
    assert.strictEqual(marker.properties.CName, 'Singapore');
    assert.strictEqual(marker.markerLat, 1.3521);
    assert.strictEqual(marker.markerLng, 103.8198);
    assert.strictEqual(prepared.features.length, 3);
    assert.deepStrictEqual(marker.bbox, [101.8198, -0.6479, 105.8198, 3.3521].map((v, i) => marker.bbox[i]));
    assert.ok(marker.bbox[0] < 103.8198 && marker.bbox[2] > 103.8198);
});

test('should use the API marker and keep its scores when a feature is flagged marker true', () => {
    const apiMarker = {
        type: 'Feature',
        properties: { CCode: 'SGP', CName: 'Singapore', SSPI: [0.61], marker: true },
        geometry: { type: 'Point', coordinates: [103.8, 1.35] }
    };
    const prepared = Markers.prepare([polygonFeature('USA'), apiMarker]);
    assert.strictEqual(prepared.markerFeatures.length, 1);
    assert.strictEqual(prepared.markerFeatures[0], apiMarker);
    assert.deepStrictEqual(apiMarker.properties.SSPI, [0.61]);
    assert.strictEqual(apiMarker.markerLat, 1.35);
    assert.strictEqual(apiMarker.markerLng, 103.8);
    assert.ok(Array.isArray(apiMarker.bbox) && apiMarker.bbox.length === 4);
});

test('should treat a feature level marker flag as a marker when geometry is a polygon', () => {
    const flagged = polygonFeature('SGP');
    flagged.marker = true;
    flagged.bbox = [103.6, 1.2, 104.0, 1.5];
    const prepared = Markers.prepare([flagged]);
    assert.strictEqual(prepared.polygonFeatures.length, 0);
    assert.strictEqual(prepared.markerFeatures.length, 1);
    assert.ok(Math.abs(flagged.markerLat - 1.35) < 1e-9);
    assert.ok(Math.abs(flagged.markerLng - 103.8) < 1e-9);
});

test('should draw SGP sent without geometry as a marker at the fallback centroid', () => {
    const noGeometry = { type: 'Feature', properties: { CCode: 'SGP', CName: 'Singapore', SSPI: [0.7] }, geometry: null };
    const prepared = Markers.prepare([noGeometry]);
    assert.strictEqual(prepared.markerFeatures.length, 1);
    assert.strictEqual(prepared.markerFeatures[0], noGeometry);
    assert.strictEqual(noGeometry.markerLat, 1.3521);
});

test('should not add a fallback marker when SGP already has a polygon', () => {
    const prepared = Markers.prepare([polygonFeature('SGP')]);
    assert.strictEqual(prepared.markerFeatures.length, 0);
    assert.strictEqual(prepared.polygonFeatures.length, 1);
});

test('should read lat and lng properties when a marker has no point geometry', () => {
    const marker = { type: 'Feature', marker: true, properties: { CCode: 'MLT', lat: 35.9, lng: 14.4 } };
    const prepared = Markers.prepare([marker]);
    assert.strictEqual(marker.markerLat, 35.9);
    assert.strictEqual(marker.markerLng, 14.4);
    assert.strictEqual(prepared.markerFeatures.length, 2);
});

test('should drop a marker without any usable position', () => {
    const bad = { type: 'Feature', marker: true, properties: { CCode: 'XXX' }, geometry: { type: 'Point', coordinates: ['a', null] } };
    const outOfRange = { type: 'Feature', properties: { CCode: 'YYY' }, geometry: { type: 'Point', coordinates: [500, 95] } };
    const prepared = Markers.prepare([bad, outOfRange], []);
    assert.strictEqual(prepared.markerFeatures.length, 0);
    assert.strictEqual(prepared.features.length, 0);
});

test('should drop null entries and features with unknown geometry', () => {
    const line = { type: 'Feature', properties: { CCode: 'ZZZ' }, geometry: { type: 'LineString', coordinates: [] } };
    const prepared = Markers.prepare([null, 'feature', line], []);
    assert.strictEqual(prepared.features.length, 0);
});

test('should return only fallback markers when features are missing', () => {
    assert.strictEqual(Markers.prepare(undefined).markerFeatures.length, 1);
    assert.strictEqual(Markers.prepare({}).features.length, 1);
});

test('should clamp the marker bounding box to valid coordinates near the poles and antimeridian', () => {
    const bbox = Markers.markerBBox({ lat: 89.5, lng: 179.5 });
    assert.deepStrictEqual(bbox, [177.5, 87.5, 180, 90]);
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
