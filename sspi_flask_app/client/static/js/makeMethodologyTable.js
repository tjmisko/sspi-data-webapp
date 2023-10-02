
var dynamicDataTable = new Tabulator("#methodology-indicator-table", {
    ajaxURL:"/api/v1/query/metadata/indicator_details", //ajax URL
    headerSortClickElement:"icon",
    groupBy: ["PillarCode", "CategoryCode"],
    groupStartOpen: [true, false],
    columns: [
        {title: "Indicator", field: "Indicator"},
        {title: "Indicator Code", field: "IndicatorCodes"},
        {title: "Indicator Description", field: "Description"},
        // {title: "xx", field: "yy"},
        // {title: "xx", field: "yy"},
        // {title: "xx", field: "yy"},
        // {title: "xx", field: "yy"},
        // {title: "xx", field: "yy"},
    ] 
});

