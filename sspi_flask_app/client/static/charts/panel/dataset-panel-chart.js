class DatasetPanelChart extends PanelChart {
    constructor(parentElement, datasetCode, { CountryList = [], endpointURL = ''} = {} ) {
        super(parentElement, { CountryList: CountryList, endpointURL: `/api/v1/panel/dataset/${datasetCode}`})
        this.datasetCode = datasetCode
    }

    updateDescription(description) {
        const summaryTitle = this.chartOptions.querySelector('.item-information-summary');
        summaryTitle.innerHTML = "Dataset Information";
        const datasetDropdown = this.chartOptions.querySelector('.item-dropdown');
        const defaultValue = '/data/dataset/' + this.datasetCode
        for (const option of description.Options) {
            const opt = document.createElement('option')
            opt.value = '/data/dataset/' + option.datasetCode
            if (option.datasetCode === this.datasetCode) {
                opt.selected = true;
            }
            opt.textContent = option.datasetName + ' (' + option.datasetCode + ')'
            datasetDropdown.appendChild(opt)
        }
        datasetDropdown.addEventListener('change', (event) => {
            window.location.href = event.target.value
        })
        const dbox = this.chartOptions.querySelector('.dynamic-item-description')
        dbox.innerHTML =`
            <div class="item-info-title">${description.Name}</div>
            <ul class="item-detail-list">
                <li class="item-detail-element"><b>Dataset Code:</b> <span class="item-detail-value">${this.datasetCode}</li>
                <li class="item-detail-element"><b>Description:</b> <span class="item-detail-value">${description.Description}</span></li>
            </ul>
        `;
    }

    updateCountryInformation() {
        if (!this.activeCountry) return;
        this.countryInformationBox.dataset.unpopulated = false
        const isPinned = this.activeCountry.pinned || false;
        const pinButtonText = isPinned ? "Unpin Country" : "Pin Country";
        const pinButtonClass = isPinned ? "unpin-country-button" : "pin-country-button";
        let dataset = this.chart.data.datasets.find((ds) => {
            return ds.CCode === this.activeCountry.CCode
        })
        try {
            const avgValue = ( dataset.value.reduce((a, b) => a + b) / dataset.value.length )
            const minValue = Math.min(...dataset.value) 
            const maxValue = Math.max(...dataset.value)
            const minValueYear = dataset.value.findIndex((el) => el === minValue) + 2000
            const maxValueYear = dataset.value.findIndex((el) => el === maxValue) + 2000
            this.countryInformationBox.innerHTML = `
<div id="#active-country-information" class="country-details-info">
<h3 class="country-details-header"><span class="country-name">${this.activeCountry.CFlag}\u0020${this.activeCountry.CName}\u0020(${this.activeCountry.CCode})</span></h3>
<div class="country-details-score-container">
    <div class="summary-stat-line">
        <span class="summary-stat-label">Average:</span> 
        <span class="summary-stat-score">${avgValue.toFixed(3)}</span>
        <span class="summary-stat-year">2000-2023</span>
    </div>
    <div class="summary-stat-line">
        <span class="summary-stat-label">Minimum:</span>
        <span class="summary-stat-score">${minValue.toFixed(3)}</span>
        <span class="summary-stat-year">${minValueYear}</span>
    </div>
    <div class="summary-stat-line">
        <span class="summary-stat-label">Maximum:</span>
        <span class="summary-stat-score">${maxValue.toFixed(3)}</span>
        <span class="summary-stat-year">${maxValueYear}</span>
    </div>
</div>
<div class="country-details-actions">
    <button class="${pinButtonClass}" data-country-code="${this.activeCountry.CCode}">${pinButtonText}</button>
    <a class="view-all-data-link" href="/data/country/${this.activeCountry.CCode}">View All Data</a>
</div>
</div>`;
        } catch (error) {
            console.log(error)
        }
        // Add event listener for Pin/Unpin Country button
        const pinButton = this.countryInformationBox.querySelector('.pin-country-button, .unpin-country-button');
        if (pinButton) {
            pinButton.addEventListener('click', (e) => {
                const countryCode = e.target.dataset.countryCode;
                // Find the feature to toggle
                const dataset = this.chart.data.datasets.find(d => d.CCode === countryCode);
                if (dataset) {
                    this.togglePin(dataset);
                    this.activeCountry = dataset;
                    window.observableStorage.setItem('activeCountry', dataset)
                    this.updateCountryInformation();
                }
            });
        }
    }

    update(data) {
        // Force refresh of chart interaction plugin labels when data changes
        if (this.chartInteractionPlugin && this.chartInteractionPlugin._forceRefreshLabels) {
            this.chartInteractionPlugin._forceRefreshLabels(this.chart)
        }
        this.chart.data = data
        this.chart.data.labels = data.labels
        console.log("Data Labels:", this.chart.data.labels)
        this.chart.data.datasets = data.data
        this.title.innerText = data.title
        this.chart.options.plugins.title = data.title
        this.groupOptions = data.groupOptions
        this.missingCountries = [] // Initialize as empty, will be populated asynchronously
        this.getPins()
        if (this.pinnedOnly) {
            this.hideUnpinned()
        } else {
            this.showGroup(this.countryGroup)
        }
        this.updateLegend()
        this.updateDescription({
            Name: data.datasetName,
            Description: data.description,
            Options: data.datasetOptions
        })
        this.updateCountryGroups()
        if (this.pinnedOnly) {
            this.hideUnpinned()
        }
        this.chart.options.scales.y.min = data.yMin
        this.chart.options.scales.y.max = data.yMax
        this.chart.update()
        this.computeMissingCountriesAsync()
        this.activeCountry = window.observableStorage.getItem("activeCountry") || null;
        if (this.activeCountry) {
            this.updateCountryInformation();
        }
    }
}
