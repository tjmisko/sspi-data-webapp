$(".data-download-reveal").click(()=>{$(".data-download-form").slideDown();$(".data-download-reveal").slideUp();})
$(".data-download-close").click(()=>{$(".data-download-reveal").slideDown();$(".data-download-form").slideUp();})
var table=new Tabulator("#api-link-coverage-data-table",{ajaxURL:"/api/v1/api_coverage",columns:[{title:"Indicator Code",field:"IndicatorCode",formatter:"textarea"},{title:"Collect Method Implemented",field:"collect_implemented",formatter:"tickCross",hozAlign:"center"},{title:"Compute Method Implemented",field:"compute_implemented",formatter:"tickCross",hozAlign:"center"}]});const BarChartCanvas=document.getElementById('BarChart');const BarChart=new Chart(BarChartCanvas,{type:'bar',data:{},options:{}});makeBarChart('BIODIV')
raw=false
async function makeBarChart(IndicatorCode){let response=await fetch('/api/v1/query/indicator/'+IndicatorCode)
let indicator_data=await response.json()
indicator_data.sort((a,b)=>b.RANK-a.RANK)
let y_axis=raw?getRaw(indicator_data):getScores(indicator_data)
BarChart.data={labels:getCountries(indicator_data),datasets:[{datacode:IndicatorCode,label:indicator_data[0].IndicatorNameShort,data:y_axis,backgroundColor:'rgb(255, 99, 132)',borderColor:'rgb(255, 99, 132)',borderWidth:1}]}
BarChart.options={scaleShowValues:true,layout:{padding:20},scales:{xAxes:[{id:'x',type:'category',title:{display:true,text:'Country'},ticks:{autoskip:true,}}]}}
BarChart.update();}
function toggleRaw(){raw=!raw
try{IndicatorCode=BarChart.data.datasets[0].datacode
makeBarChart(IndicatorCode);}catch(TypeError){console.log("No Chart Loaded!\n",TypeError)
IndicatorCode=null;}}
function getCountries(indicator_data){return indicator_data.map(data=>data.Country)}
function getScores(indicator_data){return indicator_data.map(data=>data.SCORE)}
function getRaw(indicator_data){return indicator_data.map(data=>data.RAW)}
var dynamicDataTable=new Tabulator("#dynamic-data-table",{ajaxURL:"/api/v1/dynamic/BIODIV",height:"400px",headerSortClickElement:"icon",columns:[{title:"Country Name",field:"CountryName",formatter:"string"},{title:"Country Code",field:"CountryCode",formatter:"string"},{title:2000,field:"2000",formatter:"string"},{title:2001,field:"2001",formatter:"string"},{title:2002,field:"2002",formatter:"string"},{title:2003,field:"2003",formatter:"string"},{title:2004,field:"2004",formatter:"string"},{title:2005,field:"2005",formatter:"string"},{title:2006,field:"2006",formatter:"string"},{title:2007,field:"2007",formatter:"string"},{title:2008,field:"2008",formatter:"string"},{title:2009,field:"2009",formatter:"string"},{title:2010,field:"2010",formatter:"string"},{title:2011,field:"2011",formatter:"string"},{title:2012,field:"2012",formatter:"string"},{title:2013,field:"2013",formatter:"string"},{title:2014,field:"2014",formatter:"string"},{title:2015,field:"2015",formatter:"string"},{title:2016,field:"2016",formatter:"string"},{title:2017,field:"2017",formatter:"string"},{title:2018,field:"2018",formatter:"string"},{title:2019,field:"2019",formatter:"string"},{title:2020,field:"2020",formatter:"string"},{title:2021,field:"2021",formatter:"string"},{title:2022,field:"2022",formatter:"string"}],initialSort:[{column:"CountryName",dir:"asc"}]});async function makeIndicatorTable(){var tabledata=await fetch('/api/v1/metadata/indicator_table')
var table=new Tabulator("#example-table",{data:tabledata,autoColumns:true,});}
makeIndicatorTable()
function closeThisWidget(){$(this).parent().parent().remove()}