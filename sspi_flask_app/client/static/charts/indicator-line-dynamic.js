const endLabelPlugin = {
    id: 'endLabelPlugin',
    afterDatasetsDraw(chart) {
        const { ctx } = chart;
        for (let i = 0; i < chart.data.datasets.length; i++) {
            const dataset = chart.data.datasets[i];
            if (dataset.hidden) continue;
            const meta = chart.getDatasetMeta(i);
            if (!meta || !meta.data || meta.data.length === 0) continue;

            let lastPoint = null;
            for (let j = meta.data.length - 1; j >= 0; j--) {
                const element = meta.data[j];
                if (element && element.parsed && element.parsed.y !== null) {
                    lastPoint = element;
                    break;
                }
            }
            if (!lastPoint) continue;

            const value = dataset.CCode ?? '';
            ctx.save();
            ctx.font = 'bold 14px Arial';
            ctx.fillStyle = dataset.borderColor ?? '#000';
            ctx.textAlign = 'left';
            ctx.fillText(value, lastPoint.parsed.x + 5, lastPoint.parsed.y + 4);
            ctx.restore();
        }
    }
}

const extrapolatePlugin = {
    id: 'extrapolateBackwards',
    hidden: false,
    toggle(hidden) {
        this.hidden = hidden !== undefined ? hidden : !this.hidden;
    },
    afterDatasetsDraw(chart) {
        if (this.hidden) return;
        const { ctx, chartArea: { left } } = chart;
        for (let i = 0; i < chart.data.datasets.length; i++) {
            const dataset = chart.data.datasets[i];
            if (dataset.hidden) continue;
            const meta = chart.getDatasetMeta(i);
            if (!meta || !meta.data || meta.data.length === 0) continue;

            let firstElement = null;
            for (let j = 0; j < meta.data.length; j++) {
                const element = meta.data[j];
                if (element && element.parsed && element.parsed.y !== null) {
                    firstElement = element;
                    break;
                }
            }
            if (!firstElement) continue;

            const firstPixelX = firstElement.parsed.x;
            const firstPixelY = firstElement.parsed.y;
            if (firstPixelX > left) {
                ctx.save();
                ctx.beginPath();
                ctx.setLineDash([2, 4]);
                ctx.moveTo(left, firstPixelY);
                ctx.lineTo(firstPixelX, firstPixelY);
                ctx.strokeStyle = dataset.borderColor ?? 'rgba(0,0,0,0.5)';
                ctx.lineWidth = 1;
                ctx.stroke();
                ctx.restore();
            }
        }
    }
};


class DynamicLineChart {
    constructor(parentElement, IndicatorCode, CountryList = []) {
        this.parentElement = parentElement// ParentElement is the element to attach the canvas to
        this.IndicatorCode = IndicatorCode
        this.CountryList = CountryList// CountryList is an array of CountryCodes (empty array means all countries)
        this.pinnedArray = Array() // pinnedArray contains a list of pinned countries
        this.yAxisScale = "score"
        this.endLabelPlugin = endLabelPlugin
        this.extrapolatePlugin = extrapolatePlugin
        this.setTheme(localStorage.getItem("theme"))
        this.initRoot()
        this.rigCountryGroupSelector()
        this.initChartJSCanvas()
        this.updateChartOptions()
        this.rigLegend()
        // Fetch data and update the chart
        this.fetch().then(data => {
            this.update(data)
        })
        this.rigPinStorageOnUnload()
    }

    initRoot() {
        // Create the root element
        this.root = document.createElement('div')
        this.root.classList.add('chart-section-dynamic-line')
        this.parentElement.appendChild(this.root)
        this.root.innerHTML = `
        <div class="chart-section-title-bar">
            <h2 class="chart-section-title">Dynamic Indicator Data</h2>
            <div class="chart-section-title-bar-buttons">
                <label>Report Score</label>
                <input type="checkbox" class="y-axis-scale"/>
                <label>Backward Extrapolation</label>
                <input type="checkbox" class="extrapolate-backwards"/>
                <button class="draw-button">Draw 10 Countries</button>
                <button class="showall-button">Show All</button>
                <button class="hideunpinned-button">Hide Unpinned</button>
            </div>
        </div>
        `;
        this.rigTitleBarButtons()
    }

