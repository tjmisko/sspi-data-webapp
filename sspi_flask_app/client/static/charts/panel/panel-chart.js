class PanelChart {
    constructor(parentElement, { CountryList = [], endpointURL = '', width = 400, height = 300, colorProvider = SSPIColors } ) {
        this.parentElement = parentElement// ParentElement is the element to attach the canvas to
        this.CountryList = CountryList// CountryList is an array of CountryCodes (empty array means all countries)
        this.endpointURL = endpointURL// endpointURL is the URL to fetch data from
        this.width = width// width is the width of the canvas
        this.height = height// height is the height of the canvas
        this.pins = new Set() // pins contains a list of pinned countries
        this.colorProvider = colorProvider // colorProvider is an instance of ColorProvider
        this.yAxisScale = "value"
        this.endLabelPlugin = endLabelPlugin
        this.extrapolateBackwardPlugin = extrapolateBackwardPlugin
        this.setTheme(window.observableStorage.getItem("theme"))
        this.initRoot()
        this.rigTitleBarButtons()
        this.rigCountryGroupSelector()
        this.initChartJSCanvas()
        this.updateChartOptions()
        this.rigLegend()
        this.fetch(this.endpointURL).then(data => {
            this.update(data)
        })
        this.rigPinChangeListener()
    }

    initRoot() {
        // Create the root element
        this.root = document.createElement('div')
        this.root.classList.add('panel-chart-root-container')
        this.parentElement.appendChild(this.root)
    }

    rigTitleBarButtons() {
        this.titleBar = document.createElement('div')
        this.titleBar.classList.add('chart-section-title-bar')
        this.titleBar.innerHTML = `
            <div class="chart-section-title-bar-buttons">
                <label class="title-bar-label">Backward Extrapolation</label>
                <input type="checkbox" class="extrapolate-backward"/>
                <label class="title-bar-label">Linear Interpolation</label>
                <input type="checkbox" class="interpolate-linear"/>
                <button class="draw-button">Draw 10 Countries</button>
                <button class="showall-button">Show All</button>
                <button class="hideunpinned-button">Hide Unpinned</button>
            </div>
        `;
        this.root.appendChild(this.titleBar)
        this.extrapolateBackwardCheckbox = this.root.querySelector('.extrapolate-backward')
        this.extrapolateBackwardCheckbox.checked = true
        this.extrapolateBackwardCheckbox.addEventListener('change', () => {
            this.toggleBackwardExtrapolation()
        })
        this.interpolateCheckbox = this.root.querySelector('.interpolate-linear')
        this.interpolateCheckbox.checked = true
        this.interpolateCheckbox.addEventListener('change', () => {
            this.toggleLinearInterpolation()
        })
        this.drawButton = this.root.querySelector('.draw-button')
        this.drawButton.addEventListener('click', () => {
            this.showRandomN(10)
        })
        this.showAllButton = this.root.querySelector('.showall-button')
        this.showAllButton.addEventListener('click', () => {
            this.showAll()
        })
        this.hideUnpinnedButton = this.root.querySelector('.hideunpinned-button')
        this.hideUnpinnedButton.addEventListener('click', () => {
            this.hideUnpinned()
        })
    }

    rigTitleBarScaleToggle() {
        const buttonBox = this.root.querySelector('.chart-section-title-bar-buttons')
        buttonBox.insertAdjacentHTML('afterbegin', `
            <label class="title-bar-label">Report Score</label>
            <input type="checkbox" class="y-axis-scale"/>
        `)
        this.yAxisScaleCheckbox = this.root.querySelector('.y-axis-scale')
        this.yAxisScaleCheckbox.checked = this.yAxisScale === "score"
        this.yAxisScaleCheckbox.addEventListener('change', () => {
            console.log("Toggling Y-axis scale")
            this.toggleYAxisScale()
        })
    }

    initChartJSCanvas() {
        this.canvas = document.createElement('canvas')
        this.canvas.classList.add('panel-chart-canvas')
        this.canvas.width = 400
        this.canvas.height = 300
        this.context = this.canvas.getContext('2d')
        this.root.appendChild(this.canvas)
        this.chart = new Chart(this.context, {
            type: 'line',
            plugins: [this.endLabelPlugin, this.extrapolateBackwardPlugin],
            options: {
                onClick: (event, elements) => {
                    elements.forEach(element => {
                        const dataset = this.chart.data.datasets[element.datasetIndex]
                        this.togglePin(dataset)
                    })
                },
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
                    endLabelPlugin: {}
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
        const container = document.createElement('div')
        container.id = 'country-group-selector-container'
        this.countryGroupContainer = this.root.appendChild(container)
    }

    updateCountryGroups() {
        const numOptions = this.groupOptions.length;
        this.countryGroupContainer.style.setProperty('--num-options', numOptions);
        this.groupOptions.forEach((option, index) => {
            const id = `option${index + 1}`;
            // Create the radio input
            const input = document.createElement('input');
            input.type = 'radio';
            input.id = id;
            input.name = 'options';
            input.value = option;
            // Set the first option as checked by default
            if (index === 0) {
                input.checked = true;
                // Set the initial selected index
                this.countryGroupContainer.style.setProperty('--selected-index', index);
            }
            // Add event listener to update the selected index
            input.addEventListener('change', () => {
                const countryGroupOptions = document.querySelectorAll(`#country-group-selector-container input[type="radio"]`);
                countryGroupOptions.forEach((countryGroup, index) => {
                    if (countryGroup.checked) {
                        this.countryGroupContainer.style.setProperty('--selected-index', index);
                        this.showGroup(countryGroup.value)
                    }
                });
            });
            // Create the label
            const label = document.createElement('label');
            label.htmlFor = id;
            label.textContent = option;
            // Append input and label to the container
            this.countryGroupContainer.appendChild(input);
            this.countryGroupContainer.appendChild(label);
        });
        // Create the sliding indicator
        const slider = document.createElement('div');
        slider.className = 'slider';
        this.countryGroupContainer.appendChild(slider);
    }

    rigLegend() {
        const legend = document.createElement('legend')
        legend.classList.add('dynamic-line-legend')
        legend.innerHTML = `
            <div class="legend-title-bar">
                <h4 class="legend-title">Pinned Countries</h4>
                <div class="legend-title-bar-buttons">
                    <button class="add-country-button">Search Country</button>
                    <button class="clearpins-button">Clear Pins</button>
                </div>
            </div>
            <div class="legend-items">
            </div>
        `;
        this.addCountryButton = legend.querySelector('.add-country-button')
        this.addCountryButton.addEventListener('click', () => {
            new CountrySelector(this.addCountryButton, this.chart.data.datasets, this)
        })
        this.clearPinsButton = legend.querySelector('.clearpins-button')
        this.clearPinsButton.addEventListener('click', () => {
            this.clearPins()
        })
        this.legend = this.root.appendChild(legend)
        this.legendItems = this.legend.querySelector('.legend-items')
    }

    updateLegend() {
        this.legendItems.innerHTML = ''
        if (this.pins.size > 0) {
            this.pins.forEach((PinnedCountry) => {
                this.legendItems.innerHTML += `
                    <div class="legend-item">
                        <span> ${PinnedCountry.CName} (<b class="panel-legend-item-country-code" style="color: ${PinnedCountry.borderColor};">${PinnedCountry.CCode}</b>) </span>
                        <button class="remove-button-legend-item" id="${PinnedCountry.CCode}-remove-button-legend">Remove</button>
                    </div>
                `
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
        const dbox = this.root.querySelector('.dynamic-indicator-description')
        dbox.innerText = description
    }

    setTheme(theme) {
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
        this.chart.data = data
        this.chart.data.labels = data.labels
        this.chart.data.datasets = data.data
        for (let i = 0; i < this.chart.data.datasets.length; i++) {
            const dataset = this.chart.data.datasets[i]
            const color = this.colorProvider.get(dataset.CCode)
            if (color === "#CCCCCC") {

            } else {
                dataset.borderColor = color
                dataset.backgroundColor = color + "44"
            }
        }
        this.chart.options.plugins.title = data.title
        this.groupOptions = data.groupOptions
        this.pinnedOnly = false
        this.getPins()
        this.updateLegend()
        this.updateDescription(data.description)
        this.updateCountryGroups()
        this.chart.update()
        if (data.hasScore) {
            this.toggleYAxisScale()
            this.rigTitleBarScaleToggle()
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
        console.log('Showing all countries')
        this.chart.data.datasets.forEach((dataset) => {
            dataset.hidden = false
        })
        this.chart.update({ duration: 0, lazy: false })
    }

    showGroup(groupName) {
        this.pinnedOnly = false
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
        const activeGroup = this.groupOptions[this.countryGroupContainer.style.getPropertyValue('--selected-index')]
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

    toggleBackwardExtrapolation() {
        this.extrapolateBackwardPlugin.toggle()
        this.chart.update();
    }

    toggleYAxisScale() {
        if (this.yAxisScale === "score") {
            this.yAxisScale = "value"
            this.chart.options.scales.y.title.text = 'Item Value'
        } else {
            this.yAxisScale = "score"
            this.chart.options.scales.y.title.text = 'Item Score'
        }
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

    toggleLinearInterpolation() {
        this.chart.options.datasets.line.spanGaps = !this.chart.options.datasets.line.spanGaps
        this.chart.update();
    }
}
