async function makeIndicatorTable() {
    var tabledata = await fetch('/api/v1/metadata/indicator_table')
    var table = new Tabulator("#example-table", {
        data:tabledata, //assign data to table
        autoColumns:true, //create columns from data field names
    });
}

makeIndicatorTable()
