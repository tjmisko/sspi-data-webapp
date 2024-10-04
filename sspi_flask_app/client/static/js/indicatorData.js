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
        this.rigTitleBarButtons()
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
                        dataset.pinned = !dataset.pinned
                        if (dataset.pinned) {
                            this.pinnedArray.push(dataset.CCode)
                        } else {
                            this.pinnedArray = this.pinnedArray.filter((item) => item !== dataset.CCode)
                        }
                        this.updateLegend()
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
        this.legend = this.root.appendChild(legend)
        console.log(this.legend)
    }

    updateLegend() {
        this.legend.innerHTML = ''
        this.pinnedArray.forEach((CCode) => {
            this.legend.innerHTML += `<div class="legend-item">${CCode}</div>`
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
        this.groupOptions = data.groupOptions
        this.chart.update()
        this.updateCountryGroups()
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

}
