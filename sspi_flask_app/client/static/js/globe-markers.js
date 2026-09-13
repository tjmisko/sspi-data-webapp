/**
 * GlobeMarkers - point markers for countries the globe cannot draw as
 * polygons (Singapore has no shape in the 1:110m Natural Earth layer).
 *
 * The globe API may flag such a feature with marker: true (on the feature or
 * its properties) and give it Point geometry. When it sends nothing for a
 * country in FALLBACK_MARKERS, a marker without scores is added at a known
 * centroid so the country can still be found, hovered, selected and pinned.
 *
 * Pure functions with no DOM or globe.gl dependency, so they run under Node:
 *     node tests/unit/charts/test_globe_markers.js
 */
const GlobeMarkers = {
    FALLBACK_MARKERS: [
        { CCode: 'SGP', CName: 'Singapore', CFlag: '\u{1F1F8}\u{1F1EC}', lat: 1.3521, lng: 103.8198 }
    ],

    // Half the side of the box used to frame a marker when zooming to it
    MARKER_BBOX_HALF_SPAN_DEGREES: 2,

    isFiniteCoordinate(value) {
        return typeof value === 'number' && Number.isFinite(value);
    },

    isValidLatLng(lat, lng) {
        return this.isFiniteCoordinate(lat) && this.isFiniteCoordinate(lng) &&
            Math.abs(lat) <= 90 && Math.abs(lng) <= 180;
    },

    geometryType(feature) {
        return feature && feature.geometry && typeof feature.geometry.type === 'string'
            ? feature.geometry.type
            : null;
    },

    isMarkerFeature(feature) {
        if (!feature || typeof feature !== 'object') return false;
        if (feature.marker === true) return true;
        if (feature.properties && feature.properties.marker === true) return true;
        return this.geometryType(feature) === 'Point';
    },

    isPolygonFeature(feature) {
        if (this.isMarkerFeature(feature)) return false;
        const type = this.geometryType(feature);
        return type === 'Polygon' || type === 'MultiPolygon';
    },

    fallbackMarkerFor(countryCode, fallbackMarkers = this.FALLBACK_MARKERS) {
        return fallbackMarkers.find(marker => marker.CCode === countryCode) || null;
    },

    /**
     * Marker position as {lat, lng}, read from Point geometry, then from
     * lat/lng properties, then from the centre of the bounding box, then from
     * the fallback table. Null when none of them gives a valid position.
     */
    markerPosition(feature, fallbackMarkers = this.FALLBACK_MARKERS) {
        if (!feature || typeof feature !== 'object') return null;
        const geometry = feature.geometry;
        if (geometry && geometry.type === 'Point' && Array.isArray(geometry.coordinates)) {
            const lng = geometry.coordinates[0];
            const lat = geometry.coordinates[1];
            if (this.isValidLatLng(lat, lng)) return { lat, lng };
        }
        const properties = feature.properties || {};
        const propertyLat = properties.lat ?? properties.Latitude;
        const propertyLng = properties.lng ?? properties.Longitude;
        if (this.isValidLatLng(propertyLat, propertyLng)) {
            return { lat: propertyLat, lng: propertyLng };
        }
        const bbox = feature.bbox;
        if (Array.isArray(bbox) && bbox.length === 4) {
            const lat = (bbox[1] + bbox[3]) / 2;
            const lng = (bbox[0] + bbox[2]) / 2;
            if (this.isValidLatLng(lat, lng)) return { lat, lng };
        }
        const fallback = this.fallbackMarkerFor(properties.CCode, fallbackMarkers);
        if (fallback) return { lat: fallback.lat, lng: fallback.lng };
        return null;
    },

    markerBBox(position) {
        const halfSpan = this.MARKER_BBOX_HALF_SPAN_DEGREES;
        return [
            Math.max(-180, position.lng - halfSpan),
            Math.max(-90, position.lat - halfSpan),
            Math.min(180, position.lng + halfSpan),
            Math.min(90, position.lat + halfSpan)
        ];
    },

    buildFallbackFeature(fallback) {
        const position = { lat: fallback.lat, lng: fallback.lng };
        return {
            type: 'Feature',
            marker: true,
            properties: {
                CCode: fallback.CCode,
                CName: fallback.CName,
                CFlag: fallback.CFlag,
                marker: true
            },
            geometry: { type: 'Point', coordinates: [fallback.lng, fallback.lat] },
            bbox: this.markerBBox(position),
            markerLat: position.lat,
            markerLng: position.lng
        };
    },

    /**
     * Split the globe features into polygons and markers.
     *
     * Marker features get markerLat, markerLng and (when missing) a bbox so
     * they can be drawn and zoomed to. A fallback country sent without polygon
     * geometry is drawn as a marker with its own scores. Markers without a
     * usable position, and features that are neither, are dropped. Fallback
     * markers are appended for countries the features do not mention at all.
     * Returns {features, polygonFeatures, markerFeatures}, where features is
     * every usable feature in order.
     */
    prepare(features, fallbackMarkers = this.FALLBACK_MARKERS) {
        const inputFeatures = Array.isArray(features) ? features : [];
        const presentCodes = new Set();
        const usableFeatures = [];
        const polygonFeatures = [];
        const markerFeatures = [];
        inputFeatures.forEach(feature => {
            if (!feature || typeof feature !== 'object') return;
            const countryCode = feature.properties && feature.properties.CCode;
            if (this.isPolygonFeature(feature)) {
                if (countryCode) presentCodes.add(countryCode);
                usableFeatures.push(feature);
                polygonFeatures.push(feature);
                return;
            }
            const isFallbackCountry = this.fallbackMarkerFor(countryCode, fallbackMarkers) !== null;
            if (!this.isMarkerFeature(feature) && !isFallbackCountry) return;
            const position = this.markerPosition(feature, fallbackMarkers);
            if (!position) return;
            feature.markerLat = position.lat;
            feature.markerLng = position.lng;
            if (!Array.isArray(feature.bbox) || feature.bbox.length !== 4) {
                feature.bbox = this.markerBBox(position);
            }
            if (countryCode) presentCodes.add(countryCode);
            usableFeatures.push(feature);
            markerFeatures.push(feature);
        });
        fallbackMarkers.forEach(fallback => {
            if (presentCodes.has(fallback.CCode)) return;
            const feature = this.buildFallbackFeature(fallback);
            usableFeatures.push(feature);
            markerFeatures.push(feature);
        });
        return { features: usableFeatures, polygonFeatures, markerFeatures };
    }
};

// Node / test export (no-op in the browser, where module is undefined).
if (typeof module !== 'undefined' && module.exports) {
    module.exports = GlobeMarkers;
}
