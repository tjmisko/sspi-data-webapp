const extrapolateBackwardPlugin = {
    id: 'extrapolateBackward',
    hidden: false,
    toggle(hidden) {
        this.hidden = hidden !== undefined ? hidden : !this.hidden;
    },
    afterDatasetsDraw(chart) {
        if (this.hidden) return;
        const { ctx, chartArea: { left } } = chart;
        for (let i = 0; i < chart.data.datasets.length; i++) {
            const dataset = chart.data.datasets[i];
            if (dataset.hidden) continue;
            const meta = chart.getDatasetMeta(i);
            if (!meta || !meta.data || meta.data.length === 0) continue;
            let firstElement = null;
            for (let j = 0; j < meta.data.length; j++) {
                const element = meta.data[j];
                if (element && element.parsed && element.parsed.y !== null) {
                    firstElement = element;
                    break;
                }
            }
            if (!firstElement) continue;
            const firstPixelX = firstElement.x;
            const firstPixelY = firstElement.y;
            if (firstPixelX > left) {
                ctx.save();
                ctx.beginPath();
                ctx.setLineDash([2, 4]);
                ctx.moveTo(left, firstPixelY);
                ctx.lineTo(firstPixelX, firstPixelY);
                ctx.strokeStyle = dataset.borderColor ?? 'rgba(0,0,0,0.5)';
                ctx.lineWidth = 1;
                ctx.stroke();
                ctx.restore();
            }
        }
    }
};
