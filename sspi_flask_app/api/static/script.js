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
        ajaxURL:"/api/v1/compare/BIODIV}", //ajax URL
        headerSortClickElement:"icon",
        // maxHeight: "100%",
        columns: [
            {title: "Indicator", field: "a"},
            {title: "Code", field: "a"},
            // {title: "Policy", field: "Policy", formatter: "textarea", width: 200},
            // {title: "Indicator Description", field: "Description", formatter: "textarea", width: 400},
            // {title: "Goalposts", field: "GoalpostString"},
            // {title: "Year", field: "SourceYear_sspi_main_data_v3"},
            // {title: "", field: "yy"},
            // {title: "xx", field: "yy"},
        ] 
    });
}

function updateComparisonTable(IndicatorCode, comparisonTable) {
    // takes in an IndicatorCode from the form submission and updates
    $().get(`/api/v1/compare/${IndicatorCode}`, (data) => {comparisonTable.setData(data)})
}
makeComparisonTable()