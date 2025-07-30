class CountrySelector {
    constructor(parentElement, datasets, parentChart) {
        this.parentElement = parentElement
        this.datasets = datasets
        this.parentChart = parentChart
        this.initResultsWindow()
        this.initSearch()
    }

    initResultsWindow() {
        const resultsWindow = document.createElement('div')
        resultsWindow.classList.add('add-country-pin-results-window')
        resultsWindow.classList.add('legend-item')
        resultsWindow.style.display = 'none'
        this.resultsWindow = this.parentElement.parentNode.parentNode.appendChild(resultsWindow)
    }

    initSearch() {
        this.parentElement.innerHTML = `
            <form class="add-country-pin-search-form">
                <input type="text" name="Country" placeholder="Country">
            </form>
        `;
        this.textInput = this.parentElement.querySelector("input")
        this.textInput.focus()
        this.textInput.addEventListener("input", () => this.runSearch())
        this.formElement = this.parentElement.querySelector("form")
        this.formElement.addEventListener("submit", (event) => {
            event.preventDefault()
            this.selectResultEnter()
        })
    }

    selectResultEnter() {
        let CountryCode = this.readResults()
        if (!CountryCode) {
            return
        }
        this.parentChart.pinCountryByCode(CountryCode)
        this.closeResults()
    }

    readResults() {
        let result = this.resultsWindow.querySelector('.add-country-pin-result')
        let CountryCode = result.id.split('-')[0]
        return CountryCode
    }

    async runSearch() {
        const queryString = this.textInput.value
        const options = await this.getOptions(queryString)
        if (options.length === 0) {
            this.resultsWindow.style.display = 'none'
            return
        }
        this.resultsWindow.style.display = 'flex'
        this.resultsWindow.innerHTML = ''
        options.forEach(option => {
            const resultElement = document.createElement('div')
            resultElement.classList.add('add-country-pin-result')
            resultElement.id = option.CCode + '-add-country-pin-result'
            resultElement.addEventListener('click', () => {
                this.selectResultClick(option)
                this.closeResults()
            })
            const resultSpan = document.createElement('span')
            resultSpan.classList.add('add-country-pin-button')

            resultSpan.innerHTML = `
                ${option.CName} (<b style="color: ${option.borderColor};">${option.CCode}</b>)
            `;
            resultElement.appendChild(resultSpan)
            this.resultsWindow.appendChild(resultElement)
        })
    }

    selectResultClick(option) {
        this.parentChart.pinCountry(option)
    }

    async getOptions(queryString, limit = 10) {
        queryString = queryString.toLowerCase()
        if (!queryString) {
            return []
        }
        let optionArray = Array()

        for (let i = 0; i < this.datasets.length; i++) {
            const matched_name = this.datasets[i].CName.toLowerCase().includes(queryString)
            const matched_code = this.datasets[i].CCode.toLowerCase().includes(queryString)
            if (matched_code | matched_name) {  // Condition: only even numbers
                optionArray.push(this.datasets[i]);
            }
            if (optionArray.length === limit) {  // Termination condition
                break;
            }
        }
        return optionArray
    }

    closeResults() {
        this.resultsWindow.remove()
    }
}
