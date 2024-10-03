// Static Data
async function getStaticData(IndicatorCode) {
    const response = await fetch(`/api/v1/static/indicator/${IndicatorCode}`)
    try { 
        return response.json()
    } catch (error) {
        console.error('Error:', error)
    }
}

async function getDynamicData(IndicatorCode) {
    const response = await fetch(`/api/v1/dynamic/line/${IndicatorCode}`)
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
    const DynamicCanvas = document.getElementById('dynamic-chart')
    const DynamicChart = new Chart(DynamicCanvas, {
        type: 'line',
        options: {
            plugins: {
                legend: {
                    display: false,
                    position: 'bottom'
                },
                layout: {
                    padding: {
                        bottom: 50
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    })  
    return [StaticChart, DynamicChart]
}

[StaticChart, DynamicChart] = initCharts()

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
    DynamicChart.resize()
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
        ChartObject.data.labels = sorted_data.map(document =>  document.CountryCode )
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

// function showRandomN(ChartObject, N = 10) {
//     let shownIndexArray = Array(N).fill(0).map(
//         () => Math.floor(Math.random() * ChartObject.data.datasets.length)
//     )
//     ChartObject.data.datasets.forEach((dataset, index) => {
//         if (shownIndexArray.includes(index)) {
//             dataset.hidden = false
//         }
//         else {
//             dataset.hidden = true
//         }
//     })
//     ChartObject.options.plugins.legend.display = true
//     ChartObject.update()
// }

class DynamicLineChart {
    // API:
    // showRandomN(N) - Show N random countries
    // update - 
    constructor(parentElement, IndicatorCode, CountryList = []) {
        // ParentElement is the element to attach the canvas to
        // CountryList is an array of CountryCodes (empty array means all countries)
        // Initialize the class
        this.parentElement = parentElement
        this.IndicatorCode = IndicatorCode
        this.CountryList = CountryList

        // Create the root element
        this.root = document.createElement('div')
        this.root.classList.add('chart-section-dynamic-line')
        this.parentElement.appendChild(this.root)
        this.root.innerHTML = `
        <div class="chart-section-title-bar">
            <h2>${IndicatorCode}</h2>
            <div class="chart-section-title-bar-buttons">
                <button class="draw-button">Draw 10 Countries</button>
                <button class="reset-button">Reset</button>
            </div>
        </div>
        `
        this.rigTitleBarButtons()
        // Initialize the canvas
        this.canvas = document.createElement('canvas')
        this.context = this.canvas.getContext('2d')
        this.root.appendChild(this.canvas)

        // Initialize the chart
        this.chart = new Chart(this.context, {
            type: 'line',
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

        // Fetch data and update the chart
            this.fetch().then(data => {
                this.update(data)
        })

    }

    rigTitleBarButtons() {
        this.drawButton = this.root.querySelector('.draw-button')
        this.drawButton.addEventListener('click', () => {
            this.showRandomN(10)
        })
        this.resetButton = this.root.querySelector('.reset-button')
        this.drawButton.addEventListener('click', () => {
            this.showRandomN(10)
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
        this.chart.options.scales = data.scales
        this.chart.options.plugins.title = data.title
        this.chart.update()
    }

    showRandomN(N = 10) {
        let shownIndexArray = Array(N).fill(0).map(
            () => Math.floor(Math.random() * this.chart.data.datasets.length)
        )
        this.chart.data.datasets.forEach((dataset) => {
            dataset.hidden = true
        })
        shownIndexArray.forEach(index => {
            this.chart.data.datasets[index].hidden = false
        })
    }
}
