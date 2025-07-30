const endLabelPlugin = {
    id: 'endLabelPlugin',

    defaults: {
        labelField    : 'CCode', // dataset[field] to show
        occludedAlpha : 0.15,    // opacity for non-selected labels
        animAlpha     : 0.50     // opacity while chart is animating
    },

    /* track mouse position */
    afterEvent(chart, args) {
        const e = args.event;
        if (e && typeof e.x === 'number' && typeof e.y === 'number') {
            chart._endLabelMouse = { x: e.x, y: e.y };
        }
    },

    afterDatasetsDraw(chart, _args, opts) {
        const { ctx } = chart;
        const labels = [];

        /* ----------- 1. Build label list -------------------------------- */
        chart.data.datasets.forEach((ds, i) => {
            if (ds.hidden) return;
            const meta = chart.getDatasetMeta(i);
            if (!meta?.data?.length) return;

            // last defined point in this series
            let last = null;
            for (let j = meta.data.length - 1; j >= 0; --j) {
                const el = meta.data[j];
                if (el?.parsed?.y !== null) { last = el; break; }
            }
            if (!last) return;

            const text = ds[opts.labelField] ?? '';
            ctx.save();
            ctx.font = 'bold 14px Arial';
            const w = ctx.measureText(text).width;
            ctx.restore();

            const x = last.x + 5;
            const y = last.y + 4;

            labels.push({
                idx: i,
                text,
                colour: ds.borderColor ?? '#000',
                x,
                y,
                box: { left: x, right: x + w, top: y - 14, bottom: y },
                occluded: false,
                order: 0
            });
        });

        /* ----------- 2. Animation handling ------------------------------ */
        const animating =
            chart.animating ||
            (chart._animations && chart._animations.size) ||
            (chart.animations && chart.animations.size);

        if (animating) {
            chart._endLabelRandDone = false;
            ctx.save();
            ctx.font = 'bold 14px Arial';
            ctx.globalAlpha = opts.animAlpha;
            labels.forEach(l => {
                ctx.fillStyle = l.colour;
                ctx.textAlign = 'left';
                ctx.fillText(l.text, l.x, l.y);
            });
            ctx.restore();
            return;
        }

        /* ----------- 3. Randomise order once ---------------------------- */
        if (!chart._endLabelRandDone) {
            const orderSeq = labels.map(l => l.idx);
            for (let i = orderSeq.length - 1; i > 0; --i) {
                const k = Math.floor(Math.random() * (i + 1));
                [orderSeq[i], orderSeq[k]] = [orderSeq[k], orderSeq[i]];
            }
            chart._endLabelOrder = Object.fromEntries(
                orderSeq.map((d, pos) => [d, pos])
            );
            chart._endLabelRandDone = true;
        }
        labels.forEach(l => {
            l.order = chart._endLabelOrder[l.idx] ?? 0;
        });

        /* ----------- 4. Sort for occlusion tests ------------------------ */
        labels.sort((a, b) => a.order - b.order); // bottom -> top

        for (let i = 0; i < labels.length; ++i) {
            const a = labels[i];
            for (let j = i + 1; j < labels.length; ++j) {
                const b = labels[j];
                if (
                    a.box.right >= b.box.left &&
                    a.box.left <= b.box.right &&
                    a.box.bottom >= b.box.top &&
                    a.box.top <= b.box.bottom
                ) {
                    a.occluded = true;
                    break;
                }
            }
        }

        /* ----------- 5. Pick dataset closest to cursor ------------------ */
        let closestDatasetIdx = null;
        if (chart._endLabelMouse) {
            const { x: mx, y: my } = chart._endLabelMouse;
            let minD2 = Infinity;
            chart.data.datasets.forEach((ds, i) => {
                if (ds.hidden) return;
                const meta = chart.getDatasetMeta(i);
                if (!meta?.data?.length) return;

                meta.data.forEach(el => {
                    if (!el) return;
                    const dx = el.x - mx;
                    const dy = el.y - my;
                    const d2 = dx * dx + dy * dy;

                    if (d2 < minD2 - 1e-3) {
                        minD2 = d2;
                        closestDatasetIdx = i;
                    } else if (Math.abs(d2 - minD2) < 1e-3) {
                        if (Math.random() < 0.5) closestDatasetIdx = i;
                    }
                });
            });
        }

        const closest = labels.find(l => l.idx === closestDatasetIdx) ?? null;

        /* ----------- 6. Draw ------------------------------------------- */
        if (closest) {
            const k = labels.indexOf(closest);
            if (k > -1) labels.splice(k, 1);
            labels.push(closest); // ensure selected label drawn last (top)
        }

        labels.forEach(l => {
            ctx.save();
            ctx.font = 'bold 14px Arial';
            ctx.fillStyle = l.colour;
            ctx.globalAlpha = l === closest ? 1 : opts.occludedAlpha;
            ctx.textAlign = 'left';
            ctx.fillText(l.text, l.x, l.y);
            ctx.restore();
        });
    }
};
