class PanelChart {
    constructor(parentElement, { CountryList = [], endpointURL = '', width = 400, height = 300, colorProvider = SSPIColors } ) {
        this.parentElement = parentElement// ParentElement is the element to attach the canvas to
        this.CountryList = CountryList// CountryList is an array of CountryCodes (empty array means all countries)
        this.endpointURL = endpointURL// endpointURL is the URL to fetch data from
        this.pins = new Set() // pins contains a list of pinned countries
        this.colorProvider = colorProvider // colorProvider is an instance of ColorProvider
        this.yAxisScale = "value"
        this.endLabelPlugin = endLabelPlugin
        this.extrapolateBackwardPlugin = extrapolateBackwardPlugin
        this.proximityPlugin = proximityPlugin
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
    <div class="dynamic-item-description"></div>
</details>
<details class="chart-options-details chart-view-options">
    <summary class="chart-view-options-summary">View Options</summary>
    <div class="chart-view-option">
        <input type="checkbox" class="extrapolate-backward"/>
        <label class="title-bar-label">Backward Extrapolation</label>
    </div>
    <div class="chart-view-option">
        <input type="checkbox" class="interpolate-linear"/>
        <label class="title-bar-label">Linear Interpolation</label>
    </div>
    <button class="showall-button">Show All</button>
</details>
<details class="country-group-options chart-options-details">
    <summary class="country-group-selector-summary">Country Groups</summary>
    <select class="country-group-selector"></select>
    <button class="draw-button">Draw 10 Countries</button>
    <button class="show-in-group-button">Show All in Group</button>
</details>
<details class="pinned-country-details chart-options-details">
    <summary>Pinned Countries</summary>
    <div class="legend-title-bar-buttons">
        <button class="add-country-button">Search Country</button>
        <button class="hideunpinned-button">Hide Unpinned</button>
        <button class="clearpins-button">Clear Pins</button>
    </div>
    <legend class="dynamic-line-legend">
        <div class="legend-items"></div>
    </legend>
</details>
<details class="download-data-details chart-options-details">
    <summary>Download Chart Data</summary>
    <form id="downloadForm">
        <fieldset>
            <legend>Select data scope:</legend>
            <label><input type="radio" name="scope" value="pinned" required>Pinned countries</label>
            <label><input type="radio" name="scope" value="visible">Visible countries</label>
            <label><input type="radio" name="scope" value="group">Countries in group</label>
            <label><input type="radio" name="scope" value="all">All available countries</label>
        </fieldset>
        <fieldset>
            <legend>Choose file format:</legend>
            <label><input type="radio" name="format" value="json" required>JSON</label>
            <label><input type="radio" name="format" value="csv">CSV</label>
        </fieldset>
        <button type="submit">Download Data</button>
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

        this.showAllButton = this.root.querySelector('.showall-button')
        this.showAllButton.addEventListener('click', () => {
            this.showAll()
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
    }

    rigItemDropdown() {
        this.itemInformation = this.chartOptions.querySelector('.item-information')
        this.itemDropdown = this.itemInformation.querySelector('.item-dropdown')
    }

    rigScaleToggle() {
        const buttonBox = this.chartOptions.querySelector('.chart-view-options')
        buttonBox.insertAdjacentHTML('afterbegin', `
<input type="checkbox" class="y-axis-scale"/>
<label class="title-bar-label">Report Score</label>
`)
        this.yAxisScaleCheckbox = this.root.querySelector('.y-axis-scale')
        this.yAxisScaleCheckbox.checked = this.yAxisScale === "score"
        this.yAxisScaleCheckbox.addEventListener('change', () => {
            console.log("Toggling Y-axis scale")
            this.toggleYAxisScale()
        })
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
            plugins: [this.endLabelPlugin, this.extrapolateBackwardPlugin, this.proximityPlugin],
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
                    endLabelPlugin: {},
                    tooltip: {
                        enabled: false,
                    },
                    proximityHighlight: {
                        radius: 20, // px
                        enabled: true,
                        tooltipBg: this.headerBackgroundColor,
                        tooltipFg: this.titleColor,
                        clickRadius: 2,
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

    updateDescription(description) {
        const dbox = this.chartOptions.querySelector('.dynamic-item-description')
        dbox.innerText = description
    }

    updateItemDropdown(options) {
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
            this.axisTitleColor = "#bbb"
            this.titleColor = "#ccc"
        } else {
            this.theme = "light"
            this.tickColor = "#444"
            this.axisTitleColor = "#444"
            this.titleColor = "#444"
            this.headerBackgroundColor = "#f0f0f0"
        }
        const bg = getComputedStyle(root).getPropertyValue('--header-color').trim()
        this.headerBackgroundColor = bg
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
        // this.chart.data = data
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
        this.getPins()
        this.updateLegend()
        this.updateItemDropdown(data.itemOptions, data.itemType)
        this.updateDescription(data.description)
        this.updateChartColors()
        this.updateCountryGroups()
        this.chart.update()
        if (data.hasScore) {
            this.setYAxisScale("score")
            this.rigScaleToggle()
        }
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
        this.chart.update({ duration: 0, lazy: false })
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
        this.chart.update({ duration: 0, lazy: false })
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
        this.chart.update({ duration: 0, lazy: false })
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
        this.chart.update({ duration: 0, lazy: false })
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
        this.chart.update({ duration: 0, lazy: false })
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

    dumpChartDataJSON(screenVisibility = true) {
        const observations = this.chart.data.datasets.map(dataset => {
            if (screenVisibility && dataset.hidden) {
                return []
            }
            return dataset.data.map((_, i) => ({
                "ItemCode": dataset.ICode,
                "CountryCode": dataset.CCode,
                "Score": dataset.scores[i],
                "Value": dataset.values[i],
                "Year": dataset.years[i]
            }));
        }).flat();
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
    }

    dumpChartDataCSV(screenVisibility = true) {
        const observations = this.chart.data.datasets.map(dataset => {
            if (screenVisibility && dataset.hidden) {
                return []
            }
            return dataset.data.map((_, i) => ({
                "ItemCode": dataset.ICode,
                "CountryCode": dataset.CCode,
                "Score": dataset.scores[i].toString(),
                "Value": dataset.values[i].toString(),
                "Year": dataset.years[i].toString()
            }));
        }).flat();
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

    setYAxisScale(scale) {
        this.yAxisScale = scale
        const scaleType = scale.charAt(0).toUpperCase() + scale.slice(1)
        let itemType = ""
        if (this.itemType === "sspi") {
            itemType = this.itemType.toUpperCase()
        } else {
            itemType = this.itemType.charAt(0).toUpperCase() + this.itemType.slice(1)
        }
        this.chart.options.scales.y.title.text = itemType + " " + scaleType 
        let yMin = 0
        let yMax = 1
        for (let i = 0; i < this.chart.data.datasets.length; i++) {
            const dataset = this.chart.data.datasets[i];
            if (i == 0) {
                yMin = (this.yAxisScale === "value") ? dataset.maxYValue : 0;
                yMax = (this.yAxisScale === "value") ? dataset.maxYValue : 1;
            }
            dataset.parsing.yAxisKey = this.yAxisScale;
            for (let j = 0; j < dataset.data.length; j++) {
                if (this.yAxisScale === "value") {
                    dataset.data[j] = dataset.value[j]
                } else {
                    dataset.data[j] = dataset.score[j]
                }
            }
        }
        this.chart.options.scales.y.min = yMin
        this.chart.options.scales.y.max = yMax
        this.chart.update()
    }


    toggleYAxisScale() {
        if (this.yAxisScale === "score") {
            this.setYAxisScale("value")
        } else {
            this.setYAxisScale("score")
        }
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
}
