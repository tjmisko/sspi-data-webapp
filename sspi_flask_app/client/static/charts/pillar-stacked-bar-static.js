class StaticPillarStackedBarChart {
    constructor(countryCodes, pillarCode, parentElement) {
        this.parentElement = parentElement;
        this.countryCodes = countryCodes;
        this.pillarCode = pillarCode;
        this.initRoot()
        this.initChartJSCanvas()
        this.fetch().then(data => {
            this.update(data)
        })
    }

    async fetch() {
        let url_string = `/api/v1/static/stacked/pillar/${this.pillarCode}?`;
        for (let i = 0; i < this.countryCodes.length; i++) {
            url_string += `CountryCode=${this.countryCodes[i]}&`;
        }
        url_string = url_string.slice(0, -1); // Remove trailing '&'
        const response = await fetch(url_string);
        return response.json();
    }

    initRoot() {
        // Create the root element
        this.root = document.createElement('div')
        this.root.classList.add('chart-section-pillar-stack')
        this.parentElement.appendChild(this.root)
    }

    initChartJSCanvas() {
        this.canvas = document.createElement('canvas')
        this.canvas.id = `pillar-differential-canvas-${this.pillarCode}-${this.BaseCountry}-${this.ComparisonCountry}`
        this.canvas.width = 700
        this.canvas.height = 400
        this.context = this.canvas.getContext('2d')
        this.root.appendChild(this.canvas)
        this.chart = new Chart(this.context, {
            type: 'bar',
            options: {
                plugins: {
                    legend: {
                        display: false,
                    },
                    title: {
                        display: true,
                        text: 'Chart.js Bar Chart - Stacked'
                    },
                },
                responsive: true,
                parsing: {
                    xAxisKey: 'CatCode',
                    yAxisKey: 'IScoreScaled',
                },
                interaction: {
                    intersect: false,
                },
                scales: {
                    x: {
                        stacked: true,
                    },
                    y: {
                        stacked: true,
                        beginAtZero: true
                    }
                }
            }
        })
    }

    update(data) {
        this.chart.data.datasets = data.datasets
        this.chart.labels = data.labels
        this.chart.update()
    }
}
