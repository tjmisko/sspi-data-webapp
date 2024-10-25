async function getPillarDifferentialStatic(BaseCountry, ComparisonCountry, PillarCode) {
    const response = await fetch(`/api/v1/static/differential/pillar/${PillarCode}?BaseCountry=${BaseCountry}&ComparisonCountry=${ComparisonCountry}`);
    return response.json();
}

async function pillarDifferentialStatic(BaseCountry, ComparisonCountry, PillarCode, canvas) {
    let diff_data = await getPillarDifferentialStatic(BaseCountry, ComparisonCountry, PillarCode).then(data => data);
    console.log(diff_data);

    // const data = 
    const ctx = canvas.getContext('2d');
    const config = {
        type: 'bar',
        data: {
            labels: diff_data.by_category.map(item => item.CategoryCode),
            datasets: diff_data.by_category
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
