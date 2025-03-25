function sleep(ms){return new Promise(resolve=>setTimeout(resolve,ms));}
function captureChart(chartObject,alpha=false){const textColorOriginal=chartObject.textColor
const gridColorOriginal=chartObject.gridColor
chartObject.textColor='#222'
chartObject.gridColor='#777'
chartObject.chart.update()
sleep(1000).then(()=>{if(alpha){html2canvas(chartObject.parentElement,{backgroundColor:null}).then(canvas=>{const link=document.createElement('a');link.download=chartObject.parentElement.id+'.png';link.href=canvas.toDataURL('image/png');link.click();});}else{html2canvas(chartObject.parentElement).then(canvas=>{const link=document.createElement('a');link.download=chartObject.parentElement.id+'.png';link.href=canvas.toDataURL('image/png');link.click();});}
chartObject.textColor=textColorOriginal
chartObject.gridColor=gridColorOriginal
chartObject.chart.update()})};class ColorMap{constructor(){this.SSPI="#FFD54F"
this.SUS="#28a745"
this.MS="#ff851b"
this.PG="#007bff"}
}
const SSPIColors=new ColorMap()
async function fetchComparisonData(country1,country2,country3){country_data=await fetch(`/api/v1/query/sspi_main_data_v3?CountryCode=${country1}&CountryCode=${country2}&CountryCode=${country3}`)}
function categoryComparison(chartCanvas,categoryCode,country_data){const chartConfig={type:'bar',data:data,options:{plugins:{title:{display:true,text:'Comparison of Category Scores'},},responsive:true,scales:{x:{stacked:true,},y:{stacked:true}}}};}
document.getElementById("comparison-country-selection-form").addEventListener("submit",function(event){event.preventDefault();const formData=new FormData(this);const data=Object.fromEntries(formData.entries());fetch('/compare/custom',{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(data)}).then(response=>response.json()).then(res=>{document.getElementById("comparison-result-section").innerHTML=res.html;window.custom_comparison_list=res.data;window.custom_comparison_list.forEach(cdata=>{new CategoryRadarChart(cdata.code,document.getElementById("radar-chart-flex-container"));});}).catch(error=>console.error("Error:",error));});$(".data-download-reveal").click(()=>{$(".data-download-form").slideDown();$(".data-download-reveal").slideUp();})
$(".data-download-close").click(()=>{$(".data-download-reveal").slideDown();$(".data-download-form").slideUp();})
class GlobeVisualization{constructor(){this.initalizeGlobe();}
initalizeGlobe(){const colorScale=d3.scaleSequentialSqrt(d3.interpolateYlOrRd);const getVal=feat=>feat.properties.GDP_MD_EST/Math.max(1e5,feat.properties.POP_EST);fetch("{{ url_for('client_bp.static', filename = 'globe_data.geojson') }}").then(res=>res.json()).then(countries=>{const maxVal=Math.max(...countries.features.map(getVal));colorScale.domain([0,maxVal]);console.log(countries.features.filter(d=>d.properties.ISO_A2!=='AQ'))
const world=Globe().globeImageUrl('//unpkg.com/three-globe/example/img/earth-night.jpg').backgroundColor("#1B2A3C").width("500").height("500").showGraticules(true).atmosphereColor("green").lineHoverPrecision(0).polygonsData(countries.features.filter(d=>d.properties.ISO_A2!=='AQ')).polygonAltitude(0.01).polygonCapColor(feat=>colorScale(getVal(feat))).polygonSideColor(()=>'rgba(0, 100, 0, 0.15)').polygonStrokeColor(()=>'#111').polygonLabel(({properties:d})=>`<div class="globegl-hover"<b>${d.ADMIN}(${d.ISO_A2}):</b><br/>GDP:<i>${d.GDP_MD_EST}</i>M$<br/>Population:<i>${d.POP_EST}</i></div>`).onPolygonHover(hoverD=>world.polygonAltitude(d=>d===hoverD?0.10:0.01).polygonCapColor(d=>d===hoverD?'#294b50':colorScale(getVal(d)))).polygonsTransitionDuration(200).pointOfView({lat:25,lng:60,altitude:2},500)
(document.getElementById('globeViz'))
world.controls().autoRotate=true
world.controls().autoRotateSpeed=0.3
world.controls().enableZoom=false;});}}
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