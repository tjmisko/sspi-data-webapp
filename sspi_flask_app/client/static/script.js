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
const chartArrowLabels={id:'chartArrowLabels',afterDraw(chart,args,optionVars){const{ctx,chartArea}=chart;ctx.save();ctx.fillStyle='#FF634799';ctx.font='bold 12px Arial';ctx.textAlign='center';const offset=10
const xLeftMid=(chartArea.left+chartArea.right+offset)/4;const xRightMid=3*(chartArea.left+chartArea.right-offset)/4;const yTop=(chartArea.top+chartArea.bottom)/10+5;ctx.fillText(optionVars.LeftCountry+" Higher",xLeftMid,yTop);ctx.fillStyle='#32CD3299';ctx.fillText(optionVars.RightCountry+" Higher",xRightMid,yTop);ctx.restore();}}
class StaticPillarDifferentialChart{constructor(BaseCountry,ComparisonCountry,PillarCode,parentElement){this.parentElement=parentElement;this.BaseCountry=BaseCountry;this.ComparisonCountry=ComparisonCountry;this.PillarCode=PillarCode;this.titleString=`Sustainability Score Differences(${ComparisonCountry}-${BaseCountry})`;this.initRoot()
this.initTitle()
this.initChartJSCanvas()
this.fetch().then(data=>{this.update(data)})}
colormap(diff){if(diff>0){return"#32CD3299"}else{return"#FF634799"}}
async fetch(){const response=await fetch(`/api/v1/static/differential/pillar/${this.PillarCode}?BaseCountry=${this.BaseCountry}&ComparisonCountry=${this.ComparisonCountry}`);return response.json();}
initRoot(){this.root=document.createElement('div')
this.root.classList.add('chart-section-pillar-differential')
this.parentElement.appendChild(this.root)}
initTitle(){this.title=document.createElement('h2')
this.title.classList.add('differential-chart-title')
this.title.textContent="Test Title"
this.root.appendChild(this.title)}
initChartJSCanvas(){this.canvas=document.createElement('canvas')
this.canvas.id=`pillar-differential-canvas-${this.PillarCode}-${this.BaseCountry}-${this.ComparisonCountry}`;this.canvas.width=300
this.canvas.height=300
this.context=this.canvas.getContext('2d')
this.root.appendChild(this.canvas)
this.chart=new Chart(this.context,{type:'bar',plugins:[chartArrowLabels],options:{indexAxis:'y',responsive:true,plugins:{legend:{display:false,},chartArrowLabels:{LeftCountry:this.BaseCountry,RightCountry:this.ComparisonCountry},tooltip:{callbacks:{title:function(tooltipItems){return`Category:${tooltipItems[0].raw.CategoryName}`;},label:function(tooltipItem){if(tooltipItem.raw.Diff>0){return`Difference:+${tooltipItem.formattedValue}`;}
return`Difference:${tooltipItem.formattedValue}`;},},backgroundColor:'rgba(0, 0, 0, 0.7)',titleColor:'#ffffff',bodyColor:'#ffcc00',padding:5}},parsing:{xAxisKey:'Diff',yAxisKey:'CategoryCode'},scales:{x:{beginAtZero:true,grid:{drawTicks:false},ticks:{color:'#bbb',stepSize:0.1},title:{display:true,color:'#bbb',},min:-1,max:1,},y:{ticks:{color:'#bbb',minRotation:90,maxRotation:90,align:'center',crossAlign:'center',},title:{padding:10,display:true,text:'Categories',color:'#bbb',},type:'category',reverse:false}}}})}
update(data){this.baseCCode=data.baseCCode
this.baseCName=data.baseCName
this.comparisonCCode=data.comparisonCCode
this.comparisonCName=data.comparisonCName
this.title.textContent=data.title
data.datasets.forEach(dataset=>{dataset.backgroundColor=dataset.data.map(item=>this.colormap(item.Diff))
dataset.borderColor=dataset.data.map(item=>this.colormap(item.Diff).slice(0,-2))
dataset.borderWidth=1})
this.chart.data.datasets=data.datasets
this.chart.options.scales.x.title.text=data.title
this.chart.labels=data.labels
this.chart.options.plugins.tooltip.callbacks.beforeLabel=(tooltipItem)=>{const base=`${this.baseCCode}Score:${tooltipItem.raw.baseScore.toFixed(3)}`;const comparison=`${this.comparisonCCode}Score:${tooltipItem.raw.comparisonScore.toFixed(3)}`;return[base,comparison];}
this.chart.update()}}
class CategoryRadarStatic{constructor(countryCode,parentElement,textColor="#bbb",gridColor="#cccccc33"){this.parentElement=parentElement
this.countryCode=countryCode
this.textColor=textColor
this.gridColor=gridColor
this.initRoot()
this.legend=this.initLegend()
this.initRoot()
this.initTitle()
this.initLegend()
this.initChartJSCanvas()
this.fetch().then(data=>{this.update(data)})}
initRoot(){this.root=document.createElement('div')
this.root.classList.add('radar-chart-box')
this.parentElement.appendChild(this.root)}
initTitle(){this.title=document.createElement('h3')
this.title.classList.add('radar-chart-title')
this.root.appendChild(this.title)}
initLegend(){this.legend=document.createElement('div')
this.legend.classList.add('radar-chart-legend-box')
this.root.appendChild(this.legend)}
initChartJSCanvas(){this.canvasContainer=document.createElement('div')
this.canvasContainer.classList.add('radar-chart-canvas-container')
this.canvas=document.createElement('canvas')
this.canvasContainer.appendChild(this.canvas)
this.canvas.width=300
this.canvas.height=300
this.context=this.canvas.getContext('2d')
this.root.appendChild(this.canvasContainer)
this.chart=new Chart(this.context,{type:'polarArea',options:{responsive:true,elements:{line:{borderWidth:3}},scales:{r:{pointLabels:{display:true,font:{size:10},color:this.textColor,centerPointLabels:true,padding:0},angleLines:{display:true,color:this.gridColor},grid:{color:this.gridColor,circular:true},ticks:{backdropColor:'rgba(0, 0, 0, 0)',clip:true,color:this.textColor,font:{size:8}},suggestedMin:0,suggestedMax:1}},plugins:{legend:{display:false,},tooltip:{backgroundColor:'#1B2A3Ccc',},}}})}
async fetch(){const response=await fetch(`/api/v1/static/radar/${this.countryCode}`)
return response.json();}
update(data){this.labelMap=data.labelMap
this.chart.data.labels=data.labels
this.ranks=data.ranks
this.chart.data.datasets=data.datasets
this.title.innerText=data.title
this.updateLegend(data)
this.chart.options.plugins.tooltip.callbacks.title=(context)=>{const categoryName=this.labelMap[context[0].label]
return categoryName}
this.chart.options.plugins.tooltip.callbacks.label=(context)=>{return["Category Score: "+context.raw.toFixed(3),"Category Rank: "+this.ranks[context.dataIndex].Rank,]}
this.chart.update()}
updateLegend(data){this.legendItems=data.legendItems
const pillarColorsAlpha=data.datasets.map(d=>d.backgroundColor)
const pillarColorsSolid=pillarColorsAlpha.map(c=>c.slice(0,7))
for(let i=0;i<this.legendItems.length;i++){const pillarLegendItem=document.createElement('div')
pillarLegendItem.classList.add('radar-chart-legend-item')
const pillarLegendCanvasContainer=document.createElement('div')
pillarLegendCanvasContainer.classList.add('radar-chart-legend-canvas-container')
const pillarLegendItemCanvas=document.createElement('canvas')
pillarLegendItemCanvas.width=150
pillarLegendItemCanvas.height=50
pillarLegendItemCanvas.classList.add('radar-chart-legend-item-canvas')
this.drawPillarLegendCanvas(pillarLegendItemCanvas,pillarColorsAlpha,pillarColorsSolid,i)
pillarLegendCanvasContainer.appendChild(pillarLegendItemCanvas)
pillarLegendItem.appendChild(pillarLegendCanvasContainer)
const pillarLegendItemText=document.createElement('div')
pillarLegendItemText.classList.add('radar-chart-legend-item-text')
pillarLegendItemText.innerText=this.legendItems[i].Name
pillarLegendItem.appendChild(pillarLegendItemText)
this.legend.appendChild(pillarLegendItem)}}
drawPillarLegendCanvas(pillarLegendItemCanvas,pillarColorsAlpha,pillarColorsSolid,i){const pillarLegendContext=pillarLegendItemCanvas.getContext('2d')
const shadedWidth=(pillarLegendItemCanvas.width*this.legendItems[i].Score).toFixed(0)
pillarLegendContext.strokeStyle=this.textColor
pillarLegendContext.linewidth=5
pillarLegendContext.beginPath()
pillarLegendContext.moveTo(0,0)
pillarLegendContext.lineTo(0,pillarLegendItemCanvas.height)
pillarLegendContext.moveTo(pillarLegendItemCanvas.width,0)
pillarLegendContext.lineTo(pillarLegendItemCanvas.width,pillarLegendItemCanvas.height)
pillarLegendContext.stroke()
pillarLegendContext.strokeStyle=this.gridColor
pillarLegendContext.linewidth=3
pillarLegendContext.beginPath()
const spacing=pillarLegendItemCanvas.width/10
pillarLegendContext.beginPath();for(let i=0;i<10;i++){const x=(i*spacing)
pillarLegendContext.moveTo(x,5)
pillarLegendContext.lineTo(x,pillarLegendItemCanvas.height)}
pillarLegendContext.stroke();pillarLegendContext.fillStyle=pillarColorsAlpha[i]
pillarLegendContext.fillRect(3,5,shadedWidth,pillarLegendItemCanvas.height-5)
pillarLegendContext.strokeStyle=pillarColorsSolid[i]
pillarLegendContext.linewidth=10
pillarLegendContext.strokeRect(3,5,shadedWidth,pillarLegendItemCanvas.height-5)}}
class DynamicMatrixChart{constructor(parentElement){this.parentElement=parentElement
this.initRoot()
this.initChartJSCanvas()
this.fetch().then(res=>{this.update(res)})}
initRoot(){this.root=document.createElement('div')
this.root.classList.add('chart-section-dynamic-matrix')
this.parentElement.appendChild(this.root)}
initChartJSCanvas(){this.canvas=document.createElement('canvas')
this.canvas.id='dynamic-line-chart-canvas'
this.canvas.width=400
this.canvas.height=400
this.context=this.canvas.getContext('2d')
this.root.appendChild(this.canvas)
this.chart=new Chart(this.context,{type:'matrix',options:{plugins:{legend:false,tooltip:{callbacks:{title(){return'Dynamic Data Status';},label(context){const v=context.dataset.data[context.dataIndex];if(v.problems){return["Issue:"+v.problems,'Country: '+v.CName,'Indicator: '+v.IName]}
return['Country: '+v.CName,'Indicator: '+v.IName,'Years: '+v.v];}}}}}})}
async fetch(){const response=await fetch(`/api/v1/dynamic/matrix`);return response.json();}
update(res){this.n_indicators=res.icodes.length;this.chart.data={datasets:[{label:'My Matrix',data:res.data,backgroundColor(context){const years=context.dataset.data[context.dataIndex].v;const load=context.dataset.data[context.dataIndex].to_be_loaded;const collect=context.dataset.data[context.dataIndex].collect;const compute=context.dataset.data[context.dataIndex].collect;if(years!=0){const alpha=(years+5)/40;return`rgba(15,200,15,${alpha})`;}
if(collect&&compute){return'#FFBF0066';}
if(load){return'#FFBF00';}
return"rgba(0, 0, 0, 0)";},borderColor(context){const problems=context.dataset.data[context.dataIndex].problems;const confident=context.dataset.data[context.dataIndex].confident;if(problems){return"rgba(255, 99, 132, 1)";}
if(confident){return`rgba(15,200,15,0.5)`;}},borderWidth:1,width:({chart})=>(chart.chartArea||{}).width/this.n_indicators-1,height:({chart})=>(chart.chartArea||{}).height/this.n_indicators-1}]}
this.chart.options.scales={x:{type:'category',labels:res.icodes,position:'top',ticks:{display:true},grid:{display:false}},y:{type:'category',labels:res.ccodes,offset:true,reverse:true,ticks:{display:true},grid:{display:false}}}
this.chart.update()}}
const endLabelPlugin={id:'endLabelPlugin',afterDatasetsDraw(chart){chart.data.datasets.forEach((dataset,i)=>{if(dataset.hidden){return;}
const meta=chart.getDatasetMeta(i);let lastNonNullIndex=meta.data.length-1;for(let j=meta.data.length;j>=0;j--){console.log(j)
if(meta.data[j]===undefined){continue}
console.log(meta.data[j])
if(meta.data[j].raw!==null){lastNonNullIndex=j
break}}
const lastPoint=meta.data[lastNonNullIndex];console.log(lastNonNullIndex,lastPoint)
const value=dataset.CCode;chart.ctx.save();chart.ctx.font='bold 14px Arial';chart.ctx.fillStyle=dataset.borderColor;chart.ctx.textAlign='left';chart.ctx.fillText(value,lastPoint.x+5,lastPoint.y+4);chart.ctx.restore();});}}
class DynamicLineChart{constructor(parentElement,IndicatorCode,CountryList=[]){this.parentElement=parentElement
this.IndicatorCode=IndicatorCode
this.CountryList=CountryList
this.pinnedArray=Array()
this.initRoot()
this.rigCountryGroupSelector()
this.initChartJSCanvas()
this.rigLegend()
this.fetch().then(data=>{this.update(data)})}
initRoot(){this.root=document.createElement('div')
this.root.classList.add('chart-section-dynamic-line')
this.parentElement.appendChild(this.root)
this.root.innerHTML=`<div class="chart-section-title-bar"><h2 class="chart-section-title">Dynamic Indicator Data</h2><div class="chart-section-title-bar-buttons"><button class="draw-button">Draw 10 Countries</button><button class="showall-button">Show All</button><button class="hideunpinned-button">Hide Unpinned</button></div></div>`;this.rigTitleBarButtons()}
rigTitleBarButtons(){this.drawButton=this.root.querySelector('.draw-button')
this.drawButton.addEventListener('click',()=>{this.showRandomN(10)})
this.showAllButton=this.root.querySelector('.showall-button')
this.showAllButton.addEventListener('click',()=>{this.showAll()})
this.hideUnpinnedButton=this.root.querySelector('.hideunpinned-button')
this.hideUnpinnedButton.addEventListener('click',()=>{this.hideUnpinned()})}
initChartJSCanvas(){this.canvas=document.createElement('canvas')
this.canvas.id='dynamic-line-chart-canvas'
this.canvas.width=400
this.canvas.height=200
this.context=this.canvas.getContext('2d')
this.root.appendChild(this.canvas)
this.chart=new Chart(this.context,{type:'line',options:{onClick:(event,elements)=>{elements.forEach(element=>{const dataset=this.chart.data.datasets[element.datasetIndex]
this.togglePin(dataset)})},datasets:{line:{spanGaps:true,segment:{borderWidth:2,borderDash:ctx=>{return ctx.p0.skip||ctx.p1.skip?[10,4]:[];}}}},plugins:{legend:{display:false,},endLabelPlugin:{}},layout:{padding:{right:40}},scales:{x:{ticks:{color:'#bbb',},type:"category",title:{display:true,text:'Year',color:'#bbb',font:{size:16}},},y:{ticks:{color:'#bbb',},beginAtZero:true,min:0,max:1,title:{display:true,text:'Indicator Score',color:'#bbb',font:{size:16}},}}},plugins:[endLabelPlugin]})}
rigCountryGroupSelector(){const container=document.createElement('div')
container.id='country-group-selector-container'
this.countryGroupContainer=this.root.appendChild(container)}
updateCountryGroups(){const numOptions=this.groupOptions.length;this.countryGroupContainer.style.setProperty('--num-options',numOptions);this.groupOptions.forEach((option,index)=>{const id=`option${index+1}`;const input=document.createElement('input');input.type='radio';input.id=id;input.name='options';input.value=option;if(index===0){input.checked=true;this.countryGroupContainer.style.setProperty('--selected-index',index);}
input.addEventListener('change',()=>{const countryGroupOptions=document.querySelectorAll(`#country-group-selector-container input[type="radio"]`);countryGroupOptions.forEach((countryGroup,index)=>{if(countryGroup.checked){this.countryGroupContainer.style.setProperty('--selected-index',index);this.showGroup(countryGroup.value)}});});const label=document.createElement('label');label.htmlFor=id;label.textContent=option;this.countryGroupContainer.appendChild(input);this.countryGroupContainer.appendChild(label);});const slider=document.createElement('div');slider.className='slider';this.countryGroupContainer.appendChild(slider);}
rigLegend(){const legend=document.createElement('legend')
legend.classList.add('dynamic-line-legend')
legend.innerHTML=`<div class="legend-title-bar"><h4 class="legend-title">Pinned Countries</h4><div class="legend-title-bar-buttons"><button class="saveprefs-button">Save Pins</button><button class="clearpins-button">Clear Pins</button></div></div><div class="legend-items"></div>`;this.savePrefsButton=legend.querySelector('.saveprefs-button')
this.savePrefsButton.addEventListener('click',()=>{this.sendPrefs()})
this.clearPinsButton=legend.querySelector('.clearpins-button')
this.clearPinsButton.addEventListener('click',()=>{this.clearPins()})
this.legend=this.root.appendChild(legend)
this.legendItems=this.legend.querySelector('.legend-items')}
updateLegend(){this.legendItems.innerHTML=''
this.pinnedArray.forEach((PinnedCountry)=>{this.legendItems.innerHTML+=`<div class="legend-item"><span>${PinnedCountry.CName}(<b style="color: ${PinnedCountry.borderColor};">${PinnedCountry.CCode}</b>)</span><button class="remove-button-legend-item"id="${PinnedCountry.CCode}-remove-button-legend">Remove</button></div>`})
this.legendItems.innerHTML+=`<div class="legend-item"><button class="add-country-button">Add Country</button></div>`;this.addCountryButton=this.legend.querySelector('.add-country-button')
this.addCountryButton.addEventListener('click',()=>{new SearchDropdown(this.addCountryButton,this.chart.data.datasets,this)})
let removeButtons=this.legendItems.querySelectorAll('.remove-button-legend-item')
removeButtons.forEach((button)=>{let CountryCode=button.id.split('-')[0]
button.addEventListener('click',()=>{this.unpinCountryByCode(CountryCode,true)})})}
async fetch(){const response=await fetch(`/api/v1/dynamic/line/${this.IndicatorCode}`)
try{return response.json()}catch(error){console.error('Error:',error)}}
update(data){this.chart.data=data
this.chart.data.labels=data.labels
this.chart.data.datasets=data.data
this.chart.options.plugins.title=data.title
if(data.chartPreferences.pinnedArray!==undefined){this.pinnedArray.push(...data.chartPreferences.pinnedArray)}else{this.pinnedArray=[]}
this.groupOptions=data.groupOptions
this.pinnedOnly=data.chartPreferences.pinnedOnly
this.updatePins()
this.updateLegend()
this.updateCountryGroups()
if(this.pinnedOnly){this.hideUnpinned()}
this.chart.update()}
updatePins(){if(this.pinnedArray.length===0){return}
this.chart.data.datasets.forEach(dataset=>{if(this.pinnedArray.map(cou=>cou.CCode).includes(dataset.CCode)){dataset.pinned=true
dataset.hidden=false}})
this.chart.update()}
showAll(){this.pinnedOnly=false
console.log('Showing all countries')
this.chart.data.datasets.forEach((dataset)=>{dataset.hidden=false})
this.chart.update({duration:0,lazy:false})}
showGroup(groupName){this.pinnedOnly=false
console.log('Showing group:',groupName)
this.chart.data.datasets.forEach((dataset)=>{if(dataset.CGroup.includes(groupName)|dataset.pinned){dataset.hidden=false}else{dataset.hidden=true}})
this.chart.update({duration:0,lazy:false})}
hideUnpinned(){this.pinnedOnly=true
console.log('Hiding unpinned countries')
this.chart.data.datasets.forEach((dataset)=>{if(!dataset.pinned){dataset.hidden=true}})
this.chart.update({duration:0,lazy:false})}
showRandomN(N=10){this.pinnedOnly=false
const activeGroup=this.groupOptions[this.countryGroupContainer.style.getPropertyValue('--selected-index')]
let availableDatasetIndices=[]
this.chart.data.datasets.filter((dataset,index)=>{if(dataset.CGroup.includes(activeGroup)){availableDatasetIndices.push(index)}})
console.log('Showing',N,'random countries from group',activeGroup)
this.chart.data.datasets.forEach((dataset)=>{if(!dataset.pinned){dataset.hidden=true}})
let shownIndexArray=availableDatasetIndices.sort(()=>Math.random()-0.5).slice(0,N)
shownIndexArray.forEach((index)=>{this.chart.data.datasets[index].hidden=false
console.log(this.chart.data.datasets[index].CCode,this.chart.data.datasets[index].CName)})
this.chart.update({duration:0,lazy:false})}
sendPrefs(){const activeGroup=this.groupOptions[this.countryGroupContainer.style.getPropertyValue('--selected-index')]
fetch(`/api/v1/dynamic/line/${this.IndicatorCode}`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({pinnedArray:this.pinnedArray,activeGroup:activeGroup,pinnedOnly:this.pinnedOnly})})}
pinCountry(dataset){if(dataset.pinned){return}
dataset.pinned=true
dataset.hidden=false
this.pinnedArray.push({CName:dataset.CName,CCode:dataset.CCode,borderColor:dataset.borderColor})
this.updateLegend()
this.chart.update()}
pinCountryByCode(CountryCode){this.chart.data.datasets.forEach(dataset=>{if(dataset.CCode===CountryCode){dataset.pinned=true
dataset.hidden=false
this.pinnedArray.push({CName:dataset.CName,CCode:dataset.CCode,borderColor:dataset.borderColor})}})
this.updateLegend()
this.chart.update()}
unpinCountry(dataset,hide=false){if(this.pinnedOnly){dataset.hidden=true}
dataset.pinned=false
this.pinnedArray=this.pinnedArray.filter((item)=>item.CCode!==dataset.CCode)
this.updateLegend()
this.chart.update()}
unpinCountryByCode(CountryCode,hide=false){this.chart.data.datasets.forEach(dataset=>{if(dataset.CCode===CountryCode){dataset.pinned=false
if(hide){dataset.hidden=true}
this.pinnedArray=this.pinnedArray.filter((item)=>item.CCode!==dataset.CCode)}})
this.updateLegend()
this.chart.update()}
togglePin(dataset){if(dataset.pinned){this.unpinCountry(dataset,false)}else{this.pinCountry(dataset,false)}
this.updateLegend()
this.chart.update()}
clearPins(){this.pinnedArray.forEach((PinnedCountry)=>{this.unpinCountryByCode(PinnedCountry.CCode,true)})
this.pinnedArray=Array()
this.updateLegend()}
dumpChartDataJSON(screenVisibility=true){const observations=this.chart.data.datasets.map(dataset=>{if(screenVisibility&&dataset.hidden){return[]}
return dataset.data.map((_,i)=>({"ItemCode":dataset.ICode,"CountryCode":dataset.CCode,"Score":dataset.scores[i],"Value":dataset.values[i],"Year":dataset.years[i]}));}).flat();const jsonString=JSON.stringify(observations,null,2);const blob=new Blob([jsonString],{type:'application/json'});const url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;a.download=this.IndicatorCode+'.json';document.body.appendChild(a);a.click();document.body.removeChild(a);URL.revokeObjectURL(url);}
dumpChartDataCSV(screenVisibility=true){const observations=this.chart.data.datasets.map(dataset=>{if(screenVisibility&&dataset.hidden){return[]}
return dataset.data.map((_,i)=>({"ItemCode":dataset.ICode,"CountryCode":dataset.CCode,"Score":dataset.scores[i].toString(),"Value":dataset.values[i].toString(),"Year":dataset.years[i].toString()}));}).flat();const csvString=Papa.unparse(observations);const blob=new Blob([csvString],{type:'text/csv'});const url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;a.download=this.IndicatorCode+'.csv';document.body.appendChild(a);a.click();document.body.removeChild(a);URL.revokeObjectURL(url);}}
class SearchDropdown{constructor(parentElement,datasets,parentChart){this.parentElement=parentElement
this.datasets=datasets
this.parentChart=parentChart
this.initResultsWindow()
this.initSearch()}
initResultsWindow(){const resultsWindow=document.createElement('div')
resultsWindow.classList.add('add-country-pin-results-window')
resultsWindow.classList.add('legend-item')
resultsWindow.style.display='none'
this.resultsWindow=this.parentElement.parentNode.parentNode.appendChild(resultsWindow)}
initSearch(){this.parentElement.innerHTML=`<form class="add-country-pin-search-form"><input type="text"name="Country"placeholder="Country"></form>`;this.textInput=this.parentElement.querySelector("input")
this.textInput.focus()
this.textInput.addEventListener("input",()=>this.runSearch())
this.formElement=this.parentElement.querySelector("form")
this.formElement.addEventListener("submit",(event)=>{event.preventDefault()
this.selectResultEnter()})}
selectResultEnter(){let CountryCode=this.readResults()
if(!CountryCode){return}
this.parentChart.pinCountryByCode(CountryCode)
this.closeResults()}
readResults(){let result=this.resultsWindow.querySelector('.add-country-pin-result')
let CountryCode=result.id.split('-')[0]
return CountryCode}
async runSearch(){const queryString=this.textInput.value
const options=await this.getOptions(queryString)
if(options.length===0){this.resultsWindow.style.display='none'
return}
this.resultsWindow.style.display='flex'
this.resultsWindow.innerHTML=''
options.forEach(option=>{const resultElement=document.createElement('div')
resultElement.classList.add('add-country-pin-result')
resultElement.id=option.CCode+'-add-country-pin-result'
resultElement.addEventListener('click',()=>{this.selectResultClick(option)
this.closeResults()})
const resultSpan=document.createElement('span')
resultSpan.classList.add('add-country-pin-button')
resultSpan.innerHTML=`${option.CName}(<b style="color: ${option.borderColor};">${option.CCode}</b>)`;resultElement.appendChild(resultSpan)
this.resultsWindow.appendChild(resultElement)})}
selectResultClick(option){this.parentChart.pinCountry(option)}
async getOptions(queryString,limit=10){queryString=queryString.toLowerCase()
if(!queryString){return[]}
let optionArray=Array()
for(let i=0;i<this.datasets.length;i++){const matched_name=this.datasets[i].CName.toLowerCase().includes(queryString)
const matched_code=this.datasets[i].CCode.toLowerCase().includes(queryString)
if(matched_code|matched_name){optionArray.push(this.datasets[i]);}
if(optionArray.length===limit){break;}}
return optionArray}
closeResults(){this.resultsWindow.remove()}}
class StaticOverallStackedBarChart{constructor(parentElement,colormap={}){this.parentElement=parentElement;this.textColor='#bbb';this.gridColor='#cccccc33';this.initRoot()
this.initTitle()
if(Object.keys(colormap).length===0){this.initColormap()}else{this.colormap=colormap}
this.createLegend()
this.initChartJSCanvas()
this.fetch().then(data=>{this.update(data)})}
async fetch(){const response=await fetch('/api/v1/static/stacked/sspi');return response.json();}
initRoot(){this.root=document.createElement('div')
this.root.classList.add('chart-section-overall-stack')
this.parentElement.appendChild(this.root)}
initTitle(){this.title=document.createElement('h4')
this.title.classList.add('stack-bar-title')
this.root.appendChild(this.title)}
initColormap(){this.colormap={"SUS":"#28a745","MS":"#ff851b","PG":"#007bff"}}
createLegend(){this.legend=document.createElement('div')
this.legend.classList.add('overall-stack-bar-legend')
this.root.appendChild(this.legend)}
initChartJSCanvas(){this.canvas=document.createElement('canvas')
this.canvas.id=`overall-stacked-bar-canvas`;this.canvas.width=1000
this.canvas.height=1000
this.context=this.canvas.getContext('2d')
this.root.appendChild(this.canvas)
this.chart=new Chart(this.context,{type:'bar',options:{plugins:{legend:{display:false,},tooltip:{intersect:false,padding:10,backgroundColor:'rgba(0, 0, 0, 0.7)',yAlign:'center',callbacks:{afterTitle(context){const info=context[0].dataset.info[context[0].dataIndex]
return[`SSPI Overall Score:${info.SSPIScore.toFixed(3)}`,`SSPI Overall Rank:${info.SSPIRank}`]},label(context){const info=context.dataset.info[context.dataIndex]
return['Pillar: '+info.IName,'Pillar Score: '+info.IName,'Pillar Rank: '+Number.parseFloat(info.Score).toFixed(3),'Rank: '+info.Rank,];}}}},responsive:true,indexAxis:'y',scales:{x2:{position:'top',display:true,ticks:{color:this.textColor,},grid:{display:false,},min:0,max:1,stacked:true,},x:{title:{display:true,text:'SSPI Score',color:this.textColor,},ticks:{color:this.textColor,},stacked:true,min:0,max:1,},y2:{position:'left',display:true,ticks:{color:this.textColor,callback:function(value,index,values){return index+1},padding:8,font:{size:12,weight:'bold'},},stacked:true,grid:{display:false,}},y:{position:'left',stacked:true,ticks:{color:this.textColor,},grid:{display:true,drawBorder:true,drawOnChartArea:true,color:function(context){return context.index%10===0?'#66666666':'rgba(0, 0, 0, 0)';}},},}},})}
update(data){this.chart.data=data.data
this.chart.data.datasets.forEach((dataset)=>{const color=this.colormap[dataset.label]
dataset.backgroundColor=color+"99"
dataset.borderColor=color})
this.title.innerText=data.title
this.chart.update()}}
function createDiagonalPattern(color){let shape=document.createElement('canvas')
shape.width=5
shape.height=5
let c=shape.getContext('2d')
c.strokeStyle=color
c.beginPath()
c.moveTo(1,0)
c.lineTo(5,4)
c.stroke()
c.beginPath()
c.moveTo(0,4)
c.lineTo(1,5)
c.stroke()
return c.createPattern(shape,'repeat')}
function createCrossHatch(color='black'){let shape=document.createElement('canvas')
shape.width=4
shape.height=4
let c=shape.getContext('2d')
c.strokeStyle=color
c.beginPath()
c.moveTo(0,2)
c.lineTo(4,2)
c.stroke()
return c.createPattern(shape,'repeat')}
class StaticPillarStackedBarChart{constructor(countryCodes,pillarCode,parentElement,colormap={}){this.parentElement=parentElement;this.textColor='#bbb';this.countryCodes=countryCodes;this.pillarCode=pillarCode;this.initRoot()
this.initTitle()
if(Object.keys(colormap).length===0){this.initColormap()}else{this.colormap=colormap}
this.createLegend()
this.initChartJSCanvas()
this.fetch().then(data=>{this.update(data)})}
async fetch(){let url_string=`/api/v1/static/stacked/pillar/${this.pillarCode}?`;for(let i=0;i<this.countryCodes.length;i++){url_string+=`CountryCode=${this.countryCodes[i]}&`;}
url_string=url_string.slice(0,-1);const response=await fetch(url_string);return response.json();}
initRoot(){this.root=document.createElement('div')
this.root.classList.add('chart-section-pillar-stack')
this.parentElement.appendChild(this.root)}
initTitle(){this.title=document.createElement('h4')
this.title.classList.add('stack-bar-title')
this.root.appendChild(this.title)}
initColormap(){const colors=["#f95d6a","#ff7c43","#ffa600","#665191","#a05195","#d45087"]
this.colormap={}
this.countryCodes.map((countryCode,index)=>{this.colormap[countryCode]=colors[index]})
this.patternState=null
this.patternCount=0}
createLegend(){this.legend=document.createElement('div')
this.legend.classList.add('stack-bar-legend')
this.countryCodes.map((countryCode)=>{const legendElement=document.createElement('div')
legendElement.classList.add('stack-bar-legend-element')
const legendBox=document.createElement('div')
legendBox.classList.add('legend-box')
legendBox.style.backgroundColor=this.colormap[countryCode]
legendElement.appendChild(legendBox)
const legendText=document.createElement('span')
legendText.id=countryCode+'-'+this.pillarCode+'-stack-bar-legend-text'
legendText.innerText=countryCode
legendElement.appendChild(legendText)
this.legend.appendChild(legendElement)})
this.root.appendChild(this.legend)}
initChartJSCanvas(){this.canvas=document.createElement('canvas')
this.canvas.id=`pillar-differential-canvas-${this.pillarCode}-${this.BaseCountry}-${this.ComparisonCountry}`;this.canvas.width=800
this.canvas.height=400
this.context=this.canvas.getContext('2d')
this.root.appendChild(this.canvas)
this.chart=new Chart(this.context,{type:'bar',options:{plugins:{legend:{display:false,},tooltip:{intersect:false,padding:10,backgroundColor:'rgba(0, 0, 0, 0.7)',yAlign:'center',callbacks:{title(context){if(context.length===0){return}
const currentCatName=context[0].label
if(currentCatName!==context[0].dataset.CatName){return null}
return context[0].dataset.CatCode+" - "+context[0].dataset.ICode;},label(context){const dataset=context.dataset
const currentCatName=context.label
if(currentCatName!==dataset.CatName){return null}
return['Country: '+dataset.CName+" "+dataset.flag,'Indicator: '+dataset.IName,'Score: '+Number.parseFloat(dataset.IScore).toFixed(3),'Rank: '+dataset.IRank,];}}}},responsive:true,barPercentage:3,interaction:{intersect:false,},scales:{x:{stacked:true,ticks:{color:this.textColor,},},y:{title:{display:true,text:'Category Score',color:this.textColor,},ticks:{color:this.textColor,},stacked:true,min:0,max:1,}}},})}
computePattern(dataset,color){let colorAlpha=color+"AA"
if(this.patternState===null){this.patternState=dataset.CatCode
return color}
if(this.patternState===dataset.CatCode){this.patternCount+=1
if(this.patternCount%3===1){return createDiagonalPattern(colorAlpha)}else if(this.patternCount%3===2){return createCrossHatch(colorAlpha)}
return colorAlpha}
this.patternState=dataset.CatCode
this.patternCount=0
return colorAlpha}
update(data){this.chart.data.datasets=data.datasets
this.chart.data.labels=data.labels
this.chart.data.datasets.forEach((dataset)=>{const color=this.colormap[dataset.CCode]
const pattern=this.computePattern(dataset,color)
dataset.backgroundColor=pattern
dataset.borderColor=color
dataset.borderWidth=1})
Array.from(this.legend.children).forEach((item)=>{const cou=item.querySelector('span').id.split('-')[0]
const flag=data.codeMap[cou].flag
const name=data.codeMap[cou].name
item.querySelector('span').innerText=name+" ("+cou+")"})
this.title.innerText=data.title
this.chart.update()}}
class ScoreBarStatic{constructor(parentElement,itemCode,backgroundColor=SSPIColors.SSPI,width=800,height=1000){this.parentElement=parentElement
this.itemCode=itemCode
this.textColor="#bbb"
this.gridColor="#cccccc33"
this.backgroundColor=backgroundColor+"99"
this.highlightColor="#ff0000ee"
this.borderColor=backgroundColor
this.width=width
this.height=height
this.initRoot()
this.initTitle()
this.initChartJSCanvas()
this.initSummaryBox()
this.fetch().then(data=>{this.update(data)})}
initRoot(){this.root=document.createElement('div')
this.root.classList.add('chart-container-bar-score-static')
this.parentElement.appendChild(this.root)}
initTitle(){this.title=document.createElement('h2')
this.title.classList.add('score-bar-chart-title')
this.root.appendChild(this.title)}
initChartJSCanvas(){this.canvas=document.createElement('canvas')
this.canvas.id=`score-bar-chart-canvas-${this.itemCode}`;this.canvas.width=this.width
this.canvas.height=this.height
this.context=this.canvas.getContext('2d')
this.root.appendChild(this.canvas)
this.chart=new Chart(this.context,{type:'bar',options:{onClick:(event,elements)=>{elements.forEach(element=>{this.toggleHighlight(this.chart.data.datasets[element.datasetIndex].info[element.index].CCode)
console.log(this.chart.data.datasets[element.datasetIndex].info[element.index].CCode)})},plugins:{legend:false,tooltip:{backgroundColor:'#1B2A3Ccc',callbacks:{label:function(context){const info=context.dataset.info[context.dataIndex]
return[`${info.IName}Score:${info.Score.toFixed(3)}`,`${info.IName}Rank:${info.Rank}`,`Year:${info.Year}`]}}},},scales:{x2:{position:'top',min:0,max:1,ticks:{color:this.textColor},label:{color:this.textColor,},grid:{display:false,},},x:{position:'bottom',min:0,max:1,ticks:{color:this.textColor},title:{display:true,font:{size:16,},color:this.textColor},label:{color:this.textColor,},grid:{color:this.gridColor,}},y2:{position:'left',ticks:{color:this.textColor,font:{size:12,weight:'bold'},callback:function(value,index,values){return this.chart.data.datasets[0].info[index].Rank},padding:8},},y:{position:'left',ticks:{color:this.textColor,},grid:{display:true,drawBorder:true,drawOnChartArea:true,color:function(context){return context.index%10===0?'#66666666':'rgba(0, 0, 0, 0)';}},},},indexAxis:'y',}})}
initSummaryBox(){this.summaryBox=document.createElement('div')
this.summaryBox.classList.add('score-bar-summary-box')
this.summaryBox.style.color=this.textColor
this.summaryBox.style.fontSize='16px'
this.root.appendChild(this.summaryBox)}
computeSummaryStats(data){const scores=data.datasets[0].info.map(info=>info.Score)
const meanScore=scores.reduce((a,b)=>a+b,0)/scores.length
const medianScore=scores.sort()[Math.floor(scores.length/2)]
const minScore=Math.min(...scores)
const maxScore=Math.max(...scores)
const sdScore=Math.sqrt(scores.reduce((a,b)=>a+(b-meanScore)**2,0)/(scores.length-1))
return{Mean:meanScore.toFixed(3),Median:medianScore.toFixed(3),Min:minScore.toFixed(3),Max:maxScore.toFixed(3),SD:sdScore.toFixed(3),}}
updateSummaryBox(summaryStats){for(const key in summaryStats){const stat=document.createElement('div')
stat.classList.add('score-bar-summary-stat')
stat.innerHTML=`${key}:<b>${summaryStats[key]}</b>`;this.summaryBox.appendChild(stat)}}
async fetch(){const response=await fetch(`/api/v1/static/bar/score/${this.itemCode}`);return response.json();}
getStoredHighlights(){let highlights=[]
if(localStorage.getItem('scoreBarHighlights')===null){highlights=[]}else{highlights=localStorage.getItem('scoreBarHighlights').split(',')}
return highlights}
setStoredHighlights(highlights){localStorage.setItem('scoreBarHighlights',highlights)}
clearVisibleHighlights(){this.chart.data.datasets[0].backgroundColor=Array(49).fill(this.backgroundColor)}
setVisibleHighlights(highlights){this.clearVisibleHighlights()
highlights.forEach(countryCode=>{this.addVisibleHighlight(countryCode)})}
addVisibleHighlight(countryCode){const index=this.chart.data.datasets[0].info.findIndex(info=>info.CCode===countryCode)
this.chart.data.datasets[0].backgroundColor[index]=this.highlightColor
this.chart.update()}
removeVisibleHighlight(countryCode){const index=this.chart.data.datasets[0].info.findIndex(info=>info.CCode===countryCode)
this.chart.data.datasets[0].backgroundColor[index]=this.backgroundColor
this.chart.update()}
updateHighlights(){const highlights=this.getStoredHighlights()
this.setVisibleHighlights(highlights)
this.propagateHighlights()}
syncHighlights(){const highlights=this.getStoredHighlights()
this.setVisibleHighlights(highlights)}
initHighlights(){let highlights=this.getStoredHighlights()
this.setVisibleHighlights(highlights)}
removeStoredHighlight(countryCode){let highlights=this.getStoredHighlights()
highlights=highlights.filter(highlight=>highlight!==countryCode)
this.setStoredHighlights(highlights)}
addStoredHighlight(countryCode){let highlights=this.getStoredHighlights()
if(highlights.includes(countryCode)){return}
highlights.push(countryCode)
this.setStoredHighlights(highlights)}
toggleHighlight(countryCode){let highlights=this.getStoredHighlights()
if(highlights.includes(countryCode)){this.removeVisibleHighlight(countryCode)
this.removeStoredHighlight(countryCode)}else{this.addVisibleHighlight(countryCode)
this.addStoredHighlight(countryCode)}
this.updateHighlights()}
propagateHighlights(){window.chartObjectRegistry.forEach(chartObject=>{if(chartObject!==this){chartObject.syncHighlights()}})}
update(data){this.chart.data=data.data
this.chart.data.datasets[0].backgroundColor=Array(49).fill(this.backgroundColor)
this.chart.data.datasets[0].borderColor=Array(49).fill(this.borderColor)
this.chart.data.datasets[0].borderWidth=2
this.title.innerText=data.title
this.chart.options.scales.x.title.text=data.xTitle
this.initHighlights()
this.updateSummaryBox(this.computeSummaryStats(data.data))
this.chart.update()}}