// Static Data
async function getStaticData(IndicatorCode) {
    const response = await fetch(`/api/v1/static/${IndicatorCode}`)
    try { 
        return response.json()
    } catch (error) {
        console.error('Error:', error)
    }
}

async function getDynamicData(IndicatorCode) {
    const response = await fetch(`/api/v1/dynamic/${IndicatorCode}`)
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
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    })  
    const DynamicCanvas = document.getElementById('dynamic-chart')
    const DynamicChart = new Chart(DynamicCanvas, {
        type: 'bar',
        options: {
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

function doChartUpdate(ChartData, ChartObject) {
    ChartObject.data = ChartData
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
        // Sort Alphabetically
    } else {
        console.log('Scale by Score')
        ChartObject.data.datasets[0].parsing.yAxisKey = 'Score'
    }
    ChartObject.update()
}

function handleSortOrder(ChartObject, SortByCountry) {
    const original_data = ChartObject.data
    if (SortByCountry) {
        // Sort inner data, then use that to sort labels...sort labels
        console.log('Sort by Country')
        // Sort Alphabetically
    } else {
        console.log('Sort by Value')
    }
}

const sortOptions = document.getElementById('static-sort-order')
sortOptions.addEventListener('change', () => {
    handleSortOrder(StaticChart, sortOptions.checked)
})

const scaleOptions = document.getElementById('static-axis-scale')
scaleOptions.addEventListener('change', () => {
    handleScaleAxis(StaticChart, scaleOptions.checked)
})
