/**
 * SensitivityComparisonView
 *
 * The stacked, per-level container for the custom-scoring "Sensitivity"
 * visualization. Given an ordered list of levels (smallest -> largest:
 * Indicator -> Category -> Pillar -> SSPI), it renders one comparison chart per
 * level in a vertical column and drives them all from a *single* shared,
 * sticky options panel (the first/top chart's panel), fanning that panel's
 * controls out to the sibling charts.
 *
 * Each level chart is a CustomSSPIPanelChart with `enableComparisonSeries: true`
 * so it can show two lines: the main (solid) line and a faded dashed ghost
 * (`comparisonScores`). G1 stands up this scaffold and exposes seams
 * (`setLevelMainSeries`, `setLevelComparisonSeries`) that G2 fills with the
 * linear-propagation baseline-vs-custom series.
 *
 * Reuse note: no new charting/plotting code is introduced here. The overlay,
 * pins, year range, country groups, and hover all come from PanelChart; the
 * "shared panel" is implemented purely as control-event fan-out.
 */
class SensitivityComparisonView {
    /**
     * @param {HTMLElement} mountElement - element to render the column into.
     * @param {Object} options
     * @param {string} options.configHash - hash with custom line data.
     * @param {string} [options.configId] - configuration id (for metadata).
     * @param {Array<{itemCode:string,itemType:string,role:string,title:string}>} options.levels
     *        ordered smallest -> largest.
     * @param {string|null} [options.focusCountryCode] - default focused country.
     */
    constructor(mountElement, {
        configHash = '',
        configId = '',
        levels = [],
        focusCountryCode = null
    } = {}) {
        this.mount = mountElement;
        this.configHash = configHash;
        this.configId = configId;
        this.levels = Array.isArray(levels) ? levels : [];
        this.focusCountryCode = focusCountryCode;
        this.charts = [];
        this.primary = null;

        this.root = document.createElement('div');
        this.root.classList.add('sensitivity-comparison-view');
        this.mount.appendChild(this.root);

        this.render();
    }

    render() {
        this.destroyCharts();
        this.root.innerHTML = '';
        this.charts = [];

        if (this.levels.length === 0) {
            return;
        }

        this.levels.forEach((level, index) => {
            const row = document.createElement('div');
            row.classList.add('sensitivity-level-row');
            row.dataset.role = level.role || '';
            row.dataset.level = String(index);

            const header = document.createElement('div');
            header.classList.add('sensitivity-level-header');
            header.innerHTML = `
                <span class="sensitivity-level-title">${level.title || level.itemCode}</span>
                <span class="sensitivity-level-meta">${level.itemType || ''} ${level.itemCode || ''}</span>
            `;
            row.appendChild(header);

            const chartMount = document.createElement('div');
            chartMount.classList.add('sensitivity-level-chart');
            row.appendChild(chartMount);

            this.root.appendChild(row);

            const chart = new CustomSSPIPanelChart(chartMount, level.itemCode, {
                configHash: this.configHash,
                configId: this.configId,
                enableComparisonSeries: true,
                width: 900,
                height: 320
            });
            chart._sensitivityLevel = level;
            this.charts.push(chart);
        });

        this.primary = this.charts[0] || null;
        if (this.charts.length > 1) {
            this.root.classList.add('shared-panel-mode');
        } else {
            this.root.classList.remove('shared-panel-mode');
        }

        this.wireSharedPanel();
        this.wireLinkedHover();
    }

    /**
     * Make the primary (top) chart's options panel drive every level by fanning
     * its by-code control methods out to the sibling charts. Pinning persists
     * through observableStorage (siblings react via their pin listeners); the
     * remaining controls are synced explicitly here.
     */
    wireSharedPanel() {
        if (!this.primary || this.charts.length < 2) {
            return;
        }
        const siblings = this.charts.slice(1);
        const fanned = [
            'showGroup',
            'showAll',
            'hideUnpinned',
            'clearPins',
            'pinCountryByCode',
            'unpinCountryByCode',
            'updateYearRange',
            'updateHoverRadius',
            'toggleComparisonSeries',
            'toggleBackwardExtrapolation',
            'toggleLinearInterpolation',
            'showRandomN'
        ];
        fanned.forEach((methodName) => {
            const original = this.primary[methodName];
            if (typeof original !== 'function') {
                return;
            }
            this.primary[methodName] = (...args) => {
                const result = original.apply(this.primary, args);
                siblings.forEach((sibling) => {
                    if (typeof sibling[methodName] === 'function') {
                        try {
                            sibling[methodName].apply(sibling, args);
                        } catch (error) {
                            // A sibling level may not have the same countries / data
                            // loaded yet; control fan-out is best-effort.
                        }
                    }
                });
                return result;
            };
        });
    }

    /**
     * Linked cursor/highlight across the stack. Hovering a country (via the
     * legend or a programmatic highlight) on any chart highlights the same
     * country on every other chart using the interaction plugin's external
     * hover hook.
     */
    wireLinkedHover() {
        if (this.charts.length < 2) {
            return;
        }
        this.charts.forEach((chart) => {
            const original = chart.handleChartCountryHighlight;
            if (typeof original !== 'function') {
                return;
            }
            chart.handleChartCountryHighlight = (countryCode) => {
                original.apply(chart, [countryCode]);
                this.charts.forEach((other) => {
                    if (other === chart) {
                        return;
                    }
                    this.applyExternalHover(other, countryCode);
                });
            };
        });
    }

    applyExternalHover(chart, countryCode) {
        if (!chart || !chart.chartInteractionPlugin || !chart.chart) {
            return;
        }
        if (countryCode === null || countryCode === undefined) {
            chart.chartInteractionPlugin.setExternalHover(chart.chart, null);
        } else {
            const datasetIndex = chart.chart.data.datasets.findIndex((ds) => ds.CCode === countryCode);
            chart.chartInteractionPlugin.setExternalHover(chart.chart, datasetIndex === -1 ? null : datasetIndex);
        }
        chart.updateChartPreservingYAxis();
    }

    /** Focus a single country across all levels (multi-country stays available via pins). */
    setFocusCountry(countryCode) {
        this.focusCountryCode = countryCode;
        if (!countryCode || !this.primary) {
            return;
        }
        this.primary.pinCountryByCode(countryCode);
        this.primary.hideUnpinned();
    }

    /** G2 seam: set the custom (solid) main line for a level. */
    setLevelMainSeries(levelIndex, seriesByCountryCode) {
        const chart = this.charts[levelIndex];
        if (chart && typeof chart.setMainSeries === 'function') {
            chart.setMainSeries(seriesByCountryCode);
        }
    }

    /** G2 seam: set the baseline (ghost) comparison line for a level. */
    setLevelComparisonSeries(levelIndex, seriesByCountryCode) {
        const chart = this.charts[levelIndex];
        if (chart && typeof chart.setComparisonSeries === 'function') {
            chart.setComparisonSeries(seriesByCountryCode);
        }
    }

    getChart(levelIndex) {
        return this.charts[levelIndex] || null;
    }

    destroyCharts() {
        this.charts.forEach((chart) => {
            if (chart && chart.itemTreeObject && typeof chart.itemTreeObject.destroy === 'function') {
                chart.itemTreeObject.destroy();
            }
        });
    }

    destroy() {
        this.destroyCharts();
        if (this.root && this.root.parentElement) {
            this.root.parentElement.removeChild(this.root);
        }
        this.charts = [];
        this.primary = null;
    }
}

// Node / test export (no-op in the browser, where `module` is undefined).
if (typeof module !== 'undefined' && module.exports) {
    module.exports = SensitivityComparisonView;
}
