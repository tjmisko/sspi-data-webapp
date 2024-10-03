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

        // fixedArray contains a list of fixed countries
        this.fixedArray = Array()

        this.initRoot()
        this.initChartJSCanvas()
        this.rigTitleBarButtons()
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
        this.canvas.height = 300
        this.context = this.canvas.getContext('2d')
        this.root.appendChild(this.canvas)
        this.chart = new Chart(this.context, {
            type: 'line',
            options: {
                onClick: (event, elements) => {
                    elements.forEach(element => {
                        const dataset = this.chart.data.datasets[element.datasetIndex]
                        dataset.fixed = !dataset.fixed
                        if (dataset.fixed) {
                            this.fixedArray.push(dataset.CCode)
                        } else {
                            this.fixedArray = this.fixedArray.filter((item) => item !== dataset.CCode)
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

    rigLegend() {
        const legend = document.createElement('legend')
        legend.classList.add('dynamic-line-legend') 
        this.legend = this.root.appendChild(legend)
        console.log(this.legend)
    }

    updateLegend() {
        this.legend.innerHTML = ''
        this.fixedArray.forEach((CCode) => {
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
        this.chart.options.scales = data.scales
        this.chart.options.plugins.title = data.title
        this.chart.update()
    }

    showAll() {
        console.log('Showing all countries')
        this.chart.data.datasets.forEach((dataset) => {
            dataset.hidden = false
        })
        this.chart.update({duration: 0, lazy: false})
    }

    hideAll() {
        console.log('Hiding all countries')
        this.chart.data.datasets.forEach((dataset) => {
            dataset.hidden = true
        })
        this.chart.update({duration: 0, lazy: false})
    }

    showRandomN(N = 10) {
        console.log('Showing', N, 'random countries')
        let shownIndexArray = Array(N).fill(0).map(
            () => Math.floor(Math.random() * this.chart.data.datasets.length)
        )
        this.chart.data.datasets.forEach((dataset) => {
            if ( !dataset.fixed ) {
                dataset.hidden = true
            }
        })
        shownIndexArray.forEach((index) => {
            this.chart.data.datasets[index].hidden = false
            console.log(this.chart.data.datasets[index].CCode, this.chart.data.datasets[index].CName)
        })
        this.chart.update({duration: 0, lazy: false})
    }

}
