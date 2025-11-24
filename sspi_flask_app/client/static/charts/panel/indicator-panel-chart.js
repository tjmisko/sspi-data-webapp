class IndicatorPanelChart extends PanelChart {
    constructor(parentElement, itemCode, { CountryList = [], width = 600, height = 600 } = {} ) {
        super(parentElement, { CountryList: CountryList, endpointURL: `/api/v1/panel/indicator/${itemCode}`, width: width, height: height })
        // this.rigDatasetSelector()
        this.itemCode = itemCode
        this.activeSeries = itemCode
        this.currentYMin = 0
        this.currentYMax = 1
        this.defaultYMin = 0
        this.defaultYMax = 1

        // Initialize showImputations from storage with proper boolean conversion
        this.showImputations = window.observableStorage.getItem("showImputations") === "true"

        // Store previous states of other imputation toggles
        // These will be populated after parent constructor runs and checkboxes exist
        this.savedExtrapolateBackwardState = null
        this.savedInterpolateState = null

        this.moveBurgerToBreadcrumb()
    }

    moveBurgerToBreadcrumb() {
        // Move hamburger menu from title actions to breadcrumb actions
        if (this.showChartOptions && this.breadcrumbActions) {
            this.breadcrumbActions.appendChild(this.showChartOptions)
        }
    }

    updateChartOptions() {
        // Get Y-axis title based on active series
        let yAxisTitle = 'Item\u0020Value';  // Default fallback
        if (this.activeSeries === this.itemCode) {
            yAxisTitle = 'Indicator\u0020Score';
        } else if (this.datasetOptions) {
            const dataset = this.datasetOptions.find(d => d.datasetCode === this.activeSeries);
            if (dataset) {
                const datasetName = (dataset.datasetName && dataset.datasetName.trim()) ? dataset.datasetName : dataset.datasetCode;
                const baseName = `Dataset:\u0020${datasetName}`;
                const unit = dataset.unit || dataset.Unit;
                yAxisTitle = unit ? `${baseName}\u0020(${unit})` : baseName;
            }
        }
        
        this.chart.options.scales = {
            x: {
                ticks: {
                    color: this.tickColor,
                },
                type: "category",
                title: {
                    display: true,
                    text: 'Year',
                    color: this.axisTitleColor,
                    font: {
                        size: 16
                    }
                },
            },
            y: {
                ticks: {
                    color: this.tickColor,
                },
                beginAtZero: true,
                min: this.currentYMin,
                max: this.currentYMax,
                title: {
                    display: true,
                    text: yAxisTitle,
                    color: this.axisTitleColor,
                    font: {
                        size: 16
                    }
                }
            }
        }
    }

    updateItemDropdown(options, itemType) {
        let itemTypeCapped = itemType
        if (itemType === "sspi") {
            itemTypeCapped = this.itemType.toUpperCase()
        } else {
            itemTypeCapped = this.itemType.charAt(0).toUpperCase() + this.itemType.slice(1)
        }
        const itemTitle = itemTypeCapped + ' Information';
        const itemSummary = this.itemInformation.querySelector('.item-information-summary')
        itemSummary.textContent = itemTitle;
        const defaultValue = '/data/' + itemType.toLowerCase() + '/' + this.itemCode
        console.log('Default value for item dropdown:', defaultValue)
        for (const option of options) {
            const opt = document.createElement('option')
            opt.value = option.Value
            if (option.Value === defaultValue) {
                opt.selected = true;
            }
            opt.textContent = option.Text;
            this.itemDropdown.appendChild(opt)
        }
        this.itemDropdown.addEventListener('change', (event) => {
            window.location.href = event.target.value
        })
    }

    setActiveSeries(series) {
        this.activeSeries = series
        
        // Update defaults for the new series
        this.updateDefaultsForActiveSeries()
        
        if (this.activeSeries === this.itemCode) {
            this.chart.data.datasets.forEach((dataset) => {
                dataset.data = dataset.score
            });
            this.setYAxisMinMax(this.defaultYMin, this.defaultYMax)
        } else if (this.datasetOptions && this.datasetOptions.map(o => o.datasetCode).includes(this.activeSeries)) {
            this.chart.data.datasets.forEach((dataset) => {
                dataset.data = this.getDatasetDataSafely(dataset, this.activeSeries);
            });

            // Log summary of availability
            const missingCount = this.chart.data.datasets.filter(d =>
                !d.Datasets || !d.Datasets[this.activeSeries]
            ).length;
            if (missingCount > 0) {
                console.warn(`Dataset ${this.activeSeries}: ${missingCount}/${this.chart.data.datasets.length} countries missing data`);
            }

            console.log(`Setting active series to ${this.activeSeries} with yMin: ${this.defaultYMin}, yMax: ${this.defaultYMax}`);
            this.setYAxisMinMax(this.defaultYMin, this.defaultYMax)
        } else {
            console.warn(`Active series "${this.activeSeries}" not found in dataset options.`);
        }
        
        // Update titles and UI elements
        this.updateChartTitle()
        this.updateChartOptions()  // This will update Y-axis title
        this.updateActiveSeriesDescription()  // Update active series description
        this.updateYAxisInputs()
        this.updateRestoreButton()
        this.updateYearRange()

        // Force chart to re-render with new data
        this.chart.update()

        // Apply imputation settings and update chart
        this.updateChartData()
    }

    /**
     * Safely retrieve dataset data with fallback to null array
     * @param {Object} dataset - Chart.js dataset object
     * @param {string} datasetCode - Dataset code to retrieve
     * @returns {Array} Dataset data array or null-filled array
     */
    getDatasetDataSafely(dataset, datasetCode) {
        // Check if Datasets property exists
        if (!dataset.Datasets) {
            console.warn(`Dataset ${dataset.CCode} missing Datasets property`);
            return Array(this.chart.data.labels.length).fill(null);
        }

        // Check if specific dataset exists
        if (!dataset.Datasets[datasetCode]) {
            console.warn(`Dataset ${dataset.CCode} missing ${datasetCode}`);
            return Array(this.chart.data.labels.length).fill(null);
        }

        // Check if data array exists
        const dataArray = dataset.Datasets[datasetCode].data;
        if (!dataArray || !Array.isArray(dataArray)) {
            console.warn(`Dataset ${dataset.CCode}.${datasetCode} has invalid data`);
            return Array(this.chart.data.labels.length).fill(null);
        }

        return dataArray;
    }

    setYAxisMinMax(min, max, update = true) {
        // Round to 2 decimal places for display consistency
        this.currentYMin = Math.round(min * 100) / 100
        this.currentYMax = Math.round(max * 100) / 100
        this.chart.options.scales.y.min = this.currentYMin
        this.chart.options.scales.y.max = this.currentYMax
        if (update) {
            this.chart.update()
        }
        // Update input field values if they exist
        if (this.yMinInput) {
            this.yMinInput.value = this.currentYMin
        }
        if (this.yMaxInput) {
            this.yMaxInput.value = this.currentYMax
        }
    }

    updateChartData() {
        // Merge score and imputedScore arrays based on toggle state
        // This creates perfect complement behavior: where score exists, use it;
        // where score is null and showImputations is on, use imputedScore
        // NOTE: Only applies when viewing indicator scores, not datasets
        if (!this.chart || !this.chart.data || !this.chart.data.datasets) {
            return;
        }

        // Only update data if we're viewing the indicator score, not a dataset
        if (this.activeSeries !== this.itemCode) {
            // We're viewing a dataset, not the indicator score
            // Don't modify the data arrays
            return;
        }

        this.chart.data.datasets.forEach((dataset) => {
            if (this.showImputations && dataset.imputedScore) {
                // Merge: use score where available, fill with imputedScore where score is null
                dataset.data = dataset.score.map((val, i) =>
                    val !== null ? val : (dataset.imputedScore[i] !== null ? dataset.imputedScore[i] : null)
                );
            } else {
                // Show real data only
                dataset.data = dataset.score;
            }
        });

        this.chart.update();
    }

    update(data) {
        console.log(data)

        // Check if data has an error or empty datasets
        if (data.error || !data.data || data.data.length === 0) {
            // Display error message in chart container
            const errorMessage = data.error || 'No chart data available for this indicator';
            console.warn('Chart data error:', errorMessage);

            // Create error display
            const errorDiv = document.createElement('div');
            errorDiv.className = 'chart-error-message';
            errorDiv.style.cssText = 'padding: 2rem; text-align: center; color: var(--text-color); background: var(--bg-color);';
            errorDiv.innerHTML = `
                <p style="font-size: 1.1rem; font-weight: 600; margin-bottom: 0.5rem;">⚠️ No Data Available</p>
                <p style="font-size: 0.95rem; opacity: 0.8;">${errorMessage}</p>
            `;

            // Replace chart container with error message
            this.chartContainer.innerHTML = '';
            this.chartContainer.appendChild(errorDiv);

            return; // Exit early
        }

        // Force refresh of chart interaction plugin labels when data changes
        if (this.chartInteractionPlugin && this.chartInteractionPlugin._forceRefreshLabels) {
            this.chartInteractionPlugin._forceRefreshLabels(this.chart)
        }

        this.chart.data.datasets = data.data
        this.chart.data.labels = data.labels
        if (this.pinnedOnly) {
            this.hideUnpinned()
        } else {
            this.showGroup(this.countryGroup)
        }
        this.datasetOptions = data.datasetOptions
        this.originalTitle = data.title  // Store original title for indicator score
        this.treepath = data.treepath  // Store treepath for later use
        
        // Use breadcrumb navigation for indicators, simple title for others
        if (data.itemType === "Indicator" && data.treepath) {
            this.renderBreadcrumb(data.treepath, data.title, data.itemCode, data.itemType);
        } else {
            // Fallback to simple title for non-indicators
            this.title.innerText = data.title;
            this.chartContainer.querySelector('.panel-chart-title-container').style.display = 'flex';
            if (this.breadcrumbContainer) {
                this.breadcrumbContainer.style.display = 'none';
            }
        }
        
        this.itemType = data.itemType
        this.groupOptions = data.groupOptions
        this.countryGroupMap = data.countryGroupMap || {}
        this.missingCountries = [] // Initialize as empty, will be populated asynchronously
        this.getPins()
        this.updateLegend()
        this.updateItemDropdown(data.itemOptions, data.itemType)
        this.updateDescription(data.description)
        this.updateChartColors()
        this.updateCountryGroups()
        this.initializeDefaultRanges()
        this.updateSeriesDropdown()
        this.updateChartTitle()  // Set initial title based on active series
        this.updateActiveSeriesDescription()  // Set initial active series description

        // Auto-enable imputation in country list mode if all real data is null
        if (this.isCountryListMode && data.data && data.data.length > 0) {
            const allScoresNull = data.data.every(dataset => {
                const scores = dataset.score || []
                return scores.length === 0 || scores.every(val => val === null || val === undefined)
            })

            if (allScoresNull && !this.showImputations) {
                console.log('Country List Mode: All real data is null, auto-enabling imputations')
                this.showImputations = true
                window.observableStorage.setItem("showImputations", "true")

                // Update checkbox if it exists
                const checkbox = this.chartOptions.querySelector('.show-all-imputations')
                if (checkbox) {
                    checkbox.checked = true
                }

                // Apply the state (disable other toggles, force them on)
                this.applyShowAllImputationsState(true)
            }
        }

        // Apply imputation settings and update chart
        this.updateChartData()

        // Compute missing countries asynchronously (skip in country list mode)
        if (!this.isCountryListMode) {
            console.log('=== IndicatorPanelChart about to call computeMissingCountriesAsync ===')
            console.log('countryGroupMap available?', !!this.countryGroupMap, Object.keys(this.countryGroupMap || {}).length, 'countries')
            this.computeMissingCountriesAsync()
        } else {
            console.log('Skipping missing countries computation in country list mode')
        }
    }

    initChartJSCanvas() {
        this.chartContainer = document.createElement('div')
        this.chartContainer.classList.add('panel-chart-container')
        this.chartContainer.innerHTML = `
<div class="panel-chart-breadcrumb-container" style="display: none;">
    <nav class="panel-chart-breadcrumb" aria-label="Hierarchy navigation"></nav>
    <div class="panel-chart-breadcrumb-actions"></div>
</div>
<div class="panel-chart-title-container">
    <h2 class="panel-chart-title"></h2>
    <div class="panel-chart-title-actions"></div>
</div>
<div class="panel-canvas-wrapper">
    <canvas class="panel-chart-canvas"></canvas>
</div>
`;
        this.root.appendChild(this.chartContainer)
        this.breadcrumbContainer = this.chartContainer.querySelector('.panel-chart-breadcrumb-container')
        this.breadcrumb = this.chartContainer.querySelector('.panel-chart-breadcrumb')
        this.breadcrumbActions = this.chartContainer.querySelector('.panel-chart-breadcrumb-actions')
        this.title = this.chartContainer.querySelector('.panel-chart-title')
        this.titleActions = this.chartContainer.querySelector('.panel-chart-title-actions')
        this.canvas = this.chartContainer.querySelector('.panel-chart-canvas')
        this.context = this.canvas.getContext('2d')
        this.chart = new Chart(this.context, {
            type: 'line',
            plugins: [this.chartInteractionPlugin, this.extrapolateBackwardPlugin],
            options: {
                animation: false,
                responsive: true,
                hover: {
                    mode: null
                },
                maintainAspectRatio: false,
                datasets: {
                    line: {
                        spanGaps: true,
                        pointRadius: 2,
                        pointHoverRadius: 4,
                        segment: {
                            borderWidth: 2,
                            borderDash: ctx => {
                                return ctx.p0.skip || ctx.p1.skip ? [10, 4] : [];
                                // Dashed when spanning gaps, solid otherwise
                            }
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: false,
                    },
                    tooltip: {
                        enabled: false,
                    },
                    chartInteractionPlugin: {
                        enabled: true,
                        radius: 20,
                        clickRadius: 2,
                        tooltipBg: this.headerBackgroundColor,
                        tooltipFg: this.titleColor,
                        labelField: 'CCode',
                        showDefaultLabels: true,
                        defaultLabelSpacing: 5,
                        onDatasetClick: (datasets, event, chart) => {
                            datasets.forEach((dataset) => {
                                this.togglePin(dataset)
                                this.activeCountry = dataset;
                                this.updateCountryInformation();
                            });
                        }
                    },
                },
                layout: {
                    padding: {
                        right: 40
                    }
                }
            }
        })
    }

    renderBreadcrumb(treePath, title, itemCode, itemType) {
        if (itemType !== "Indicator" || !treePath || treePath.length === 0) {
            // Show simple title container for non-indicators or invalid treepath
            this.chartContainer.querySelector('.panel-chart-title-container').style.display = 'flex';
            this.breadcrumbContainer.style.display = 'none';
            return;
        }

        // Hide title container and show breadcrumb container for indicators
        this.chartContainer.querySelector('.panel-chart-title-container').style.display = 'none';
        this.breadcrumbContainer.style.display = 'flex';

        // Build breadcrumb HTML
        let breadcrumbHTML = '';
        
        // Process each level in the tree path (except the last one)
        for (let i = 0; i < treePath.length - 1; i++) {
            const item = treePath[i];
            let code, itemName, displayName, url, tooltip;
            
            // Handle both old format (strings) and new format (objects) for backwards compatibility
            if (typeof item === 'string') {
                code = item.toLowerCase();
                // Fallback to old logic for backwards compatibility
                if (code === 'sspi') {
                    displayName = 'SSPI';
                    itemName = 'Social Policy and Progress Index';
                    url = '/data';
                } else if (i === 1) {
                    displayName = code.toUpperCase();
                    itemName = code.toUpperCase();
                    url = '/data/pillar/' + code.toUpperCase();
                } else if (i === 2) {
                    displayName = code.toUpperCase();
                    itemName = code.toUpperCase();
                    url = '/data/category/' + code.toUpperCase();
                } else {
                    displayName = code.toUpperCase();
                    itemName = code.toUpperCase();
                    url = null;
                }
            } else {
                // New object format with itemCode and itemName
                code = item.itemCode;
                itemName = item.itemName;
                
                // Map codes to display names and URLs
                if (code === 'sspi') {
                    displayName = 'SSPI';
                    url = '/data';
                } else if (i === 1) {
                    // Second level is pillar
                    displayName = code.toUpperCase();
                    url = '/data/pillar/' + code.toUpperCase();
                } else if (i === 2) {
                    // Third level is category
                    displayName = code.toUpperCase();
                    url = '/data/category/' + code.toUpperCase();
                } else {
                    // Fallback for other levels
                    displayName = code.toUpperCase();
                    url = null;
                }
            }

            // Add separator if not first item
            if (i > 0) {
                breadcrumbHTML += '<span class="breadcrumb-separator">></span>';
            }

            // Add breadcrumb item with link and tooltip
            breadcrumbHTML += '<a href="' + url + '" class="breadcrumb-item" title="' + itemName + '">' + displayName + '</a>';
        }

        // Add final separator and current page title with itemCode (no link)
        if (treePath.length > 0) {
            breadcrumbHTML += '<span class="breadcrumb-separator">></span>';
        }
        breadcrumbHTML += '<span class="breadcrumb-current">' + title + ' (' + itemCode + ')</span>';

        this.breadcrumb.innerHTML = breadcrumbHTML;
    }

    buildChartOptions() {
        // Call parent method first
        super.buildChartOptions()
        const viewOptions = this.chartOptions.querySelector('.chart-view-options')
        if (viewOptions) {
            // Find the existing container with Imputation Options
            const existingContainer = viewOptions.querySelector('.view-options-suboption-container')
            if (existingContainer) {
                // Add our new content to the existing container
                const seriesControlsHTML = `
                    <div class="chart-view-subheader">Active Series</div>
                    <div class="chart-view-option series-selector-container">
                        <select class="series-selector" id="series-selector">
                            <option value="` + this.itemCode + `" selected>` + this.itemCode + ` Indicator Score</option>
                        </select>
                    </div>
                    <div class="chart-view-subheader y-axis-range-subheader">Y-Axis Range</div>
                    <div class="chart-view-option y-axis-controls">
                        <div class="y-axis-input-group">
                            <label class="title-bar-label" for="y-min-input">Y Min:</label>
                            <input type="number" class="y-min-input" id="y-min-input" step="0.01" value="0"/>
                        </div>
                        <div class="y-axis-input-group">
                            <label class="title-bar-label" for="y-max-input">Y Max:</label>
                            <input type="number" class="y-max-input" id="y-max-input" step="0.01" value="1"/>
                        </div>
                        <button class="restore-y-axis-button" style="display: none;">Restore Default Range</button>
                    </div>
                `;
                // Insert at the beginning so Imputation Options stay at the bottom
                existingContainer.insertAdjacentHTML('afterbegin', seriesControlsHTML)

                // Add Show All Imputations toggle to existing Imputation Options section
                const imputationOptionsHeader = Array.from(existingContainer.querySelectorAll('.chart-view-subheader'))
                    .find(header => header.textContent.includes('Imputation Options'));
                if (imputationOptionsHeader) {
                    const imputationToggleHTML = `
                        <div class="chart-view-option">
                            <input type="checkbox" class="show-all-imputations" ${this.showImputations ? 'checked' : ''}/>
                            <label class="title-bar-label">Show All Imputations</label>
                        </div>
                    `;
                    // Insert after the Imputation Options header
                    imputationOptionsHeader.insertAdjacentHTML('afterend', imputationToggleHTML);
                }
            }
        }
    }

    rigChartOptions() {
        // Call parent method first
        super.rigChartOptions()

        // Wire up our custom controls
        this.rigViewOptionsControls()

        // Initialize imputation state after checkboxes exist
        this.initializeImputationState()
    }

    initializeImputationState() {
        // This is called after parent setup, so checkboxes exist
        if (this.extrapolateBackwardCheckbox && this.interpolateCheckbox) {
            // Store initial states
            this.savedExtrapolateBackwardState = this.extrapolateBackwardCheckbox.checked
            this.savedInterpolateState = this.interpolateCheckbox.checked

            // If showImputations is already on (from storage), apply it immediately
            if (this.showImputations) {
                this.applyShowAllImputationsState(true)
            }
        }
    }

    applyShowAllImputationsState(enabled) {
        if (!this.extrapolateBackwardCheckbox || !this.interpolateCheckbox) {
            return
        }

        if (enabled) {
            // Save current states before overriding
            this.savedExtrapolateBackwardState = this.extrapolateBackwardCheckbox.checked
            this.savedInterpolateState = this.interpolateCheckbox.checked

            // Force both toggles ON and DISABLE them
            this.extrapolateBackwardCheckbox.checked = true
            this.interpolateCheckbox.checked = true
            this.extrapolateBackwardCheckbox.disabled = true
            this.interpolateCheckbox.disabled = true

            // Apply the toggle states to the chart
            // Ensure backward extrapolation is active
            if (!this.extrapolateBackwardPlugin.enabled) {
                this.extrapolateBackwardPlugin.toggle()
            }
            // Ensure linear interpolation is active (spanGaps = true)
            if (!this.chart.options.datasets.line.spanGaps) {
                this.chart.options.datasets.line.spanGaps = true
            }
        } else {
            // Restore previous states
            this.extrapolateBackwardCheckbox.checked = this.savedExtrapolateBackwardState
            this.interpolateCheckbox.checked = this.savedInterpolateState
            this.extrapolateBackwardCheckbox.disabled = false
            this.interpolateCheckbox.disabled = false

            // Apply the restored states to the chart
            if (this.extrapolateBackwardPlugin.enabled !== this.savedExtrapolateBackwardState) {
                this.extrapolateBackwardPlugin.toggle()
            }
            this.chart.options.datasets.line.spanGaps = this.savedInterpolateState
        }
    }

    rigUnloadListener() {
        // Call parent method first
        super.rigUnloadListener()

        // Add our own beforeunload listener for showImputations state
        window.addEventListener("beforeunload", () => {
            window.observableStorage.setItem("showImputations", this.showImputations.toString())
        })
    }

    rigViewOptionsControls() {
        // Get references to our controls
        this.seriesSelector = this.chartOptions.querySelector('.series-selector')
        this.yMinInput = this.chartOptions.querySelector('.y-min-input')
        this.yMaxInput = this.chartOptions.querySelector('.y-max-input')
        this.restoreYAxisButton = this.chartOptions.querySelector('.restore-y-axis-button')
        if (this.seriesSelector) {
            this.seriesSelector.addEventListener('change', (event) => {
                this.setActiveSeries(event.target.value)
            })
        }
        const handleYAxisChange = (event) => {
            const yMinValue = this.yMinInput.value
            const yMaxValue = this.yMaxInput.value
            
            // Allow temporary invalid states during typing (like "0." or "-")
            if (event.type === 'input' && (yMinValue.endsWith('.') || yMinValue === '-' || yMaxValue.endsWith('.') || yMaxValue === '-')) {
                return // Don't validate incomplete decimal inputs
            }
            
            const yMin = parseFloat(yMinValue)
            const yMax = parseFloat(yMaxValue)
            
            if (isNaN(yMin) || isNaN(yMax)) {
                return // Wait for valid input
            }
            
            if (yMin >= yMax) {
                return // Wait for valid range
            }
            
            this.setYAxisMinMax(yMin, yMax)
            this.updateRestoreButton()
        }
        
        // Listen for input changes with enhanced validation
        if (this.yMinInput) {
            this.yMinInput.addEventListener('input', handleYAxisChange)
            this.yMinInput.addEventListener('blur', handleYAxisChange)
        }
        
        if (this.yMaxInput) {
            this.yMaxInput.addEventListener('input', handleYAxisChange)
            this.yMaxInput.addEventListener('blur', handleYAxisChange)
        }
        
        // Wire up restore button
        if (this.restoreYAxisButton) {
            this.restoreYAxisButton.addEventListener('click', () => {
                this.setYAxisMinMax(this.defaultYMin, this.defaultYMax)
                this.updateRestoreButton()
            })
        }

        // Wire up show all imputations toggle
        const showImputationsCheckbox = this.chartOptions.querySelector('.show-all-imputations')
        if (showImputationsCheckbox) {
            // Ensure checkbox reflects current state on load
            showImputationsCheckbox.checked = this.showImputations

            showImputationsCheckbox.addEventListener('change', (e) => {
                this.showImputations = e.target.checked
                window.observableStorage.setItem("showImputations", this.showImputations.toString())

                // Apply state to other toggles
                this.applyShowAllImputationsState(this.showImputations)

                // Update chart data
                this.updateChartData()
            })
        }
    }

    updateRestoreButton() {
        if (!this.restoreYAxisButton) return
        
        // Show button only if current values differ from defaults
        const hasChanged = (this.currentYMin !== this.defaultYMin || this.currentYMax !== this.defaultYMax)
        this.restoreYAxisButton.style.display = hasChanged ? 'block' : 'none'
    }

    updateYAxisInputs() {
        // Update Y-axis inputs with current values
        if (this.yMinInput) {
            this.yMinInput.value = this.currentYMin
        }
        if (this.yMaxInput) {
            this.yMaxInput.value = this.currentYMax
        }
    }

    initializeDefaultRanges() {
        // Initialize default ranges for all series
        this.seriesDefaults = {
            [this.itemCode]: { yMin: 0, yMax: 1 }
        }
        
        // Add defaults from datasetOptions
        if (this.datasetOptions) {
            this.datasetOptions.forEach(dataset => {
                this.seriesDefaults[dataset.datasetCode] = {
                    yMin: dataset.yMin || 0,
                    yMax: dataset.yMax || 100
                }
            })
        }
        this.updateDefaultsForActiveSeries()
    }
    
    updateDefaultsForActiveSeries() {
        if (this.seriesDefaults && this.seriesDefaults[this.activeSeries]) {
            this.defaultYMin = this.seriesDefaults[this.activeSeries].yMin
            this.defaultYMax = this.seriesDefaults[this.activeSeries].yMax
        } else {
            // Fallback defaults
            this.defaultYMin = this.activeSeries === this.itemCode ? 0 : 0
            this.defaultYMax = this.activeSeries === this.itemCode ? 1 : 100
        }
    }

    updateChartTitle() {
        if (!this.title) return

        if (this.activeSeries === this.itemCode) {
            // For indicator score, show breadcrumb if we have treepath data
            if (this.treepath && this.itemType === "Indicator") {
                this.renderBreadcrumb(this.treepath, this.originalTitle || 'Indicator Chart', this.itemCode, this.itemType);
            } else {
                // Use original title for indicator score
                this.title.innerText = this.originalTitle || 'Indicator Chart';
                this.chartContainer.querySelector('.panel-chart-title-container').style.display = 'flex';
                if (this.breadcrumbContainer) {
                    this.breadcrumbContainer.style.display = 'none';
                }
            }
        } else if (this.datasetOptions) {
            // For datasets, use format: "Dataset Name (DATASET_CODE)"
            const dataset = this.datasetOptions.find(d => d.datasetCode === this.activeSeries);
            if (dataset) {
                // Use datasetName if available and non-empty, otherwise use datasetCode
                const datasetName = (dataset.datasetName && dataset.datasetName.trim()) ? dataset.datasetName : dataset.datasetCode;
                this.title.innerText = `${datasetName}\u0020(${dataset.datasetCode})`;
            } else {
                // Fallback if dataset not found in options
                this.title.innerText = `Dataset:\u0020${this.activeSeries}`;
            }
            this.chartContainer.querySelector('.panel-chart-title-container').style.display = 'flex';
            if (this.breadcrumbContainer) {
                this.breadcrumbContainer.style.display = 'none';
            }
        }
    }

    updateSeriesDropdown() {
        if (!this.seriesSelector) {
            return
        }
        // Clear all existing options
        this.seriesSelector.innerHTML = ''
        // Add the indicator score option first
        const indicatorOption = document.createElement('option')
        indicatorOption.value = this.itemCode
        indicatorOption.textContent = "Indicator: " + this.itemCode + ' Indicator Score'
        this.seriesSelector.appendChild(indicatorOption)
        // Add dataset options if available
        if (this.datasetOptions) {
            this.datasetOptions.forEach(dataset => {
                // Count how many countries have this dataset
                const availableCount = this.chart.data.datasets.filter(d =>
                    d.Datasets && d.Datasets[dataset.datasetCode] &&
                    d.Datasets[dataset.datasetCode].data
                ).length;
                const totalCount = this.chart.data.datasets.length;

                const option = document.createElement('option');
                option.value = dataset.datasetCode;

                // Build descriptive label with explicit spaces
                const baseName = (dataset.datasetName && dataset.datasetName.trim()) ? dataset.datasetName : dataset.datasetCode;
                if (availableCount < totalCount) {
                    // Show availability info for partial datasets
                    option.textContent = `Dataset:\u0020${baseName}\u0020(${availableCount}/${totalCount}\u0020countries)`;
                } else {
                    // Clean name for fully available datasets
                    option.textContent = `Dataset:\u0020${baseName}`;
                }

                this.seriesSelector.appendChild(option);
            });
        }
        // Set the current active series as selected
        this.seriesSelector.value = this.activeSeries
        // Update Y-axis inputs with current values
        this.updateYAxisInputs()
    }

    updateActiveSeriesDescription() {
        // Find the Y-Axis Range subheader to insert before it
        const yAxisSubheader = this.chartOptions.querySelector('.y-axis-range-subheader');
        if (!yAxisSubheader) {
            return;
        }

        // Remove existing description elements if they exist
        const existingSubheader = this.chartOptions.querySelector('.chart-view-subheader.active-series-description');
        const existingContent = this.chartOptions.querySelector('.chart-view-option.active-series-description-content');
        if (existingSubheader) {
            existingSubheader.remove();
        }
        if (existingContent) {
            existingContent.remove();
        }

        // Only add description when viewing a dataset (not the indicator score)
        if (this.activeSeries === this.itemCode) {
            // Viewing indicator score - no dataset description needed
            return;
        }

        if (!this.datasetOptions) {
            return;
        }

        // Find the dataset in options
        const dataset = this.datasetOptions.find(d => d.datasetCode === this.activeSeries);

        // Create the subheader (uses standard chart-view-subheader class)
        const subheader = document.createElement('div');
        subheader.className = 'chart-view-subheader\u0020active-series-description';
        subheader.textContent = 'Dataset\u0020Description';

        // Create the content div (uses standard chart-view-option class)
        const contentDiv = document.createElement('div');
        contentDiv.className = 'chart-view-option\u0020active-series-description-content';

        if (dataset && dataset.datasetDescription) {
            // Display description text
            contentDiv.textContent = dataset.datasetDescription;
        } else if (dataset) {
            // Dataset found but no description available
            const unit = dataset.unit ? `\u0020(${dataset.unit})` : '';
            contentDiv.innerHTML = `<em>No\u0020description\u0020available${unit}</em>`;
        } else {
            // Dataset not found in options
            contentDiv.innerHTML = '<em>Dataset\u0020not\u0020found</em>';
        }

        // Insert before the Y-Axis Range subheader (content first, then subheader before it)
        yAxisSubheader.parentNode.insertBefore(contentDiv, yAxisSubheader);
        yAxisSubheader.parentNode.insertBefore(subheader, contentDiv);
    }
}
