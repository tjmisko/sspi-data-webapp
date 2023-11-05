async function DatabaseStatus(database){
    let response = await fetch('/api/v1/database/' + database +'/status')
}

function closeBox(obj) {
    $(obj).parent(".results-box").hide()
}

function toggleQueryMenu(IndicatorCode){
    $(`#${IndicatorCode}-query-menu`).toggle("fast")
}

async function handleQuery(IndicatorCode, database){
    $.get(`/api/v1/query/indicator/${IndicatorCode}?database=${database}`, 
        (data)=>{
            console.log(data)
            $("#" + IndicatorCode + ".results-box")
                .children(".return-content")
                .empty()
                .append(JSON.stringify(data, null, 2))
        });
    $(`#${IndicatorCode}.results-box`).show()
    $("#" + IndicatorCode + ".results-box").children(".return-content").empty().append("waiting")
}

function handleCollect(IndicatorCode) {
    $(`#${IndicatorCode}.results-box`).show()
    let message_handler = new EventSource(`/api/v1/collect/${IndicatorCode}`)
    console.log(`GET /api/v1/collect/${IndicatorCode}`)
    message_handler.addEventListener("message", function (event) {
        if (event.data === "close") {
            message_handler.close()
        } else {
            console.log(event)
            results_box.children.innerHTML = event.data
        }
    });
}

function handleCompute(IndicatorCode) {
    $.get(`/api/v1/compute/${IndicatorCode}`, 
        (data)=>{
            console.log(data)
            $(`#${IndicatorCode}.results-box`)
                .children(".return-content")
                .empty()
                .append(JSON.stringify(data, null, 2))
        });
    $(`#${IndicatorCode}.results-box`).show()
    $(`#${IndicatorCode}.results-box`).children(".return-content").empty().append("processing")
}

function makeComparisonTable() {
    // Only runs once on pageload and creates the tabulator object with BIODIV default
    var comparisonTable = new Tabulator("#comparison-table", {
        // ajaxURL:"/api/v1/compare/BIODIV", //ajax URL
        // headerSortClickElement:"icon",
        // maxHeight: "100%",
        columns: [
            {title: "Country", field: "Country"},
            {title: "COU", field: "CountryCode"},
            {title: "Indicator Code", field: "IndicatorCode"},
            {title: "Indicator", field: "IndicatorNameShort"},
            {title: "Year", field: "YEAR"},
            {title: "sspi_static_value", field: "sspi_static_raw"},
            {title: "sspi_dynamic_value", field: "sspi_dynamic_raw"},
        ] 
    });
    return comparisonTable
}

async function handleComparisonDataUpdate(selectObject, comparisonTable, comparisonChart) {
    console.log("I run on startup")
    IndicatorCode = selectObject.value
    updateComparisonChart(IndicatorCode, comparisonChart)
    updateComparisonTable(IndicatorCode, comparisonTable)
}

async function updateComparisonTable(IndicatorCode, comparisonTable) {
    // takes in an IndicatorCode from the form submission and updates
    console.log("Updating comparison table with " + IndicatorCode)
    $.get(`/api/v1/compare/${IndicatorCode}`, (data) => {comparisonTable.setData(data)})
}

async function updateComparisonChart(IndicatorCode, comparisonChart) {
    let response = await fetch(`/api/v1/compare/${IndicatorCode}`)
    let indicator_data = await response.json()
    indicator_data.sort((a, b) => b.RANK - a.RANK)
    console.log(indicator_data)
    console.log(indicator_data.map(d => {return {x: d.RANK, y: d.sspi_static_raw}}))
    comparisonChart.data = {
        labels: indicator_data.map(d => d.Country),
        datasets: [
            {
                label: 'SSPI Static Data',
                data: indicator_data.map(d => {return {x: d.RANK, y: d.sspi_static_raw}})
            },
            {
                label: 'SSPI Dynamic Data',
                data: indicator_data.map(d => {return {x: d.RANK, y: d.sspi_dynamic_raw}})
            }
            // {
            //     label: 'SSPI Dynamic Data',
            //     data: {
            //         x: indicator_data.map(d => d.RANK),
            //         y: indicator_data.map(d => d.sspi_static_raw)
            //     }
            // }
        ]
    }
    console.log("Updating the data")
    comparisonChart.update();
}

function makeComparisonChart() {
    let comparisonChartCanvas = $("#comparison-chart").get(0)
    const comparisonChart = new Chart(comparisonChartCanvas, {
        type: 'scatter',
        data: {
            datasets: [
                {
                    label: "Hello",
                    data: [{RANK: 0.4, y: 0.3}, {RANK: 0.5, y: 0.6}]
                },
                {
                    label: "Goodbye",
                    data: [{RANK: 0.14, y: 0.33}, {RANK: 0.25, y: 0.6}]
                }
            ]
        },
        options: {
            scales: {
                x: {
                    title: "Rank in SSPI Static Data",
                    type: 'linear',
                    position: 'bottom'
                }, 
                y: {
                    title: "Indicator Raw Value",
                    type: 'linear',
                    position: 'left'
                }
            }
        }
    })
    return comparisonChart
}
comparisonTable = makeComparisonTable()
comparisonChart = makeComparisonChart()
handleComparisonDataUpdate({"value": "BIODIV"}, comparisonTable, comparisonChart)