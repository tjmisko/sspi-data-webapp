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
        this.rigSummary()
        this.initChartJSCanvas()
        this.fetch(`/api/v1/item/coverage/matrix/${this.itemCode}/${this.countryGroup}`).then(res => {
            this.update(res)
        })
    }

    initRoot() {
        this.root = document.createElement('div')
        this.root.classList.add('coverage-section-dynamic-matrix')
        this.parentElement.appendChild(this.root)
    }

    rigSummary() {
        // Create a summary section
        this.summary = document.createElement('div')
        this.summary.classList.add('item-coverage-summary')
        this.root.appendChild(this.summary)
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
                                return 'Data Coverage';
                            },
                            label(context) {
                                const v = context.dataset.data[context.dataIndex];
                                return [
                                    'Country Code: ' + v.x, 
                                    'Year: ' + v.y, 
                                    'Coverage Level: ' + v.v + ' / ' + v.vComplete,
                                    'Data Available: ' + (v.intermediateCodes ? v.intermediateCodes.join(', ') : 'None')
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
        this.vComplete = res.vComplete;
        res.summary.forEach((line, i) => {
            const summaryLine = document.createElement('div');
            summaryLine.classList.add('item-coverage-summary-line');
            summaryLine.innerHTML = `<span class="item-coverage-summary-color-block"></span><span class="item-coverage-summary-country">${line}</span>`;
            const color = summaryLine.querySelector('.item-coverage-summary-color-block')
            color.classList.add(`coverage-summary-color-${i}`);
            this.summary.appendChild(summaryLine);
        });
        this.chart.data = {
            datasets: [{
                label: 'SSPI Data Coverage Matrix',
                data: res.data,
                backgroundColor(context) {
                    if (context.dataset.data[context.dataIndex].v === context.dataset.data[context.dataIndex].vComplete) {
                        return "rgba(0, 200, 0, 0.2)";
                    } else if (context.dataset.data[context.dataIndex].v ===  context.dataset.data[context.dataIndex].vComplete - 1) {
                        return "rgba(200, 200, 0, 0.2)";
                    } else {
                        return "rgba(200, 0, 0, 0.2)";
                    }
                },
                borderColor(context) {
                    if (context.dataset.data[context.dataIndex].v == context.dataset.data[context.dataIndex].vComplete) {
                        return "rgba(0, 200, 0, 1)";
                    } else if (context.dataset.data[context.dataIndex].v ==  context.dataset.data[context.dataIndex].vComplete - 1) {
                        return "rgba(200, 200, 0, 1)";
                    } else {
                        return "rgba(200, 0, 0, 1)";
                    }
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
