class CountryPillarPanelChart {
    constructor(parentElement, countryCode, rootItemCode, { colorProvider = SSPIColors } ) {
        this.parentElement = parentElement// ParentElement is the element to attach the canvas to
        this.countryCode = countryCode
        this.endpointURL = "/api/v1/country/dynamic/stack/" + countryCode + "/" + rootItemCode
        this.colorProvider = colorProvider // colorProvider is an instance of ColorProvider
        this.extrapolateBackwardPlugin = extrapolateBackwardPlugin
        this.pillarBreakdownPlugin = pillarBreakdownInteractionPlugin
        this.setTheme(window.observableStorage.getItem("theme"))
        this.initRoot()
        this.initChartJSCanvas()
        this.updateChartOptions()
        this.fetch(this.endpointURL).then(data => {
            this.update(data)
        })
    }

    initRoot() {
        // Create the root element
        this.root = document.createElement('div')
        this.root.classList.add('panel-chart-root-container')
        this.parentElement.appendChild(this.root)
    }

    initChartJSCanvas() {
        this.chartContainer = document.createElement('div')
        this.chartContainer.classList.add('panel-chart-container')
        this.chartContainer.innerHTML = `
<div class="panel-chart-title-container">
    <h2 class="panel-chart-title"></h2>
</div>
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
            plugins: [this.pillarBreakdownPlugin, this.extrapolateBackwardPlugin],
            options: {
                animation: false,
                responsive: true,
                hover: {
                    mode: null
                },
                maintainAspectRatio: false,
                datasets: {
                    fill: true,
                    line: {
                        spanGaps: true,
                        pointRadius: 2,
                        pointHoverRadius: 4,
                        pointBorderWidth: 0,
                        pointBackgroundColor: function(context) {
                            return context.dataset.borderColor;
                        },
                        segment: {
                            borderWidth: 2,
                            borderDash: ctx => {
                                return ctx.p0.skip || ctx.p1.skip ? [10, 4] : [];
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
                    },
                    tooltip: {
                        enabled: false,
                    },
                    pillarBreakdownInteractionPlugin: {
                        enabled: true,
                        radius: 30,
                        guideColor: this.tickColor,
                        showTotal: true,
                        countryName: null,
                        countryFlag: null
                    },
                },
                layout: {
                    padding: {
                        right: 20
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
            dataset.pointBackgroundColor = color
            dataset.pointBorderColor = color
        }
    }

    setTheme(theme) {
        const root = document.documentElement
        if (theme !== "light") {
            this.theme = "dark"
            this.tickColor = "#bbb"
            this.guideColor = "#333333"
            this.axisTitleColor = "#bbb"
            this.titleColor = "#ccc"
        } else {
            this.theme = "light"
            this.tickColor = "#444"
            this.guideColor = "#bbbbbb"
            this.axisTitleColor = "#444"
            this.titleColor = "#444"
            this.headerBackgroundColor = "#f0f0f0"
        }
        const bg = getComputedStyle(root).getPropertyValue('--header-color').trim()
        this.headerBackgroundColor = bg
        if (this.chart) {
            this.updateChartOptionsPreservingYAxis()
        }
    }

    updateChartOptionsPreservingYAxis() {
        // Store current y-axis scale settings
        const currentYMin = this.chart.options.scales?.y?.min
        const currentYMax = this.chart.options.scales?.y?.max
        const currentYTitle = this.chart.options.scales?.y?.title?.text
        // Update chart options with new theme colors
        this.updateChartOptions()
        if (this.chart.options.plugins.pillarBreakdownInteractionPlugin) {
            this.chart.options.plugins.pillarBreakdownInteractionPlugin.guideColor = this.tickColor
        }
        // Restore preserved y-axis scale settings
        if (currentYMin !== undefined) {
            this.chart.options.scales.y.min = currentYMin
        }
        if (currentYMax !== undefined) {
            this.chart.options.scales.y.max = currentYMax
        }
        if (currentYTitle !== undefined) {
            this.chart.options.scales.y.title.text = currentYTitle
        }
        // Update the chart to apply changes
        this.chart.update()
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
        this.chart.data.datasets = data.data
        this.chart.data.labels = data.labels
        this.title.innerText = data.title
        this.itemType = data.itemType
        if (data.countryDetails) {
            this.chart.options.plugins.pillarBreakdownInteractionPlugin.countryName = data.countryDetails.CName;
            this.chart.options.plugins.pillarBreakdownInteractionPlugin.countryFlag = data.countryDetails.CFlag;
        }
        this.updateChartColors()
        this.chart.options.scales.y.min = 0
        this.chart.options.scales.y.max = 1
        this.chart.update()
    }
}
