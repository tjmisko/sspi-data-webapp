async function getPillarDifferentialStatic(BaseCountry, ComparisonCountry, PillarCode) {
    const response = await fetch(`/api/v1/static/pillar/differential/${PillarCode}?BaseCountry=${BaseCountry}&ComparisonCountry=${ComparisonCountry}`);
    return response.json();
}

async function pillarDifferentialStatic(BaseCountry, ComparisonCountry, PillarCode, canvas) {
    const res = await getPillarDifferentialStatic(BaseCountry, ComparisonCountry, PillarCode).then(data => data);
    console.log(res);

    // const data = 
    const ctx = canvas.getContext('2d');
    const config = {
        type: 'bar',
    }

    var StaticPillarDifferentialChart = new Chart(ctx, config);
    StaticPillarDifferentialChart.update();
    return StaticPillarDifferentialChart
}
