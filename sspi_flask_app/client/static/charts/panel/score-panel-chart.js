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

    updateItemDropdown(options, itemType) {
        let itemTypeCapped = itemType
        if (itemType === "sspi") {
            itemTypeCapped = this.itemType.toUpperCase()
        } else {
            itemTypeCapped = this.itemType.charAt(0).toUpperCase() + this.itemType.slice(1)
        }
        const itemTitle = itemTypeCapped + ' Information';
        const itemSummary = this.itemInformation.querySelector('.item-information-summary')
        itemSummary.textContent = itemTitle;
        const defaultValue = '/data/' + itemType.toLowerCase() + '/' + this.itemCode
        console.log('Default value for item dropdown:', defaultValue)
        for (const option of options) {
            const opt = document.createElement('option')
            opt.value = option.Value
            if (option.Value === defaultValue) {
                opt.selected = true;
            }
            opt.textContent = option.Text;
            this.itemDropdown.appendChild(opt)
        }
        this.itemDropdown.addEventListener('change', (event) => {
            window.location.href = event.target.value
        })
    }
}
