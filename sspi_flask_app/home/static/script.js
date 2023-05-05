console.log("makeGraph.js loaded with chart.js version: "+Chart.version);const BarChartCanvas=document.getElementById('BarChart');const BarChart=new Chart(BarChartCanvas,{type:'bar',data:{},options:{}});makeBarChart('BIODIV')
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
async function makeIndicatorTable(){var tabledata=[{id:1,name:"Oli Bob",progress:12,gender:"male",rating:1,col:"red",dob:"19/02/1984",car:1},{id:2,name:"Mary May",progress:1,gender:"female",rating:2,col:"blue",dob:"14/05/1982",car:true},{id:3,name:"Christine Lobowski",progress:42,gender:"female",rating:0,col:"green",dob:"22/05/1982",car:"true"},{id:4,name:"Brendon Philips",progress:100,gender:"male",rating:1,col:"orange",dob:"01/08/1980"},{id:5,name:"Margret Marmajuke",progress:16,gender:"female",rating:5,col:"yellow",dob:"31/01/1999"},{id:6,name:"Frank Harbours",progress:38,gender:"male",rating:4,col:"red",dob:"12/05/1966",car:1},];var table=new Tabulator("#example-table",{data:tabledata,autoColumns:true,});}
makeIndicatorTable()