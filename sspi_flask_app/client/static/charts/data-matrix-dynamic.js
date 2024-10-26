async function getMatrixDynamicData() {
    const response = await fetch(`/api/v1/dynamic/matrix`);
    return response.json();
}

async function dataMatrixDynamic(canvas) {
    const res = await getMatrixDynamicData().then(data => data);
    const n_indicators = res.icodes.length;

    // Map categories to numbers and provide corresponding data
    const data = {
        datasets: [{
            label: 'My Matrix',
            data: res.data,
            backgroundColor(context) {
                const value = context.dataset.data[context.dataIndex].v;
                const alpha = (value - 5) / 40;
                return "rgba(255, 99, 132, " + alpha + ")";
            },
            borderColor(context) {
                const value = context.dataset.data[context.dataIndex].v;
                const alpha = (value - 5) / 40;
                return "rgba(0, 0, 0, " + alpha + ")";
            },
            borderWidth: 1,
            width: ({chart}) => (chart.chartArea || {}).width / n_indicators - 1,
            height: ({chart}) =>(chart.chartArea || {}).height / n_indicators - 1
        }]
    };

    const ctx = canvas.getContext('2d');
    const config = {
        type: 'matrix',
        data: data,
        options: {
            plugins: {
                legend: false,
                tooltip: {
                    callbacks: {
                        title() {
                            return '';
                        },
                        label(context) {
                            const v = context.dataset.data[context.dataIndex];
                            return ['x: ' + v.x, 'y: ' + v.y, 'v: ' + v.v];
                        }
                    }
                }
            },
            scales: {
                x: {
                    type: 'category',
                    labels: res.icodes,
                    position: 'top',
                    ticks: {
                        display: true
                    },
                    grid: {
                        display: false
                    }
                },
                y: {
                    type: 'category',
                    labels: res.ccodes,
                    reverse: true,
                    offset: true,
                    ticks: {
                        display: true
                    },
                    grid: {
                        display: false
                    }
                }
            }
        }
    };


    var DataMatrixOverviewChart = new Chart(ctx, config);
    DataMatrixOverviewChart.update();
    return DataMatrixOverviewChart
}
