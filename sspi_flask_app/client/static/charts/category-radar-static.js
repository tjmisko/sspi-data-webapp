class CategoryRadarStatic {
    constructor(countryCode, parentElement, textColor="#bbb", gridColor="#cccccc33") {
        this.parentElement = parentElement
        this.countryCode = countryCode
        this.textColor = textColor
        this.gridColor = gridColor

        this.initRoot()
        this.legend = this.initLegend()
        this.initRoot()
        this.initTitle()
        this.initLegend()
        this.initChartJSCanvas()

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
        this.canvas.width = 300
        this.canvas.height = 300
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
        const response = await fetch(`/api/v1/static/radar/${this.countryCode}`)
        return response.json();
    }

    update(data) {
        this.labelMap = data.labelMap
        this.chart.data.labels = data.labels
        this.ranks = data.ranks
        this.chart.data.datasets = data.datasets
        this.title.innerText = data.title
        this.updateLegend(data)
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

    updateLegend(data) {
        this.legendItems = data.legendItems
        const pillarColorsAlpha = data.datasets.map(d => d.backgroundColor)
        const pillarColorsSolid = pillarColorsAlpha.map(c => c.slice(0, 7))
        for (let i = 0; i < this.legendItems.length; i++) {
            const pillarLegendItem = document.createElement('div')
            pillarLegendItem.classList.add('radar-chart-legend-item')
            const pillarLegendCanvasContainer = document.createElement('div')
            pillarLegendCanvasContainer.classList.add('radar-chart-legend-canvas-container')
            const pillarLegendItemCanvas = document.createElement('canvas')
            pillarLegendItemCanvas.width = 150
            pillarLegendItemCanvas.height = 50
            pillarLegendItemCanvas.classList.add('radar-chart-legend-item-canvas')
            this.drawPillarLegendCanvas(pillarLegendItemCanvas, pillarColorsAlpha, pillarColorsSolid, i)
            pillarLegendCanvasContainer.appendChild(pillarLegendItemCanvas)
            pillarLegendItem.appendChild(pillarLegendCanvasContainer)
            const pillarLegendItemText = document.createElement('div')
            pillarLegendItemText.classList.add('radar-chart-legend-item-text')
            pillarLegendItemText.innerText = this.legendItems[i].Name
            pillarLegendItem.appendChild(pillarLegendItemText)
            this.legend.appendChild(pillarLegendItem)
        }
    }

    drawPillarLegendCanvas(pillarLegendItemCanvas, pillarColorsAlpha, pillarColorsSolid, i) {
        const pillarLegendContext = pillarLegendItemCanvas.getContext('2d')
        const shadedWidth = (pillarLegendItemCanvas.width * this.legendItems[i].Score).toFixed(0)
        // Draw the main boundary lines at 0 and 1
        pillarLegendContext.strokeStyle = this.textColor
        pillarLegendContext.linewidth = 5
        pillarLegendContext.beginPath()
        pillarLegendContext.moveTo(0, 0) // Move to the top of the canvas at x = 0
        pillarLegendContext.lineTo(0, pillarLegendItemCanvas.height) // Draw a line to the bottom of the canvas at x = 0
        pillarLegendContext.moveTo(pillarLegendItemCanvas.width, 0) // Move to the top of the canvas at x = width
        pillarLegendContext.lineTo(pillarLegendItemCanvas.width, pillarLegendItemCanvas.height) // Draw a line to the bottom of the canvas at x = width
        pillarLegendContext.stroke() // Render the lines
        // Draw the grid lines
        pillarLegendContext.strokeStyle = this.gridColor
        pillarLegendContext.linewidth = 3
        pillarLegendContext.beginPath()
        const spacing = pillarLegendItemCanvas.width / 10
        pillarLegendContext.beginPath();
        for (let i = 0; i < 10; i++) {
            const x = (i * spacing)
            pillarLegendContext.moveTo(x, 5)
            pillarLegendContext.lineTo(x, pillarLegendItemCanvas.height)
        }
        pillarLegendContext.stroke(); // Render all lines
        // Draw the main shaded rectangle
        pillarLegendContext.fillStyle = pillarColorsAlpha[i]
        pillarLegendContext.fillRect(3, 5, shadedWidth, pillarLegendItemCanvas.height-5)
        pillarLegendContext.strokeStyle = pillarColorsSolid[i]
        pillarLegendContext.linewidth = 10
        pillarLegendContext.strokeRect(3, 5, shadedWidth, pillarLegendItemCanvas.height-5)
    }
}
