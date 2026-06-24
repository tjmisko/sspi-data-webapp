/**
 * CustomSSPIPanelChart
 *
 * A lean custom analog of SSPIPanelChart that renders panel data for a *custom*
 * SSPI configuration. It is wired to the live custom panel endpoint
 *   GET /api/v1/customize/panel/score/<item_code>?config_hash=...&config_id=...
 * which returns the identical payload shape as the standard
 *   GET /api/v1/panel/score/<item_code>
 * endpoint, so the chart is a drop-in overlay for the baseline.
 *
 * It extends PanelChart directly (not SSPIPanelChart) so that the custom
 * endpoint URL can be threaded through the PanelChart constructor's
 * auto-fetch. The small item-tree handling is mirrored from SSPIPanelChart
 * but re-fetches against the custom endpoint.
 *
 * Comparison-series support is enabled (enableComparisonSeries: true) and a
 * `setComparisonSeries(seriesByCountryCode)` seam writes per-country
 * `dataset.comparisonScores`, which the chart-interaction-plugin draws as a
 * faded dashed ghost line. This is the baseline-vs-custom overlay primitive
 * consumed by the Sensitivity view.
 */
class CustomSSPIPanelChart extends PanelChart {
    constructor(parentElement, itemCode, {
        configHash = '',
        configId = '',
        CountryList = [],
        width = 600,
        height = 600,
        enableComparisonSeries = true,
        showItemTree = true
    } = {}) {
        super(parentElement, {
            CountryList: CountryList,
            endpointURL: CustomSSPIPanelChart.buildCustomURL(itemCode, configHash, configId),
            width: width,
            height: height,
            enableComparisonSeries: enableComparisonSeries
        });
        this.itemCode = itemCode;
        this.activeItemCode = itemCode;
        this.configHash = configHash;
        this.configId = configId;
    }

    /** Build the custom panel-score URL for an item, carrying the config hash. */
    static buildCustomURL(itemCode, configHash, configId) {
        const params = new URLSearchParams();
        if (configHash) {
            params.set('config_hash', configHash);
        }
        if (configId) {
            params.set('config_id', configId);
        }
        const queryString = params.toString();
        return `/api/v1/customize/panel/score/${itemCode}${queryString ? `?${queryString}` : ''}`;
    }

    initItemTree() {
        this.itemTree = document.createElement('div');
        this.itemTree.classList.add('custom-sspi-tree-container');
        this.itemTree.innerHTML = `
            <div class="custom-sspi-tree-description">
                <h3 class="custom-sspi-tree-header">Custom SSPI Structure</h3>
                <p class="custom-sspi-tree-description-text">
                    Explore the scores across your custom SSPI structure below. Click on an item to view its data.
                </p>
            </div>
            <div class="item-tree-content">
            </div>
        `;
    }

    initRoot() {
        this.initItemTree();
        this.root = document.createElement('div');
        this.root.classList.add('custom-panel-chart-root-container');
        this.root.appendChild(this.itemTree);
        this.parentElement.appendChild(this.root);
    }

    rigItemDropdown() {
        this.itemInformation = this.chartOptions.querySelector('.item-information');
        this.itemDropdown = this.itemInformation.querySelector('.item-dropdown');
        this.itemDropdown.style.display = "none";
    }

    updateItemDropdown(options, itemType) {
        // Mirror SSPIPanelChart: the dropdown is hidden; only update the summary label.
        let itemTypeCapped;
        const resolvedType = itemType || this.itemType || '';
        if (resolvedType === "sspi" || resolvedType === "SSPI") {
            itemTypeCapped = resolvedType.toUpperCase();
        } else {
            itemTypeCapped = resolvedType.charAt(0).toUpperCase() + resolvedType.slice(1);
        }
        const itemSummary = this.itemInformation.querySelector('.item-information-summary');
        if (itemSummary) {
            itemSummary.textContent = `${itemTypeCapped} Information`;
        }
    }

