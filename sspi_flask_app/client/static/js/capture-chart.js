function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

function captureChart(chartObject, alpha = false) {
    const textColorOriginal = chartObject.textColor
    const gridColorOriginal = chartObject.gridColor
    chartObject.textColor = '#222'
    chartObject.gridColor = '#777'
    chartObject.chart.update()
    sleep(1000).then(() => {
        if (alpha) {
            html2canvas(chartObject.parentElement, { backgroundColor: null }).then(canvas => {
                const link = document.createElement('a');
                link.download = chartObject.parentElement.id + '.png';
                link.href = canvas.toDataURL('image/png');
                link.click();
            });
        } else {
            html2canvas(chartObject.parentElement).then(canvas => {
                const link = document.createElement('a');
                link.download = chartObject.parentElement.id + '.png';
                link.href = canvas.toDataURL('image/png');
                link.click();
            });
        }
        chartObject.textColor = textColorOriginal
        chartObject.gridColor = gridColorOriginal
        chartObject.chart.update()
    })
};
