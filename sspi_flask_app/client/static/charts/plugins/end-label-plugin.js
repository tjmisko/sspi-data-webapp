const endLabelPlugin = {
    id: 'endLabelPlugin',

    defaults: {
        labelField         : 'CCode', // dataset[field] to show
        occludedAlpha      : 0.15,   // opacity for non-selected labels
        animAlpha          : 0.50,   // opacity while chart is animating
        showDefaultLabels  : true,   // show random non-overlapping subset by default
        defaultLabelSpacing: 5       // minimum spacing between default visible labels (px)
    },

    /* track mouse position - unified with proximity plugin */
    afterEvent(chart, args) {
        const e = args.event;
        if (e && typeof e.x === 'number' && typeof e.y === 'number') {
            chart._unifiedMouse = { x: e.x, y: e.y };
        } else if (e && e.type === "mouseout") {
            chart._unifiedMouse = null;
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

        /* ----------- 4. Build default visible set ------------------------ */
        labels.sort((a, b) => a.order - b.order); // bottom -> top
        
        // Build default visible set of non-overlapping labels
        if (opts.showDefaultLabels && !chart._defaultVisibleLabels) {
            const spacing = opts.defaultLabelSpacing;
            const defaultVisible = new Set();
            
            for (const label of labels) {
                let overlaps = false;
                for (const visibleIdx of defaultVisible) {
                    const visible = labels[visibleIdx];
                    // Check overlap with spacing buffer
                    if (
                        label.box.right + spacing >= visible.box.left - spacing &&
                        label.box.left - spacing <= visible.box.right + spacing &&
                        label.box.bottom + spacing >= visible.box.top - spacing &&
                        label.box.top - spacing <= visible.box.bottom + spacing
                    ) {
                        overlaps = true;
                        break;
                    }
                }
                if (!overlaps) {
                    defaultVisible.add(labels.indexOf(label));
                }
            }
            chart._defaultVisibleLabels = defaultVisible;
        }

        // Traditional occlusion detection for cursor interactions
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
        if (chart._unifiedMouse) {
            const { x: mx, y: my } = chart._unifiedMouse;
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

        labels.forEach((l, i) => {
            ctx.save();
            ctx.font = 'bold 14px Arial';
            ctx.fillStyle = l.colour;
            
            // Determine opacity based on interaction state
            let alpha;
            if (closest) {
                // Mouse interaction: highlight closest, fade others
                alpha = l === closest ? 1 : opts.occludedAlpha;
            } else if (opts.showDefaultLabels && chart._defaultVisibleLabels) {
                // No mouse interaction: show default visible set
                alpha = chart._defaultVisibleLabels.has(i) ? 1 : opts.occludedAlpha;
            } else {
                // Fallback: use original behavior
                alpha = opts.occludedAlpha;
            }
            
            ctx.globalAlpha = alpha;
            ctx.textAlign = 'left';
            ctx.fillText(l.text, l.x, l.y);
            ctx.restore();
        });
    }
};