    update(data) {
        // Gracefully handle the custom endpoint's error / no-data envelopes.
        if (!data || data.success === false) {
            this.handleDataError(data || {});
            return;
        }
        if (!data.data || data.data.length === 0) {
            this.handleNoData(data);
            return;
        }
        // The custom endpoint does not carry itemOptions / description fields that
        // PanelChart.update() expects; backfill them so super.update() is safe.
        data.itemOptions = data.itemOptions || [];
        data.description = data.description || '';

        this.activeItemCode = data.itemCode;
        super.update(data);
        this.buildItemTree(data.tree, data.itemCode);

        // Re-apply any comparison overlay supplied by the host (e.g. the
        // Sensitivity view) after the datasets were replaced by super.update().
        if (this.pendingComparisonSeries) {
            this.applyComparisonSeries(this.pendingComparisonSeries);
        }
    }

    buildItemTree(tree, selectedItemCode) {
        if (!tree) {
            return;
        }
        if (this.itemTreeObject && typeof this.itemTreeObject.destroy === 'function') {
            this.itemTreeObject.destroy();
        }
        this.itemTreeObject = new SSPIItemTree(
            this.itemTree.querySelector('.item-tree-content'),
            tree,
            (itemCode) => {
                this.activeItemCode = itemCode;
                this.fetch(CustomSSPIPanelChart.buildCustomURL(itemCode, this.configHash, this.configId))
                    .then((d) => this.update(d));
            },
            selectedItemCode
        );
    }

    /**
     * Comparison-series seam.
     *
     * Writes a per-country baseline (or custom) series onto each matching
     * dataset's `comparisonScores` field so the interaction plugin paints a
     * faded dashed ghost line alongside the main line. The series map is keyed
     * by country code (CCode) and each value is an array aligned to the
     * chart's labels.
     *
     * The supplied map is remembered (`pendingComparisonSeries`) so it can be
     * re-applied after a subsequent data refresh replaces the dataset objects.
     */
    setComparisonSeries(seriesByCountryCode) {
        this.pendingComparisonSeries = seriesByCountryCode || null;
        this.applyComparisonSeries(seriesByCountryCode);
    }

    applyComparisonSeries(seriesByCountryCode) {
        if (!seriesByCountryCode || !this.chart || !this.chart.data) {
            return;
        }
        this.chart.data.datasets.forEach((dataset) => {
            const series = seriesByCountryCode[dataset.CCode];
            if (series) {
                dataset.comparisonScores = series;
            }
        });
        this.updateChartPreservingYAxis();
    }

    clearComparisonSeries() {
        this.pendingComparisonSeries = null;
        if (!this.chart || !this.chart.data) {
            return;
        }
        this.chart.data.datasets.forEach((dataset) => {
            delete dataset.comparisonScores;
        });
        this.updateChartPreservingYAxis();
    }

    /**
     * Replace the main per-country series with a caller-supplied map.
     * Used by the Sensitivity view to set the custom (baseline + Delta)
     * proposal line. Keys are country codes; values are label-aligned arrays.
     */
    setMainSeries(seriesByCountryCode) {
        if (!seriesByCountryCode || !this.chart || !this.chart.data) {
            return;
        }
        this.chart.data.datasets.forEach((dataset) => {
            const series = seriesByCountryCode[dataset.CCode];
            if (series) {
                dataset.score = series;
                dataset.data = series;
            }
        });
        this.updateChartPreservingYAxis();
    }

    handleDataError(data) {
        if (this.title) {
            this.title.innerText = 'Error Loading Custom SSPI Data';
        }
        this.chart.data.datasets = [];
        this.chart.data.labels = [];
        this.chart.update();
        const treeContent = this.itemTree.querySelector('.item-tree-content');
        if (treeContent) {
            treeContent.innerHTML = `
                <div class="error-message">
                    <h4>Error Loading Data</h4>
                    <p>${data && data.error ? data.error : 'Unable to load custom scoring data.'}</p>
                </div>
            `;
        }
    }

    handleNoData(data) {
        if (this.title) {
            this.title.innerText = (data && data.title) || 'Custom SSPI - No Data';
        }
        this.chart.data.datasets = [];
        this.chart.data.labels = [];
        this.chart.update();
        const treeContent = this.itemTree.querySelector('.item-tree-content');
        if (treeContent) {
            treeContent.innerHTML = `
                <div class="no-data-message">
                    <h4>No Data Available</h4>
                    <p>This configuration has no scored data for the requested item.</p>
                </div>
            `;
        }
    }
}
