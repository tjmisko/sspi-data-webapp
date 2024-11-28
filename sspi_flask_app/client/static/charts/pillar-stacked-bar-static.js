function createDiagonalPattern(color) {
    // create a 10x10 px canvas for the pattern's base shape
    let shape = document.createElement('canvas')
    shape.width = 5
    shape.height = 5
    // get the context for drawing
    let c = shape.getContext('2d')
    // draw 1st line of the shape 
    c.strokeStyle = color
    c.beginPath()
    c.moveTo(1, 0)
    c.lineTo(5, 4)
    c.stroke()
    // draw 2nd line of the shape 
    c.beginPath()
    c.moveTo(0, 4)
    c.lineTo(1, 5)
    c.stroke()
    // create the pattern from the shape
    return c.createPattern(shape, 'repeat')
}

function createCrossHatch(color = 'black') {
    // create a 10x10 px canvas for the pattern's base shape
    let shape = document.createElement('canvas')
    shape.width = 4
    shape.height = 4
    // get the context for drawing
    let c = shape.getContext('2d')
    // draw 1st line of the shape 
    c.strokeStyle = color
    c.beginPath()
    c.moveTo(0, 2)
    c.lineTo(4, 2)
    c.stroke()
    return c.createPattern(shape, 'repeat')
}


class StaticPillarStackedBarChart {
    constructor(countryCodes, pillarCode, parentElement, colormap = {}) {
        this.parentElement = parentElement;
        this.textColor = '#bbb';
        this.countryCodes = countryCodes;
        this.pillarCode = pillarCode;
        this.initRoot()
        this.initTitle()
        if (Object.keys(colormap).length === 0) {
            this.initColormap()
        } else {
            this.colormap = colormap
        }
        this.createLegend()
        this.initChartJSCanvas()
        this.fetch().then(data => {
            this.update(data)
        })
    }

    async fetch() {
        let url_string = `/api/v1/static/stacked/pillar/${this.pillarCode}?`;
        for (let i = 0; i < this.countryCodes.length; i++) {
            url_string += `CountryCode=${this.countryCodes[i]}&`;
        }
        url_string = url_string.slice(0, -1); // Remove trailing '&'
        const response = await fetch(url_string);
        return response.json();
    }

    initRoot() {
        // Create the root element
        this.root = document.createElement('div')
        this.root.classList.add('chart-section-pillar-stack')
        this.parentElement.appendChild(this.root)
    }

    initTitle() {
        this.title = document.createElement('h4')
        this.title.classList.add('stack-bar-title')
        this.root.appendChild(this.title)
    }

    initColormap() {
        const colors = [
            "#f95d6a",
            "#ff7c43",
            "#ffa600",
            "#665191",
            "#a05195",
            "#d45087"
        ]
        this.colormap = {}
        this.countryCodes.map((countryCode, index) => {
            this.colormap[countryCode] = colors[index]
        })
        this.patternState = null
        this.patternCount = 0
    }

    createLegend() {
        this.legend = document.createElement('div')
        this.legend.classList.add('stack-bar-legend')
        this.countryCodes.map((countryCode) => {
            const legendElement = document.createElement('div')
            legendElement.classList.add('stack-bar-legend-element')
            const legendBox = document.createElement('div')
            legendBox.classList.add('legend-box')
            legendBox.style.backgroundColor = this.colormap[countryCode]
            legendElement.appendChild(legendBox)
            const legendText = document.createElement('span')
            legendText.id = countryCode + '-' + this.pillarCode + '-stack-bar-legend-text'
            legendText.innerText = countryCode
            legendElement.appendChild(legendText)
            this.legend.appendChild(legendElement)
        })
        this.root.appendChild(this.legend)
    }

    initChartJSCanvas() {
        this.canvas = document.createElement('canvas')
        this.canvas.id = `pillar-differential-canvas-${this.pillarCode}-${this.BaseCountry}-${this.ComparisonCountry}`
        this.canvas.width = 800
        this.canvas.height = 400
        this.context = this.canvas.getContext('2d')
        this.root.appendChild(this.canvas)
        this.chart = new Chart(this.context, {
            type: 'bar',
            options: {
                plugins: {
                    legend: {
                        display: false,
                    },
                    tooltip: {
                        intersect: false,
                        padding: 10,
                        backgroundColor: 'rgba(0, 0, 0, 0.7)',
                        yAlign: 'center',
                        callbacks: {
                            title(context) {
                                if (context.length === 0) {
                                    return
                                }
                                const currentCatName = context[0].label
                                if (currentCatName !== context[0].dataset.CatName) {
                                    return null
                                }
                                return context[0].dataset.CatCode + " - " + context[0].dataset.ICode;
                            },
                            label(context) {
                                const dataset = context.dataset
                                const currentCatName = context.label
                                if (currentCatName !== dataset.CatName) {
                                    return null
                                }
                                return [
                                    'Country: ' + dataset.CName + " " + dataset.flag,
                                    'Indicator: ' + dataset.IName,
                                    'Score: ' + Number.parseFloat(dataset.IScore).toFixed(3),
                                    'Rank: ' + dataset.IRank,
                                ];
                            }
                        }
                    }
                },
                responsive: true,
                barPercentage: 3,
                interaction: {
                    intersect: false,
                },
                scales: {
                    x: {
                        stacked: true,
                        ticks: {
                            color: this.textColor,
                        },
                    },
                    y: {
                        title: {
                            display: true,
                            text: 'Category Score',
                            color: this.textColor,
                        },
                        ticks: {
                            color: this.textColor,
                        },
                        stacked: true,
                        min: 0,
                        max: 1,
                    }
                }
            },
        })
    }

    computePattern(dataset, color) {
        let colorAlpha = color + "AA"
        if (this.patternState === null) {
            this.patternState = dataset.CatCode
            return color
        }
        if (this.patternState === dataset.CatCode) {
            this.patternCount += 1
            if (this.patternCount % 3 === 1) {
                return createDiagonalPattern(colorAlpha)
            } else if (this.patternCount % 3 === 2) {
                return createCrossHatch(colorAlpha)
            }
            return colorAlpha
        }
        this.patternState = dataset.CatCode
        this.patternCount = 0
        return colorAlpha
    }

    update(data) {
        this.chart.data.datasets = data.datasets
        this.chart.data.labels = data.labels
        this.chart.data.datasets.forEach((dataset) => {
            const color = this.colormap[dataset.CCode]
            const pattern = this.computePattern(dataset, color)
            dataset.backgroundColor = pattern
            dataset.borderColor = color
            dataset.borderWidth = 1
        })
        Array.from(this.legend.children).forEach((item) => {
            const cou = item.querySelector('span').id.split('-')[0]
            const flag = data.codeMap[cou].flag
            const name = data.codeMap[cou].name
            item.querySelector('span').innerText = name + " (" + cou + ")"
        })
        this.title.innerText = data.title
        this.chart.update()
    }
}
