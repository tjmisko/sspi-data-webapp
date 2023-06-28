async function makeAPICoverageReport() {
    var endpoint_coverage = await fetch('/api/v1/api_coverage')
    var endpoint_coverage_table = await endpoint_coverage.json()
    console.log(endpoint_coverage_table)
    var table = new Tabulator("#api-link-coverage-data-table", {
        data:endpoint_coverage_table, //assign data to table
        autoColumns:true, //create columns from data field names
    });
}

makeAPICoverageReport()
