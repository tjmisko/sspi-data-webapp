console.log("makeGraph.js loaded with chart.js version: " + Chart.version);
const ctx = document.getElementById('BarChart');
const BarChart = new Chart(ctx, {
    type: 'bar',
    data: {},
    options: {}
});
// global raw value set by tickbox
makeBarChart('BIODIV')
raw=false

async function makeBarChart(IndicatorCode){
    let response = await fetch('/api/v1/query/indicator/' + IndicatorCode)
    let indicator_data = await response.json()
    indicator_data.sort((a, b) => b.RANK - a.RANK)
    let y_axis = raw ? getRaw(indicator_data) : getScores(indicator_data)
    BarChart.data = {
        labels: getCountries(indicator_data),
        datasets: [{
            datacode: IndicatorCode,
            label: indicator_data[0].IndicatorNameShort,
            data: y_axis,
            backgroundColor: 'rgb(255, 99, 132)',
            borderColor: 'rgb(255, 99, 132)',
            borderWidth: 1
        }]
    }
    
    BarChart.options = {
        scaleShowValues: true,
        layout: {padding : 20},
        scales: {
          xAxes: [{
            id: 'x',
            type: 'category',
            title: {
                display: true,
                text: 'Country'
            },
            ticks: {
              autoskip: true,
            }
          }]
        }
    }
    BarChart.update();
}

function toggleRaw() {
    raw = !raw
    try {
        IndicatorCode = BarChart.data.datasets[0].datacode
        makeBarChart(IndicatorCode);
    } catch (TypeError) {
        console.log("No Chart Loaded!\n", TypeError)
        IndicatorCode = null;
    }
}


function getCountries(indicator_data) {
    return indicator_data.map(data => data.Country)
}

function getScores(indicator_data) {
    return indicator_data.map(data => data.SCORE)
}

function getRaw(indicator_data) {
    return indicator_data.map(data => data.RAW)
}