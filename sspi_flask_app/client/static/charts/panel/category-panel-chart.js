class CategoryPanelChart extends PanelChart {
    constructor(parentElement, categoryCode, { CountryList = [], width = 400, height = 300 } = {} ) {
        super(parentElement, { CountryList: CountryList, endpointURL: `/api/v1/panel/score/${categoryCode}`, width: width, height: height })
    }

    updateChartOptions() {
        this.chart.options.scales = {
            x: {
                ticks: {
                    color: this.tickColor,
                },
                type: "category",
                title: {
                    display: true,
                    text: 'Year',
                    color: this.axisTitleColor,
                    font: {
                        size: 16
                    }
                },
            },
            y: {
                ticks: {
                    color: this.tickColor,
                },
                beginAtZero: true,
                min: 0,
                max: 1,
                title: {
                    display: true,
                    text: 'Indicator Score',
                    color: this.axisTitleColor,
                    font: {
                        size: 16
                    }
                }
            }
        }
    }

    updateDescription(description) {
        // const dbox = document.getElementById("dynamic-indicator-description")
        // dbox.innerText = description
    }
}
