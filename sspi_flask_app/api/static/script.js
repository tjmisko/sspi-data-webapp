async function DatabaseStatus(database){
    let response = await fetch('/api/v1/database/' + database +'/status')
}

function closeBox(obj) {
    $(obj).parent(".results-box").hide()
}

async function handleQuery(IndicatorCode){
    $.get(`/api/v1/query/indicator/${IndicatorCode}`, 
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
    // (e) => {
    //     $(`#${IndicatorCode}.results-box`).children(".return-content").text(e.data)
    //     if (e.data === "Collection complete") {message_handler.close()}
    // }
}

function handleCompute(IndicatorCode) {
    $.get(`/api/v1/compute/${IndicatorCode}`, 
        (data)=>{
            console.log(data)
            $("#" + IndicatorCode + ".results-box")
                .children(".return-content")
                .empty()
                .append(JSON.stringify(data, null, 2))
        });
    $(`#${IndicatorCode}.results-box`).show()
    $("#" + IndicatorCode + ".results-box").children(".return-content").empty().append("processing")

}