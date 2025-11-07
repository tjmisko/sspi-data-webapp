class ScoreBarStatic {
    constructor(parentElement, itemCode, { backgroundColor = SSPIColors.SSPI, width = 800, height = 1000, animate = true } = {}) {
        this.parentElement = parentElement
        this.itemCode = itemCode
        this.backgroundBase = backgroundColor
        this.width = width
        this.height = height
        this.animate = animate
        console.log(this.animate)
        this.initRoot()
        this.initTitle()
        this.initChartJSCanvas()
        this.updateChartOptions()
        this.initSummaryBox()
        this.fetch().then(data => {
            this.update(data)
        })
        this.setTheme(window.observableStorage.getItem("theme"))
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
        this.canvas.id = `score-bar-canvas-container${this.itemCode}`;
        // this.canvas.width = this.width
        // this.canvas.height = this.height
        this.chartContainer = document.createElement('div')
        this.context = this.canvas.getContext('2d')
        this.chartContainer.classList.add('score-bar-chart-container')
        this.chartContainer.appendChild(this.canvas)
        this.root.appendChild(this.chartContainer)
        this.chart = new Chart(this.context, {
            type: 'bar',
            options: {
                animation: { 
                    duration: this.animation? 1000 : 0,
                },
                maintainAspectRatio: false,
                layout: {
                    padding: {
                        left: 0,
                    }
                },
                onClick: (event, elements) => {
                    elements.forEach(element => {
                        this.toggleHighlight(
                            this.chart.data.datasets[element.datasetIndex].info[element.index].CCode
                        )
                        console.log(this.chart.data.datasets[element.datasetIndex].info[element.index].CCode)
                    })
                },
                plugins: {
                    legend: false,
                    tooltip: {
                        backgroundColor: '#1B2A3Ccc',
                        callbacks: {
                            label: function(context) {
                                const info = context.dataset.info[context.dataIndex]
                                return [
                                    info.IName + ' (' + info.ICode + ')', 
                                    'Score: ' + info.Score.toFixed(3),
                                    'Rank: ' + info.Rank,
                                    'Year: ' + info.Year
                                ]
                            }
                        }
                    },
                },
                indexAxis: 'y',
            }
        })
    }
    updateChartOptions() {
        this.chart.options.scales = {
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
                        size: 10,
                        weight: 'bold'
                    },
                    callback: function(value, index, values) {
                        return this.chart.data.datasets[0].info[index].Rank
                    },
                    padding: 8
                },
            },
            y: {
                position: 'left',
                ticks: {
                    color: this.textColor,
                    font: {
                        size: 10,
                    }
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
    }

    initSummaryBox() {
        this.summaryBox = document.createElement('div')
        this.summaryBox.classList.add('score-bar-summary-box')
        this.summaryBox.style.color = this.textColor
        this.summaryBox.style.fontSize = '16px'
        this.root.appendChild(this.summaryBox)
    }

    computeSummaryStats(data) {
        const scores = data.datasets[0].info.map(info => info.Score)
        const meanScore = scores.reduce((a, b) => a + b, 0) / scores.length
        const medianScore = scores.sort()[Math.floor(scores.length / 2)]
        const minScore = Math.min(...scores)
        const maxScore = Math.max(...scores)
        const sdScore = Math.sqrt(scores.reduce((a, b) => a + (b - meanScore) ** 2, 0) / (scores.length - 1))
        return {
            Mean: meanScore.toFixed(3),
            Median: medianScore.toFixed(3),
            Min: minScore.toFixed(3),
            Max: maxScore.toFixed(3),
            SD: sdScore.toFixed(3),
        }
    }

    updateSummaryBox(summaryStats) {
        for (const key in summaryStats) {
            const stat = document.createElement('div')
            stat.classList.add('score-bar-summary-stat')
            stat.innerHTML = key + ': <b>' + summaryStats[key] + '</b>'
            this.summaryBox.appendChild(stat)
        }
    }

    async fetch() {
        const response = await fetch(`/api/v1/static/bar/score/${this.itemCode}`);
        return response.json();
    }

    setTheme(theme) {
        if (theme !== "light") {
            this.theme = "dark"
            this.textColor = "#dddddd"
            this.gridColor = "#cccccc33"
            this.backgroundColor = this.backgroundBase + "99"
            this.highlightColor = "#ff0000ee"
            this.borderColor = this.backgroundBase
            this.titleColor = "#ccc"
        } else {
            this.theme = "light"
            this.textColor = "#444"
            this.gridColor = "#333333cc"
            this.backgroundColor = this.backgroundBase + "cc"
            this.highlightColor = "#ff0000ee"
            this.borderColor = this.backgroundBase
            this.titleColor = "#333"
        }
        if (this.chart) {
            this.updateChartOptions()
            this.chart.update()
        }
    }

    getStoredHighlights() {
        let highlights = []
        if (localStorage.getItem('scoreBarHighlights') === null) {
            highlights = []
        } else {
            highlights = localStorage.getItem('scoreBarHighlights').split(',')
        }
        return highlights
    }

    setStoredHighlights(highlights) {
        localStorage.setItem('scoreBarHighlights', highlights)
    }

    clearVisibleHighlights() {
        this.chart.data.datasets[0].backgroundColor = Array(49).fill(this.backgroundColor)
    }

    setVisibleHighlights(highlights) {
        this.clearVisibleHighlights()
        highlights.forEach(countryCode => {
            this.addVisibleHighlight(countryCode)
        })
    }

    addVisibleHighlight(countryCode) {
        const index = this.chart.data.datasets[0].info.findIndex(info => info.CCode === countryCode)
        this.chart.data.datasets[0].backgroundColor[index] = this.highlightColor
        this.chart.update()
    }

    removeVisibleHighlight(countryCode) {
        const index = this.chart.data.datasets[0].info.findIndex(info => info.CCode === countryCode)
        this.chart.data.datasets[0].backgroundColor[index] = this.backgroundColor
        this.chart.update()
    }

    updateHighlights() {
        const highlights = this.getStoredHighlights()
        this.setVisibleHighlights(highlights)
        this.propagateHighlights()
    }

    syncHighlights() {
        const highlights = this.getStoredHighlights()
        this.setVisibleHighlights(highlights)
    }

    initHighlights() {
        let highlights = this.getStoredHighlights()
        this.setVisibleHighlights(highlights)
    }

    removeStoredHighlight(countryCode) {
        let highlights = this.getStoredHighlights()
        highlights = highlights.filter(highlight => highlight !== countryCode)
        this.setStoredHighlights(highlights)
    }

    addStoredHighlight(countryCode) {
        let highlights = this.getStoredHighlights()
        if (highlights.includes(countryCode)) {
            return
        }
        highlights.push(countryCode)
        this.setStoredHighlights(highlights)
    }

    toggleHighlight(countryCode) {
        let highlights = this.getStoredHighlights()
        if (highlights.includes(countryCode)) {
            this.removeVisibleHighlight(countryCode)
            this.removeStoredHighlight(countryCode)
        } else {
            this.addVisibleHighlight(countryCode)
            this.addStoredHighlight(countryCode)
        }
        this.updateHighlights()
    }

    propagateHighlights() {
        window.SSPICharts.forEach(chartObject => {
            if (chartObject !== this) {
                chartObject.syncHighlights()
            }
        })
    }

    update(data) {
        this.chart.data = data.data
        if (this.chart.width < 400) {
            const chartInfo = this.chart.data.datasets[0].info
            const codeLabels = chartInfo.map((i) => i.CCode + " " + i.CFlag)
            this.chart.data.labels = codeLabels
        }
        this.chart.data.datasets[0].backgroundColor = Array(49).fill(this.backgroundColor)
        this.chart.data.datasets[0].borderColor = Array(49).fill(this.borderColor)
        this.chart.data.datasets[0].borderWidth = 2
        this.title.innerText = data.title
        this.chart.options.scales.x.title.text = data.xTitle
        this.initHighlights()
        this.updateSummaryBox(this.computeSummaryStats(data.data))
        this.chart.update()
    }

}
