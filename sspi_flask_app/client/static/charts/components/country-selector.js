class CountrySelector {
    constructor(parentElement, resultsWindow, datasets, parentChart) {
        this.parentElement = parentElement
        this.buttonHTML = parentElement.innerHTML
        this.resultsWindow = resultsWindow
        this.datasets = datasets
        this.parentChart = parentChart
        this.searchSelectorIndex = -1;
        this.initResultsWindow()
        this.initSearch()
    }

    initResultsWindow() {
        const resultsWindow = document.createElement('div')
        this.resultsWindow.style.display = 'none'
    }

    initSearch() {
        this.parentElement.innerHTML = `
            <form class="add-country-pin-search-form">
                <input type="text" name="Country" placeholder="Country Name or Code" autocomplete="off">
            </form>
        `;
        this.textInput = this.parentElement.querySelector("input")
        this.textInput.focus()
        this.textInput.addEventListener("keydown", () => {
            if (event.key === "ArrowDown" && this.searchSelectorIndex < this.resultsWindow.children.length - 1) {
                this.searchSelectorIndex++
                this.highlightSelectedIndex()
            } else if (event.key == "ArrowUp" && this.searchSelectorIndex > -1) {
                this.searchSelectorIndex--
                this.highlightSelectedIndex()
            }
        })
        this.textInput.addEventListener("focusout", (event) => {
            // teardown on focusout
            setTimeout(() => {
                console.log("Teardown!")
                this.parentElement.innerHTML = this.buttonHTML;
                this.closeResults();
            }, 100);
        })
        this.textInput.addEventListener("input", () => this.runSearch())
        this.formElement = this.parentElement.querySelector("form")
        this.formElement.addEventListener("submit", (event) => {
            event.preventDefault()
            this.selectResultEnter()
        })
    }

    selectResultEnter() {
        let countryCode = this.readResults()
        if (!countryCode | countryCode === null) {
            return
        }
        this.parentChart.pinCountryByCode(countryCode)
        this.closeResults()
        this.textInput.value = "";
    }

    readResults() {
        let result = null;
        if (this.resultsWindow.style.display == 'none') {
            return result
        } else if (this.searchSelectorIndex === -1) {
            result = this.resultsWindow.children[0]
        } else {
            result = this.resultsWindow.children[this.searchSelectorIndex]
        }
        if (result === null) {
            return null;
        }
        const countryCode = result.id.split('-')[0]
        return countryCode 

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
        options.forEach((option, i) => {
            const resultElement = document.createElement('div')
            resultElement.classList.add('add-country-pin-result')
            resultElement.id = option.CCode + '-add-country-pin-result'
            const resultSpan = document.createElement('span')
            resultSpan.classList.add('add-country-pin-button')
            resultSpan.innerHTML = option.CName + ' (<b style="color:' + option.borderColor + '">' + option.CCode + '</b>)';
            resultSpan.addEventListener('click', (event) => {
                this.selectResultClick(option)
                this.closeResults()
            })
            resultElement.appendChild(resultSpan)
            this.resultsWindow.appendChild(resultElement)
        })
        this.highlightSelectedIndex();
    }

    selectResultClick(option) {
        this.parentChart.pinCountryByCode(option.CCode)
    }

    async getOptions(queryString, limit = 10) {
        queryString = queryString.toLowerCase()
        if (!queryString) {
            return []
        }
        let optionArray = Array()

        for (let i = 0; i < this.datasets.length; i++) {
            const dataset = this.datasets[i]
            // Skip datasets without CName or CCode
            if (!dataset || !dataset.CName || !dataset.CCode) {
                continue
            }
            const matched_name = dataset.CName.toLowerCase().includes(queryString)
            const matched_code = dataset.CCode.toLowerCase().includes(queryString)
            if (matched_code | matched_name) {
                optionArray.push(dataset);
            }
            if (optionArray.length === limit) {  // Termination condition
                break;
            }
        }
        return optionArray
    }

    closeResults() {
        this.resultsWindow.innerHTML = '';
        this.resultsWindow.style.display = 'none';
    }

    highlightSelectedIndex() { 
        if (this.searchSelectorIndex > this.resultsWindow.children.length - 1) {
            this.searchSelectorIndex = this.resultsWindow.children.length - 1
        }
        for (var j = 0; j < this.resultsWindow.children.length; j++) {
            if (this.searchSelectorIndex === j) {
                this.resultsWindow.children[this.searchSelectorIndex].classList.add('search-result-index-selected');
            } else {
                this.resultsWindow.children[j].classList.remove('search-result-index-selected');
            }
        }
    }
}
    
