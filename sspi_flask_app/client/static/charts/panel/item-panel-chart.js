class ItemPanelChart extends PanelChart {
    constructor(parentElement, { CountryList = [], endpointURL = '', width = 400, height = 300 } = {} ) {
        super(parentElement, { CountryList: CountryList, endpointURL: endpointURL, width: width, height: height })
    }

    rigItemInfoBox() {
        const infoBox = document.createElement('div')
        infoBox.classList.add('item-panel-info-box')
        this.root.appendChild(infoBox)
    }

    updateDescription(description) {
        const dbox = this.root.querySelector('.item-panel-info-box')
        let identifiersHTML = ''
        let code = ''
        let desc = ''
        for (const [k, v] of Object.entries(description)) {
            if (k === 'Description') {
                desc = v
            } 
            if (k === 'ItemCode' || k === 'IntermediateCode') {
                code = v
            }
            identifiersHTML += `<li class="item-panel-info-box-element"><b>${k}</b>:<span class="item-panel-info-box-value">${v}</span></li>`
        }
        dbox.innerHTML = `
            <p class="item-panel-info-box-title"> </b>${code}</b>: ${desc}</p>
            <ul class="item-panel-info-box-list">${identifiersHTML}</ul>
        `;
    }

    update(data) {
        this.chart.data = data
        this.chart.data.labels = data.labels
        this.chart.data.datasets = data.data
        this.chart.options.plugins.title = data.title
        this.groupOptions = data.groupOptions
        this.pinnedOnly = false
        this.getPins()
        this.updateLegend()
        this.rigItemInfoBox()
        this.updateDescription(data.description)
        this.updateCountryGroups()
        if (this.pinnedOnly) {
            this.hideUnpinned()
        }
        this.chart.options.scales.y.min = data.yMin
        this.chart.options.scales.y.max = data.yMax
        if (data.hasScore) {
            this.yAxisScale = "score"
            this.rigTitleBarScaleToggle()
        }
        this.chart.update()
    }
}
