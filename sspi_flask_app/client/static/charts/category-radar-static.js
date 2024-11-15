class CategoryRadarStatic {
    constructor(countryCode, parentElement) {
        this.parentElement = parentElement
        this.countryCode = countryCode

        this.initRoot()
        this.legend = this.initLegend()
        this.textColor = '#bbb'
        this.gridColor = '#cccccc33'
        this.initRoot()
        this.initTitle()
        this.initChartJSCanvas()
        this.initLegend()

        this.fetch().then(data => {
            this.update(data)
        })
    }

    initRoot() {
        this.root = document.createElement('div')
        this.root.classList.add('radar-chart-box')
        this.parentElement.appendChild(this.root)
    }

    initTitle() {
        this.title = document.createElement('h3')
        this.title.classList.add('radar-chart-title')
        this.root.appendChild(this.title)
    }

    initLegend() {
        this.legend = document.createElement('div')
        this.legend.classList.add('radar-chart-legend-box')
        this.root.appendChild(this.legend)
    }

    initChartJSCanvas() {
        this.canvasContainer = document.createElement('div')
        this.canvasContainer.classList.add('radar-chart-canvas-container')
        this.canvas = document.createElement('canvas')
        this.canvasContainer.appendChild(this.canvas)
        this.canvas.width = 400
        this.canvas.height = 400
        this.context = this.canvas.getContext('2d')
        this.root.appendChild(this.canvasContainer)
        this.chart = new Chart(this.context, {
            type: 'polarArea',
            options: {
                responsive: true,
                elements: {
                    line: {
                        borderWidth: 3
                    }
                },
                scales: {
                    r: {
                        pointLabels: {
                            display: true,
                            font: {
                                size: 10
                            },
                            color: this.textColor,
                            centerPointLabels: true,
                            padding:0
                        },
                        angleLines: {
                            display: true,
                            color: this.gridColor
                        },
                        grid: {
                            color: this.gridColor,
                            circular: true
                        },
                        ticks: {
                            backdropColor: 'rgba(0, 0, 0, 0)',
                            clip: true,
                            color: this.textColor,
                            font: {
                                size: 8
                            }
                        },
                        suggestedMin: 0,
                        suggestedMax: 1
                    }
                },
                plugins: {
                    legend: {
                        display: false,
                    },
                    tooltip: {
                        backgroundColor: '#1B2A3Ccc',
                    },
                }
            }
        })
    }

    async fetch() {
        const response = await fetch(`/api/v1/static/radar/${this.countryCode}`);
        return response.json();
    }

    update(data) {
        this.labelMap = data.labelMap
        this.chart.data.labels = data.labels
        this.ranks = data.ranks
        this.chart.data.datasets = data.datasets
        this.title.innerText = data.title
        this.legendItems = data.legendItems
        this.chart.options.plugins.tooltip.callbacks.title = (context) => {
            const categoryName = this.labelMap[context[0].label]
            return categoryName
        }
        this.chart.options.plugins.tooltip.callbacks.label = (context) => {
            return [
                "Category Score: " + context.raw.toFixed(3),
                "Category Rank: " + this.ranks[context.dataIndex].Rank,
            ]
        }
        this.chart.update()
    }
}
