class ScoreBarStatic {
    constructor(parentElement, itemCode) {
        this.parentElement = parentElement
        this.itemCode = itemCode

        this.initRoot()
        this.initChartJSCanvas()
        this.initTitle()

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
        this.root.appendChild(this.titleElement)
    }

    initChartJSCanvas() {
        // Initialize the chart canvas
        this.canvas = document.createElement('canvas')
        this.canvas.id = `score-bar-chart-canvas-${this.itemCode}`
        this.canvas.width = 400
        this.canvas.height = 800
        this.context = this.canvas.getContext('2d')
        this.root.appendChild(this.canvas)
        this.chart = new Chart(this.context, {
            type: 'bar',
            options: {
                plugins: {
                    legend: false,
                }
            }
        })
    }

    async fetch() {
        const response = await fetch(`/api/v1/static/bar/score/${this.itemCode}`);
        return response.json();
    }

    update(data) {
        this.chart.datasets = data.datasets
        this.title = data.title
        this.chart.update()
    }
}
