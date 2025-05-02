const endLabelPlugin = {
    id: 'endLabelPlugin',
    afterDatasetsDraw(chart) {
        const { ctx } = chart;
        for (let i = 0; i < chart.data.datasets.length; i++) {
            const dataset = chart.data.datasets[i];
            if (dataset.hidden) continue;
            const meta = chart.getDatasetMeta(i);
            if (!meta || !meta.data || meta.data.length === 0) continue;
            let lastPoint = null;
            for (let j = meta.data.length - 1; j >= 0; j--) {
                const element = meta.data[j];
                if (element && element.parsed && element.parsed.y !== null) {
                    lastPoint = element;
                    break;
                }
            }
            if (!lastPoint) continue;
            const value = dataset.CCode ?? '';
            ctx.save();
            ctx.font = 'bold 14px Arial';
            ctx.fillStyle = dataset.borderColor ?? '#000';
            ctx.textAlign = 'left';
            ctx.fillText(value, lastPoint.x + 5, lastPoint.y + 4);
            ctx.restore();
        }
    }
}
