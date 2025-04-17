const shiftRotatedTicksPlugin = {
  id: 'shiftRotatedTicks',
  afterDraw(chart) {
    const xScale = chart.scales['x'];
    if (!xScale) return;

    const ctx = chart.ctx;
    const ticks = xScale.ticks;
    const options = xScale.options.ticks;
    const rotation = options.maxRotation || 0;
    const rad = rotation * Math.PI / 180;
    const shift = 20; // Adjust as needed

    ctx.save();
    ctx.font = Chart.helpers.toFont(options.font).string;
    ctx.textAlign = 'left';
    ctx.textBaseline = 'middle';

    ticks.forEach((tick, i) => {
      const x = xScale.getPixelForTick(i);
      const y = xScale.bottom + options.padding;
      ctx.save();
      ctx.translate(x, y - shift);
      ctx.rotate(-rad);
      ctx.fillStyle = typeof options.color === 'function' ? options.color({ chart, tick, index: i }) : options.color || '#666';
      ctx.fillText(tick.label, 0, 0);
      ctx.restore();
    });

    ctx.restore();
  }
};


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
        const response = await fetch(`/api/v1/dynamic/matrix`);
        return response.json();
    }

    update(res) {
        this.n_indicators = res.icodes.length;
        this.chart.data = {
            datasets: [{
                label: 'SSPI Data Coverage Matrix',
                data: res.data,
                backgroundColor(context) {
                    const years = context.dataset.data[context.dataIndex].v;
                    const load = context.dataset.data[context.dataIndex].to_be_loaded;
                    const collect = context.dataset.data[context.dataIndex].collect;
                    const compute = context.dataset.data[context.dataIndex].collect;
                    if (years != 0) {
                        const alpha = (years + 5) / 40;
                        return `rgba(15, 200, 15, ${alpha})`;
                    }
                    if (collect && compute) {
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
