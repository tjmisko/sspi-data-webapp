class PillarPanelChart extends PanelChart {
    constructor(parentElement, pillarCode, { CountryList = [], width = 400, height = 300 } = {} ) {
        super(parentElement, { CountryList: CountryList, endpointURL: `/api/v1/panel/score/${pillarCode}`, width: width, height: height })
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
                    text: 'Pillar Score',
                    color: this.axisTitleColor,
                    font: {
                        size: 16
                    }
                }
            }
        }
    }

    updateDescription(description) {
        // const dbox = document.getElementById("dynamic-pillar-description")
        // dbox.innerText = description
    }
}