    rigTitleBarButtons() {
        this.yAxisScaleCheckbox = this.root.querySelector('.y-axis-scale')
        this.yAxisScaleCheckbox.checked = this.yAxisScale === "score"
        this.yAxisScaleCheckbox.addEventListener('change', () => {
            this.toggleYAxisScale()
        })
        this.extrapolateCheckbox = this.root.querySelector('.extrapolate-backwards')
        this.extrapolateCheckbox.checked = !this.extrapolatePlugin.hidden
        this.extrapolateCheckbox.addEventListener('change', () => {
            this.toggleBackwardExtrapolation()
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

    initChartJSCanvas() {
        // Initialize the chart canvas
        this.canvas = document.createElement('canvas')
        this.canvas.id = 'dynamic-line-chart-canvas'
        this.canvas.width = 400
        this.canvas.height = 300
        this.context = this.canvas.getContext('2d')
        this.root.appendChild(this.canvas)
        this.chart = new Chart(this.context, {
            type: 'line',
            plugins: [endLabelPlugin, extrapolatePlugin],
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
                min: 0,
                max: 1,
                title: {
                    display: true,
                    text: 'Indicator Score',
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
                    <button class="saveprefs-button">Save Pins</button>
                    <button class="clearpins-button">Clear Pins</button>
                </div>
            </div>
            <div class="legend-items">
            </div>
        `;
        this.savePrefsButton = legend.querySelector('.saveprefs-button')
        this.savePrefsButton.addEventListener('click', () => {
            this.sendPrefs()
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
        this.pinnedArray.forEach((PinnedCountry) => {
            this.legendItems.innerHTML += `
                <div class="legend-item">
                    <span> ${PinnedCountry.CName} (<b style="color: ${PinnedCountry.borderColor};">${PinnedCountry.CCode}</b>) </span>
                    <button class="remove-button-legend-item" id="${PinnedCountry.CCode}-remove-button-legend">Remove</button>
                </div>
            `
        })
        this.legendItems.innerHTML += `
            <div class="legend-item">
                <button class="add-country-button">Add Country</button>
            </div>
        `;
        this.addCountryButton = this.legend.querySelector('.add-country-button')
        this.addCountryButton.addEventListener('click', () => {
            new SearchDropdown(this.addCountryButton, this.chart.data.datasets, this)
        })
        let removeButtons = this.legendItems.querySelectorAll('.remove-button-legend-item')
        removeButtons.forEach((button) => {
            let CountryCode = button.id.split('-')[0]
            button.addEventListener('click', () => {
                this.unpinCountryByCode(CountryCode, true)
            })
        })
    }

    updateDescription(description) {
        const dbox = document.getElementById("dynamic-indicator-description")
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

    async fetch() {
        const response = await fetch(`/api/v1/dynamic/line/${this.IndicatorCode}`)
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
        this.chart.options.plugins.title = data.title
        if (data.chartPreferences.pinnedArray !== undefined) {
            this.pinnedArray.push(...data.chartPreferences.pinnedArray)
        } else {
            this.pinnedArray = []
        }
        this.groupOptions = data.groupOptions
        this.pinnedOnly = data.chartPreferences.pinnedOnly
        this.updatePins()
        this.updateLegend()
        this.updateDescription(data.description)
        this.updateCountryGroups()
        if (this.pinnedOnly) {
            this.hideUnpinned()
        }
        this.chart.update()
    }

    updatePins() {
        if (this.pinnedArray.length === 0) {
            return
        }
        this.chart.data.datasets.forEach(dataset => {
            if (this.pinnedArray.map(cou => cou.CCode).includes(dataset.CCode)) {
                dataset.pinned = true
                dataset.hidden = false
            }
        })
        this.chart.update()
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

    sendPrefs() {
        const activeGroup = this.groupOptions[this.countryGroupContainer.style.getPropertyValue('--selected-index')]
        fetch(`/api/v1/dynamic/line/${this.IndicatorCode}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                pinnedArray: this.pinnedArray,
                activeGroup: activeGroup,
                pinnedOnly: this.pinnedOnly
            })
        })
    }

    pinCountry(dataset) {
        if (dataset.pinned) {
            return
        }
        dataset.pinned = true
        dataset.hidden = false
        this.pinnedArray.push({ CName: dataset.CName, CCode: dataset.CCode, borderColor: dataset.borderColor })
        this.updateLegend()
        this.chart.update()
    }

    pinCountryByCode(CountryCode) {
        this.chart.data.datasets.forEach(dataset => {
            if (dataset.CCode === CountryCode) {
                dataset.pinned = true
                dataset.hidden = false
                this.pinnedArray.push({ CName: dataset.CName, CCode: dataset.CCode, borderColor: dataset.borderColor })
            }
        })
        this.updateLegend()
        this.chart.update()
    }

    unpinCountry(dataset, hide = false) {
        if (this.pinnedOnly) {
            dataset.hidden = true
        }
        dataset.pinned = false
        this.pinnedArray = this.pinnedArray.filter((item) => item.CCode !== dataset.CCode)
        this.updateLegend()
        this.chart.update()
    }

    unpinCountryByCode(CountryCode, hide = false) {
        this.chart.data.datasets.forEach(dataset => {
            if (dataset.CCode === CountryCode) {
                dataset.pinned = false
                if (hide) {
                    dataset.hidden = true
                }
                this.pinnedArray = this.pinnedArray.filter((item) => item.CCode !== dataset.CCode)
            }
        })
        this.updateLegend()
        this.chart.update()
    }

    togglePin(dataset) {
        if (dataset.pinned) {
            this.unpinCountry(dataset, false)
        } else {
            this.pinCountry(dataset, false)
        }
        this.updateLegend()
        this.chart.update()
    }

    clearPins() {
        this.pinnedArray.forEach((PinnedCountry) => {
            this.unpinCountryByCode(PinnedCountry.CCode, true)
        })
        this.pinnedArray = Array()
        this.updateLegend()
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
        a.download = this.IndicatorCode + '.json';
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
        a.download = this.IndicatorCode + '.csv';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }

    rigPinStorageOnUnload() {
        window.addEventListener("beforeunload", () => {
            localStorage.setItem('pins', JSON.stringify(this.chart.data.datasets.map(
                (dataset) => { dataset.pinned }
            )));
        })
    }

    toggleBackwardExtrapolation() {
        this.extrapolatePlugin.toggle()
        this.chart.update();
    }

    toggleYAxisScale() {
        this.chart.data.datasets.forEach((dataset) => {
            if (this.yAxisScale === "score") {
                dataset.parsing.yAxisKey = "values"
                this.YAxisScale = "value"
                this.chart.options.scales.y.title.text = 'Indicator Value'
            } else {
                dataset.parsing.yAxisKey = "scores"
                this.YAxisScale = "score"
                this.chart.options.scales.y.title.text = 'Indicator Score'
            }
            this.chart.update()
        })
    }
}

class SearchDropdown {
    constructor(parentElement, datasets, parentChart) {
        this.parentElement = parentElement
        this.datasets = datasets
        this.parentChart = parentChart
        this.initResultsWindow()
        this.initSearch()
    }

    initResultsWindow() {
        const resultsWindow = document.createElement('div')
        resultsWindow.classList.add('add-country-pin-results-window')
        resultsWindow.classList.add('legend-item')
        resultsWindow.style.display = 'none'
        this.resultsWindow = this.parentElement.parentNode.parentNode.appendChild(resultsWindow)
    }

    initSearch() {
        this.parentElement.innerHTML = `
            <form class="add-country-pin-search-form">
                <input type="text" name="Country" placeholder="Country">
            </form>
        `;
        this.textInput = this.parentElement.querySelector("input")
        this.textInput.focus()
        this.textInput.addEventListener("input", () => this.runSearch())
        this.formElement = this.parentElement.querySelector("form")
        this.formElement.addEventListener("submit", (event) => {
            event.preventDefault()
            this.selectResultEnter()
        })
    }

    selectResultEnter() {
        let CountryCode = this.readResults()
        if (!CountryCode) {
            return
        }
        this.parentChart.pinCountryByCode(CountryCode)
        this.closeResults()
    }

    readResults() {
        let result = this.resultsWindow.querySelector('.add-country-pin-result')
        let CountryCode = result.id.split('-')[0]
        return CountryCode
    }

    async runSearch() {
        const queryString = this.textInput.value
        const options = await this.getOptions(queryString)
        if (options.length === 0) {
            this.resultsWindow.style.display = 'none'
            return
        }
        this.resultsWindow.style.display = 'flex'
        this.resultsWindow.innerHTML = ''
        options.forEach(option => {
            const resultElement = document.createElement('div')
            resultElement.classList.add('add-country-pin-result')
            resultElement.id = option.CCode + '-add-country-pin-result'
            resultElement.addEventListener('click', () => {
                this.selectResultClick(option)
                this.closeResults()
            })
            const resultSpan = document.createElement('span')
            resultSpan.classList.add('add-country-pin-button')

            resultSpan.innerHTML = `
                ${option.CName} (<b style="color: ${option.borderColor};">${option.CCode}</b>)
            `;
            resultElement.appendChild(resultSpan)
            this.resultsWindow.appendChild(resultElement)
        })
    }

    selectResultClick(option) {
        this.parentChart.pinCountry(option)
    }

    async getOptions(queryString, limit = 10) {
        queryString = queryString.toLowerCase()
        if (!queryString) {
            return []
        }
        let optionArray = Array()

        for (let i = 0; i < this.datasets.length; i++) {
            const matched_name = this.datasets[i].CName.toLowerCase().includes(queryString)
            const matched_code = this.datasets[i].CCode.toLowerCase().includes(queryString)
            if (matched_code | matched_name) {  // Condition: only even numbers
                optionArray.push(this.datasets[i]);
            }
            if (optionArray.length === limit) {  // Termination condition
                break;
            }
        }
        return optionArray
    }

    closeResults() {
        this.resultsWindow.remove()
    }
}
