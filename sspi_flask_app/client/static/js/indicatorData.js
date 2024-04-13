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
    console.log(ChartObject.data)
    ChartObject.data = ChartData
    console.log(ChartObject.data)
    ChartObject.update()
    console.log("Chart Updated")
}

const ctx = document.getElementById('myChart');

new Chart(ctx, {
    type: 'bar',
    data: {
        labels: ['Red', 'Blue', 'Yellow', 'Green', 'Purple', 'Orange'],
        datasets: [{
            label: '# of Votes',
            data: [12, 19, 3, 5, 2, 3],
            borderWidth: 1
        }]
    },
    options: {
        scales: {
            y: {
                beginAtZero: true
            }
        }
    }
});

//getStaticData("BIODIV").then(data => doChartUpdate(data, StaticChart));

