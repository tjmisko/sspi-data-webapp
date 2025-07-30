class OutcomeScatterStatic {
    constructor(parentElement, outcomeVariable) {
        this.outcomeVariable = outcomeVariable
        this.parentElement = parentElement;
        this.initRoot()
        // this.initTitle()
        // this.initChartJSCanvas()
        // this.fetch().then(data => {
        //     this.update(data)
        // })
    }

    async fetch() {
        const response = await fetch(`/api/v1/...`);
        return response.json();
    }

    initRoot() {
        // Create the root element
        this.root = document.createElement('div')
        this.root.classList.add('outcome-scatter-static')
        this.parentElement.appendChild(this.root)
    }

    initTitle() {
    }

    initChartJSCanvas() {
    }

    update(data) {
    }
}
