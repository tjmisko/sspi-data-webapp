class PanelChart {
    constructor(parentElement, { CountryList = [], endpointURL = '', width = 400, height = 300, colorProvider = SSPIColors } ) {
        this.parentElement = parentElement// ParentElement is the element to attach the canvas to
        this.CountryList = CountryList// CountryList is an array of CountryCodes (empty array means all countries)
        this.endpointURL = endpointURL// endpointURL is the URL to fetch data from
        this.pins = new Set() // pins contains a list of pinned countries
        this.missingCountries = [] // Array of countries with no data, populated from API response
        this.colorProvider = colorProvider // colorProvider is an instance of ColorProvider
        this.extrapolateBackwardPlugin = extrapolateBackwardPlugin
        this.chartInteractionPlugin = chartInteractionPlugin
        this.setTheme(window.observableStorage.getItem("theme"))
        this.pinnedOnly = window.observableStorage.getItem("pinnedOnly") || false
        this.countryGroup = window.observableStorage.getItem("countryGroup") || "SSPI67"
        this.initRoot()
        this.initChartJSCanvas()
        this.buildChartOptions()
        this.rigChartOptions()
        this.rigItemDropdown()
        this.rigCountryGroupSelector()
        this.updateChartOptions()
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
<button class="icon-button hide-chart-options" aria-label="Hide Chart Options" title="Hide Chart Options">
    <svg class="hide-chart-options-svg" width="24" height="24">
        <use href="#icon-close" />
    </svg>
</button>
<details class="item-information chart-options-details">
    <summary class="item-information-summary">Item Information</summary>
    <select class="item-dropdown"></select>
    <div class="dynamic-item-description-container">
        <div class="dynamic-item-description"></div>
    </div>
</details>
<details class="chart-options-details chart-view-options">
    <summary class="chart-view-options-summary">View Options</summary>
    <div class="view-options-suboption-container">
        <div class="chart-view-subheader">Imputation Options</div>
        <div class="chart-view-option">
            <input type="checkbox" class="extrapolate-backward"/>
            <label class="title-bar-label">Backward Extrapolation</label>
        </div>
        <div class="chart-view-option">
            <input type="checkbox" class="interpolate-linear"/>
            <label class="title-bar-label">Linear Interpolation</label>
        </div>
    </div>
</details>
<details class="select-countries-options chart-options-details">
    <summary class="select-countries-summary">Select Countries</summary>
    <div class="view-options-suboption-container">
        <div class="chart-view-subheader">Country Groups</div>
        <div class="chart-view-option">
            <select class="country-group-selector"></select>
        </div>
        <div class="chart-view-option country-group-buttons">
            <div class="country-group-button-group">
                <button class="draw-button">Draw 10 Countries</button>
                <button class="show-in-group-button">Show All in Group</button>
            </div>
        </div>
        <div class="chart-view-subheader">Pinned Countries</div>
        <div class="legend-title-bar-buttons">
            <button class="add-country-button">Search Country</button>
            <button class="hideunpinned-button">Hide Unpinned</button>
            <button class="clearpins-button">Clear Pins</button>
        </div>
        <legend class="dynamic-line-legend">
            <div class="legend-items"></div>
        </legend>
        <div class="chart-view-subheader">Missing Countries</div>
        <div class="missing-countries-container">
            <div class="missing-countries-list"></div>
            <div class="missing-countries-summary"></div>
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
    <use href="#icon-menu" />
</svg>
`;
        this.root.appendChild(this.showChartOptions)
        this.overlay = document.createElement('div')
        this.overlay.classList.add('chart-options-overlay')
        this.overlay.addEventListener('click', () => {
            this.closeChartOptionsSidebar()
        })
        this.root.appendChild(this.overlay)
        const wrapper = document.createElement('div')
        wrapper.classList.add('chart-options-wrapper')
        wrapper.appendChild(this.chartOptions)
        this.root.appendChild(wrapper)
    }

    rigChartOptions() {
        this.showChartOptions.addEventListener('click', () => {
            this.openChartOptionsSidebar()
        })
        this.hideChartOptions = this.chartOptions.querySelector('.hide-chart-options')
        this.hideChartOptions.addEventListener('click', () => {
            this.closeChartOptionsSidebar()
        })
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
        this.drawButton = this.root.querySelector('.draw-button')
        this.drawButton.addEventListener('click', () => {
            this.showRandomN(10)
        })
        this.showInGroupButton = this.chartOptions.querySelector('.show-in-group-button')
        this.showInGroupButton.addEventListener('click', () => {
            const activeGroup = this.groupOptions[this.countryGroupSelector.selectedIndex]
            this.showGroup(activeGroup)
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
<h2 class="panel-chart-title"></h2>
<div class="panel-canvas-wrapper">
    <canvas class="panel-chart-canvas"></canvas>
</div>
`;
        this.root.appendChild(this.chartContainer)
        this.title = this.chartContainer.querySelector('.panel-chart-title')
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
                        circleColor: this.tickColor,
                        guideColor: this.tickColor,
                        labelField: 'CCode',
                        showDefaultLabels: true,
                        defaultLabelSpacing: 5,
                        onDatasetClick: (datasets, event, chart) => {
                            datasets.forEach((dataset) => {
                                this.togglePin(dataset)
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

    updateChartOptions() {
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
        this.addCountryButton = this.chartOptions.querySelector('.add-country-button')
        this.addCountryButton.addEventListener('click', () => {
            new CountrySelector(this.addCountryButton, this.chart.data.datasets, this)
        })
        this.clearPinsButton = this.chartOptions.querySelector('.clearpins-button')
        this.clearPinsButton.addEventListener('click', () => {
            this.clearPins()
        })
        this.legend = this.chartOptions.querySelector('.dynamic-line-legend')
        this.legendItems = this.legend.querySelector('.legend-items')
    }

    updateLegend() {
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
                newPin.appendChild(pinSpan)
                newPin.appendChild(removeButton)
                this.legendItems.appendChild(newPin)
            })
        }
        let removeButtons = this.legendItems.querySelectorAll('.remove-button-legend-item')
        removeButtons.forEach((button) => {
            let CountryCode = button.id.split('-')[0]
            button.addEventListener('click', () => {
                this.unpinCountryByCode(CountryCode, true)
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

    updateDescription(description) {
        const dbox = this.chartOptions.querySelector('.dynamic-item-description')
        dbox.innerHTML = '<p><b>Description: </b> ' + description + '</p>'
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
        const bg = getComputedStyle(root).getPropertyValue('--header-color').trim()
        this.headerBackgroundColor = bg
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
        this.chart.update()
        
        // Compute missing countries asynchronously after chart rendering
        console.log('=== About to call computeMissingCountriesAsync ===')
        console.log('countryGroupMap available?', !!this.countryGroupMap, Object.keys(this.countryGroupMap || {}).length, 'countries')
        this.computeMissingCountriesAsync()
    }

    computeMissingCountriesAsync() {
        console.log('=== computeMissingCountriesAsync called ===')
        // Use setTimeout to defer execution until after chart rendering is complete
        setTimeout(() => {
            console.log('=== setTimeout callback executing ===')
            this.computeMissingCountries()
        }, 0)
    }

    computeMissingCountries() {
        console.log('=== Starting computeMissingCountries ===')
        
        if (!this.countryGroupMap || Object.keys(this.countryGroupMap).length === 0) {
            console.log('No country group map available for missing countries computation')
            return
        }

        console.log('Country group map keys:', Object.keys(this.countryGroupMap).length, 'countries')
        console.log('First 10 countries in group map:', Object.keys(this.countryGroupMap).slice(0, 10))
        console.log('SGP in group map?', 'SGP' in this.countryGroupMap, this.countryGroupMap['SGP'])

        const missingCountries = []
        const seenCountries = new Set()

        console.log('Total datasets:', this.chart.data.datasets.length)
        console.log('Dataset country codes:', this.chart.data.datasets.map(d => d.CCode))

        // First pass: process countries that appear in datasets
        this.chart.data.datasets.forEach(countryData => {
            const countryCode = countryData.CCode
            console.log(`Processing dataset for country: ${countryCode}`)
            seenCountries.add(countryCode)
            const scores = countryData.data || []
            const scoresEmpty = !scores || scores.length === 0 || scores.every(s => s === null || s === undefined || s === '')
            console.log(`Country ${countryCode}: data length=${scores.length}, empty=${scoresEmpty}`)
            if (scoresEmpty) {
                console.log(`Adding ${countryCode} to missing (empty data)`)
                missingCountries.push({
                    CCode: countryCode,
                    CName: countryData.CName || countryCode,
                    CGroup: countryData.CGroup || this.countryGroupMap[countryCode] || []
                })
            }
        })

        console.log('Seen countries:', Array.from(seenCountries))
        console.log('SGP in seen countries?', seenCountries.has('SGP'))

        // Second pass: find countries in group map that don't appear in datasets at all
        let notSeenCount = 0
        Object.entries(this.countryGroupMap).forEach(([countryCode, countryGroups]) => {
            if (!seenCountries.has(countryCode)) {
                notSeenCount++
                if (countryCode === 'SGP') {
                    console.log(`SGP not seen - adding to missing. Groups:`, countryGroups)
                }
                missingCountries.push({
                    CCode: countryCode,
                    CName: countryCode, // We only have the country code from the map
                    CGroup: countryGroups
                })
            }
        })

        console.log(`Countries not seen in datasets: ${notSeenCount}`)
        console.log(`Total missing countries found: ${missingCountries.length}`)
        console.log('Missing countries:', missingCountries.map(c => c.CCode))
        console.log('=== End computeMissingCountries ===')

        // Update the missing countries and refresh display
        this.missingCountries = missingCountries
        this.updateMissingCountries()
    }

    getPins() {
        const storedPins = window.observableStorage.getItem('pinnedCountries')
        console.log("Stored pins:", storedPins)
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
        this.chart.update()
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
        })
        let shownIndexArray = availableDatasetIndices.sort(() => Math.random() - 0.5).slice(0, N)
        shownIndexArray.forEach((index) => {
            this.chart.data.datasets[index].hidden = false
            console.log(this.chart.data.datasets[index].CCode, this.chart.data.datasets[index].CName)
        })
        this.updateChartPreservingYAxis()
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

    pinCountryByCode(CountryCode) {
        this.chart.data.datasets.forEach(dataset => {
            if (dataset.CCode === CountryCode) {
                dataset.pinned = true
                dataset.hidden = false
                this.pins.add({ CName: dataset.CName, CCode: dataset.CCode, borderColor: dataset.borderColor })
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
        this.overlay.classList.remove('active')
        this.overlay.classList.add('inactive')
    }

    openChartOptionsSidebar() {
        this.chartOptions.classList.add('active')
        this.chartOptions.classList.remove('inactive')
        this.overlay.classList.remove('inactive')
        this.overlay.classList.add('active')
    }

    toggleChartOptionsSidebar() {
        if (this.chartOptions.classList.contains('active')) {
            this.closeChartOptionsSidebar()
        } else {
            this.openChartOptionsSidebar()
        }
    }

    dumpChartDataJSON(scope = 'visible') {
        console.log('dumpChartDataJSON called with scope:', scope)
        console.log('Available datasets:', this.chart.data.datasets.length)
        
        // Debug: log the structure of the first dataset
        if (this.chart.data.datasets.length > 0) {
            console.log('First dataset structure:', Object.keys(this.chart.data.datasets[0]))
            console.log('First dataset sample:', this.chart.data.datasets[0])
        }
        
        const observations = this.chart.data.datasets.map(dataset => {
            const shouldInclude = this.shouldIncludeDataset(dataset, scope)
            console.log(`Dataset ${dataset.CCode} (${dataset.CName}) - include: ${shouldInclude}`)
            
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
            
            return dataset.data.map((_, i) => ({
                "ItemCode": dataset.ICode || '',
                "CountryCode": dataset.CCode || '',
                "CountryName": dataset.CName || '',
                "Score": scores[i] ?? null,
                "Value": values[i] ?? null,
                "Year": years[i] ?? null
            }));
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
        a.download = 'item-panel-data.json';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        
        console.log('JSON download initiated')
    }

    dumpChartDataCSV(scope = 'visible') {
        console.log('dumpChartDataCSV called with scope:', scope)
        
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
            
            return dataset.data.map((_, i) => ({
                "ItemCode": dataset.ICode || '',
                "CountryCode": dataset.CCode || '',
                "CountryName": dataset.CName || '',
                "Score": scores[i]?.toString() || '',
                "Value": values[i]?.toString() || '',
                "Year": years[i]?.toString() || ''
            }));
        }).flat();
        
        console.log('Total observations for CSV:', observations.length)
        
        if (observations.length === 0) {
            alert('No data available for the selected scope. Please try a different scope or ensure data is loaded.')
            return
        }
        
        const csvString = Papa.unparse(observations);
        const blob = new Blob([csvString], { type: 'text/csv' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'item-panel-data.csv';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        
        console.log('CSV download initiated')
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
        this.chart.update();
    }

    toggleLinearInterpolation() {
        this.chart.options.datasets.line.spanGaps = !this.chart.options.datasets.line.spanGaps
        this.chart.update();
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
        console.log('Download request initiated')
        const formData = new FormData(this.downloadForm)
        const scope = formData.get('scope')
        const format = formData.get('format')
        
        console.log('Download scope:', scope)
        console.log('Download format:', format)
        
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
