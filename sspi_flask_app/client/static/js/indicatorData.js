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

function handleSortOrder(ChartObject, option) {
    const original_data = ChartObject.data
    if (option === 'Alphabetical') {
        original_data.datasets.forEach((dataset) => {
            dataset.data.sort((a, b) => {
                if (a > b) return 1
                if (a < b) return -1
                return 0
            })
        }

        console.log(original_data)
        original_data.labels.sort()
        doChartUpdate(original_data, ChartObject)
        // Sort Alphabetically
    } else {
        console.log(original_data)
    }
}
