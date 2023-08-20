var table = new Tabulator("#api-link-coverage-data-table", {
    ajaxURL:"/api/v1/api_coverage", //ajax URL
    columns:[
        {title: "Indicator Code" , field:"IndicatorCode", formatter:"textarea"},
        {title: "Collect Method Implemented" , field:"collect_implemented", formatter: "tickCross", hozAlign:"center"},
        {title: "Compute Method Implemented" , field:"compute_implemented", formatter: "tickCross", hozAlign:"center"}
    ]
});

// // https://tabulator.info/docs/5.5/columns#overview