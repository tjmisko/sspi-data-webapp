/**
 * SeriesCorrelationChart - A self-contained, monolithic chart component
 * for visualizing correlations between two data series.
 *
 * Features:
 * - Embedded series selection (searchable dropdowns)
 * - Multiple analysis modes (pooled, cross-sectional, first differences)
 * - Collapsible sidebar with all options
 * - Responsive design (mobile and desktop)
 * - Reuses panel-chart CSS architecture
 */
class SeriesCorrelationChart {
    constructor(parentElement, options = {}) {
        // Core configuration
        this.parentElement = parentElement;
        this.options = {
            initialSeriesX: options.initialSeriesX || '',
            initialSeriesY: options.initialSeriesY || '',
            colorProvider: options.colorProvider || SSPIColors,
            ...options
        };

        // State
        this.seriesX = this.options.initialSeriesX;
        this.seriesY = this.options.initialSeriesY;
        this.seriesOptions = null; // Populated from API
        this.rawData = null;
        this.transformedData = null;
        this.currentMode = 'differences';
        this.currentYear = 2023;
        this.countryGroup = 'SSPI67';
        this.regressionLine = true;
        this.choropleth = false;

        // Mode definitions
        this.modes = {
            pooled: 'Pooled Correlation',
            crossSectional: 'Year-by-Year Cross-Sectional',
            differences: 'First Differences'
        };

        // Mode descriptions
        this.modeDescriptions = {
            differences: 'Examines how changes in one variable relate to contemporaneous changes in another (Δy vs Δx).',
            crossSectional: 'Compares values across countries in a single year.',
            pooled: 'Combines all country-year observations into one analysis.'
        };

        // Initialize theme
        this.setTheme(window.observableStorage?.getItem('theme') || 'light');

        // Initialize UI
        this.initRoot();
        this.initChartCanvas();
        this.buildChartOptions();
        this.rigChartOptions();

        // Fetch series options and initialize
        this.fetchSeriesOptions().then(() => {
            this.populateSeriesDropdowns();
            if (this.seriesX && this.seriesY) {
                this.loadCorrelationData();
            } else {
                this.showSelectionPrompt();
            }
        }).catch(error => {
            console.error('Failed to fetch series options:', error);
            this.showError('Failed to load series options. Please refresh the page.');
        });
    }

    /* ===== INITIALIZATION ===== */

    initRoot() {
        this.root = document.createElement('div');
        this.root.classList.add('panel-chart-root-container');
        this.parentElement.appendChild(this.root);
    }

    initChartCanvas() {
        this.chartContainer = document.createElement('div');
        this.chartContainer.classList.add('panel-chart-container');
        this.chartContainer.innerHTML = `
            <div class="panel-chart-title-container">
                <div class="correlation-header-row">
                    <div class="correlation-title-and-selectors">
                        <h2 class="panel-chart-title">Select series to begin</h2>
                        <div class="correlation-series-selectors">
                            <div class="correlation-series-selector-group">
                                <label class="correlation-series-label">Series X</label>
                                <select class="series-x-selector series-selector-inline"></select>
                            </div>
                            <div class="correlation-series-selector-group">
                                <label class="correlation-series-label">Series Y</label>
                                <select class="series-y-selector series-selector-inline"></select>
                            </div>
                        </div>
                    </div>
                    <div class="panel-chart-title-actions"></div>
                </div>
            </div>
            <div class="panel-canvas-wrapper">
                <canvas class="panel-chart-canvas"></canvas>
            </div>
        `;
        this.root.appendChild(this.chartContainer);

        this.title = this.chartContainer.querySelector('.panel-chart-title');
        this.titleActions = this.chartContainer.querySelector('.panel-chart-title-actions');
        this.canvas = this.chartContainer.querySelector('.panel-chart-canvas');
        this.context = this.canvas.getContext('2d');

        // Register custom tooltip plugin
        if (typeof seriesCorrelationTooltip !== 'undefined') {
            Chart.register(seriesCorrelationTooltip);
        }

        // Initialize Chart.js instance
        const chartConfig = {
            type: 'scatter',
            data: { datasets: [] },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                animation: false,
                plugins: {
                    legend: { display: false },
                    tooltip: { enabled: false },
                    seriesCorrelationTooltip: { enabled: true }
                },
                scales: {
                    x: {
                        type: 'linear',
                        position: 'bottom',
                        title: { display: true, text: 'X Axis' }
                    },
                    y: {
                        type: 'linear',
                        title: { display: true, text: 'Y Axis' }
                    }
                }
            }
        };

