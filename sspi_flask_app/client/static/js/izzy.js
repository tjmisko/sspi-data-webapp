function basicExample() {
    let canvas = document.getElementById("BasicExample")
    console.log(canvas)
    const BarChart = new Chart(canvas, {
        type: 'bar',
        data: {},
        options: {}
    })
    BarChart.data = {
        datasets: [{
          data: [{x: "Category1", y: 11}, {x: "Category1", y: 20}, {x: "Category2", y: 10}],
        }]
    }
    BarChart.update()
}
basicExample()

// function setupBarChart() {
//     let canvas = $("#BarChartByIndicator")[0].get()
//     console.log(Chart)
//     const BarChart = new Chart(BarChartCanvas, {
//         type: 'bar',
//         data: {},
//         options: {}
//     })
//     makeBarChart(BarChart, "BIODIV")
// }

// async function makeBarChart(BarChart, IndicatorCode){
//     let response = await fetch('/api/v1/query/sspi_clean_api_data?IndicatorCode=' + IndicatorCode)
//     let indicator_data = await response.json()
//     indicator_data.sort((a, b) => b.RANK - a.RANK)
//     console.log(indicator_data)
//     BarChart.data = {
//         labels: getCountries(indicator_data),
//         datasets: [{
//             datacode: IndicatorCode,
//             label: indicator_data[0].IndicatorNameShort,
//             data: y_axis,
//             backgroundColor: 'rgb(255, 99, 132)',
//             borderColor: 'rgb(255, 99, 132)',
//             borderWidth: 1
//         }]
//     }
    
//     BarChart.options = {
//         elements: {
//             bar: {
//               borderWidth: 2,
//             }
//         },
//         scaleShowValues: true,
//         layout: {padding : 10},
//         responsive: true,
//         plugins: {
//             legend: {
//                 display: false,
//             }
//         },
//         maintainAspectRatio: false,
//         scales: {
//           xAxes: [{
//             id: 'x',
//             type: 'category',
//             title: {
//                 display: true,
//                 text: 'Country'
//             },
//             ticks: {
//               autoskip: true,
//             }
//           }]
//         }
//     }
//     BarChart.update();
// }
