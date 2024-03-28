$(".data-download-reveal").click(()=>{$(".data-download-form").slideDown();$(".data-download-reveal").slideUp();})
$(".data-download-close").click(()=>{$(".data-download-reveal").slideDown();$(".data-download-form").slideUp();})
const StaticChartData=fetch('/api/v1/static/{{IndicatorCode}}')
const StaticChartDataJson=StaticChartData.then(response=>response.json())
const StaticCanvas=document.getElementById('static-chart')
const StaticChart=new Chart(StaticCanvas,{options:{type:'bar',scales:{y:{beginAtZero:true}}}})
StaticChartDataJson.then(indicator_data=>{console.log(indicator_data)
StaticChart.data={datasets:[{label:'Static Data',data:[{x:1,y:2},{x:2,y:4}],backgroundColor:'rgba(255, 99, 132, 0.2)',borderColor:'rgba(255, 99, 132, 1)',borderWidth:1}]}}).catch(error=>{console.log(error)})
const DynamicChartData=fetch('/api/v1/dynamic/{{IndicatorCode}}')
const DynamicChartDataJson=DynamicChartData.then(response=>response.json())
const DynamicCanvas=document.getElementById('dynamic-chart')
const DynamicChart=new Chart(DynamicCanvas,{options:{type:'bar',scales:{y:{beginAtZero:true}}}})
console.log(DynamicCanvas)
console.log(DynamicChart)
DynamicChartDataJson.then(indicator_data=>{console.log(indicator_data)
DynamicChart.data={datasets:[{label:'Static Data',data:[{x:1,y:2},{x:2,y:4}],backgroundColor:'rgba(255, 99, 132, 0.2)',borderColor:'rgba(255, 99, 132, 1)',borderWidth:1}]}}).catch(error=>{console.log(error)})
const ctx=document.getElementById('myChart');new Chart(ctx,{type:'bar',data:{labels:['Red','Blue','Yellow','Green','Purple','Orange'],datasets:[{label:'# of Votes',data:[12,19,3,5,2,3],borderWidth:1}]},options:{scales:{y:{beginAtZero:true}}}});function setupBarChart(){let Chart=$("#izzy")[0].getContext('2d')
console.log(Chart)
const BarChart=new Chart(BarChartCanvas,{type:'bar',data:{},options:{}})
makeBarChart(BarChart,"BIODIV")}
async function makeBarChart(BarChart,IndicatorCode){let response=await fetch('/api/v1/query/sspi_clean_api_data?IndicatorCode='+IndicatorCode)
let indicator_data=await response.json()
indicator_data.sort((a,b)=>b.RANK-a.RANK)
console.log(indicator_data)
let y_axis=raw?getRaw(indicator_data):getScores(indicator_data)
BarChart.data={labels:getCountries(indicator_data),datasets:[{datacode:IndicatorCode,label:indicator_data[0].IndicatorNameShort,data:y_axis,backgroundColor:'rgb(255, 99, 132)',borderColor:'rgb(255, 99, 132)',borderWidth:1}]}
BarChart.options={elements:{bar:{borderWidth:2,}},scaleShowValues:true,layout:{padding:10},responsive:true,plugins:{legend:{display:false,}},maintainAspectRatio:false,scales:{xAxes:[{id:'x',type:'category',title:{display:true,text:'Country'},ticks:{autoskip:true,}}]}}
BarChart.update();}
function toggleRaw(){raw=!raw
try{IndicatorCode=BarChart.data.datasets[0].datacode
makeBarChart(IndicatorCode);}catch(TypeError){console.log("No Chart Loaded!\n",TypeError)
IndicatorCode=null;}}
function getCountries(indicator_data){return indicator_data.map(data=>data.Country)}
function getScores(indicator_data){return indicator_data.map(data=>data.SCORE)}
function getRaw(indicator_data){return indicator_data.map(data=>data.RAW)}
setupBarChart()
raw=false
async function makeBarChart(BarChart,IndicatorCode){let response=await fetch('/api/v1/query/sspi_clean_api_data?IndicatorCode='+IndicatorCode)
let indicator_data=await response.json()
indicator_data.sort((a,b)=>b.RANK-a.RANK)
console.log(indicator_data)
let y_axis=raw?getRaw(indicator_data):getScores(indicator_data)
BarChart.data={labels:getCountries(indicator_data),datasets:[{datacode:IndicatorCode,label:indicator_data[0].IndicatorNameShort,data:y_axis,backgroundColor:'rgb(255, 99, 132)',borderColor:'rgb(255, 99, 132)',borderWidth:1}]}
BarChart.options={elements:{bar:{borderWidth:2,}},scaleShowValues:true,layout:{padding:10},responsive:true,plugins:{legend:{display:false,}},maintainAspectRatio:false,scales:{xAxes:[{id:'x',type:'category',title:{display:true,text:'Country'},ticks:{autoskip:true,}}]}}
BarChart.update();}
function toggleRaw(){raw=!raw
try{IndicatorCode=BarChart.data.datasets[0].datacode
makeBarChart(IndicatorCode);}catch(TypeError){console.log("No Chart Loaded!\n",TypeError)
IndicatorCode=null;}}
function getCountries(indicator_data){return indicator_data.map(data=>data.Country)}
function getScores(indicator_data){return indicator_data.map(data=>data.SCORE)}
function getRaw(indicator_data){return indicator_data.map(data=>data.RAW)}
var dynamicDataTable=new Tabulator("#methodology-indicator-table",{ajaxURL:"/api/v1/query/metadata/indicator_details",headerSortClickElement:"icon",groupBy:["Pillar","Category"],maxHeight:"100%",groupStartOpen:[true,false],columns:[{title:"Indicator",field:"Indicator",formatter:"textarea",width:200},{title:"Code",field:"IndicatorCodes",width:75},{title:"Policy",field:"Policy",formatter:"textarea",width:200},{title:"Indicator Description",field:"Description",formatter:"textarea",width:400},{title:"Goalposts",field:"GoalpostString"},{title:"Year",field:"SourceYear_sspi_main_data_v3"},]});$(".widget-type-options-menu").hide()
function revealWidgetOptions(){$(".widget-type-options-menu").slideToggle(0.1)}
async function addWidget(widgettype){await $.get(`/widget/${widgettype}`,(data)=>{gsId=crypto.randomUUID()
grid.addWidget({w:6,h:20,minW:4,minH:5,content:data,id:gsId});revealWidgetOptions();}).then(()=>{if(widgettype==="barchart"){setupBarChart(gsId)}});}
function removeWidget(el){widget=$(el).parents('.grid-stack-item')
console.log(widget.attr('gs-id'))
grid.removeWidget(widget.get(0))}
function fullscreenWidget(el){widget=$(el).parents('.grid-stack-item')
console.log(widget.get(0))
console.log(widget.attr('gs-id'))
widgetW=widget.attr('gs-w')
widgetH=widget.attr('gs-h')
console.log(widgetW,widgetH)
fullscreenHeight=Math.floor(0.95*window.innerHeight/25)
grid.update(widget.get(0),{w:12,h:fullscreenHeight})
window.scrollTo(0,widget.offset().top-10)
fullscreenButton=widget.find(".fullscreen-button").attr("onclick",`returnWidgetToOriginalSize(this,${widgetW},${widgetH})`)}
function returnWidgetToOriginalSize(el,widgetW,widgetH){$(el).parents().eq(2).attr('gs-id')
widget=$(`[gs-id=${widgetId}]`).get(0)
grid.update(widget,{w:widgetW,h:widgetH})
fullscreenButton=$(`[gs-id=${widgetId}]`).find(".fullscreen-button").attr("onclick","fullscreenWidget(this)")}
function setupBarChart(gsId){let BarChartCanvas=$(`[gs-id=${gsId}]`).find(".bar-chart").get(0)
console.log(BarChartCanvas)
const BarChart=new Chart(BarChartCanvas,{type:'bar',data:{},options:{}})
makeBarChart(BarChart,"BIODIV")}