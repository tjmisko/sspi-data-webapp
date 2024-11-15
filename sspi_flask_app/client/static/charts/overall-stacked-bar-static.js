class StaticOverallStackedBarChart {
    constructor(parentElement, colormap = {}) {
        this.parentElement = parentElement;
        this.textColor = '#bbb';
        this.gridColor = '#cccccc33';
        this.initRoot()
        this.initTitle()
        if (Object.keys(colormap).length === 0) {
            this.initColormap()
        } else {
            this.colormap = colormap
        }
        this.createLegend()
        this.initChartJSCanvas()
        this.fetch().then(data => {
            this.update(data)
        })
    }

    async fetch() {
        const response = await fetch('/api/v1/static/stacked/sspi');
        return response.json();
    }

    initRoot() {
        // Create the root element
        this.root = document.createElement('div')
        this.root.classList.add('chart-section-overall-stack')
        this.parentElement.appendChild(this.root)
    }

    initTitle() {
        this.title = document.createElement('h4')
        this.title.classList.add('stack-bar-title')
        this.root.appendChild(this.title)
    }

    initColormap() {
        this.colormap = {
            "SUS": "#28a745",
            "MS": "#ff851b",
            "PG": "#007bff"
        }
    }

    createLegend() {
        this.legend = document.createElement('div')
        this.legend.classList.add('overall-stack-bar-legend')
        // this.countryCodes.map((countryCode) => {
        //     const legendElement = document.createElement('div')
        //     legendElement.classList.add('stack-bar-legend-element')
        //     const legendBox = document.createElement('div')
        //     legendBox.classList.add('legend-box')
        //     legendBox.style.backgroundColor = this.colormap[countryCode]
        //     legendElement.appendChild(legendBox)
        //     const legendText = document.createElement('span')
        //     legendText.id = countryCode + '-' + this.pillarCode + '-stack-bar-legend-text'
        //     legendText.innerText = countryCode
        //     legendElement.appendChild(legendText)
        //     this.legend.appendChild(legendElement)
        // })
        this.root.appendChild(this.legend)
    }

    initChartJSCanvas() {
        this.canvas = document.createElement('canvas')
        this.canvas.id = `overall-stacked-bar-canvas`
        this.canvas.width = 1000
        this.canvas.height = 1000
        this.context = this.canvas.getContext('2d')
        this.root.appendChild(this.canvas)
        this.chart = new Chart(this.context, {
            type: 'bar',
            options: {
                plugins: {
                    legend: {
                        display: false,
                    },
                    tooltip: {
                        intersect: false,
                        padding: 10,
                        backgroundColor: 'rgba(0, 0, 0, 0.7)',
                        yAlign: 'center',
                        callbacks: {
                            afterTitle(context) {
                                const info = context[0].dataset.info[context[0].dataIndex]
                                return [
                                    `SSPI Overall Score: ${info.SSPIScore.toFixed(3)}`,
                                    `SSPI Overall Rank: ${info.SSPIRank}`
                                ]
                            },
                            label(context) {
                                const info = context.dataset.info[context.dataIndex]
                                return [
                                    'Pillar: ' + info.IName,
                                    'Pillar Score: ' + info.IName,
                                    'Pillar Rank: ' + Number.parseFloat(info.Score).toFixed(3),
                                    'Rank: ' + info.Rank,
                                ];
                            }
                        }
                    }
                },
                responsive: true,
                indexAxis: 'y',
                scales: {
                    x2: {
                        position: 'top',
                        display: true,
                        ticks: {
                            color: this.textColor,
                        },
                        grid: {
                            display: false,
                        },
                        min: 0,
                        max: 1,
                        stacked: true,
                    },
                    x: {
                        title: {
                            display: true,
                            text: 'SSPI Score',
                            color: this.textColor,
                        },
                        ticks: {
                            color: this.textColor,
                        },
                        stacked: true,
                        min: 0,
                        max: 1,
                    },
                    y2: {
                        position: 'left',
                        display: true,
                        ticks: {
                            color: this.textColor,
                            callback: function(value, index, values) {
                                return index + 1
                            },
                            padding: 8,
                            font: {
                                size: 12,
                                weight: 'bold'
                            },
                        },
                        stacked: true,
                        grid: {
                            display: false,
                        }
                    },
                    y: {
                        position: 'left',
                        stacked: true,
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
                }
            },
        })
    }

    update(data) {
        this.chart.data = data.data
        this.chart.data.datasets.forEach((dataset) => {
            const color = this.colormap[dataset.label]
            dataset.backgroundColor = color + "99"
            dataset.borderColor = color
        })
        this.title.innerText = data.title
        this.chart.update()
    }
}
