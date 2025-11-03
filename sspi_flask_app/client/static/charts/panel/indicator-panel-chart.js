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
        let yAxisTitle = 'Item Value'  // Default fallback
        
        if (this.activeSeries === this.itemCode) {
            yAxisTitle = 'Indicator Score'
        } else if (this.datasetOptions) {
            const dataset = this.datasetOptions.find(d => d.datasetCode === this.activeSeries)
            if (dataset) {
                const baseName = dataset.datasetName || dataset.datasetCode
                const unit = dataset.unit || dataset.Unit
                yAxisTitle = unit ? `${baseName} (${unit})` : baseName
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
                dataset.data = dataset.Datasets[this.activeSeries].data
            });
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
        this.chart.update()
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

    update(data) {
        console.log(data)
        
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
        this.chart.update()
        
        // Compute missing countries asynchronously after chart rendering
        console.log('=== IndicatorPanelChart about to call computeMissingCountriesAsync ===')
        console.log('countryGroupMap available?', !!this.countryGroupMap, Object.keys(this.countryGroupMap || {}).length, 'countries')
        this.computeMissingCountriesAsync()
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
                // animation: false,
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
                    <div class="chart-view-option active-series-description" style="display: none;">
                        <div class="active-series-description-content"></div>
                    </div>
                    <div class="chart-view-subheader">Y-Axis Range</div>
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
            }
        }
    }

    rigChartOptions() {
        // Call parent method first
        super.rigChartOptions()
        
        // Wire up our custom controls
        this.rigViewOptionsControls()
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
        
        // Set defaults for current active series
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
            // For datasets, use simple title (no breadcrumb)
            const dataset = this.datasetOptions.find(d => d.datasetCode === this.activeSeries)
            if (dataset) {
                const datasetName = dataset.datasetName || dataset.datasetCode
                this.title.innerText = `${dataset.datasetCode} - ${datasetName}`;
            } else {
                this.title.innerText = this.activeSeries;
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
        indicatorOption.textContent = this.itemCode + ' Indicator Score'
        this.seriesSelector.appendChild(indicatorOption)
        
        // Add dataset options if available
        if (this.datasetOptions) {
            this.datasetOptions.forEach(dataset => {
                const option = document.createElement('option')
                option.value = dataset.datasetCode
                option.textContent = dataset.datasetName || dataset.datasetCode
                this.seriesSelector.appendChild(option)
            })
        }
        
        // Set the current active series as selected
        this.seriesSelector.value = this.activeSeries
        
        // Update Y-axis inputs with current values
        this.updateYAxisInputs()
    }

    updateActiveSeriesDescription() {
        const activeSeriesDescription = this.chartOptions.querySelector('.active-series-description')
        if (!activeSeriesDescription) {
            console.warn('Active series description element not found')
            return
        }
        
        const contentDiv = activeSeriesDescription.querySelector('.active-series-description-content')
        if (!contentDiv) {
            console.warn('Active series description content element not found')
            return
        }
        
        console.log('Updating active series description for:', this.activeSeries)
        
        if (this.activeSeries === this.itemCode) {
            // Hide for indicator score - it already has its own description
            activeSeriesDescription.style.display = 'none'
        } else if (this.datasetOptions) {
            // Show dataset description for dataset series
            const dataset = this.datasetOptions.find(d => d.datasetCode === this.activeSeries)
            console.log('Found dataset:', dataset)
            if (dataset && dataset.description) {
                contentDiv.innerHTML = '<strong>Dataset:</strong> ' + dataset.description
                activeSeriesDescription.style.display = 'block'
            } else if (dataset) {
                contentDiv.innerHTML = '<strong>Dataset:</strong> ' + (dataset.datasetName || dataset.datasetCode) + ' (no description available)'
                activeSeriesDescription.style.display = 'block'
            } else {
                contentDiv.innerHTML = '<em>Dataset not found</em>'
                activeSeriesDescription.style.display = 'block'
            }
        } else {
            contentDiv.innerHTML = '<em>No dataset options available</em>'
            activeSeriesDescription.style.display = 'block'
        }
    }
}
