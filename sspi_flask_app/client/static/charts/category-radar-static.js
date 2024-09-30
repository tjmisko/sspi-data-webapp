async function getCategoryRadarData(CountryCode) {
    const data = {
        'BRA': {
            labels: [
                'Category 1', 'Category 2', 'Category 3', 'Category 4', 'Category 5', // Pillar 1
                'Category 6', 'Category 7', 'Category 8', 'Category 9', 'Category 10', // Pillar 2
                'Category 11', 'Category 12', 'Category 13', 'Category 14', 'Category 15', 'Category 16' // Pillar 3
            ],
            datasets: [
                {
                    label: 'Pillar 1',
                    data: [0.65, 0.59, 0.90, 0.81, 0.56, null, null, null, null, null, null, null, null, null, null, null],
                    backgroundColor: '#28a74566',
                    borderColor: '#28a74566',
                    pointBackgroundColor: '#28a74566',
                    pointBorderColor: '#fff',
                    pointHoverBackgroundColor: '#fff',
                    pointHoverBorderColor: '#28a745',
                    fill: true
                },
                {
                    label: 'Pillar 2',
                    data: [null, null, null, null, null, 0.28, 0.48, 0.40, 0.19, 0.96, null, null, null, null, null, null],
                    backgroundColor: '#ff851b66',
                    borderColor: '#ff851b66',
                    pointBackgroundColor: '#ff851b66',
                    pointBorderColor: '#fff',
                    pointHoverBackgroundColor: '#fff',
                    pointHoverBorderColor: '#ff851b66',
                    fill: true
                },
                {
                    label: 'Pillar 3',
                    data: [null, null, null, null, null, null, null, null, null, null, 0.12, 0.80, 0.33, 0.40, 0.50, 0.75],
                    backgroundColor: '#007bff66',
                    borderColor: '#007bff66',
                    pointBackgroundColor: '#007bff66',
                    pointBorderColor: '#fff',
                    pointHoverBackgroundColor: '#fff',
                    pointHoverBorderColor: '#007bff66',
                    fill: true
                }
            ]
        },
        'IND': {
            labels: [
                'Category 1', 'Category 2', 'Category 3', 'Category 4', 'Category 5', // Pillar 1
                'Category 6', 'Category 7', 'Category 8', 'Category 9', 'Category 10', // Pillar 2
                'Category 11', 'Category 12', 'Category 13', 'Category 14', 'Category 15', 'Category 16' // Pillar 3
            ],
            datasets: [
                {
                    label: 'Pillar 1',
                    data: [0.63, 0.09, 0.50, 0.50, 0.53, null, null, null, null, null, null, null, null, null, null, null],
                    backgroundColor: '#28a74566',
                    borderColor: '#28a74566',
                    pointBackgroundColor: '#28a74566',
                    pointBorderColor: '#fff',
                    pointHoverBackgroundColor: '#fff',
                    pointHoverBorderColor: '#28a745',
                    fill: true
                },
                {
                    label: 'Pillar 2',
                    data: [null, null, null, null, null, 0.98, 0.45, 0.63, 0.22, 0.33, null, null, null, null, null, null],
                    backgroundColor: '#ff851b66',
                    borderColor: '#ff851b66',
                    pointBackgroundColor: '#ff851b66',
                    pointBorderColor: '#fff',
                    pointHoverBackgroundColor: '#fff',
                    pointHoverBorderColor: '#ff851b66',
                    fill: true
                },
                {
                    label: 'Pillar 3',
                    data: [null, null, null, null, null, null, null, null, null, null, 0.11, 0.66, 0.65, 0.30, 0.11, 0.74],
                    backgroundColor: '#007bff66',
                    borderColor: '#007bff66',
                    pointBackgroundColor: '#007bff66',
                    pointBorderColor: '#fff',
                    pointHoverBackgroundColor: '#fff',
                    pointHoverBorderColor: '#007bff66',
                    fill: true
                }
            ]
        },
        "IDN": {
            labels: [
                'Category 1', 'Category 2', 'Category 3', 'Category 4', 'Category 5', // Pillar 1
                'Category 6', 'Category 7', 'Category 8', 'Category 9', 'Category 10', // Pillar 2
                'Category 11', 'Category 12', 'Category 13', 'Category 14', 'Category 15', 'Category 16' // Pillar 3
            ],
            datasets: [
                {
                    label: 'Sustainability',
                    data: [0.55, 0.09, 0.50, 0.50, 0.53, null, null, null, null, null, null, null, null, null, null, null],
                    backgroundColor: '#28a74566',
                    borderColor: '#28a74566',
                    pointBackgroundColor: '#28a74566',
                    pointBorderColor: '#fff',
                    pointHoverBackgroundColor: '#fff',
                    pointHoverBorderColor: '#28a745',
                    fill: true
                },
                {
                    label: 'Market Structure',
                    data: [null, null, null, null, null, 0.98, 0.45, 0.63, 0.22, 0.33, null, null, null, null, null, null],
                    backgroundColor: '#ff851b66',
                    borderColor: '#ff851b66',
                    pointBackgroundColor: '#ff851b66',
                    pointBorderColor: '#fff',
                    pointHoverBackgroundColor: '#fff',
                    pointHoverBorderColor: '#ff851b66',
                    fill: true
                },
                {
                    label: 'Public Goods',
                    data: [null, null, null, null, null, null, null, null, null, null, 0.11, 0.66, 0.65, 0.30, 0.11, 0.74],
                    backgroundColor: '#007bff66',
                    borderColor: '#007bff66',
                    pointBackgroundColor: '#007bff66',
                    pointBorderColor: '#fff',
                    pointHoverBackgroundColor: '#fff',
                    pointHoverBorderColor: '#007bff66',
                    fill: true
                }
            ]
        }
    };
    return data[CountryCode];
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
