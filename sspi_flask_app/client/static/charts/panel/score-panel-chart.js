class ScorePanelChart extends PanelChart {
    constructor(parentElement, itemCode, { CountryList = [], width = 600, height = 600 } = {} ) {
        super(parentElement, { CountryList: CountryList, endpointURL: `/api/v1/panel/score/${itemCode}`, width: width, height: height })
        this.itemCode = itemCode
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

    updateItemDropdown(options) {
        for (const option of options) {
            const opt = document.createElement('option')
            opt.value = option.Value
            opt.textContent = option.Text;
            this.itemDropdown.appendChild(opt)
        }
        const defaultValue = '/data/' + options[0].Value.split('/')[2] + '/' + this.itemCode
        this.itemDropdown.value = defaultValue
        this.itemDropdown.addEventListener('change', (event) => {
            window.location.href = event.target.value
        })
    }
}
