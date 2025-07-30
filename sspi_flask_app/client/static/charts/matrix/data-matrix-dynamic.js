class DynamicMatrixChart {
    constructor(parentElement, countryGroup="SSPI49", width=400, height=400) {
        this.parentElement = parentElement
        this.countryGroup = countryGroup
        this.width = width
        this.height = height

        this.initRoot()
        this.initChartJSCanvas()


        this.fetch().then(res => {
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

    async fetch() {
        const response = await fetch(`/api/v1/dynamic/matrix/${this.countryGroup}`);
        return response.json();
    }

    update(res) {
        this.n_indicators = res.icodes.length;
        this.n_countries = res.ccodes.length;
        this.chart.data = {
            datasets: [{
                label: 'SSPI Data Coverage Matrix',
                data: res.data,
                backgroundColor(context) {
                    const years = context.dataset.data[context.dataIndex].v;
                    const load = context.dataset.data[context.dataIndex].to_be_loaded;
                    const collect = context.dataset.data[context.dataIndex].collect;
                    if (years != 0) {
                        const alpha = (years + 5) / 40;
                        return `rgba(15, 200, 15, ${alpha})`;
                    }
                    if (collect) {
                        return '#FFBF0066';
                    }
                    if (load) {
                        return '#FFBF00';
                    }
                    return "rgba(0, 0, 0, 0)";
                },
                borderColor(context) {
                    const problems = context.dataset.data[context.dataIndex].problems;
                    const confident = context.dataset.data[context.dataIndex].confident;
                    if (problems) {
                        return "rgba(255, 99, 132, 1)";
                    }
                    if (confident) {
                        return `rgba(15, 200, 15, 0.5)`;
                    }
                },
                borderWidth: 1,
                width: ({ chart }) => (chart.chartArea || {}).width / this.n_indicators - 2,
                height: ({ chart }) => (chart.chartArea || {}).height / this.n_countries - 2
            }]
        }
        this.chart.options.scales = {
            x: {
                type: 'category',
                labels: res.icodes,
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
            x2: {
                position: 'top',
                ticks: {
                    font: this.font,
                    type: 'category',
                    display: false,
                    padding: 40,
                    autoSkip: false,
                    callback: function(value, index, ticks) {
                        if (index < 2) { 
                            return 'ECO' 
                        } else if (index >= 2 && index <= 5) {
                            return 'LND'
                        } else {
                            return 'GHG'
                        }
                    }
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
