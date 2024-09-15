async function categoryRadarStatic(CountryCode) {
    // fetch data
    const categoryData = await fetch(`/api/v1/chart/radar/${CountryCode}`).then((data) => data.json())
    // create and return a canvas with the chart

    return chartCanvas
}
