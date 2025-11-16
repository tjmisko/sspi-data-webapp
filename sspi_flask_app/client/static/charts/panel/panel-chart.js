class PanelChart {
    constructor(parentElement, { CountryList = [], endpointURL = '', colorProvider = SSPIColors, startYear = 2000, endYear = 2025, favorCachedTimePeriod = true, yBeginAtZero = true} ) {
        this.parentElement = parentElement// ParentElement is the element to attach the canvas to
        this.CountryList = CountryList// CountryList is an array of CountryCodes (empty array means all countries)
        this.endpointURL = endpointURL// endpointURL is the URL to fetch data from
        this.pins = new Set() // pins contains a list of pinned countries
        this.missingCountries = [] // Array of countries with no data, populated from API response
        this.colorProvider = colorProvider // colorProvider is an instance of ColorProvider
        this.extrapolateBackwardPlugin = extrapolateBackwardPlugin
        this.chartInteractionPlugin = chartInteractionPlugin
        this.favorCachedTimePeriod = favorCachedTimePeriod // Set to false to ensure that specified years override user-set custom time periods
        this.argDefaultStartYear = startYear
        this.argDefaultEndYear = endYear
        this.yBeginAtZero = yBeginAtZero
        this.hoverRadius = window.observableStorage.getItem('hoverRadius') || 15
        let cachedStartYear = window.observableStorage.getItem('startYear')
        if (cachedStartYear && favorCachedTimePeriod) {
            startYear = cachedStartYear
        }
        let cachedEndYear = window.observableStorage.getItem('endYear')
        if (cachedStartYear && favorCachedTimePeriod) {
            endYear = cachedEndYear
        }
        this.startYear = startYear
        this.endYear = endYear
        this.setTheme(window.observableStorage.getItem("theme"))
        this.pinnedOnly = window.observableStorage.getItem("pinnedOnly") || false
        this.countryGroup = window.observableStorage.getItem("countryGroup") || "SSPI67"
        this.randomN = window.observableStorage.getItem("randomN") || 10
        this.randomHistoryIndex = 0;
        this.initRoot()
        this.initChartJSCanvas()
        this.buildChartOptions()
        this.rigChartOptions()
        this.rigItemDropdown()
        this.rigCountryGroupSelector()
        this.updateChartOptions()
        this.updateYearRange({startYear: this.startYear, endYear: this.endYear});
        this.rigLegend()
        this.fetch(this.endpointURL).then(data => {
            this.update(data)
        })
        this.rigPinChangeListener()
        this.rigUnloadListener()
    }

    initRoot() {
        // Create the root element
        this.root = document.createElement('div')
        this.root.classList.add('panel-chart-root-container')
        this.parentElement.appendChild(this.root)
    }

    buildChartOptions() {
        this.chartOptions = document.createElement('div')
        this.chartOptions.classList.add('chart-options')
        this.chartOptions.innerHTML = `
<div class="hide-chart-button-container">
    <button class="icon-button hide-chart-options" aria-label="Hide Chart Options" title="Hide Chart Options">
        <svg class="hide-chart-options-svg" width="24" height="24">
            <use href="#icon-close" />
        </svg>
    </button>
</div>
<details class="item-information chart-options-details">
    <summary class="item-information-summary">Item Information</summary>
    <select class="item-dropdown"></select>
    <div class="dynamic-item-description-container">
        <div class="dynamic-item-description"></div>
    </div>
</details>
<details class="country-information chart-options-details">
    <summary class="item-information-summary">Country Information</summary>
    <div class="country-information-box" data-unpopulated=true>
        Click on a Country to Show Details and Links Here.
    </div>
</details>
<details class="select-countries-options chart-options-details">
    <summary class="select-countries-summary">Select Countries</summary>
    <div class="view-options-suboption-container">
        <div class="chart-view-subheader">Pinned Countries</div>
        <div class="legend-title-bar-buttons">
            <div class="pin-actions-box">
                <button class="hideunpinned-button">Hide Unpinned</button>
                <button class="clearpins-button">Clear Pins</button>
                <button class="add-country-button">Search Country</button>
            </div>
            <div class="country-search-results-window"></div>
        </div>
        <legend class="dynamic-line-legend">
            <div class="legend-items"></div>
        </legend>
        <div class="chart-view-subheader">Country Groups</div>
        <div class="chart-view-option">
            <select class="country-group-selector"></select>
        </div>
        <div class="chart-view-option country-group-buttons">
            <div class="country-group-button-group">
                <div class="random-draw-controls">
                    <button class="random-history-back-button"><svg class="history-button-svg" width="16" height="16"><use href="#icon-open-arrow-right"/></svg></button>
                    <button class="draw-button">Draw 10 Countries</button>
                    <button class="random-history-forward-button"><svg class="history-button-svg" width="16" height="16"><use href="#icon-open-arrow-left"/></svg></button>
                </div>
                <button class="show-in-group-button">Show All in Group</button>
            </div>
        </div>
        <div class="chart-view-subheader">Missing Countries</div>
        <div class="missing-countries-container">
            <div class="missing-countries-list"></div>
            <div class="missing-countries-summary"></div>
        </div>
    </div>
</details>
<details class="chart-options-details chart-view-options">
    <summary class="chart-view-options-summary">View Options</summary>
    <div class="view-options-suboption-container">
        <div class="chart-view-subheader">
            <div>Year Range</div>
            <button class="reset-year-range-button">Reset to Default</button>
        </div>
        <div class="chart-view-option">
            <div class="randomization-options">
                <label class="title-bar-label">Start Year</label>
                <input type="number" class="start-year" value="${this.startYear}" min="2000" max="2025"/>
            </div>
            <div class="randomization-options">
                <label class="title-bar-label">End Year</label>
                <input type="number" class="end-year" value="${this.endYear}" min="2000" max="2025"/>
            </div>
        </div>
        <div class="chart-view-subheader">Imputation Options</div>
        <div class="chart-view-option">
            <input type="checkbox" class="extrapolate-backward"/>
            <label class="title-bar-label">Backward Extrapolation</label>
        </div>
        <div class="chart-view-option">
            <input type="checkbox" class="interpolate-linear"/>
            <label class="title-bar-label">Linear Interpolation</label>
        </div>
        <div class="chart-view-subheader">Randomization</div>
        <div class="chart-view-option">
            <div class="randomization-options">
                <label class="title-bar-label" for="random-country-sample">Draw Size:</label>
                <input type="number" class="random-country-sample" id="random-country-sample" step="1" value="10"/>
            </div>
        </div>
        <div class="chart-view-subheader">Chart Interaction</div>
        <div class="chart-view-option">
            <div class="randomization-options">
                <label class="title-bar-label">Hover Radius:</label>
                <input type="number" class="hover-radius" step="1" value="15" min="1" max="25"/>
            </div>
        </div>
    </div>
</details>
<details class="download-data-details chart-options-details">
    <summary>Download Chart Data</summary>
    <form class="panel-download-form">
        <fieldset class="download-scope-fieldset">
            <legend>Select data scope:</legend>
            <label class="download-scope-option"><input type="radio" name="scope" value="pinned" required>Pinned countries</label>
            <label class="download-scope-option"><input type="radio" name="scope" value="visible">Visible countries</label>
            <label class="download-scope-option"><input type="radio" name="scope" value="group">Countries in group</label>
            <label class="download-scope-option"><input type="radio" name="scope" value="all">All available countries</label>
        </fieldset>
        <fieldset class="download-format-fieldset">
            <legend>Choose file format:</legend>
            <label class="download-format-option"><input type="radio" name="format" value="json" required>JSON</label>
            <label class="download-format-option"><input type="radio" name="format" value="csv">CSV</label>
        </fieldset>
        <button type="submit" class="download-submit-button">Download Data</button>
    </form>
</details>
`;
        this.showChartOptions = document.createElement('button')
        this.showChartOptions.classList.add("icon-button", "show-chart-options")
        this.showChartOptions.ariaLabel = "Show Chart Options"
        this.showChartOptions.title = "Show Chart Options"
        this.showChartOptions.innerHTML = `
<svg class="svg-button show-chart-options-svg" width="24" height="24">
    <use href="#icon-settings" />
</svg>
`;
        this.titleActions.appendChild(this.showChartOptions)
        this.overlay = document.createElement('div')
        this.overlay.classList.add('chart-options-overlay')
        this.overlay.addEventListener('click', () => {
            this.closeChartOptionsSidebar()
        })
        this.root.appendChild(this.overlay)
        this.chartOptionsWrapper = document.createElement('div')
        this.chartOptionsWrapper.classList.add('chart-options-wrapper')
        this.chartOptionsWrapper.appendChild(this.chartOptions)
        this.root.appendChild(this.chartOptionsWrapper)
    }

    rigChartOptions() {
        this.showChartOptions.addEventListener('click', () => {
            this.openChartOptionsSidebar()
        })
        this.hideChartOptions = this.chartOptions.querySelector('.hide-chart-options')
        this.hideChartOptions.addEventListener('click', () => {
            this.closeChartOptionsSidebar()
        })
        this.countryInformationBox = this.chartOptions.querySelector(".country-information-box");
        this.extrapolateBackwardCheckbox = this.chartOptions.querySelector('.extrapolate-backward')
        this.extrapolateBackwardCheckbox.checked = true
        this.extrapolateBackwardCheckbox.addEventListener('change', () => {
            this.toggleBackwardExtrapolation()
        })
        this.interpolateCheckbox = this.chartOptions.querySelector('.interpolate-linear')
        this.interpolateCheckbox.checked = true
        this.interpolateCheckbox.addEventListener('change', () => {
            this.toggleLinearInterpolation()
        })
        this.randomHistoryBackButton = this.root.querySelector('.random-history-back-button')
        this.randomHistoryBackButton.addEventListener('click', () => { this.randomHistoryBack() })
        this.randomHistoryBackButton.style.display = "none";
        this.randomHistoryForwardButton = this.root.querySelector('.random-history-forward-button')
        this.randomHistoryForwardButton.addEventListener('click', () => { this.randomHistoryForward() })
        this.randomHistoryForwardButton.style.display = "none";
        this.drawButton = this.root.querySelector('.draw-button')
        this.drawButton.innerText = "Draw " + this.randomN.toString() + " Countries ";
        this.drawButton.addEventListener('click', () => {
            this.showRandomN(this.randomN)
        })
        this.showInGroupButton = this.chartOptions.querySelector('.show-in-group-button')
        this.showInGroupButton.addEventListener('click', () => {
            const activeGroup = this.groupOptions[this.countryGroupSelector.selectedIndex]
            this.showGroup(activeGroup)
        })
        this.resetYearInput = this.chartOptions.querySelector('.reset-year-range-button')
        this.resetYearInput.addEventListener('click', (event) => {
            this.resetYearRange()
        })
        this.startYearInput = this.chartOptions.querySelector('.start-year')
        this.startYearInput.addEventListener('change', (event) => {
            if (this.startYearInput.value < this.startYearInput.min || this.startYearInput.value > this.startYearInput.max) {
                this.startYearInput.classList.add("invalid-year-input")
            } else {
                this.startYearInput.classList.remove("invalid-year-input")
            }
            this.updateYearRange({ startYear: this.startYearInput.value })
        })
        this.endYearInput = this.chartOptions.querySelector('.end-year')
        this.endYearInput.addEventListener('change', (event) => {
            if (this.endYearInput.value < this.endYearInput.min || this.endYearInput.value > this.endYearInput.max) {
                this.endYearInput.classList.add("invalid-year-input")
            } else {
                this.endYearInput.classList.remove("invalid-year-input")
            }
            this.updateYearRange({ endYear: this.endYearInput.value })
        })
        this.randomNumberField = this.chartOptions.querySelector('.random-country-sample')
        this.randomNumberField.value = this.randomN
        this.randomNumberField.addEventListener('input', (event) => {
            this.updateRandomN(this.randomNumberField.value)
        })
        this.hoverRadiusInput = this.chartOptions.querySelector('.hover-radius')
        this.hoverRadiusInput.value = this.hoverRadius
        this.hoverRadiusInput.addEventListener('change', (event) => {
            let radius = this.hoverRadiusInput.value
            if (radius > 50 || radius < 5) {
                this.hoverRadiusInput.classList.add("invalid-year-input")
                radius = 15;
            } else {
                this.endYearInput.classList.remove("invalid-year-input")
            }
            this.updateHoverRadius(radius)
            window.observableStorage.setItem('hoverRadius', radius)
        })


        const detailsElements = this.chartOptions.querySelectorAll('.chart-options-details')
        let openDetails = window.observableStorage.getItem("openPanelChartDetails")
        detailsElements.forEach((details) => {
            if (openDetails && openDetails.includes(details.classList[0])) {
                details.open = true
            } else {
                details.open = false
            }
        })
        const sidebarStatus = window.observableStorage.getItem("chartOptionsStatus")
        if (sidebarStatus === "active") {
            this.openChartOptionsSidebar()
        } else {
            this.closeChartOptionsSidebar()
        }
        
        this.rigDownloadForm()
    }

    rigItemDropdown() {
        this.itemInformation = this.chartOptions.querySelector('.item-information')
        this.itemDropdown = this.itemInformation.querySelector('.item-dropdown')
    }

    initChartJSCanvas() {
        this.chartContainer = document.createElement('div')
        this.chartContainer.classList.add('panel-chart-container')
        this.chartContainer.innerHTML = `
<div class="panel-chart-title-container">
    <h2 class="panel-chart-title"></h2>
    <div class="panel-chart-title-actions"></div>
</div>
<div class="panel-canvas-wrapper">
    <canvas class="panel-chart-canvas"></canvas>
</div>
`;
        this.root.appendChild(this.chartContainer)
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
                        radius: this.hoverRadius,
                        clickRadius: 4,
                        tooltipBg: this.headerBackgroundColor,
                        tooltipFg: this.titleColor,
                        circleColor: this.tickColor,
                        guideColor: this.tickColor,
                        labelField: 'CCode',
                        showDefaultLabels: true,
                        defaultLabelSpacing: 0,
                        onDatasetClick: (datasets, event, chart) => {
                            datasets.forEach((dataset) => {
                                this.activeCountry = dataset;
                                window.observableStorage.setItem('activeCountry', dataset)
                                this.updateCountryInformation();
                            });
                        }
                    },
                },
                layout: {
                    padding: {
                        right: 40,
                    }
                }
            }
        })
    }

    updateChartOptions() {
        this.chart.options.scales = {
            x: {
                ticks: {
                    color: this.tickColor,
                },
                min: this.startYear,
                max: this.endYear,
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
                beginAtZero: this.yBeginAtZero,
                title: {
                    display: true,
                    text: 'Item Value',
                    color: this.axisTitleColor,
                    font: {
                        size: 16
                    }
                }
            }
        }
        this.chart.options.plugins.chartInteractionPlugin.tooltipBg = this.headerBackgroundColor;
        this.chart.options.plugins.chartInteractionPlugin.tooltipFg = this.titleColor;
        this.chart.options.plugins.chartInteractionPlugin.tooltipFgAccent = this.greenAccent || "green";
        this.chart.options.plugins.chartInteractionPlugin.circleColor = this.tickColor;
        this.chart.options.plugins.chartInteractionPlugin.guideColor = this.tickColor;
    }

    rigCountryGroupSelector() {
        this.countryGroupSelector = this.chartOptions.querySelector('.country-group-selector')
        this.countryGroupSelector.addEventListener('change', (event) => {
            this.showGroup(event.target.value)
        })
        this.hideUnpinnedButton = this.chartOptions.querySelector('.hideunpinned-button')
        this.hideUnpinnedButton.addEventListener('click', () => {
            this.hideUnpinned()
        })
    }

    updateCountryGroups() {
        const groupOptionDefault = window.observableStorage.getItem("countryGroup") || "SSPI67"
        this.countryGroupSelector.innerHTML = ''
        this.groupOptions.forEach((option, index) => {
            const opt = document.createElement('option');
            opt.value = option;
            opt.textContent = option;
            if (option === groupOptionDefault) {
                opt.selected = true;
            }
            this.countryGroupSelector.appendChild(opt);
        });
    }

    rigLegend() {
        this.countrySearchResultsWindow =  this.chartOptions.querySelector('.country-search-results-window')
        this.addCountryButton = this.chartOptions.querySelector('.add-country-button')
        this.addCountryButton.addEventListener('click', () => {
            new CountrySelector(this.addCountryButton, this.countrySearchResultsWindow, this.chart.data.datasets, this)
        })
        this.clearPinsButton = this.chartOptions.querySelector('.clearpins-button')
        this.clearPinsButton.addEventListener('click', () => {
            this.clearPins()
        })
        this.legend = this.chartOptions.querySelector('.dynamic-line-legend')
        this.legendItems = this.legend.querySelector('.legend-items')
    }

    updateCountryInformation() {
        if (!this.activeCountry) return;
        this.countryInformationBox.dataset.unpopulated = false
        const isPinned = this.activeCountry.pinned || false;
        const pinButtonText = isPinned ? "Unpin Country" : "Pin Country";
        const pinButtonClass = isPinned ? "unpin-country-button" : "pin-country-button";
        let dataset = this.chart.data.datasets.find((ds) => {
            return ds.CCode === this.activeCountry.CCode
        })
        const startIndex = this.startYear - 2000;
        let endIndex = this.endYear - 2000;
        const yearScreen = dataset.score.slice(startIndex, endIndex)
        const dataEndYear = this.startYear + yearScreen.length - 1;
        const avgScore = ( yearScreen.reduce((a, b) => a + b) / yearScreen.length )
        const minScore = Math.min(...yearScreen) 
        const maxScore = Math.max(...yearScreen)
        const minScoreIndex = yearScreen.findIndex((el) => el === minScore) 
        const maxScoreIndex = yearScreen.findIndex((el) => el === maxScore) 
        const minScoreYear = minScoreIndex === -1 ? "Error" : minScoreIndex + this.startYear
        const maxScoreYear = maxScoreIndex === -1 ? "Error" : maxScoreIndex + this.startYear
        const chgScore = (yearScreen[yearScreen.length - 1] - yearScreen[0]) / yearScreen[0] * 100
        this.countryInformationBox.innerHTML = `
<div id="#active-country-information" class="country-details-info">
<h3 class="country-details-header"><span class="country-name">${this.activeCountry.CFlag}\u0020${this.activeCountry.CName}\u0020(${this.activeCountry.CCode})</span></h3>
<div class="country-details-score-container">
    <div class="summary-stat-line">
        <span class="summary-stat-label">Average:</span> 
        <span class="summary-stat-score">${avgScore.toFixed(3)}</span>
        <span class="summary-stat-year">${this.startYear}-${dataEndYear}</span>
    </div>
    <div class="summary-stat-line">
        <span class="summary-stat-label">Change:</span>
        <span class="summary-stat-score">${chgScore.toFixed(2)}%</span>
        <span class="summary-stat-year">${this.startYear}-${dataEndYear}</span>
    </div>
    <div class="summary-stat-line">
        <span class="summary-stat-label">Minimum:</span>
        <span class="summary-stat-score">${minScore.toFixed(3)}</span>
        <span class="summary-stat-year">${minScoreYear}</span>
    </div>
    <div class="summary-stat-line">
        <span class="summary-stat-label">Maximum:</span>
        <span class="summary-stat-score">${maxScore.toFixed(3)}</span>
        <span class="summary-stat-year">${maxScoreYear}</span>
    </div>
</div>
<div class="country-details-actions">
    <button class="${pinButtonClass}" data-country-code="${this.activeCountry.CCode}">${pinButtonText}</button>
    <a class="view-all-data-link" href="/data/country/${this.activeCountry.CCode}">View All Data</a>
</div>
</div>`;
        // Add event listener for Pin/Unpin Country button
        const pinButton = this.countryInformationBox.querySelector('.pin-country-button, .unpin-country-button');
        if (pinButton) {
            pinButton.addEventListener('click', (e) => {
                const countryCode = e.target.dataset.countryCode;
                // Find the feature to toggle
                const dataset = this.chart.data.datasets.find(d => d.CCode === countryCode);
                if (dataset) {
                    this.togglePin(dataset);
                    this.activeCountry = dataset;
                    window.observableStorage.setItem('activeCountry', dataset)
                    this.updateCountryInformation();
                }
            });
        }
    }

    updateLegend() {
        function generateListener(countryCode, PanelChartObject) {
            function listener() {
                let dataset = PanelChartObject.chart.data.datasets.find((d) => d.CCode === countryCode);
                if (dataset) {
                    PanelChartObject.activeCountry = dataset;
                    window.observableStorage.setItem('activeCountry', dataset)
                    PanelChartObject.countryInformationBox.dataset.unpopulated = false;
                    PanelChartObject.updateCountryInformation();
                } else {
                    console.log("Country " + countryCode + " Not Found in Datasets!")
                }
            }
            return listener
        }
        this.legendItems.innerHTML = ''
        if (this.pins.size > 0) {
            this.pins.forEach((PinnedCountry) => {
                const pinSpan = document.createElement('span')
                pinSpan.innerText = PinnedCountry.CName + " (" + PinnedCountry.CCode + ")"
                const removeButton = document.createElement('button')
                removeButton.classList.add('icon-button', 'remove-button-legend-item')
                removeButton.id = `${PinnedCountry.CCode}-remove-button-legend`;
                removeButton.ariaLabel = `Remove ${PinnedCountry.CName} from pinned countries`;
                removeButton.title = `Unpin ${PinnedCountry.CName}`;
                removeButton.innerHTML = `
<svg class="remove-button-legend-item-svg" width="16" height="16">
    <use href="#icon-close" />
</svg>
`;
                const newPin = document.createElement('div')
                newPin.classList.add('legend-item')
                newPin.style.borderColor = PinnedCountry.borderColor
                newPin.style.backgroundColor = PinnedCountry.borderColor + "44"
                newPin.dataset.ccode = PinnedCountry.CCode
                newPin.appendChild(pinSpan)
                newPin.appendChild(removeButton)
                newPin.addEventListener('click', generateListener(PinnedCountry.CCode, this))
                newPin.addEventListener('mouseenter', (event) => this.handleChartCountryHighlight(event.target.dataset.ccode))
                this.legendItems.appendChild(newPin)
                this.legendItems.addEventListener('mouseleave', (event) => this.handleChartCountryHighlight(null))
            })
        }
        let removeButtons = this.legendItems.querySelectorAll('.remove-button-legend-item')
        removeButtons.forEach((button) => {
            let countryCode = button.id.split('-')[0]
            button.addEventListener('click', () => {
                this.unpinCountryByCode(countryCode, true)
                this.handleChartCountryHighlight(countryCode)
            })
        })
    }

    updateMissingCountries() {
        const missingCountriesList = this.chartOptions.querySelector('.missing-countries-list')
        const missingCountriesSummary = this.chartOptions.querySelector('.missing-countries-summary')
        
        if (!missingCountriesList || !missingCountriesSummary) {
            return
        }
        
        // Filter missing countries by current country group and display
        this.refreshMissingCountriesDisplay()
    }

    refreshMissingCountriesDisplay() {
        const missingCountriesList = this.chartOptions.querySelector('.missing-countries-list')
        const missingCountriesSummary = this.chartOptions.querySelector('.missing-countries-summary')
        
        if (!missingCountriesList || !missingCountriesSummary) {
            return
        }
        
        // Filter missing countries by current country group
        const filteredMissing = this.missingCountries.filter(country => {
            return country.CGroup && country.CGroup.includes(this.countryGroup)
        })
        
        // Count visible countries in the current group
        const visibleCountriesInGroup = this.chart.data.datasets.filter(dataset => {
            return dataset.CGroup && dataset.CGroup.includes(this.countryGroup)
        }).length
        
        // Total countries that should be visible = missing in group + visible in group
        const totalCountriesInGroup = filteredMissing.length + visibleCountriesInGroup
        
        missingCountriesList.innerHTML = ''
        
        if (filteredMissing.length === 0) {
            const message = this.missingCountries.length === 0 
                ? 'All countries have data' 
                : 'All countries in ' + this.countryGroup + ' have data'
            missingCountriesList.innerHTML = '<div class="missing-countries-none">' + message + '</div>'
            missingCountriesSummary.innerHTML = ''
        } else {
            // Display missing countries as a compact list
            const countryElements = filteredMissing.map(country => {
                return '<span class="missing-country-item">' + country.CCode + '</span>'
            }).join(', ')
            
            missingCountriesList.innerHTML = countryElements
            missingCountriesSummary.innerHTML = filteredMissing.length + ' of ' + totalCountriesInGroup + ' countries in ' + this.countryGroup + ' missing data'
        }
    }

    handleChartCountryHighlight(countryCode) {
        if (countryCode === null) {
            this.chartInteractionPlugin.setExternalHover(this.chart, null)
        }
        const ds = this.chart.data.datasets.findIndex((ds) => ds.CCode === countryCode)
        if (ds == -1) {
            this.chartInteractionPlugin.setExternalHover(this.chart, null)
        } else if (ds) {
            this.chartInteractionPlugin.setExternalHover(this.chart, ds)
        }
        this.updateChartPreservingYAxis();
    }

    updateHoverRadius(radius) {
        this.chart.options.plugins.chartInteractionPlugin.radius = radius;
        this.updateChartPreservingYAxis();
    }

    updateYearRange({ startYear = this.startYear, endYear = this.endYear } = {}) {
        this.startYear = parseInt(startYear)
        this.endYear = parseInt(endYear)
        if (startYear != this.startYear) {
            this.startYear = parseInt(startYear)
        }
        if (endYear != this.endYear) {
            this.endYear = parseInt(endYear)
        }
        if (this.startYear < 2000) {
            console.log("Invalid Start Year: Start Year must be 2000 or later")
            this.startYear = 2000
            return
        }
        if (this.endYear > 2025) {
            console.log("Invalid End Year: End Year must be 2025 or earlier")
            this.endYear = 2025
            return
        }
        if (this.startYear > this.endYear ) {
            this.endYear = this.startYear + 1
            console.log("Invalid End Year: End Year must not be less than or equal to start Year")
            return 
        }
        if (this.startYearInput.value != this.startYear) {
            this.startYearInput.value = this.startYear
        }
        if (this.endYearInput.value != this.endYear) {
            this.endYearInput.value = this.endYear
        }
        this.chart.options.scales.x.min = this.startYear;
        this.chart.options.scales.x.max = this.endYear;
        this.updateCountryInformation();
        this.updateChartPreservingYAxis();
        window.observableStorage.setItem("startYear", this.startYear)
        window.observableStorage.setItem("endYear", this.endYear)
    }

    resetYearRange() {
        this.updateYearRange({ startYear: this.argDefaultStartYear, endYear: this.argDefaultEndYear })
        this.startYearInput.classList.remove("invalid-year-input")
        this.endYearInput.classList.remove("invalid-year-input")
    }

    updateDescription(description) {
        const dbox = this.chartOptions.querySelector('.dynamic-item-description')
        dbox.innerHTML = '<p><b>Description: </b> ' + description + '</p>'
        var itemCode;
        if (this.activeItemCode) {
            itemCode = this.activeItemCode;
        } else if (this.itemCode) {
            itemCode = this.itemCode;
        }
        if (itemCode) {
            this.chartOptions.querySelector('.item-data-link-button')?.remove()
            this.chartOptions.querySelector('.item-metadata-link-button')?.remove()
            const hrefCandidate = "/data/" + this.itemType.toLowerCase() + "/" + itemCode
            if (itemCode !== "SSPI" && !window.location.href.includes(hrefCandidate)) {
                const dataLink = document.createElement('a');
                dataLink.innerText = itemCode + " Data Page";
                dataLink.classList.add("view-all-data-link", "item-data-link-button")
                dataLink.href = hrefCandidate
                dbox.parentElement.appendChild(dataLink)
            }
            const metadataLink = document.createElement('a');
            metadataLink.classList.add("view-all-data-link", "item-metadata-link-button")
            if (itemCode === "SSPI") {
                metadataLink.innerText = itemCode + " Indicator Table";
                metadataLink.href = "/indicators"
            } else {
                metadataLink.innerText = itemCode + " in Indicator Table";
                metadataLink.href = "/indicators?viewItem=" + itemCode + "#" + itemCode
            }
            dbox.parentElement.appendChild(metadataLink)
        }
    }

    updateItemDropdown(options) {
        const default_item = this.window.location.href.split('/')[-1]
        for (const option of options) {
            const opt = document.createElement('option')
            opt.value = option.Code
            opt.textContent = `${option.Name} (${option.Code})`;
            this.itemDropdown.appendChild(opt)
        }
    }

    updateChartColors() {
        for (let i = 0; i < this.chart.data.datasets.length; i++) {
            const dataset = this.chart.data.datasets[i]
            const color = this.colorProvider.get(dataset.CCode)
            dataset.borderColor = color
            dataset.backgroundColor = color + "44"
        }
    }

    setTheme(theme) {
        const root = document.documentElement
        const bg = getComputedStyle(root).getPropertyValue('--header-color').trim()
        this.headerBackgroundColor = bg
        const greenAccent = getComputedStyle(root)?.getPropertyValue('--green-accent')?.trim() || "green";
        this.greenAccent = greenAccent
        if (theme !== "light") {
            this.theme = "dark"
            this.tickColor = "#bbb"
            this.guideColor = "#333333"
            this.axisTitleColor = "#bbb"
            this.titleColor = "#ccc"
        } else {
            this.theme = "light"
            this.tickColor = "#444"
            this.guideColor = "#bbbbbb"
            this.axisTitleColor = "#444"
            this.titleColor = "#444"
            this.headerBackgroundColor = "#f0f0f0"
        }
        if (this.chart) {
            this.updateChartOptions()
            this.updateChartPreservingYAxis()
        }
    }

    async fetch(url) {
        const response = await fetch(url)
        try {
            return response.json()
        } catch (error) {
            console.error('Error:', error)
        }
    }

    update(data) {
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
        this.title.innerText = data.title
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
        // Compute missing countries asynchronously after chart rendering
        this.updateChartPreservingYAxis();
        this.computeMissingCountriesAsync()
        this.activeCountry = window.observableStorage.getItem("activeCountry") || null;
        if (this.activeCountry) {
            this.updateCountryInformation();
        }
    }

    computeMissingCountriesAsync() {
        // Use setTimeout to defer execution until after chart rendering is complete
        setTimeout(() => {
            this.computeMissingCountries()
        }, 0)
    }

    computeMissingCountries() {
        if (!this.countryGroupMap || Object.keys(this.countryGroupMap).length === 0) {
            console.log('No country group map available for missing countries computation')
            return
        }
        const missingCountries = []
        const seenCountries = new Set()
        // First pass: process countries that appear in datasets
        this.chart.data.datasets.forEach(countryData => {
            const countryCode = countryData.CCode
            seenCountries.add(countryCode)
            const scores = countryData.data || []
            const scoresEmpty = !scores || scores.length === 0 || scores.every(s => s === null || s === undefined || s === '')
            if (scoresEmpty) {
                missingCountries.push({
                    CCode: countryCode,
                    CName: countryData.CName || countryCode,
                    CGroup: countryData.CGroup || this.countryGroupMap[countryCode] || []
                })
            }
        })
        let notSeenCount = 0
        Object.entries(this.countryGroupMap).forEach(([countryCode, countryGroups]) => {
            if (!seenCountries.has(countryCode)) {
                notSeenCount++
                missingCountries.push({
                    CCode: countryCode,
                    CName: countryCode, // We only have the country code from the map
                    CGroup: countryGroups
                })
            }
        })
        // Update the missing countries and refresh display
        this.missingCountries = missingCountries
        this.updateMissingCountries()
    }

    getPins() {
        const storedPins = window.observableStorage.getItem('pinnedCountries')
        if (storedPins) {
            this.pins = new Set(storedPins)
        }
        if (this.pins.size === 0) {
            return
        }
        this.chart.data.datasets.forEach(dataset => {
            for (const element of this.pins) {
                if (dataset.CCode === element.CCode) {
                    dataset.pinned = true
                    dataset.hidden = false
                }
            }
        })
        this.updateLegend()
        this.updateChartPreservingYAxis();
    }

    pushPinUpdate() {
        window.observableStorage.setItem("pinnedCountries", Array.from(this.pins))
    }

    showAll() {
        this.pinnedOnly = false
        window.observableStorage.setItem("pinnedOnly", false)
        console.log('Showing all countries')
        this.chart.data.datasets.forEach((dataset) => {
            dataset.hidden = false
        })
        this.updateChartPreservingYAxis()
    }

    showGroup(groupName) {
        this.pinnedOnly = false
        window.observableStorage.setItem("pinnedOnly", false)
        this.countryGroup = groupName
        window.observableStorage.setItem("countryGroup", groupName)
        console.log('Showing group:', groupName)
        this.chart.data.datasets.forEach((dataset) => {
            if (dataset.CGroup.includes(groupName) | dataset.pinned) {
                dataset.hidden = false
            } else {
                dataset.hidden = true
            }
        })
        this.updateChartPreservingYAxis()
        // Update missing countries display for the new group
        this.refreshMissingCountriesDisplay()
    }

    hideUnpinned() {
        this.pinnedOnly = true
        window.observableStorage.setItem("pinnedOnly", true)
        console.log('Hiding unpinned countries')
        this.chart.data.datasets.forEach((dataset) => {
            if (!dataset.pinned) {
                dataset.hidden = true
            }
        })
        this.updateChartPreservingYAxis()
    }

    updateRandomN(N) {
        N = parseInt(N)
        if (isNaN(N) || N <= 0) {
            this.updateRandomN(10)
        } else {
            this.randomN = N;
            window.observableStorage.setItem("randomN", N);
            this.drawButton.innerText = "Draw " + N.toString() + " Countries";
        }
    }

    showRandomN(N = 10) {
        // Adjust this to only select from those in the current country group
        this.pinnedOnly = false
        window.observableStorage.setItem("pinnedOnly", false)
        const activeGroup = this.groupOptions[this.countryGroupSelector.selectedIndex]
        let availableDatasetIndices = []
        this.chart.data.datasets.filter((dataset, index) => {
            if (dataset.CGroup.includes(activeGroup)) {
                availableDatasetIndices.push(index)
            }
        })
        console.log('Showing', N, 'random countries from group', activeGroup)
        this.chart.data.datasets.forEach((dataset) => {
            if (!dataset.pinned) {
                dataset.hidden = true
            }
            if (dataset.drawHistoryArray === undefined) {
                dataset.drawHistoryArray = new Array();
            }
            dataset.drawHistoryArray.push(0)
        })
        this.randomHistoryIndex = this.chart.data.datasets[0].drawHistoryArray.length - 1;
        let shownIndexArray = availableDatasetIndices.sort(() => Math.random() - 0.5).slice(0, N)
        shownIndexArray.forEach((index) => {
            this.chart.data.datasets[index].hidden = false;
            this.chart.data.datasets[index].drawHistoryArray[this.randomHistoryIndex] = 1;
        })
        this.updateChartPreservingYAxis()
        if (this.randomHistoryIndex > 0) {
            this.randomHistoryBackButton.style.display = "block";
            this.randomHistoryForwardButton.style.display = "none";
        } else {
            this.randomHistoryBackButton.style.display = "none";
        }
    }
    

    randomHistoryBack() {
        if (this.randomHistoryIndex > 0) {
            this.randomHistoryIndex--
        }
        this.chart.data.datasets.forEach((dataset) => {
            if (!dataset.pinned) {
                dataset.hidden = true
            }
            if (dataset.drawHistoryArray[this.randomHistoryIndex] == 1) {
                dataset.hidden = false
            }
        })
        this.updateChartPreservingYAxis()
        if (this.randomHistoryIndex == 0) {
            this.randomHistoryBackButton.style.display = "none";
        }
        this.randomHistoryForwardButton.style.display = "block";
    }

    randomHistoryForward() {
        const lastHistoryIndex = this.chart.data.datasets[0].drawHistoryArray.length - 1;
        if (this.randomHistoryIndex < lastHistoryIndex) {
            this.randomHistoryIndex++
        }
        this.chart.data.datasets.forEach((dataset) => {
            if (!dataset.pinned) {
                dataset.hidden = true
            }
            if (dataset.drawHistoryArray[this.randomHistoryIndex] == 1) {
                dataset.hidden = false
            }
        })
        this.updateChartPreservingYAxis()
        if (this.randomHistoryIndex == lastHistoryIndex) {
            this.randomHistoryForwardButton.style.display = "none";
        }
        this.randomHistoryBackButton.style.display = "block";

    }

    pinCountry(dataset) {
        if (dataset.pinned) {
            return
        }
        dataset.pinned = true
        dataset.hidden = false
        this.pins.add({ CName: dataset.CName, CCode: dataset.CCode, borderColor: dataset.borderColor })
        this.pushPinUpdate()
        this.updateLegend()
    }

    pinCountryByCode(countryCode) {
        this.chart.data.datasets.forEach(dataset => {
            if (dataset.CCode === countryCode) {
                if (!dataset.pinned) {
                    this.pins.add({ CName: dataset.CName, CCode: dataset.CCode, borderColor: dataset.borderColor })
                }
                dataset.pinned = true
                dataset.hidden = false
            }
        })
        this.pushPinUpdate()
        this.updateLegend()
    }

    unpinCountry(dataset, hide = false) {
        dataset.pinned = false
        if (hide && this.pinnedOnly) {
            dataset.hidden = true
        }
        for (const element of this.pins) {
            if (element.CCode === dataset.CCode) {
                this.pins.delete(element)
            }
        }
        this.updateChartPreservingYAxis()
        this.pushPinUpdate()
        this.updateLegend()
    }

    unpinCountryByCode(CountryCode, hide = false) {
        this.chart.data.datasets.forEach(dataset => {
            if (dataset.CCode === CountryCode) {
                this.unpinCountry(dataset, hide)
            }
        })
    }

    togglePin(dataset) {
        if (dataset.pinned) {
            this.unpinCountry(dataset, false)
        } else {
            this.pinCountry(dataset, false)
        }
    }

    clearPins() {
        this.pins.forEach((PinnedCountry) => {
            this.unpinCountryByCode(PinnedCountry.CCode, true)
        })
        this.pins = new Set()
        this.updateLegend()
        this.pushPinUpdate()
    }

    closeChartOptionsSidebar() {
        this.chartOptions.classList.remove('active')
        this.chartOptions.classList.add('inactive')
        this.chartOptionsWrapper.classList.remove('active')
        this.chartOptionsWrapper.classList.add('inactive')
        this.overlay.classList.remove('active')
        this.overlay.classList.add('inactive')
        this.showChartOptions.style.display = 'block'
    }

    openChartOptionsSidebar() {
        this.chartOptions.classList.add('active')
        this.chartOptions.classList.remove('inactive')
        this.chartOptionsWrapper.classList.add('active')
        this.chartOptionsWrapper.classList.remove('inactive')
        this.overlay.classList.remove('inactive')
        this.overlay.classList.add('active')
        this.showChartOptions.style.display = 'none'
    }

    toggleChartOptionsSidebar() {
        if (this.chartOptions.classList.contains('active')) {
            this.closeChartOptionsSidebar()
        } else {
            this.openChartOptionsSidebar()
        }
    }

    dumpChartDataJSON(scope = 'visible') {
        const observations = this.chart.data.datasets.map(dataset => {
            const shouldInclude = this.shouldIncludeDataset(dataset, scope)
            if (!shouldInclude) {
                return []
            }
            
            // Handle different possible data structures
            const scores = dataset.scores || dataset.score || []
            const values = dataset.values || dataset.value || []
            const years = dataset.years || dataset.year || this.chart.data.labels || []
            
            if (!dataset.data || !Array.isArray(dataset.data)) {
                console.warn(`Dataset ${dataset.CCode} has no data array`)
                return []
            }
            
            return dataset.data.map((_, i) => {
                const year = years[i]
                // Filter by year range if year is available
                if (year !== null && year !== undefined) {
                    if (year < this.startYear || year > this.endYear) {
                        return null // Skip this observation
                    }
                }
                return {
                    "ItemCode": dataset.ICode || '',
                    "CountryCode": dataset.CCode || '',
                    "CountryName": dataset.CName || '',
                    "Score": scores[i] ?? null,
                    "Value": values[i] ?? null,
                    "Year": year ?? null
                }
            }).filter(obs => obs !== null); // Remove filtered observations
        }).flat();
        console.log('Total observations to download:', observations.length)
        if (observations.length === 0) {
            alert('No data available for the selected scope. Please try a different scope or ensure data is loaded.')
            return
        }
        const jsonString = JSON.stringify(observations, null, 2);
        const blob = new Blob([jsonString], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        const today = new Date().toISOString().split('T')[0];
        const title = this.title.innerText || 'item-panel-data';
        const itemCode = this.activeItemCode || this.itemCode;
        a.download = today + ' - ' + title + (itemCode ? ' - ' + itemCode : '') + '.json';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        console.log('JSON download initiated')
    }

    dumpChartDataCSV(scope = 'visible') {
        const observations = this.chart.data.datasets.map(dataset => {
            if (!this.shouldIncludeDataset(dataset, scope)) {
                return []
            }
            
            // Handle different possible data structures
            const scores = dataset.scores || dataset.score || []
            const values = dataset.values || dataset.value || []
            const years = dataset.years || dataset.year || this.chart.data.labels || []
            
            if (!dataset.data || !Array.isArray(dataset.data)) {
                console.warn(`Dataset ${dataset.CCode} has no data array`)
                return []
            }
            
            return dataset.data.map((_, i) => {
                const year = years[i]
                // Filter by year range if year is available
                if (year !== null && year !== undefined) {
                    if (year < this.startYear || year > this.endYear) {
                        return null // Skip this observation
                    }
                }
                return {
                    "ItemCode": dataset.ICode || '',
                    "CountryCode": dataset.CCode || '',
                    "CountryName": dataset.CName || '',
                    "Score": scores[i]?.toString() || '',
                    "Value": values[i]?.toString() || '',
                    "Year": year?.toString() || ''
                }
            }).filter(obs => obs !== null); // Remove filtered observations
        }).flat();
        if (observations.length === 0) {
            alert('No data available for the selected scope. Please try a different scope or ensure data is loaded.')
            return
        }
        
        const csvString = Papa.unparse(observations);
        const blob = new Blob([csvString], { type: 'text/csv' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        const today = new Date().toISOString().split('T')[0];
        const title = this.title.innerText || 'item-panel-data';
        const itemCode = this.activeItemCode || this.itemCode;
        a.download = today + ' - ' + title + (itemCode ? ' - ' + itemCode : '') + '.csv';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }

    rigPinChangeListener() {
        window.observableStorage.onChange("pinnedCountries", () => {
            this.getPins()
            console.log("Pin change detected!")
        })
    }

    rigUnloadListener() {
        window.addEventListener('beforeunload', () => {
            window.observableStorage.setItem(
                "openPanelChartDetails",
                Array.from(this.chartOptions.querySelectorAll('.chart-options-details'))
                    .filter(details => details.open)
                    .map(details => details.classList[0])
            )
            window.observableStorage.setItem(
                "chartOptionsStatus",
                this.chartOptions.classList.contains('active') ? "active" : "inactive"
            )
        })
    }

    toggleBackwardExtrapolation() {
        this.extrapolateBackwardPlugin.toggle()
        this.updateChartPreservingYAxis();
    }

    toggleLinearInterpolation() {
        this.chart.options.datasets.line.spanGaps = !this.chart.options.datasets.line.spanGaps
        this.updateChartPreservingYAxis();
    }

    warnHidden() {
        if(this.pinnedOnly && this.pins.size === 0) {
            alert("All countries are hidden!")
            return true
        }
    }

    rigDownloadForm() {
        this.downloadForm = this.chartOptions.querySelector('.panel-download-form')
        if (this.downloadForm) {
            this.downloadForm.addEventListener('submit', (e) => {
                e.preventDefault()
                e.stopPropagation()
                this.handleDownloadRequest()
                return false
            })
        }
    }

    handleDownloadRequest() {
        const formData = new FormData(this.downloadForm)
        const scope = formData.get('scope')
        const format = formData.get('format')
        const today = new Date().toISOString().split('T')[0]; // YYYY-MM-DD format
        if (!scope || !format) {
            console.error('Missing scope or format in form data')
            alert('Please select both scope and format options')
            return
        }

        if (format === 'json') {
            console.log('Calling dumpChartDataJSON with scope:', scope)
            this.dumpChartDataJSON(scope)
        } else if (format === 'csv') {
            console.log('Calling dumpChartDataCSV with scope:', scope)
            this.dumpChartDataCSV(scope)
        } else {
            console.error('Unknown format:', format)
            alert('Unknown format selected')
        }
    }

    shouldIncludeDataset(dataset, scope) {
        let result
        switch(scope) {
            case 'pinned':
                result = !!dataset.pinned
                break
            case 'visible':
                result = !dataset.hidden
                break
            case 'group':
                const activeGroup = this.groupOptions[this.countryGroupSelector.selectedIndex]
                result = dataset.CGroup && dataset.CGroup.includes(activeGroup)
                break
            case 'all':
                result = true
                break
            default:
                result = !dataset.hidden
                break
        }
        return result
    }

    // Helper method to update chart while preserving any set y-axis limits
    // Chart.js automatically recalculates y-axis min/max during chart.update() based on visible data,
    // which overrides any bounds that have been set (programmatically or by users). 
    // This method preserves those bounds to respect the configured limits.
    updateChartPreservingYAxis(updateOptions = { duration: 0, lazy: false }) {
        // Get the actual current scale values from the chart's scales object
        const yScale = this.chart.scales?.y
        const currentMin = yScale?.min
        const currentMax = yScale?.max
        // Also check if there are explicitly set bounds in options
        const yAxis = this.chart.options.scales?.y
        const configuredMin = yAxis?.min
        const configuredMax = yAxis?.max
        // Prefer configured bounds, but fall back to current scale if not explicitly configured
        const minToPreserve = configuredMin !== undefined ? configuredMin : currentMin
        const maxToPreserve = configuredMax !== undefined ? configuredMax : currentMax
        this.chart.update(updateOptions)
        // Restore the y-axis limits
        if (minToPreserve !== undefined || maxToPreserve !== undefined) {
            this.chart.options.scales.y.min = minToPreserve
            this.chart.options.scales.y.max = maxToPreserve
            this.chart.update({ duration: 0, lazy: false })
        }
    }
}
