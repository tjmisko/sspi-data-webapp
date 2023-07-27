async function DatabaseStatus(database){
    let response = await fetch('/api/v1/database/' + database +'/status')
}

function closeBox(obj) {
    $(obj).parent(".results-box").hide()
}

async function handleQuery(IndicatorCode){
    $.get('/api/v1/query/indicator/' + IndicatorCode, 
        (data)=>{
            console.log(data)
            $("#" + IndicatorCode + ".results-box")
                .children(".return-content")
                .empty()
                .append(JSON.stringify(data, null, 2))
        });
    console.log()
    $(`#${IndicatorCode}.results-box`).show()
    $("#" + IndicatorCode + ".results-box").children(".return-content").empty().append("waiting")
}