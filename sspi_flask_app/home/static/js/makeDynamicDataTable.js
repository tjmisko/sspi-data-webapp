// https://tabulator.info/docs/5.5/columns#overview
// async function makeDynamicDataTable(IndicatorCode="BIODIV") {
//     var country_groups = await fetch('/api/v1/metadata')
//     var dynamic_data = await fetch('/api/v1/query/indicator/' + IndicatorCode + '?database=sspi_clean_api_data')
//     var country_group_data = await country_groups.json()
//     var dynamic_data_table = await dynamic_data.json()
//     console.log(country_group_data)
//     console.log(dynamic_data_table)
//     var table = new Tabulator("#dynamic-data-table", {
//         data:dynamic_data_table, //assign data to table
//         autoColumns:true, //create columns from data field names
//     });
// }
