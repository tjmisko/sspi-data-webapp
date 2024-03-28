// Static Data
async function getStaticData(IndicatorCode) {
    const response = fetch(`/api/v1/static/${IndicatorCode}`)
    .then(response => response.json())
    .then(data => {
        console.log(data)
        return response
    })
    .catch(error => { console.log(error) })
}

async function getDynamicData(IndicatorCode) {
    const response = fetch(`/api/v1/dynamic/${IndicatorCode}`)
    .then(response => response.json())
    .then(data => {
        console.log(data)
        return response
    })
    .catch(error => { console.log(error) })
}

function initCharts() {
    const StaticCanvas = document.getElementById('static-chart')
    const StaticChart = new Chart(StaticCanvas, {
        options: {
            type: 'bar',
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    })  
    const DynamicCanvas = document.getElementById('dynamic-chart')
    const DynamicChart = new Chart(DynamicCanvas, {
        options: {
            type: 'bar',
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
