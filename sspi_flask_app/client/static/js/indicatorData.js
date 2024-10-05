// Static Data

async function getStaticData(IndicatorCode) {
    const response = await fetch(`/api/v1/static/indicator/${IndicatorCode}`)
    try {
        return response.json()
    } catch (error) {
        console.error('Error:', error)
    }
}

function initCharts() {
    const StaticCanvas = document.getElementById('static-chart')
    const StaticChart = new Chart(StaticCanvas, {
        type: 'bar',
        options: {
            plugins: {
                legend: {
                    display: false,
                }
            },
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    })
    return [StaticChart]
}

[StaticChart] = initCharts()

function doStaticChartUpdate(ChartData, ChartObject) {
    ChartObject.data = ChartData
    ChartObject.update()
}

function doDynamicChartUpdate(ChartData, ChartObject) {
    // ChartData returns two elements: dataset and labels
    ChartObject.data.labels = ChartData.labels
    ChartObject.data.datasets = ChartData.data
    ChartObject.options.scales = ChartData.scales
    ChartObject.options.plugins.title = ChartData.title
    // ChartData.forEach(document => {
    //     document.dataset.data = document.dataset.scores
    // })
    // ChartObject.data.labels = ChartData.map(document => document.CountryCode)
    ChartObject.update()
}

window.onresize = function() {
    StaticChart.resize()
}

function handleScaleAxis(ChartObject, ScaleByValue) {
    const original_data = ChartObject.data
    if (ScaleByValue) {
        // Sort inner data, then use that to sort labels...sort labels
        console.log('Scale by Value')
        ChartObject.data.datasets[0].parsing.yAxisKey = 'Value'
        ChartObject.data.datasets[0].label = 'Value'
        // Sort Alphabetically
    } else {
        console.log('Scale by Score')
        ChartObject.data.datasets[0].parsing.yAxisKey = 'Score'
        ChartObject.data.datasets[0].label = 'Score'
    }
    ChartObject.update()
}

function handleSortOrder(ChartObject, SortByCountry) {
    const original_data = ChartObject.data
    if (SortByCountry) {
        const sorted_data = original_data.datasets[0].data.sort((a, b) => a.CountryCode.localeCompare(b.CountryCode))
        ChartObject.data.datasets[0].data = sorted_data
        ChartObject.data.labels = sorted_data.map(document => document.CountryCode)
        // Sort inner data, then use that to sort labels...sort labels
        console.log('Sort by Country')
        // Sort Alphabetically
    } else {
        const sorted_data = original_data.datasets[0].data.sort((a, b) => a.Value - b.Value)
        ChartObject.data.datasets[0].data = sorted_data
        ChartObject.data.labels = sorted_data.map(document => document.CountryCode)
        console.log('Sort by Value')
    }
    ChartObject.update()
}

const sortOptions = document.getElementById('static-sort-order')
sortOptions.addEventListener('change', () => {
    handleSortOrder(StaticChart, sortOptions.checked)
})

const scaleOptions = document.getElementById('static-axis-scale')
scaleOptions.addEventListener('change', () => {
    handleScaleAxis(StaticChart, scaleOptions.checked)
})

const endLabelPlugin = {
    id: 'endLabelPlugin',
    afterDatasetsDraw(chart, args, options) {
        const { ctx, chartArea: { top, bottom }, scales: { x, y } } = chart;

        chart.data.datasets.forEach(function(dataset, i) {
            if (dataset.hidden) {
                return;
            }
            const meta = chart.getDatasetMeta(i);
            const lastPoint = meta.data[meta.data.length - 1];
            const value = dataset.CCode;

            ctx.save();
            ctx.font = 'bold 14px Arial';
            ctx.fillStyle = dataset.borderColor;
            ctx.textAlign = 'left';
            ctx.fillText(value, lastPoint.x + 5, lastPoint.y + 4);
            ctx.restore();
        });
    }
}

class DynamicLineChart {
    constructor(parentElement, IndicatorCode, CountryList = []) {
        // ParentElement is the element to attach the canvas to
        // CountryList is an array of CountryCodes (empty array means all countries)
        // Initialize the class
        this.parentElement = parentElement
        this.IndicatorCode = IndicatorCode
        this.CountryList = CountryList

        // pinnedArray contains a list of pinned countries
        this.pinnedArray = Array()

        this.initRoot()
        this.rigCountryGroupSelector()
        this.initChartJSCanvas()
        this.rigLegend()

        // Fetch data and update the chart
        this.fetch().then(data => {
            this.update(data)
        })


    }

    initRoot() {
        // Create the root element
        this.root = document.createElement('div')
        this.root.classList.add('chart-section-dynamic-line')
        this.parentElement.appendChild(this.root)
        this.root.innerHTML = `
        <div class="chart-section-title-bar">
            <h2>Dynamic Indicator Data</h2>
            <div class="chart-section-title-bar-buttons">
                <button class="draw-button">Draw 10 Countries</button>
                <button class="showall-button">Show All</button>
                <button class="hideall-button">Hide All</button>
            </div>
        </div>
        `
        this.rigTitleBarButtons()
    }

    rigTitleBarButtons() {
        this.drawButton = this.root.querySelector('.draw-button')
        this.drawButton.addEventListener('click', () => {
            this.showRandomN(10)
        })
        this.showAllButton = this.root.querySelector('.showall-button')
        this.showAllButton.addEventListener('click', () => {
            this.showAll()
        })
        this.hideAllButton = this.root.querySelector('.hideall-button')
        this.hideAllButton.addEventListener('click', () => {
            this.hideAll()
        })
    }

    initChartJSCanvas() {
        // Initialize the chart canvas
        this.canvas = document.createElement('canvas')
        this.canvas.id = 'dynamic-line-chart-canvas'
        this.canvas.width = 400
        this.canvas.height = 200
        this.context = this.canvas.getContext('2d')
        this.root.appendChild(this.canvas)
        this.chart = new Chart(this.context, {
            type: 'line',
            options: {
                onClick: (event, elements) => {
                    elements.forEach(element => {
                        const dataset = this.chart.data.datasets[element.datasetIndex]
                        this.togglePin(dataset)
                    })
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
                },
                scales: {
                    x: {
                        ticks: {
                            color: '#bbb',
                        },
                        title: {
                            display: true,
                            text: 'Year',
                            color: '#bbb',
                            font: {
                                size: 16
                            }
                        },
                    },
                    y: {
                        ticks: {
                            color: '#bbb',
                        },
                        beginAtZero: true,
                        min: 0,
                        max: 1,
                        title: {
                            display: true,
                            text: 'Indicator Score',
                            color: '#bbb',
                            font: {
                                size: 16
                            }
                        },
                    }
                }
            },
            plugins: [endLabelPlugin]
        })
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
                <h4>Pinned Countries</h4>
                <button class="saveprefs-button">Save Pins</button>
                <button class="clearpins-button">Clear Pins</button>
            </div>
            <div class="legend-items">
            </div>
        `

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
                    ${PinnedCountry.CName} (<b style="color: ${PinnedCountry.borderColor};">${PinnedCountry.CCode}</b>)
                    <button class="remove-button">Remove</button>
                </div>
            `
        })
        this.legendItems.innerHTML += `
            <div class="legend-item">
                <button class="add-country-button">Add Country</button>
            </div>
        `
        this.addCountryButton = this.legend.querySelector('.add-country-button')
        this.addCountryButton.addEventListener('click', () => {
            const search = new SearchDropdown(this.addCountryButton, this.chart.data.datasets, this)
        })
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
        this.pinnedArray.push(...data.chartPreferences.pinnedArray) 
        this.groupOptions = data.groupOptions
        this.updatePins()
        this.updateLegend()
        this.updateCountryGroups()
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
        console.log('Showing all countries')
        this.chart.data.datasets.forEach((dataset) => {
            dataset.hidden = false
        })
        this.chart.update({ duration: 0, lazy: false })
    }

    showGroup(groupName) {
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

    hideAll() {
        console.log('Hiding all countries')
        this.chart.data.datasets.forEach((dataset) => {
            if (!dataset.pinned) {
                dataset.hidden = true
            }
        })
        this.chart.update({ duration: 0, lazy: false })
    }

    showRandomN(N = 10) {
        // Adjust this to only select from those in the current country group
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
        console.log('Sending preferences')
        console.log(this.pinnedArray)
        const activeGroup = this.groupOptions[this.countryGroupContainer.style.getPropertyValue('--selected-index')]
        fetch(`/api/v1/dynamic/line/${this.IndicatorCode}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ 
                pinnedArray: this.pinnedArray, 
                activeGroup: activeGroup,
            })
        })
    }

    pinCountry(dataset) {
        dataset.pinned = true
        this.pinnedArray.push({ CName: dataset.CName, CCode: dataset.CCode, borderColor: dataset.borderColor })
        this.updateLegend()
    }

    unpinCountry(dataset) {
        dataset.pinned = false
        this.pinnedArray = this.pinnedArray.filter((item) => item.CCode !== dataset.CCode)
        this.updateLegend()
    }
    
    togglePin(dataset) {
        dataset.pinned = !dataset.pinned
        if (dataset.pinned) {
            this.pinnedArray.push({ CName: dataset.CName, CCode: dataset.CCode, borderColor: dataset.borderColor })
        } else {
            this.pinnedArray = this.pinnedArray.filter((item) => item.CCode !== dataset.CCode)
        }
        this.updateLegend()
    }
    
    clearPins() {
        this.pinnedArray = Array()
        this.updateLegend()
    }
}

class SearchDropdown {
    constructor(parentElement, datasets, parentChart) {
        this.parentElement = parentElement
        this.datasets = datasets
        this.parentChart = parentChart
        console.log("Beginning Search")
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
        `
        this.textInput = this.parentElement.querySelector("input")
        this.textInput.focus()
        this.textInput.addEventListener("input", () => this.runSearch())
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
            const resultSpan = document.createElement('span')
            resultSpan.classList.add('add-country-pin-button')
            resultSpan.innerHTML = `
                ${option.CName} (<b style="color: ${option.borderColor};">${option.CCode}</b>)
            `
            resultSpan.addEventListener('click', () => {
                this.parentChart.pinCountry(option)
                this.closeResults()
            })
            resultElement.appendChild(resultSpan)
            this.resultsWindow.appendChild(resultElement)
        })
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
