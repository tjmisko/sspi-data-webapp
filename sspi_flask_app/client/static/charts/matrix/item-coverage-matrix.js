class ItemCoverageMatrixChart {
    constructor(parentElement, itemCode, { countryGroup = "SSPI67", minYear = 2000, maxYear = 2023, width = 400, height = 400 } ) {
        this.parentElement = parentElement
        this.itemCode = itemCode
        this.countryGroup = countryGroup
        this.minYear = minYear
        this.maxYear = maxYear
        this.width = width
        this.height = height
        this.initRoot()
        this.initChartJSCanvas()
        this.fetch(`/api/v1/item/coverage/matrix/${this.itemCode}/${this.countryGroup}`).then(res => {
            this.update(res)
        })
    }

    initRoot() {
        this.root = document.createElement('div')
        this.root.classList.add('chart-section-dynamic-matrix')
        this.parentElement.appendChild(this.root)
    }

    initChartJSCanvas() {
        // Initialize the chart canvas
        this.canvas = document.createElement('canvas')
        this.canvas.id = 'dynamic-line-chart-canvas'
        this.canvas.width = this.width
        this.canvas.height = this.height
        this.font = {
            family: 'Courier New',
            size: 12,
            style: "normal",
            weight: "normal"
        }
        this.context = this.canvas.getContext('2d')
        this.root.appendChild(this.canvas)
        this.chart = new Chart(this.context, {
            type: 'matrix',
            options: {
                layout: {
                    padding: {
                        top: 40,
                        right: 25
                    }
                },
                plugins: {
                    legend: false,
                    tooltip: {
                        callbacks: {
                            title() {
                                return 'Dynamic Data Status';
                            },
                            label(context) {
                                const v = context.dataset.data[context.dataIndex];
                                if (v.problems) {
                                    return [
                                        "Issue:" + v.problems,
                                        'Country: ' + v.CName, 
                                        'Indicator: ' + v.IName
                                    ]
                                }
                                return [
                                    'Country: ' + v.CName, 
                                    'Indicator: ' + v.IName, 
                                    'Years: ' + v.v
                                ];
                            }
                        }
                    }
                }
            },
            plugins: [shiftRotatedTicksPlugin]
        })
    }

    async fetch(url) {
        const response = await fetch(url);
        return response.json();
    }

    update(res) {
        this.n_years = res.years.length;
        this.n_countries = res.ccodes.length;
        console.log(res.data)
        this.chart.data = {
            datasets: [{
                label: 'SSPI Data Coverage Matrix',
                data: res.data,
                backgroundColor(context) {
                    // const years = context.dataset.data[context.dataIndex].v;
                    // const load = context.dataset.data[context.dataIndex].to_be_loaded;
                    // const collect = context.dataset.data[context.dataIndex].collect;
                    // if (years != 0) {
                    //     const alpha = (years + 5) / 40;
                    //     return `rgba(15, 200, 15, ${alpha})`;
                    // }
                    // if (collect) {
                    //     return '#FFBF0066';
                    // }
                    // if (load) {
                    //     return '#FFBF00';
                    // }
                    // return "rgba(0, 0, 0, 0)";
                    return "rgba(2000, 0, 0, 0.2)";
                },
                borderColor(context) {
                    return "rgba(200, 0, 0, 1)";
                    // const problems = context.dataset.data[context.dataIndex].problems;
                    // const confident = context.dataset.data[context.dataIndex].confident;
                    // if (problems) {
                    //     return "rgba(255, 99, 132, 1)";
                    // }
                    // if (confident) {
                    //     return `rgba(15, 200, 15, 0.5)`;
                    // }
                },
                borderWidth: 1,
                width: ({ chart }) => (chart.chartArea || {}).width / this.n_years - 2,
                height: ({ chart }) => (chart.chartArea || {}).height / this.n_countries - 2
            }]
        }
        this.chart.options.scales = {
            x: {
                type: 'category',
                labels: res.years,
                position: 'top',
                ticks: {
                    align: "start",
                    color: "#666666",
                    font: this.font,
                    display: true,
                    padding: 10,
                    autoSkip: false,
                    minRotation: 60,
                    maxRoatation: 60,
                    display: false
                },
                grid: {
                    display: true,
                    color: "#666666",
                    drawOnChartArea: false,
                    drawTicks: true
                }
            },
            y: {
                type: 'category',
                labels: res.ccodes,
                offset: true,
                reverse: false,
                ticks: {
                    font: this.font,
                    display: true,
                    autoSkip: false
                },
                grid: {
                    display: true
                }
            }
        }
        this.chart.update()
    }
}
