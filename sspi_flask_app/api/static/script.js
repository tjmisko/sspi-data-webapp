async function DatabaseStatus(database){
    let response = await fetch('/api/v1/database/' + database +'/status')
}

async function handleQuery(IndicatorCode){
    $.get('/api/v1/IndicatorCode', 
    (data)=>{
        $("#" + IndicatorCode + ".results-box").children(".")
    });
    $("#" + IndicatorCode + ".results-box").style.display = "block"
    $("#" + IndicatorCode + ".results-box").children(".").append("waiting")
}