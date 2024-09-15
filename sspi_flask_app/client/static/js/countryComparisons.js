async function fetchComparisonData(country1, country2, country3) {
    country_data = await fetch(`/api/v1/query/sspi_main_data_v3?CountryCode=${country1}&CountryCode=${country2}&CountryCode=${country3}`)
}

function categoryComparison(chartCanvas, categoryCode, country_data) {
    const chartConfig = {
        type: 'bar',
        data: data,
        options: {
            plugins: {
                title: {
                    display: true,
                    text: 'Comparison of Category Scores'
                },
            },
            responsive: true,
            scales: {
                x: {
                    stacked: true,
                },
                y: {
                    stacked: true
                }
            }
        }
    };
}
