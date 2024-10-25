class StaticPillarDifferentialChart {
    constructor(BaseCountry, ComparisonCountry, PillarCode, parentElement) {
        this.parentElement = parentElement;
        this.BaseCountry = BaseCountry;
        this.ComparisonCountry = ComparisonCountry;
        this.PillarCode = PillarCode;
        this.titleString = `Sustainability Score Differences (${ComparisonCountry} - ${BaseCountry}`

        this.initRoot()
        this.initChartJSCanvas()
        this.fetch().then(data => {
            this.update(data)
        })
    }

    colormap(diff) {
        if (diff > 0) {
            return "#32CD3299"
        } else {
            return "#FF634799"
        }
    }

    async fetch() {
        const response = await fetch(`/api/v1/static/differential/pillar/${this.PillarCode}?BaseCountry=${this.BaseCountry}&ComparisonCountry=${this.ComparisonCountry}`);
        return response.json();
    }

    initRoot() {
        // Create the root element
        this.root = document.createElement('div')
        this.root.classList.add('chart-section-pillar-differential')
        this.parentElement.appendChild(this.root)
    }

    initChartJSCanvas() {
        this.canvas = document.createElement('canvas')
        this.canvas.id = `pillar-differential-canvas-${this.PillarCode}-${this.BaseCountry}-${this.ComparisonCountry}`
        this.canvas.width = 450
        this.canvas.height = 300
        this.context = this.canvas.getContext('2d')
        this.root.appendChild(this.canvas)
        this.chart = new Chart(this.context, {
            type: 'bar',
            options: {
                indexAxis: 'y',
                responsive: true,
                plugins: {
                    legend: {
                        display: false,
                    },
                },
                parsing:
                {
                    xAxisKey: 'Diff',
                    yAxisKey: 'CategoryCode'
                },
                scales: {
                    x: {
                        beginAtZero: true,
                        grid: {
                            drawTicks: false
                        },
                        ticks: {
                            color: '#bbb',
                            stepSize: 0.1
                        },
                        title: {
                            display: true,
                            color: '#bbb',
                            text: 'Score Difference (Base - Comparison)'
                        },
                        min: -1,
                        max: 1,
                    },
                    y: {
                        ticks: {
                            color: '#bbb',
                            minRotation: 90,
                            maxRotation: 90,
                            align: 'center',
                            crossAlign: 'center',
                        },
                        title: {
                            padding: 10,
                            display: true,
                            text: 'Categories',
                            color: '#bbb',
                        },
                        type: 'category',
                        reverse: false
                    }
                }
            }
        })
    }

    update(data) {
        data.datasets.forEach(dataset => {
            dataset.backgroundColor = dataset.data.map(item => this.colormap(item.Diff)) // Assign colors dynamically
            dataset.borderColor = dataset.data.map(item => this.colormap(item.Diff).slice(0, -2)) // Assign colors dynamically
            dataset.borderWidth = 1
        })
        this.chart.data.datasets = data.datasets
        this.chart.labels = data.labels
        this.chart.update()
    }
}
