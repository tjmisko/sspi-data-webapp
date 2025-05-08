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
        dbox.innerText = description
    }

    update(data) {
        this.chart.data = data
        this.chart.data.labels = data.labels
        this.chart.data.datasets = data.data
        this.chart.options.plugins.title = data.title
        let prefs = data.chartPreferences !== undefined ? data.chartPreferences : {};
        if (Object.keys(prefs).length === 0) {
            prefs.pinnedArray = []
            prefs.pinnedOnly = false
        }
        if (prefs.pinnedArray !== undefined) {
            this.pinnedArray.push(...prefs.pinnedArray)
        } else {
            this.pinnedArray = []
        }
        this.groupOptions = data.groupOptions
        this.pinnedOnly = prefs.pinnedOnly
        this.updatePins()
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
