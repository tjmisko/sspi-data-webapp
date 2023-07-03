

var table = new Tabulator("#dynamic-data-table", {
    ajaxURL:"/api/v1/coverage/BIODIV", //ajax URL
    height: "400px",
    headerSortClickElement:"icon",
    columns:[
        {title: "Country Name", field:"CountryName", formatter:"string"},
        {title: "Country Code", field:"CountryCode", formatter:"string"},
        {title: 2000, field: "2000", formatter:"string"},
        {title: 2001, field: "2001", formatter:"string"},
        {title: 2002, field: "2002", formatter:"string"},
        {title: 2003, field: "2003", formatter:"string"},
        {title: 2004, field: "2004", formatter:"string"},
        {title: 2005, field: "2005", formatter:"string"},
        {title: 2006, field: "2006", formatter:"string"},
        {title: 2007, field: "2007", formatter:"string"},
        {title: 2008, field: "2008", formatter:"string"},
        {title: 2009, field: "2009", formatter:"string"},
        {title: 2010, field: "2010", formatter:"string"},
        {title: 2011, field: "2011", formatter:"string"},
        {title: 2012, field: "2012", formatter:"string"},
        {title: 2013, field: "2013", formatter:"string"},
        {title: 2014, field: "2014", formatter:"string"},
        {title: 2015, field: "2015", formatter:"string"},
        {title: 2016, field: "2016", formatter:"string"},
        {title: 2017, field: "2017", formatter:"string"},
        {title: 2018, field: "2018", formatter:"string"},
        {title: 2019, field: "2019", formatter:"string"},
        {title: 2020, field: "2020", formatter:"string"},
        {title: 2021, field: "2021", formatter:"string"},
        {title: 2022, field: "2022", formatter:"string"}
    ]
});