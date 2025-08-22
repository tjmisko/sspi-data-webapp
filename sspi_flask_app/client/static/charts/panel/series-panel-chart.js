class SeriesPanelChart extends PanelChart {
    constructor(parentElement, { CountryList = [], endpointURL = '', width = 400, height = 300 } = {} ) {
        super(parentElement, { CountryList: CountryList, endpointURL: endpointURL, width: width, height: height })
    }

    updateDescription(description) {
        const dbox = this.root.querySelector('.dynamic-item-description')
        let identifiersHTML = ''
        let code = ''
        let desc = ''
        for (const [k, v] of Object.entries(description)) {
            if (k === 'Description') {
                desc = v
            } 
            if (k === 'ItemCode' || k === 'DatasetCode') {
                code = v
            }
            identifiersHTML += `<li class="item-detail-element"><b>${k}</b>: <span class="item-detail-value">${v}</span></li>`
        }
        dbox.innerHTML = `
            <div class="item-info-title"><strong>${code}</strong>: ${desc}</div>
            <ul class="item-detail-list">${identifiersHTML}</ul>
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
