

class StaticPillarDifferentialChart {
    constructor(BaseCountry, ComparisonCountry, PillarCode, root) {
        this.BaseCountry = BaseCountry;
        this.ComparisonCountry = ComparisonCountry;
        this.PillarCode = PillarCode;
        this.canvas = canvas;
        this.chart = null;
    }

    async fetch(BaseCountry, ComparisonCountry, PillarCode) {
        const response = await fetch(`/api/v1/static/differential/pillar/${PillarCode}?BaseCountry=${BaseCountry}&ComparisonCountry=${ComparisonCountry}`);
        return response.json();
    }
    initChartJSCanvas() {
        this.canvas = document.createElement('canvas')
        this.canvas.id = `pillar-differential-canvas-${this.PillarCode}-${this.BaseCountry}-${this.ComparisonCountry}`
        this.canvas.width = 200
        this.canvas.height = 200
        this.context = this.canvas.getContext('2d')
        this.root.appendChile(this.canvas)
    }

    update(data) {
        this.chart.data = data
        this.chart.labels = data.labels
        this.chart.update()
    }


}
async function pillarDifferentialStatic(BaseCountry, ComparisonCountry, PillarCode, canvas) {
    diff_data.by_category.forEach(cat => {
        cat.x = cat.Diff;
    })

    // const data = 
    const ctx = canvas.getContext('2d');
    const config = {
        type: 'bar',
        data: {
            labels: diff_data.by_category.map(item => item.CategoryCode),
            datasets: diff_data.by_category.forEach(cat => {
                return {
                    label: cat.CategoryCode,
                    data: cat.Diff,
                    backgroundColor: 'rgba(75, 192, 192, 0.2)',
                    borderColor: 'rgba(75, 192, 192, 1)',
                    borderWidth: 1
                }
            })
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            parsing:
            {
                xAxisKey: 'Diff',
                yAxisKey: 'CategoryCode'
            },
            scales: {
                x: {
                    title: {
                        display: true,
                        text: 'Score Difference (Base - Comparison)'
                    },
                    min: -1,
                    max: 1,
                },
                y: {
                    title: {
                        display: true,
                        text: 'Categories'
                    },
                    type: 'category',
                    reverse: false
                }
            }
        }
    }

    var StaticPillarDifferentialChart = new Chart(ctx, config);
    StaticPillarDifferentialChart.update();
    return StaticPillarDifferentialChart
}
