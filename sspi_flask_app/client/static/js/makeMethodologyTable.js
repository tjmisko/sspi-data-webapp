
var dynamicDataTable = new Tabulator("#methodology-indicator-table", {
    ajaxURL:"/api/v1/query/metadata/indicator_info", //ajax URL
    headerSortClickElement:"icon",
});

