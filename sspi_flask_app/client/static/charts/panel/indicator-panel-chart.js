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
        this.currentYMin = min
        this.currentYMax = max
        this.chart.options.scales.y.min = min
        this.chart.options.scales.y.max = max
        if (update) {
            this.chart.update()
        }
        // Update input field values if they exist
        if (this.yMinInput) {
            this.yMinInput.value = min
        }
        if (this.yMaxInput) {
            this.yMaxInput.value = max
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
        this.title.innerText = data.title
        this.itemType = data.itemType
        this.groupOptions = data.groupOptions
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
    }

    buildChartOptions() {
        // Call parent method first
        super.buildChartOptions()
        
        // Find the View Options details element and add our custom controls
        const viewOptions = this.chartOptions.querySelector('.chart-view-options')
        if (viewOptions) {
            // Create series selector HTML
            const seriesControlsHTML = `
                <div class="chart-view-option series-selector-container">
                    <label class="title-bar-label" for="series-selector">Active Series:</label>
                    <select class="series-selector" id="series-selector">
                        <option value="` + this.itemCode + `" selected>` + this.itemCode + ` Indicator Score</option>
                    </select>
                </div>
                <div class="chart-view-option active-series-description" style="display: none;">
                    <div class="active-series-description-content"></div>
                </div>
                <div class="chart-view-option y-axis-controls">
                    <div class="y-axis-input-group">
                        <label class="title-bar-label" for="y-min-input">Y Min:</label>
                        <input type="number" class="y-min-input" id="y-min-input" step="any" value="0"/>
                    </div>
                    <div class="y-axis-input-group">
                        <label class="title-bar-label" for="y-max-input">Y Max:</label>
                        <input type="number" class="y-max-input" id="y-max-input" step="any" value="1"/>
                    </div>
                    <button class="restore-y-axis-button" style="display: none;">Restore Default Range</button>
                </div>
            `;
            // Insert at the beginning of View Options
            viewOptions.insertAdjacentHTML('afterbegin', seriesControlsHTML)
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
        
        // Wire up series selector
        if (this.seriesSelector) {
            this.seriesSelector.addEventListener('change', (event) => {
                this.setActiveSeries(event.target.value)
            })
        }
        
        // Wire up Y-axis input change listeners
        const handleYAxisChange = () => {
            const yMin = parseFloat(this.yMinInput.value)
            const yMax = parseFloat(this.yMaxInput.value)
            
            if (isNaN(yMin) || isNaN(yMax)) {
                return // Wait for valid input
            }
            
            if (yMin >= yMax) {
                return // Wait for valid range
            }
            
            this.setYAxisMinMax(yMin, yMax)
            this.updateRestoreButton()
        }
        
        // Listen for input changes (on input event for immediate feedback)
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
            // Use original title for indicator score
            this.title.innerText = this.originalTitle || 'Indicator Chart'
        } else if (this.datasetOptions) {
            // Find the dataset and use its name
            const dataset = this.datasetOptions.find(d => d.datasetCode === this.activeSeries)
            if (dataset) {
                const datasetName = dataset.datasetName || dataset.datasetCode
                this.title.innerText = `${dataset.datasetCode} - ${datasetName}`
            } else {
                this.title.innerText = this.activeSeries
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
