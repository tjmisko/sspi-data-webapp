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
            legend: {
                display: false
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
                    display: false
                },
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
