async function DatabaseStatus(database){
    let response = await fetch('/api/v1/database/' + database +'/status')
}

async function handleQuery(IndicatorCode){
    $.get('/api/v1/query/indicator/' + IndicatorCode, 
        (data)=>{
            $("#" + IndicatorCode + ".results-box")
                .children(".return-content")
                .empty()
                .append("finished")
        });
    console.log()
    $(`#${IndicatorCode}.results-box`).show()
    $("#" + IndicatorCode + ".results-box").children(".return-content").empty().append("waiting")
}