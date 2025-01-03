const chartArrowLabels = {
    id: 'chartArrowLabels',
    afterDraw(chart, args, optionVars) {
        const {ctx, chartArea} = chart;
        ctx.save();

        console.log(optionVars.LeftCountry)
        console.log(optionVars.RightCountry)
        ctx.fillStyle = '#FF634799';
        ctx.font = 'bold 12px Arial';
        ctx.textAlign = 'center';
        const xLeftMid = (chartArea.left + chartArea.right) / 4;
        const xRightMid = 3 * (chartArea.left + chartArea.right) / 4;
        const yTop = (chartArea.top + chartArea.bottom) / 10 + 10;
        ctx.fillText(optionVars.LeftCountry + " Higher", xLeftMid, yTop);
        ctx.fillStyle = '#32CD3299';
        ctx.fillText(optionVars.RightCountry + " Higher", xRightMid, yTop);

        ctx.restore();
    }
}

class StaticPillarDifferentialChart {
    constructor(BaseCountry, ComparisonCountry, PillarCode, parentElement) {
        this.parentElement = parentElement;
        this.BaseCountry = BaseCountry;
        this.ComparisonCountry = ComparisonCountry;
        this.PillarCode = PillarCode;
        this.titleString = `Sustainability Score Differences (${ComparisonCountry} - ${BaseCountry}`

        this.initRoot()
        this.initTitle()
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

    initTitle() {
        this.title = document.createElement('h2')
        this.title.classList.add('differential-chart-title')
        this.title.textContent = "Test Title"
        this.root.appendChild(this.title)
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
            plugins: [ chartArrowLabels ],
            options: {
                indexAxis: 'y',
                responsive: true,
                plugins: {
                    legend: {
                        display: false,
                    },
                    chartArrowLabels: {
                        LeftCountry: this.BaseCountry,
                        RightCountry: this.ComparisonCountry
                    },
                    tooltip: {
                        callbacks: {
                            // Customize the title (top line in tooltip)
                            title: function(tooltipItems) {
                                return `Category: ${tooltipItems[0].raw.CategoryName}`;
                            },
                            // Customize the label (each line below the title)
                            label: function(tooltipItem) {
                                // const diff = tooltipItem.raw;
                                if (tooltipItem.raw.Diff > 0) {
                                    return `Difference: +${tooltipItem.formattedValue}`;
                                }
                                return `Difference: ${tooltipItem.formattedValue}`;
                            },
                            // Customize any additional lines
                        },
                        backgroundColor: 'rgba(0, 0, 0, 0.7)',  // Customize tooltip background color
                        titleColor: '#ffffff',                 // Customize tooltip title color
                        bodyColor: '#ffcc00',                  // Customize tooltip body color
                        padding: 5                            // Tooltip padding
                    }
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
        this.baseCCode = data.baseCCode
        this.baseCName = data.baseCName
        this.comparisonCCode = data.comparisonCCode
        this.comparisonCName = data.comparisonCName
        this.title.textContent = data.title
        data.datasets.forEach(dataset => {
            dataset.backgroundColor = dataset.data.map(item => this.colormap(item.Diff)) // Assign colors dynamically
            dataset.borderColor = dataset.data.map(item => this.colormap(item.Diff).slice(0, -2)) // Assign colors dynamically
            dataset.borderWidth = 1
        })
        this.chart.data.datasets = data.datasets
        this.chart.options.scales.x.title.text = data.title
        this.chart.labels = data.labels
        this.chart.options.plugins.tooltip.callbacks.beforeLabel = (tooltipItem) => {
            const base = `${this.baseCCode} Score: ${tooltipItem.raw.baseScore.toFixed(3)}`;
            const comparison = `${this.comparisonCCode} Score: ${tooltipItem.raw.comparisonScore.toFixed(3)}`;
            return [base, comparison];
        }
        // this.chart.plugins[0].options.LeftCountry = this.baseCName
        // this.chart.plugins[0].options.RightCountry = this.comparisonCName
        this.chart.update()
    }
}
