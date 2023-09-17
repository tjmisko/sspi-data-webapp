$(".data-download-reveal").click(()=>{$(".data-download-form").slideDown();$(".data-download-reveal").slideUp();})
$(".data-download-close").click(()=>{$(".data-download-reveal").slideDown();$(".data-download-form").slideUp();})
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
function addWidget(){$("widget-menu")}
async function addWidget(widgettype){await $.get(`/widget/${widgettype}`,(data)=>{grid.addWidget({w:6,h:10,minW:4,minH:5,content:data,id:crypto.randomUUID()})})}
function removeWidget(el){widgetId=$(el).parents().eq(4).attr('gs-id')
grid.removeWidget($(`[gs-id=${widgetId}]`).get(0))}