        this.chart = new Chart(this.context, chartConfig);
    }

    buildChartOptions() {
        // Create sidebar structure
        this.chartOptions = document.createElement('div');
        this.chartOptions.classList.add('chart-options', 'inactive');
        this.chartOptions.innerHTML = `
            <div class="hide-chart-button-container">
                <button class="icon-button hide-chart-options" aria-label="Hide Options" title="Hide Options">
                    <svg class="hide-chart-options-svg" width="24" height="24">
                        <use href="#icon-close" />
                    </svg>
                </button>
            </div>

            <details class="chart-options-details analysis-mode-details" open>
                <summary>Analysis Mode</summary>
                <div class="view-options-suboption-container">
                    <div class="chart-view-option">
                        <select class="mode-selector">
                            <option value="differences">First Differences</option>
                            <option value="crossSectional">Year-by-Year Cross-Sectional</option>
                            <option value="pooled">Pooled Correlation</option>
                        </select>
                    </div>
                    <div class="mode-description"></div>
                    <div class="year-slider-container" style="display: block;">
                        <div class="chart-view-option year-slider-wrapper"></div>
                    </div>
                </div>
            </details>

            <details class="chart-options-details display-options-details" open>
                <summary>Display Options</summary>
                <div class="view-options-suboption-container">
                    <div class="chart-view-subheader">Country Group</div>
                    <div class="chart-view-option">
                        <select class="country-group-selector"></select>
                    </div>
                    <div class="chart-view-subheader">Regression</div>
                    <div class="chart-view-option">
                        <label>
                            <input type="checkbox" class="regression-toggle" checked>
                            Show Regression Line
                        </label>
                    </div>
                    <div class="chart-view-subheader">Point Colors</div>
                    <div class="chart-view-option">
                        <label>
                            <input type="checkbox" class="choropleth-toggle">
                            Color by Country
                        </label>
                    </div>
                </div>
            </details>

            <details class="chart-options-details statistics-details" open>
                <summary>Regression Statistics</summary>
                <div class="view-options-suboption-container">
                    <div class="stat-row">
                        <span class="stat-label">Slope (β₁):</span>
                        <span class="stat-value slope-value">-</span>
                    </div>
                    <div class="stat-row stat-row-se">
                        <span class="stat-label-indent">SE(β₁):</span>
                        <span class="stat-value se-slope-value">-</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">Constant (β₀):</span>
                        <span class="stat-value intercept-value">-</span>
                    </div>
                    <div class="stat-row stat-row-se">
                        <span class="stat-label-indent">SE(β₀):</span>
                        <span class="stat-value se-intercept-value">-</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">Std. Error:</span>
                        <span class="stat-value ser-value">-</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">R²:</span>
                        <span class="stat-value r-squared-value">-</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">Observations:</span>
                        <span class="stat-value n-value">-</span>
                    </div>
                </div>
            </details>
        `;

        // Create show options button
        this.showChartOptions = document.createElement('button');
        this.showChartOptions.classList.add('icon-button', 'show-chart-options');
        this.showChartOptions.setAttribute('aria-label', 'Show Chart Options');
        this.showChartOptions.setAttribute('title', 'Show Chart Options');
        this.showChartOptions.innerHTML = `
            <svg class="show-chart-options-svg" width="24" height="24">
                <use href="#icon-settings" />
            </svg>
        `;
        this.titleActions.appendChild(this.showChartOptions);

        // Create overlay for mobile
        this.overlay = document.createElement('div');
        this.overlay.classList.add('chart-options-overlay', 'inactive');
        this.root.appendChild(this.overlay);

        // Wrap and append options
        this.chartOptionsWrapper = document.createElement('div');
        this.chartOptionsWrapper.classList.add('chart-options-wrapper', 'inactive');
        this.chartOptionsWrapper.appendChild(this.chartOptions);
        this.root.appendChild(this.chartOptionsWrapper);
    }

    rigChartOptions() {
        // Show/hide sidebar
        this.showChartOptions.addEventListener('click', () => this.openChartOptionsSidebar());

        const hideButton = this.chartOptions.querySelector('.hide-chart-options');
        hideButton.addEventListener('click', () => this.closeChartOptionsSidebar());

        this.overlay.addEventListener('click', () => this.closeChartOptionsSidebar());

        // Series selectors (now in title area, not sidebar)
        this.seriesXSelector = this.chartContainer.querySelector('.series-x-selector');
        this.seriesYSelector = this.chartContainer.querySelector('.series-y-selector');

        this.seriesXSelector.addEventListener('change', () => this.handleSeriesChange());
        this.seriesYSelector.addEventListener('change', () => this.handleSeriesChange());

        // Mode selector
        this.modeSelector = this.chartOptions.querySelector('.mode-selector');
        this.modeSelector.value = this.currentMode;
        this.modeSelector.addEventListener('change', () => {
            this.switchMode(this.modeSelector.value);
            this.updateModeDescription();
        });

        // Mode description
        this.modeDescription = this.chartOptions.querySelector('.mode-description');
        this.updateModeDescription();

        // Year slider
        this.yearSliderWrapper = this.chartOptions.querySelector('.year-slider-wrapper');
        this.yearSliderContainer = this.chartOptions.querySelector('.year-slider-container');
        this.initYearSlider();

        // Country group selector
        this.countryGroupSelector = this.chartOptions.querySelector('.country-group-selector');
        this.countryGroupSelector.addEventListener('change', () => {
            this.countryGroup = this.countryGroupSelector.value;
            this.switchMode(this.currentMode);
        });

        // Regression toggle
        this.regressionToggle = this.chartOptions.querySelector('.regression-toggle');
        this.regressionToggle.addEventListener('change', (e) => {
            this.regressionLine = e.target.checked;
            this.updateChart();
        });

        // Choropleth toggle
        this.choroplethToggle = this.chartOptions.querySelector('.choropleth-toggle');
        this.choroplethToggle.addEventListener('change', (e) => {
            this.choropleth = e.target.checked;
            this.updateChart();
        });
    }

    initYearSlider() {
        this.yearSliderComponent = new YearSlider({
            containerId: 'correlation-year-slider',
            minYear: 2000,
            maxYear: 2023,
            initialYear: this.currentYear,
            storageKey: 'correlationYear',
            enablePlayback: false,
            onChange: (year) => {
                this.currentYear = year;
                if (this.currentMode === 'crossSectional') {
                    this.switchMode('crossSectional');
                }
            }
        });
        this.yearSliderWrapper.appendChild(this.yearSliderComponent.getElement());
    }

    openChartOptionsSidebar() {
        this.chartOptions.classList.remove('inactive');
        this.chartOptions.classList.add('active');
        this.chartOptionsWrapper.classList.remove('inactive');
        this.chartOptionsWrapper.classList.add('active');
        this.overlay.classList.remove('inactive');
        this.overlay.classList.add('active');
    }

    closeChartOptionsSidebar() {
        this.chartOptions.classList.remove('active');
        this.chartOptions.classList.add('inactive');
        this.chartOptionsWrapper.classList.remove('active');
        this.chartOptionsWrapper.classList.add('inactive');
        this.overlay.classList.remove('active');
        this.overlay.classList.add('inactive');
    }

    /* ===== DATA FETCHING ===== */

    async fetchSeriesOptions() {
        const response = await fetch('/api/v1/series-options');
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        this.seriesOptions = await response.json();
    }

    populateSeriesDropdowns() {
        // Define the desired order of optgroups (matching API keys)
        const groupOrder = ['Index', 'Pillars', 'Categories', 'Indicators', 'Datasets'];

        // Populate both dropdowns
        [this.seriesXSelector, this.seriesYSelector].forEach((selector, index) => {
            selector.innerHTML = '<option value="">-- Select --</option>';

            // Add optgroups in the specified order
            groupOrder.forEach(groupName => {
                const series = this.seriesOptions[groupName];
                if (series && series.length > 0) {
                    const optgroup = document.createElement('optgroup');
                    optgroup.label = groupName;

                    series.forEach(s => {
                        const option = document.createElement('option');
                        option.value = s.code;
                        option.textContent = `${s.name}\u0020(${s.code})`;

                        // Set selected if matches initial values
                        if ((index === 0 && s.code === this.seriesX) ||
                            (index === 1 && s.code === this.seriesY)) {
                            option.selected = true;
                        }

                        optgroup.appendChild(option);
                    });

                    selector.appendChild(optgroup);
                }
            });
        });

        // Initialize searchable dropdowns
        this.searchableDropdownX = new SearchableDropdown(this.seriesXSelector, {
            placeholder: 'Search series...',
            onChange: () => this.handleSeriesChange()
        });

        this.searchableDropdownY = new SearchableDropdown(this.seriesYSelector, {
            placeholder: 'Search series...',
            onChange: () => this.handleSeriesChange()
        });
    }

    handleSeriesChange() {
        this.seriesX = this.seriesXSelector.value;
        this.seriesY = this.seriesYSelector.value;

        if (this.seriesX && this.seriesY) {
            if (this.seriesX === this.seriesY) {
                this.showError('Please select different series for X and Y axes.');
                return;
            }

            // Update URL
            this.updateURL();

            // Load data
            this.loadCorrelationData();
        } else {
            this.showSelectionPrompt();
        }
    }

    async loadCorrelationData() {
        try {
            this.showLoading();
            const response = await fetch(`/api/v1/correlation/${this.seriesX}/${this.seriesY}`);

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || `HTTP ${response.status}`);
            }

            this.rawData = await response.json();
            this.updateCountryGroupSelector();
            this.switchMode(this.currentMode);
        } catch (error) {
            console.error('Failed to load correlation data:', error);
            this.showError(`Failed to load data: ${error.message}`);
        }
    }

    updateURL() {
        const url = new URL(window.location);
        url.searchParams.set('seriesX', this.seriesX);
        url.searchParams.set('seriesY', this.seriesY);
        window.history.pushState({}, '', url);
    }

    /* ===== MODE SWITCHING & DATA TRANSFORMATION ===== */

    switchMode(mode) {
        this.currentMode = mode;
        this.modeSelector.value = mode;

        // Show/hide year slider
        if (mode === 'crossSectional') {
            this.yearSliderContainer.style.display = 'block';

            // Sync chart year with slider's current year when entering cross-sectional mode
            if (this.yearSliderComponent) {
                this.currentYear = this.yearSliderComponent.year;
            }
        } else {
            this.yearSliderContainer.style.display = 'none';
        }

        // Transform and update
        if (this.rawData) {
            this.transformData();
            this.updateChart();
        }
    }

    updateModeDescription() {
        if (this.modeDescription) {
            const description = this.modeDescriptions[this.currentMode] || '';
            this.modeDescription.textContent = description;
        }
    }

    transformData() {
        switch (this.currentMode) {
            case 'pooled':
                this.transformedData = this.transformPooled();
                break;
            case 'crossSectional':
                this.transformedData = this.transformCrossSectional();
                break;
            case 'differences':
                this.transformedData = this.transformDifferences();
                break;
        }
    }

    transformPooled() {
        const points = [];
        this.rawData.data.forEach(country => {
            if (!this.shouldIncludeCountry(country)) return;

            country.years.forEach((year, idx) => {
                const x = country.xValues[idx];
                const y = country.yValues[idx];
                if (x == null || y == null) return;

                points.push({
                    x, y,
                    CCode: country.CCode,
                    CName: country.CName,
                    CFlag: country.CFlag,
                    year
                });
            });
        });
        return points;
    }

    transformCrossSectional() {
        const points = [];
        const yearIndex = this.currentYear - 2000;

        this.rawData.data.forEach(country => {
            if (!this.shouldIncludeCountry(country)) return;

            const x = country.xValues[yearIndex];
            const y = country.yValues[yearIndex];
            if (x == null || y == null) return;

            points.push({
                x, y,
                CCode: country.CCode,
                CName: country.CName,
                CFlag: country.CFlag,
                year: this.currentYear
            });
        });
        return points;
    }

    transformDifferences() {
        const points = [];

        this.rawData.data.forEach(country => {
            if (!this.shouldIncludeCountry(country)) return;

            for (let i = 1; i < country.years.length; i++) {
                const x_curr = country.xValues[i];
                const x_prev = country.xValues[i - 1];
                const y_curr = country.yValues[i];
                const y_prev = country.yValues[i - 1];

                if (x_curr == null || x_prev == null || y_curr == null || y_prev == null) {
                    continue;
                }

                points.push({
                    x: x_curr - x_prev,
                    y: y_curr - y_prev,
                    CCode: country.CCode,
                    CName: country.CName,
                    CFlag: country.CFlag,
                    year: country.years[i]
                });
            }
        });
        return points;
    }

    shouldIncludeCountry(country) {
        if (this.countryGroup === 'All') return true;
        return country.CGroup && country.CGroup.includes(this.countryGroup);
    }

    /* ===== CHART UPDATING ===== */

    updateChart() {
        if (!this.transformedData) return;

        // Build scatter dataset
        const scatterDataset = {
            label: 'Countries',
            data: this.transformedData,
            backgroundColor: this.choropleth
                ? this.transformedData.map(point => this.options.colorProvider.get(point.CCode))
                : 'rgba(75, 192, 192, 0.6)',
            pointRadius: 4,
            pointHoverRadius: 6
        };

        // Update tooltip plugin options with current series metadata and theme colors
        // IMPORTANT: Sync hoverRadius with pointHoverRadius for consistent UX
        if (this.rawData) {
            this.chart.options.plugins.seriesCorrelationTooltip = {
                enabled: true,
                seriesX: this.rawData.seriesX,
                seriesY: this.rawData.seriesY,
                choropleth: this.choropleth,
                colorProvider: this.options.colorProvider,
                tooltipBg: this.headerBackgroundColor,
                tooltipFg: this.titleColor,
                tooltipFgAccent: this.greenAccent,
                hoverRadius: scatterDataset.pointHoverRadius  // Match point hover radius
            };
        }

        this.chart.data.datasets = [scatterDataset];

        // Add regression line
        if (this.regressionLine && this.transformedData.length >= 2) {
            const regression = this.calculateRegression();
            if (regression) {
                this.chart.data.datasets.push(regression.dataset);
                this.updateStatistics(regression);
            }
        } else {
            this.updateStatistics(null);
        }

        // Update axes
        this.updateAxisLabels();
        this.updateAxisRanges();

        // Update title
        this.updateTitle();

        this.chart.update();
    }

    updateTitle() {
        if (!this.rawData) return;

        let title = `${this.rawData.seriesX.name}\u0020vs\u0020${this.rawData.seriesY.name}`;
        if (this.currentMode === 'crossSectional') {
            title += `\u0020(${this.currentYear})`;
        } else if (this.currentMode === 'differences') {
            title += '\u0020(First Differences)';
        }
        this.title.textContent = title;
    }

    updateAxisLabels() {
        if (!this.rawData) return;

        let xLabel = this.rawData.seriesX.name;
        let yLabel = this.rawData.seriesY.name;

        if (this.currentMode === 'differences') {
            xLabel = 'Δ' + xLabel;
            yLabel = 'Δ' + yLabel;
        }

        this.chart.options.scales.x.title.text = xLabel;
        this.chart.options.scales.y.title.text = yLabel;
    }

    isItemSeries(series) {
        // Item series (Indicator, Pillar, Category, SSPI) have scores that range 0-1
        // Dataset series have values that can be any range
        const itemTypes = ['Indicator', 'Pillar', 'Category', 'SSPI'];
        return itemTypes.includes(series.type);
    }

    updateAxisRanges() {
        if (!this.rawData) return;

        const isYItem = this.isItemSeries(this.rawData.seriesY);
        const isXItem = this.isItemSeries(this.rawData.seriesX);
        const isNotDifferences = this.currentMode !== 'differences';

        // Y-axis
        if (isYItem && isNotDifferences) {
            this.chart.options.scales.y.min = 0;
            this.chart.options.scales.y.max = 1;
        } else {
            this.chart.options.scales.y.min = undefined;
            this.chart.options.scales.y.max = undefined;
        }

        // X-axis
        if (isXItem && isNotDifferences) {
            this.chart.options.scales.x.min = 0;
            this.chart.options.scales.x.max = 1;
        } else {
            this.chart.options.scales.x.min = undefined;
            this.chart.options.scales.x.max = undefined;
        }
    }

    /* ===== STATISTICS & REGRESSION ===== */

    calculateRegression() {
        const data = this.transformedData;
        const n = data.length;
        if (n < 2) return null;

        const xMean = data.reduce((sum, p) => sum + p.x, 0) / n;
        const yMean = data.reduce((sum, p) => sum + p.y, 0) / n;

        let numerator = 0;
        let denominator = 0;

        data.forEach(p => {
            numerator += (p.x - xMean) * (p.y - yMean);
            denominator += (p.x - xMean) ** 2;
        });

        if (denominator === 0) return null;

        const slope = numerator / denominator;
        const intercept = yMean - slope * xMean;

        // Calculate R² and residual sum of squares
        let ssTot = 0;
        let ssRes = 0;

        data.forEach(p => {
            const yPred = slope * p.x + intercept;
            ssTot += (p.y - yMean) ** 2;
            ssRes += (p.y - yPred) ** 2;
        });

        const rSquared = ssTot === 0 ? 0 : 1 - (ssRes / ssTot);
        const correlation = Math.sqrt(Math.abs(rSquared)) * Math.sign(slope);

        // Calculate standard errors
        // Standard error of the regression (SER)
        const ser = n > 2 ? Math.sqrt(ssRes / (n - 2)) : 0;

        // Standard error of the slope coefficient
        const seSlopeDenominator = Math.sqrt(denominator);
        const seSlope = seSlopeDenominator > 0 ? ser / seSlopeDenominator : 0;

        // Standard error of the intercept coefficient
        // SE(β₀) = SER × √[Σx²/(n×Σ(x-x̄)²)]
        const sumXSquared = data.reduce((sum, p) => sum + p.x ** 2, 0);
        const seIntercept = denominator > 0 ? ser * Math.sqrt(sumXSquared / (n * denominator)) : 0;

        const xMin = Math.min(...data.map(p => p.x));
        const xMax = Math.max(...data.map(p => p.x));

        return {
            slope,
            intercept,
            rSquared,
            correlation,
            n,
            ser,
            seSlope,
            seIntercept,
            dataset: {
                label: 'Regression Line',
                data: [
                    { x: xMin, y: slope * xMin + intercept },
                    { x: xMax, y: slope * xMax + intercept }
                ],
                type: 'line',
                borderColor: 'rgba(255, 99, 132, 0.8)',
                borderWidth: 2,
                pointRadius: 0,
                fill: false
            }
        };
    }

    updateStatistics(regression) {
        const rSquaredValue = this.chartOptions.querySelector('.r-squared-value');
        const slopeValue = this.chartOptions.querySelector('.slope-value');
        const seSlopeValue = this.chartOptions.querySelector('.se-slope-value');
        const interceptValue = this.chartOptions.querySelector('.intercept-value');
        const seInterceptValue = this.chartOptions.querySelector('.se-intercept-value');
        const nValue = this.chartOptions.querySelector('.n-value');
        const serValue = this.chartOptions.querySelector('.ser-value');

        if (!regression) {
            rSquaredValue.textContent = '-';
            slopeValue.textContent = '-';
            seSlopeValue.textContent = '-';
            interceptValue.textContent = '-';
            seInterceptValue.textContent = '-';
            nValue.textContent = this.transformedData ? this.transformedData.length : '-';
            serValue.textContent = '-';
            return;
        }

        slopeValue.textContent = regression.slope.toFixed(3);
        seSlopeValue.textContent = `(${regression.seSlope.toFixed(3)})`;
        interceptValue.textContent = regression.intercept.toFixed(3);
        seInterceptValue.textContent = `(${regression.seIntercept.toFixed(3)})`;
        serValue.textContent = regression.ser.toFixed(3);
        rSquaredValue.textContent = regression.rSquared.toFixed(3);
        nValue.textContent = regression.n;
    }

    updateCountryGroupSelector() {
        if (!this.rawData) return;

        this.countryGroupSelector.innerHTML = '';

        // Add "All" option
        const allOption = document.createElement('option');
        allOption.value = 'All';
        allOption.textContent = 'All Countries';
        this.countryGroupSelector.appendChild(allOption);

        // Add group options
        this.rawData.groupOptions.forEach(group => {
            const option = document.createElement('option');
            option.value = group;
            option.textContent = group;
            if (group === this.countryGroup) {
                option.selected = true;
            }
            this.countryGroupSelector.appendChild(option);
        });
    }

    /* ===== UI HELPERS ===== */

    showSelectionPrompt() {
        this.title.textContent = 'Select series to begin';
        this.chart.data.datasets = [];
        this.chart.update();
    }

    showLoading() {
        this.title.textContent = 'Loading...';
    }

    showError(message) {
        this.title.textContent = 'Error';
        this.chart.data.datasets = [];
        this.chart.update();
        console.error(message);
    }

    /* ===== THEME MANAGEMENT ===== */

    setTheme(theme) {
        const root = document.documentElement;
        const bg = getComputedStyle(root).getPropertyValue('--header-color').trim();
        this.headerBackgroundColor = bg;
        const greenAccent = getComputedStyle(root)?.getPropertyValue('--green-accent')?.trim() || '#8BA342';
        this.greenAccent = greenAccent;

        if (theme !== 'light') {
            this.theme = 'dark';
            this.tickColor = '#bbb';
            this.titleColor = '#ccc';
        } else {
            this.theme = 'light';
            this.tickColor = '#444';
            this.titleColor = '#444';
            this.headerBackgroundColor = this.headerBackgroundColor || '#f0f0f0';
        }

        // Update chart if it exists
        if (this.chart) {
            this.updateChart();
        }
    }
}
