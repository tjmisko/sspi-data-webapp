async function getCategoryRadarData(CountryCode) {
    const response = await fetch(`/api/v1/static/radar/${CountryCode}`);
    return response.json();
}

async function categoryRadarStatic(CountryCode, canvas) {
    const data = await getCategoryRadarData(CountryCode).then(data => data);
        
    canvas.width = 400;
    canvas.height = 400;

    const ctx = canvas.getContext('2d');

    const config = {
        type: 'polarArea',
        data: data,
        options: {
            responsive: true,
            elements: {
                line: {
                    borderWidth: 3
                }
            },
            scales: {
                r: {
                    pointLabels: {
                        display: true,
                        font: {
                            size: 8
                        },
                        color: "#ccc",
                        boxWidth: 0,
                    },
                    grid: {
                        color: '#cccccc33',
                        circular: true
                    },
                    ticks: {
                        backdropColor: 'rgba(0, 0, 0, 0)',
                        clip: true,
                        font: {
                            size: 8   
                        }
                    },
                    suggestedMin: 0,
                    suggestedMax: 1

                }
            },
            plugins: {
                tooltip: {
                    backgroundColor: '#1B2A3Ccc',
                    callbacks: {
                        title: function(context) {
                            return `${context[0].label}`
                        },
                        label: function(context) {
                            const score = context.raw;
                            console.log(context.dataset.label)
                            return [`Category Score: ${score}`] 
                        }
                    }
                },
            }
        }
    };

    var CountryComparisonStaticChart = new Chart(ctx, config);
    // CountryComparisonStaticChart.update() 
    Chart.overrides["polarArea"].plugins.legend = {
        display: true,
        position: 'top',
        labels: {
            fontColor: '#ccc'
        }
    }        

    CountryComparisonStaticChart.update();
    return CountryComparisonStaticChart
}
