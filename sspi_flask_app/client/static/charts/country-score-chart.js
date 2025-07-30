class CountryScoreChart {
    constructor(parentElement, countryCode, rootItemCode, { colorProvider = SSPIColors } ) {
        this.parentElement = parentElement// ParentElement is the element to attach the canvas to
        this.endpointURL = "/api/v1/country/dynamic/stack/" + countryCode + "/" + rootItemCode
        this.pins = new Set() // pins contains a list of pinned countries
        this.colorProvider = colorProvider // colorProvider is an instance of ColorProvider
        this.yAxisScale = "value"
        this.endLabelPlugin = endLabelPlugin
        this.extrapolateBackwardPlugin = extrapolateBackwardPlugin
        this.setTheme(window.observableStorage.getItem("theme"))
        this.initRoot()
        this.initChartJSCanvas()
        this.buildChartOptions()
        this.rigChartOptions()
        this.rigItemDropdown()
        this.updateChartOptions()
        this.fetch(this.endpointURL).then(data => {
            this.update(data)
        })
        this.rigUnloadListener()
    }

    initRoot() {
        // Create the root element
        this.root = document.createElement('div')
        this.root.classList.add('panel-chart-root-container')
        this.parentElement.appendChild(this.root)
    }

    buildChartOptions() {
        this.chartOptions = document.createElement('div')
        this.chartOptions.classList.add('chart-options')
        this.chartOptions.innerHTML = `
            <button class="icon-button hide-chart-options" aria-label="Hide Chart Options" title="Hide Chart Options">
                <svg class="hide-chart-options-svg" width="24" height="24">
                    <use href="#icon-close" />
                </svg>
            </button>
            <details class="item-information chart-options-details">
                <summary class="item-information-summary">Item Information</summary>
                <select class="item-dropdown"></select>
                <div class="dynamic-item-description"></div>
            </details>
            <details class="download-data-details chart-options-details">
                <summary>Download Chart Data</summary>
                <form id="downloadForm">
                    <fieldset>
                        <legend>Select data scope:</legend>
                        <label><input type="radio" name="scope" value="pinned" required>Pinned countries</label>
                        <label><input type="radio" name="scope" value="visible">Visible countries</label>
                        <label><input type="radio" name="scope" value="group">Countries in group</label>
                        <label><input type="radio" name="scope" value="all">All available countries</label>
                    </fieldset>
                    <fieldset>
                        <legend>Choose file format:</legend>
                        <label><input type="radio" name="format" value="json" required>JSON</label>
                        <label><input type="radio" name="format" value="csv">CSV</label>
                    </fieldset>
                    <button type="submit">Download Data</button>
                </form>
            </details>
            `;
        this.showChartOptions = document.createElement('button')
        this.showChartOptions.classList.add("icon-button", "show-chart-options")
        this.showChartOptions.ariaLabel = "Show Chart Options"
        this.showChartOptions.title = "Show Chart Options"
        this.showChartOptions.innerHTML = `
            <svg class="svg-button show-chart-options-svg" width="24" height="24">
                <use href="#icon-menu" />
            </svg>
        `;
        this.root.appendChild(this.showChartOptions)
        this.overlay = document.createElement('div')
        this.overlay.classList.add('chart-options-overlay')
        this.overlay.addEventListener('click', () => {
            this.closeChartOptionsSidebar()
        })
        this.root.appendChild(this.overlay)
        const wrapper = document.createElement('div')
        wrapper.classList.add('chart-options-wrapper')
        wrapper.appendChild(this.chartOptions)
        this.root.appendChild(wrapper)
    }

    rigChartOptions() {
        this.showChartOptions.addEventListener('click', () => {
            this.openChartOptionsSidebar()
        })
        this.hideChartOptions = this.chartOptions.querySelector('.hide-chart-options')
        this.hideChartOptions.addEventListener('click', () => {
            this.closeChartOptionsSidebar()
        })
        let openDetails = window.observableStorage.getItem("openCountryChartDetails")
        const detailsElements = this.chartOptions.querySelectorAll('.chart-options-details')
        detailsElements.forEach((details) => {
            if (openDetails && openDetails.includes(details.classList[0])) {
                details.open = true
            } else {
                details.open = false
            }
        })
        const sidebarStatus = window.observableStorage.getItem("chartOptionsStatus")
        if (sidebarStatus === "active") {
            this.openChartOptionsSidebar()
        } else {
            this.closeChartOptionsSidebar()
        }
    }

    rigItemDropdown() {
        this.itemInformation = this.chartOptions.querySelector('.item-information')
        this.itemDropdown = this.itemInformation.querySelector('.item-dropdown')
    }

    initChartJSCanvas() {
        this.chartContainer = document.createElement('div')
        this.chartContainer.classList.add('panel-chart-container')
        this.chartContainer.innerHTML = `
            <h2 class="panel-chart-title"></h2>
            <div class="panel-canvas-wrapper">
                <canvas class="panel-chart-canvas"></canvas>
            </div>
        `;
        this.root.appendChild(this.chartContainer)
        this.title = this.chartContainer.querySelector('.panel-chart-title')
        this.canvas = this.chartContainer.querySelector('.panel-chart-canvas')
        this.context = this.canvas.getContext('2d')
        this.chart = new Chart(this.context, {
            type: 'line',
            plugins: [this.endLabelPlugin, this.extrapolateBackwardPlugin],
            options: {
                responsive: true,
                maintainAspectRatio: false,
                datasets: {
                    fill: true,
                    line: {
                        spanGaps: true,
                        pointRadius: 2,
                        pointHoverRadius: 4,
                        segment: {
                            borderWidth: 2,
                            borderDash: ctx => {
                                return ctx.p0.skip || ctx.p1.skip ? [10, 4] : [];
                                // Dashed when spanning gaps, solid otherwise
                            }
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: false,
                    },
                    endLabelPlugin: {
                        labelField: 'ICode'
                    },
                    tooltip: {
                        mode: 'index',
                    }
                },
                layout: {
                    padding: {
                        right: 40
                    }
                }
            }
        })
    }

    updateChartOptions() {
        this.chart.options.scales = {
            x: {
                ticks: {
                    color: this.tickColor,
                },
                type: "category",
                title: {
                    display: true,
                    text: 'Year',
                    color: this.axisTitleColor,
                    font: {
                        size: 16
                    }
                },
            },
            y: {
                stacked: true,
                ticks: {
                    color: this.tickColor,
                },
                beginAtZero: true,
                title: {
                    display: true,
                    text: 'Item Value',
                    color: this.axisTitleColor,
                    font: {
                        size: 16
                    }
                }
            }
        }
    }

    updateChartColors() {
        for (let i = 0; i < this.chart.data.datasets.length; i++) {
            const dataset = this.chart.data.datasets[i]
            const color = this.colorProvider.get(dataset.ICode)
            dataset.borderColor = color
            dataset.backgroundColor = color + "44"
        }
    }

    setTheme(theme) {
        if (theme !== "light") {
            this.theme = "dark"
            this.tickColor = "#bbb"
            this.axisTitleColor = "#bbb"
            this.titleColor = "#ccc"
        } else {
            this.theme = "light"
            this.tickColor = "#444"
            this.axisTitleColor = "#444"
            this.titleColor = "#444"
        }
    }

    async fetch(url) {
        const response = await fetch(url)
        try {
            return response.json()
        } catch (error) {
            console.error('Error:', error)
        }
    }

    update(data) {
        console.log(data)
        // this.chart.data = data
        this.chart.data.datasets = data.data
        this.chart.data.labels = data.labels
        this.title.innerText = data.title
        this.itemType = data.itemType
        this.updateChartColors()
        this.chart.options.scales.y.min = 0
        this.chart.options.scales.y.max = 1
        this.chart.update()
    }


    closeChartOptionsSidebar() {
        this.chartOptions.classList.remove('active')
        this.chartOptions.classList.add('inactive')
        this.overlay.classList.remove('active')
        this.overlay.classList.add('inactive')
    }

    openChartOptionsSidebar() {
        this.chartOptions.classList.add('active')
        this.chartOptions.classList.remove('inactive')
        this.overlay.classList.remove('inactive')
        this.overlay.classList.add('active')
    }

    toggleChartOptionsSidebar() {
        if (this.chartOptions.classList.contains('active')) {
            this.closeChartOptionsSidebar()
        } else {
            this.openChartOptionsSidebar()
        }
    }

    dumpChartDataJSON(screenVisibility = true) {
        const observations = this.chart.data.datasets.map(dataset => {
            if (screenVisibility && dataset.hidden) {
                return []
            }
            return dataset.data.map((_, i) => ({
                "ItemCode": dataset.ICode,
                "CountryCode": dataset.CCode,
                "Score": dataset.scores[i],
                "Value": dataset.values[i],
                "Year": dataset.years[i]
            }));
        }).flat();
        const jsonString = JSON.stringify(observations, null, 2);
        const blob = new Blob([jsonString], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'item-panel-data.json';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }

    dumpChartDataCSV(screenVisibility = true) {
        const observations = this.chart.data.datasets.map(dataset => {
            if (screenVisibility && dataset.hidden) {
                return []
            }
            return dataset.data.map((_, i) => ({
                "ItemCode": dataset.ICode,
                "CountryCode": dataset.CCode,
                "Score": dataset.scores[i].toString(),
                "Value": dataset.values[i].toString(),
                "Year": dataset.years[i].toString()
            }));
        }).flat();
        const csvString = Papa.unparse(observations);
        const blob = new Blob([csvString], { type: 'text/csv' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'item-panel-data.csv';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }

    rigUnloadListener() {
        window.addEventListener('beforeunload', () => {
            window.observableStorage.setItem(
                "openCountryChartDetails",
                Array.from(this.chartOptions.querySelectorAll('.chart-options-details'))
                    .filter(details => details.open)
                    .map(details => details.classList[0])
            )
            window.observableStorage.setItem(
                "chartOptionsStatus",
                this.chartOptions.classList.contains('active') ? "active" : "inactive"
            )
        })
    }

    setYAxisScale(scale) {
        this.yAxisScale = scale
        const scaleType = scale.charAt(0).toUpperCase() + scale.slice(1)
        let itemType = ""
        if (this.itemType === "sspi") {
            itemType = this.itemType.toUpperCase()
        } else {
            itemType = this.itemType.charAt(0).toUpperCase() + this.itemType.slice(1)
        }
        this.chart.options.scales.y.title.text = itemType + " " + scaleType 
        let yMin = 0
        let yMax = 1
        for (let i = 0; i < this.chart.data.datasets.length; i++) {
            const dataset = this.chart.data.datasets[i];
            if (i == 0) {
                yMin = (this.yAxisScale === "value") ? dataset.maxYValue : 0;
                yMax = (this.yAxisScale === "value") ? dataset.maxYValue : 1;
            }
            dataset.parsing.yAxisKey = this.yAxisScale;
            for (let j = 0; j < dataset.data.length; j++) {
                if (this.yAxisScale === "value") {
                    dataset.data[j] = dataset.value[j]
                } else {
                    dataset.data[j] = dataset.score[j]
                }
            }
        }
        this.chart.options.scales.y.min = yMin
        this.chart.options.scales.y.max = yMax
        this.chart.update()
    }


    toggleYAxisScale() {
        if (this.yAxisScale === "score") {
            this.setYAxisScale("value")
        } else {
            this.setYAxisScale("score")
        }
    }
}
