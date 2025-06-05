const proximityPlugin = {
    id: 'proximityHighlight',
    defaults: {
        enabled     : true,          // ← toggle here or per chart
        radius      : 20,
        circleColor : 'rgba(0,0,0,.5)',
        circleWidth : 1,
        fadeAlpha   : 0.1
    },
    _mouse: null,                   // last mouse position
    afterEvent(chart, {event}) {
        if (!event) return;
        if (event.type === 'mousemove')  this._mouse = {x: event.x, y: event.y};
        if (event.type === 'mouseout')   this._mouse = null;
        chart.draw();                   // immediate redraw, no animation
    },

    beforeDatasetsDraw(chart, _args, opts) {
        const pos = this._mouse;
        if (!pos) return resetAll();    // no cursor → restore originals
        const R = opts?.radius ?? 20;   // px
        const ctx = chart.ctx;
        let anyNear = false;
        chart.data.datasets.forEach((ds, i) => {
            const meta = chart.getDatasetMeta(i);
            // cache original colours once
            ds._full ??= {border: ds.borderColor, bg: ds.backgroundColor};
            ds._faded ??= fade(ds._full.border, 0.1);
            const near = meta.data.some(pt => {
                const dx = pt.x - pos.x, dy = pt.y - pos.y;
                return dx*dx + dy*dy <= R*R;
            }) && !ds.hidden;
            if (near) anyNear = true
            ds.borderColor     = near ? ds._full.border : ds._faded;
            ds.backgroundColor = near ? ds._full.bg     : ds._faded;
            const lineEl = meta.dataset;
            if (lineEl) lineEl.options.borderColor = ds.borderColor;
            meta.data.forEach(pt => {
                pt.options.backgroundColor = ds.backgroundColor;
                pt.options.borderColor     = ds.borderColor;
            });
        });
        if (!anyNear) return resetAll();    // no dataset is near → restore originals

        // guide circle
        ctx.save();
        ctx.beginPath();
        ctx.arc(pos.x, pos.y, R, 0, 2*Math.PI);
        ctx.strokeStyle = opts?.circleColor || 'rgba(0,0,0,.5)';
        ctx.lineWidth   = opts?.circleWidth || 1;
        ctx.setLineDash([3, 3]);
        ctx.stroke();
        ctx.restore();

        function resetAll() {
            chart.data.datasets.forEach((ds, i) => {
                if (!ds._full) return;
                ds.borderColor     = ds._full.border;
                ds.backgroundColor = ds._full.bg;

                // sync reset on elements too
                const meta = chart.getDatasetMeta(i);
                if (meta?.dataset) meta.dataset.options.borderColor = ds.borderColor;
                meta?.data.forEach(pt => {
                    pt.options.backgroundColor = ds.backgroundColor;
                    pt.options.borderColor     = ds.borderColor;
                });
            });        
        }

        function fade(col, a) {
            if (col.startsWith('rgba')) return col.replace(/, *[^,]+\)$/, `, ${a})`);
            if (col.startsWith('rgb'))  return col.replace('rgb', 'rgba').replace(')', `, ${a})`);
            if (col.startsWith('#')) { return col + "22" }
            return col; // fallback – supply rgba in your data for best results
        }
    }
};
