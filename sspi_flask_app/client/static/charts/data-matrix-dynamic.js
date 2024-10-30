class DynamicMatrixChart {
    constructor(parentElement) {
        this.parentElement = parentElement

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
        this.canvas.width = 400
        this.canvas.height = 400
        this.context = this.canvas.getContext('2d')
        this.root.appendChild(this.canvas)
        this.chart = new Chart(this.context, {
            type: 'matrix',
            options: {
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
                                    return v.problems
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
            }
        })
    }

    async fetch() {
        const response = await fetch(`/api/v1/dynamic/matrix`);
        return response.json();
    }

    update(res) {
        this.n_indicators = res.icodes.length;
        this.chart.data = {
            datasets: [{
                label: 'My Matrix',
                data: res.data,
                backgroundColor(context) {
                    const years = context.dataset.data[context.dataIndex].v;
                    const collect = context.dataset.data[context.dataIndex].collect;
                    const compute = context.dataset.data[context.dataIndex].collect;
                    if (years != 0) {
                        const alpha = (years - 5) / 40;
                        return `rgba(15, 200, 15, ${alpha})`;
                    }
                    if (collect && compute) {
                        return '#FFBF0066';
                    }
                    return "rgba(0, 0, 0, 0)";
                },
                borderColor(context) {
                    const problems = context.dataset.data[context.dataIndex].problems;
                    if (problems) {
                        return "rgba(255, 99, 132, 1)";
                    }
                },
                borderWidth: 1,
                width: ({ chart }) => (chart.chartArea || {}).width / this.n_indicators - 1,
                height: ({ chart }) => (chart.chartArea || {}).height / this.n_indicators - 1
            }]
        }
        this.chart.options.scales = {
            x: {
                type: 'category',
                labels: res.icodes,
                position: 'top',
                ticks: {
                    display: true
                },
                grid: {
                    display: false
                }
            },
            y: {
                type: 'category',
                labels: res.ccodes,
                offset: true,
                reverse: true,
                ticks: {
                    display: true
                },
                grid: {
                    display: false
                }
            }
        }
        this.chart.update()
    }
}
