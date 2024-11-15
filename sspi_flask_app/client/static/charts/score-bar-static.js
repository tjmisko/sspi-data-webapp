class ScoreBarStatic {
    constructor(parentElement, itemCode, backgroundColor = SSPIColors.SSPI) {
        this.parentElement = parentElement
        this.itemCode = itemCode
        this.textColor = "#bbb"
        this.gridColor = "#cccccc33"
        this.backgroundColor = backgroundColor + "99"
        this.borderColor = backgroundColor

        this.initRoot()
        this.initTitle()
        this.initChartJSCanvas()

        this.fetch().then(data => {
            this.update(data)
        })
    }

    initRoot() {
        this.root = document.createElement('div')
        this.root.classList.add('chart-container-bar-score-static')
        this.parentElement.appendChild(this.root)
    }

    initTitle() {
        this.title = document.createElement('h2')
        this.title.classList.add('score-bar-chart-title')
        this.root.appendChild(this.title)
    }

    initChartJSCanvas() {
        // Initialize the chart canvas
        this.canvas = document.createElement('canvas')
        this.canvas.id = `score-bar-chart-canvas-${this.itemCode}`
        this.canvas.width = 800
        this.canvas.height = 1000
        this.context = this.canvas.getContext('2d')
        this.root.appendChild(this.canvas)
        this.chart = new Chart(this.context, {
            type: 'bar',
            options: {
                onClick: (event, elements) => {
                    elements.forEach(element => {
                        const color = this.chart.data.datasets[0].backgroundColor[element.index] 
                        if (color === this.backgroundColor) {
                            this.chart.data.datasets[0].backgroundColor[element.index] = "#ff0000"
                        } else {
                            this.chart.data.datasets[0].backgroundColor[element.index] = this.backgroundColor
                        }
                    })
                    this.chart.update()
                },
                plugins: {
                    legend: false,
                    tooltip: {
                        backgroundColor: '#1B2A3Ccc',
                        callbacks: {
                            label: function(context) {
                                const info = context.dataset.info[context.dataIndex]
                                return [
                                    `${info.IName} Score: ${info.Score.toFixed(3)}`,
                                    `${info.IName} Rank: ${info.Rank}`,
                                    `Year: ${info.Year}`
                                ]
                            }
                        }
                    },
                },
                scales: {
                    x2: {
                        position: 'top',
                        min: 0,
                        max: 1,
                        ticks: {
                            color: this.textColor
                        },
                        label: {
                            color: this.textColor,
                        },
                        grid: {
                            display: false,
                        },
                    },
                    x: {
                        position: 'bottom',
                        min: 0,
                        max: 1,
                        ticks: {
                            color: this.textColor
                        },
                        title: {
                            display: true,
                            font: {
                                size: 16,
                            },
                            color: this.textColor
                        },
                        label: {
                            color: this.textColor,
                        },
                        grid: {
                            color: this.gridColor,
                        }
                    },
                    y2: {
                        position: 'left',
                        ticks: {
                            color: this.textColor,
                            font: {
                                size: 12,
                                weight: 'bold'
                            },
                            callback: function(value, index, values) {
                                return index + 1
                            },
                            padding: 8
                        },
                    },
                    y: {
                        position: 'left',
                        ticks: {
                            color: this.textColor,
                        },
                        grid: {
                            display: true,
                            drawBorder: true,
                            drawOnChartArea: true,
                            color: function(context) {
                                // Draw gridline only every 10 indices
                                return context.index % 10 === 0 ? '#66666666' : 'rgba(0, 0, 0, 0)';
                            }
                        },
                    },
                },
                indexAxis: 'y',
            }
        })
    }

    async fetch() {
        const response = await fetch(`/api/v1/static/bar/score/${this.itemCode}`);
        return response.json();
    }

    update(data) {
        this.chart.data = data.data
        this.chart.data.datasets[0].backgroundColor = Array(49).fill(this.backgroundColor)
        this.chart.data.datasets[0].borderColor = Array(49).fill(this.borderColor)
        this.chart.data.datasets[0].borderWidth = 2
        this.title.innerText = data.title
        this.chart.options.scales.x.title.text = data.xTitle
        this.chart.update()
    }
}
