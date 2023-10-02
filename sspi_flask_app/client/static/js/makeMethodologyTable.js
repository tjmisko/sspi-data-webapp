
var dynamicDataTable = new Tabulator("#methodology-indicator-table", {
    ajaxURL:"/api/v1/query/metadata/indicator_details", //ajax URL
    headerSortClickElement:"icon",
    groupBy: ["Pillar", "Category"],
    maxHeight: "100%",
    groupStartOpen: [true, false],
    columns: [
        {title: "Indicator", field: "Indicator", formatter: "textarea", width: 200},
        {title: "Code", field: "IndicatorCodes", width: 75},
        {title: "Indicator Description", field: "Description", formatter: "textarea", width: 400},
        // {title: "xx", field: "yy"},
        // {title: "xx", field: "yy"},
        // {title: "xx", field: "yy"},
        // {title: "xx", field: "yy"},
        // {title: "xx", field: "yy"},
    ] 
});

