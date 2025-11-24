/* ---------------------------------------------------------------------
 *  Chart Interaction Plugin
 *  -------------------------------------------------------------
 *  Combines proximity highlighting and end label functionality:
 *  
 *  PROXIMITY FEATURES:
 *  • Tooltip rows: CName (CCode): 12.345 #3 / 12
 *  • Points inside clickRadius grow by 60%
 *  • Lines fade based on proximity to cursor
 *  • Optional onDatasetClick callback for pinning
 *  
 *  LABEL FEATURES:
 *  • End labels at last data point of each series
 *  • Smart default visibility (random non-overlapping subset)
 *  • Proximity-based label highlighting
 *  • Configurable label spacing and opacity
 * ------------------------------------------------------------------ */
const chartInteractionPlugin = {
    id: "chartInteractionPlugin",

    defaults: {
        // Core settings
        enabled: true,

        // Proximity settings
        radius: 20,
        clickRadius: 5,
        fadeAlpha: 0.1,

        // Visual guide settings
        circleColor: "#bbbbbb",
        circleWidth: 1,
        guideColor: "#bbbbbb",
        guideWidth: 1,
        guideDash: [],

        // Tooltip settings
        tooltipBg: "rgba(255,255,255,0.85)",
        tooltipFg: "#111",
        tooltipFgAccent: "#AECC53",
        tooltipFont: "12px sans-serif",
        tooltipPad: 8,
        tooltipGap: 10,
        colGap: 6,

        // Label settings
        labelField: 'CCode',
        showDefaultLabels: true,
        defaultLabelSpacing: 0,
        occludedAlpha: 0.12,
        animAlpha: 0.50,

        // Comparison series settings
        comparisonEnabled: false,
        comparisonOpacity: 0.35,
        comparisonDashPattern: [6, 4],
        comparisonLineWidth: 1.5,
        comparisonDataField: 'comparisonScores',

        // Callbacks
        onDatasetClick: null
    },

    // Internal state - unified interaction data
    _interaction: {
        mouse: null,
        nearest: null,
        tooltipItems: null,
        closestDatasetIdx: null
    },

    // Collision detection throttling
    _lastCollisionTime: 0,
    _collisionCooldown: 1000, // Minimum milliseconds between collision detections

    // Constants
    _LABEL_FONT: 'bold 16px Arial',
    _POINT_SCALE: 1.6,

    setExternalHover(chart, datasetIndex) {
        this._interaction.mouse = null;               // turn off normal proximity
        this._interaction.closestDatasetIdx = datasetIndex;
        this._interaction.tooltipItems = null;        // no tooltip
        chart.update('none');                         // redraw without animation
    },

    /* ---------- data change detection -------------------------------- */
    beforeUpdate(chart, args, opts) {
        // Clear label state when data changes to force rebuild with new data
        if (args.mode !== 'resize') {
            this._clearLabelState(chart);
            // Reset collision throttle to allow immediate recalculation after data change
            this._lastCollisionTime = 0;
        }
    },

    /* ---------- unified mouse & click tracking ----------------------- */
    afterEvent(chart, args) {
        const cfg = chart.options.plugins && chart.options.plugins.chartInteractionPlugin;
        if (!cfg || !cfg.enabled) return;
        const ev = args.event;
        if (!ev) return;

        if (ev.type === "mousemove") {
            this._interaction.mouse = { x: ev.x, y: ev.y };
        } else if (ev.type === "mouseout") {
            this._interaction.mouse = null;
        } else if (ev.type === "click") {
            const r2 = (cfg.clickRadius ?? this.defaults.clickRadius) ** 2;
            const hit = [];
            chart.data.datasets.forEach((ds, i) => {
                if (ds.hidden) return;
                const meta = chart.getDatasetMeta(i);
                if (!meta) return;
                if (meta.data.some(pt => {
                    const dx = pt.x - ev.x, dy = pt.y - ev.y;
                    return dx * dx + dy * dy <= r2;
                })) hit.push(ds);
            });
            if (hit.length && typeof cfg.onDatasetClick === "function") {
                try { cfg.onDatasetClick(hit, ev, chart); }
                catch (e) { console.error("chartInteractionPlugin onDatasetClick:", e); }
            }
        }
        chart.draw();
    },

    /* ---------- main proximity & label logic ------------------------- */
    beforeDatasetsDraw(chart, _args, opts) {
        const ctx = chart.ctx;
        const area = chart.chartArea;

        // If plugin disabled, just bail (no custom clip, but you also shouldn't have disabled ds.clip)
        if (!opts || !opts.enabled) {
            this._resetProximity(chart);
            return;
        }

        // 1. Disable per-dataset internal clipping
        chart.data.datasets.forEach(ds => {
            ds.clip = false;
        });

        // 2. Always apply our own clip for dataset drawing
        ctx.save();
        ctx.beginPath();
        ctx.rect(area.left, area.top, area.right - area.left, area.bottom - area.top);
        ctx.clip();
        chart._interactionClipApplied = true;  // mark that we did a save()

        // 2.5. Draw comparison series FIRST (background layer, before proximity guides and datasets)
        this._drawComparisonSeries(chart, opts);

        // 3. Now do interaction logic; but DO NOT early-return before datasets draw
        const pos = this._interaction.mouse;
        const externalIdx = this._interaction.closestDatasetIdx;
        const isExternalHover = !pos && externalIdx !== null;


        if (!pos && !isExternalHover) { // No mouse: reset proximity state, but do not touch clipping.
            this._resetProximity(chart);
            return;
        }


        const R = opts.radius;
        const CR = opts.clickRadius;
        const cr2 = CR * CR;

        // Initialize unified tracking
        let nearest = { d2: Infinity, x: null, idx: null, valX: null };
        let closestDatasetMinD2 = Infinity;
        let anyNear = false;

        if (!isExternalHover) {
            this._interaction.closestDatasetIdx = null;
        }

        /* Single loop: find nearest point, closest dataset, apply proximity effects */
        chart.data.datasets.forEach((ds, i) => {
            const meta = chart.getDatasetMeta(i);
            if (ds.hidden || !meta?.data?.length) { 
                ds._isNear = ds._isHover = false; 
                return; 
            }

            // Initialize colors once
            ds._full = ds._full || { border: ds.borderColor, bg: ds.backgroundColor };
            ds._faded = ds._faded || this._fade(ds._full.border, opts.fadeAlpha);

            if (isExternalHover) {
                // Highlight this dataset only
                const isTarget = i === externalIdx;

                ds.borderColor = isTarget ? ds._full.border : ds._faded;
                ds.backgroundColor = isTarget ? ds._full.bg : ds._faded;
                ds._isNear = isTarget;
                ds._isHover = false;

                const meta = chart.getDatasetMeta(i);
                meta?.data?.forEach(p => {
                    p.options.backgroundColor = ds.backgroundColor;
                    p.options.borderColor = ds.borderColor;
                });

                return
            }

            // Find nearest point and closest dataset in same pass
            let datasetClosestD2 = Infinity;
            meta.data.forEach((pt, colIdx) => {
                if (!pt) return;
                const dx = pt.x - pos.x, dy = pt.y - pos.y, d2 = dx * dx + dy * dy;

                // Track global nearest point
                if (d2 < nearest.d2) nearest = {
                    d2, x: pt.x, idx: colIdx,
                    valX: pt.parsed?.x ?? colIdx
                };

                // Track closest point in this dataset
                if (d2 < datasetClosestD2) datasetClosestD2 = d2;
            });

            // Update closest dataset
            if (datasetClosestD2 < closestDatasetMinD2 - 1e-3) {
                closestDatasetMinD2 = datasetClosestD2;
                this._interaction.closestDatasetIdx = i;
            } else if (Math.abs(datasetClosestD2 - closestDatasetMinD2) < 1e-3) {
                if (Math.random() < 0.5) this._interaction.closestDatasetIdx = i;
            }

            // Apply proximity effects if within range
            const pt = meta.data[nearest.idx];
            const d2pt = pt ? (pt.x - pos.x) ** 2 + (pt.y - pos.y) ** 2 : Infinity;
            const near = d2pt <= R * R;
            const hover = d2pt <= cr2;

            ds._isNear = near;
            ds._isHover = hover;
            if (near) anyNear = true;

            // Apply colors and point scaling
            ds.borderColor = near ? ds._full.border : ds._faded;
            ds.backgroundColor = near ? ds._full.bg : ds._faded;
            if (meta.dataset) meta.dataset.options.borderColor = ds.borderColor;

            meta.data.forEach(p => {
                p.options.backgroundColor = ds.backgroundColor;
                p.options.borderColor = ds.borderColor;

                const clickNear = (p.x - pos.x) ** 2 + (p.y - pos.y) ** 2 <= cr2;
                if (clickNear) {
                    if (p.__origR === undefined)
                        p.__origR = p.options.radius ?? p.radius ?? 3;
                    p.options.radius = p.__origR * this._POINT_SCALE;
                } else if (p.__origR !== undefined) {
                    p.options.radius = p.__origR;
                }
            });
        });

        if (!anyNear && !isExternalHover) {
            this._resetProximity(chart);
            return;
        }

        if (!pos) {
            return;
        }
        // Store nearest info for tooltip positioning
        this._interaction.nearest = nearest;

        /* circle + guide */
        ctx.save();
        ctx.beginPath();
        ctx.arc(pos.x, pos.y, R, 0, 2 * Math.PI);
        ctx.strokeStyle = opts.circleColor;
        ctx.lineWidth = opts.circleWidth;
        ctx.setLineDash([3,3]);
        ctx.stroke();
        ctx.beginPath();
        ctx.moveTo(nearest.x, area.top);
        ctx.lineTo(nearest.x, area.bottom);
        ctx.strokeStyle = opts.guideColor;
        ctx.lineWidth = opts.guideWidth;
        ctx.setLineDash(opts.guideDash);
        ctx.stroke();
        ctx.restore();

        /* prepare tooltip data */
        const vis = [];
        chart.data.datasets.forEach((ds, i) => {
            if (ds.hidden) return;
            const el = chart.getDatasetMeta(i).data[nearest.idx];
            const v = el?.parsed?.y ?? el?.raw;
            if (v == null || isNaN(v)) return;
            vis.push({ i, v });
        });
        vis.sort((a,b) => b.v - a.v);
        const tot = vis.length, rankMap = {};
        vis.forEach((o,r) => rankMap[o.i] = "#" + (r+1) + " / " + tot);

        /* tooltip items */
        const items = [];
        chart.data.datasets.forEach((ds, i) => {
            if (!ds._isNear) return;
            const el = chart.getDatasetMeta(i).data[nearest.idx];
            let val = el?.parsed?.y ?? el?.raw;
            if (typeof val === "number") val = val.toFixed(3);

            const prefix = ds.CName ? ds.CName + " (" + ds.CCode + ")"
                : (ds.CCode ? ds.CCode + ":" : `Series ${i+1}:`);

            items.push({
                prefix, value: val, rank: rankMap[i] || "",
                colour: ds._full ? ds._full.border : ds.borderColor,
                y: el.y, hover: ds._isHover
            });
        });
        items.sort((a,b) => a.y - b.y);

        this._interaction.tooltipItems = items;
    },

    /* ---------- restore context to clip left edge -------------------- */
    afterDatasetsDraw(chart, _args, opts) {
        const ctx = chart.ctx;
        if (chart._interactionClipApplied) {
            ctx.restore();
            chart._interactionClipApplied = false;
        }
    },

    /* ---------- unified drawing: tooltip + labels -------------------- */
    afterDraw(chart, _a, opts) {
        if (!opts?.enabled) return;
        this._drawTooltip(chart, opts);
        this._drawLabels(chart, opts);
    },

    /* ---------- tooltip drawing --------------------------------------- */
    _drawTooltip(chart, opts) {
        const rows = this._interaction.tooltipItems;
        if (!rows?.length) return;

        const ctx = chart.ctx;
        const pad = opts.tooltipPad, gap = opts.colGap, lh = 14;
        const baseFont = opts.tooltipFont;
        const boldFont = "bold " + baseFont;
        const boldItal = "italic bold " + baseFont;

        /* ================================================================
     * 1. Parse rank into padded 4-segment block:
     *      "  # "   +   [num centered]   +   " / "   +   [den centered]
     * ================================================================ */
        rows.forEach(r => {
            const raw = (r.rank || "").replace(/\s+/g, "");
            const m = raw.match(/^#?(\d+)(?:\/(\d+))?$/);

            if (m) {
                r.rankHash  = "  # ";         // TWO spaces + "#" + ONE space
                r.rankNum   = m[1];           // "3", "12"
                r.rankSlash = " / ";          // ONE space + "/" + ONE space
                r.rankDen   = m[2] || "";
            } else {
                r.rankHash  = "  # ";
                r.rankNum   = "";
                r.rankSlash = " / ";
                r.rankDen   = "";
            }
        });

        /* ================================================================
     * 2. Measure columns INCLUDING padded strings
     * ================================================================ */

        // prefix column
        let prefixW = 0;
        rows.forEach(r => {
            ctx.font = r.hover ? boldItal : baseFont;
            prefixW = Math.max(prefixW, ctx.measureText(r.prefix).width);
        });

        // value column
        ctx.font = boldFont;
        let valW = 0;
        rows.forEach(r => {
            valW = Math.max(valW, ctx.measureText(r.value).width);
        });

        // rank block
        ctx.font = baseFont;

        const hashW  = ctx.measureText("  # ").width;  // padded hash block
        const slashW = ctx.measureText(" / ").width;    // padded slash block

        let numW = 0;
        let denW = 0;
        rows.forEach(r => {
            numW = Math.max(numW, ctx.measureText(r.rankNum).width);
            denW = Math.max(denW, ctx.measureText(r.rankDen).width);
        });

        const rankBlockW = hashW + numW + slashW + denW;

        /* ================================================================
     * 3. Header width — your original logic (kept)
     * ================================================================ */

        const yearText = this._yearText(chart, this._interaction.nearest.valX);
        const itemCodeHeader = chart.data.datasets[0].ICode + " Score";

        ctx.font = boldFont;
        const itemWidth = ctx.measureText(itemCodeHeader).width;
        const yearWidth = ctx.measureText(yearText).width;
        const headerWidth = pad + Math.max(itemWidth, yearWidth) + pad;

        /* body width uses rankBlockW now */
        const bodyWidth = pad + 12 + prefixW + gap + valW + rankBlockW + pad;
        const width = Math.max(bodyWidth, headerWidth);
        const height = (rows.length + 1) * lh + pad * 2;

        /* ================================================================
     * 4. Position (your original logic)
     * ================================================================ */

        const area = chart.chartArea;
        const nearestX = this._interaction.nearest.x;
        const right = nearestX < (area.left + area.right) / 2;
        let x = right ? nearestX + opts.tooltipGap
            : nearestX - opts.tooltipGap - width;

        if (x + width > area.right) x = nearestX - opts.tooltipGap - width;
        if (x < area.left) x = nearestX + opts.tooltipGap;
        if (x + width > area.right) x = area.right - width - 2;

        const above = this._interaction.mouse.y > (area.top + area.bottom) / 2;
        let y = above
            ? this._interaction.mouse.y - opts.radius - height - 2
            : this._interaction.mouse.y + opts.radius + 2;

        if (y < area.top) y = area.top + 2;
        if (y + height > area.bottom) y = area.bottom - height - 2;

        /* ================================================================
     * 5. Draw box
     * ================================================================ */
        ctx.save();
        ctx.fillStyle = opts.tooltipBg;
        ctx.strokeStyle = "rgba(0,0,0,0.25)";
        ctx.beginPath();
        ctx.rect(x, y, width, height);
        ctx.fill();
        ctx.stroke();

        /* ================================================================
     * 6. Header (your logic remains exactly)
     * ================================================================ */
        ctx.font = boldFont;
        const headerY = y + pad + 0.75 * lh;

        ctx.textAlign = "left";
        ctx.fillStyle = opts.tooltipFg;
        ctx.fillText(itemCodeHeader, x + pad, headerY);

        ctx.textAlign = "right";
        ctx.fillStyle = opts.tooltipFgAccent;
        ctx.fillText(yearText, x + width - pad, headerY);

        ctx.textAlign = "left";

        /* ================================================================
     * 7. Draw rows with padded rank block
     * ================================================================ */
        rows.forEach((r, i) => {
            const rowY = y + pad + lh + (i + 0.75) * lh;

            // color box
            ctx.fillStyle = r.colour;
            ctx.fillRect(x + pad, rowY - 8, 8, 8);

            const preX  = x + pad + 12;
            const valX  = preX + prefixW + gap;
            const rankX = valX + valW;

            // prefix
            ctx.font = r.hover ? boldItal : baseFont;
            ctx.fillStyle = opts.tooltipFg;
            ctx.fillText(r.prefix, preX, rowY);

            // value
            ctx.font = boldFont;
            ctx.fillText(r.value, valX, rowY);

            // rank block
            ctx.font = baseFont;
            let rx = rankX;

            // 1. "  # "
            ctx.fillText(r.rankHash, rx, rowY);
            rx += hashW;

            // 2. centered rank number
            const numActual = ctx.measureText(r.rankNum).width;
            ctx.fillText(r.rankNum, rx + (numW - numActual) / 2, rowY);
            rx += numW;

            // 3. " / "
            ctx.fillText(r.rankSlash, rx, rowY);
            rx += slashW;

            // 4. centered denominator
            const denActual = ctx.measureText(r.rankDen).width;
            ctx.fillText(r.rankDen, rx + (denW - denActual) / 2, rowY);
        });

        ctx.restore();
    },

    /* ---------- label drawing ----------------------------------------- */
    _drawLabels(chart, opts) {
        const ctx = chart.ctx;
        const labels = [];
        const pos = this._interaction.mouse;
        const externalIdx = this._interaction.closestDatasetIdx;
        const isExternalHover = !pos && externalIdx != null;

        /* Build label list */
        chart.data.datasets.forEach((ds, i) => {
            if (ds.hidden) return;
            const meta = chart.getDatasetMeta(i);
            if (!meta?.data?.length) return;

            // last defined point in this series
            let maxXIndex = null;
            if (chart.options.scales.x.max !== undefined) {
                maxXIndex = chart?.data?.labels.findIndex(y => y === chart.options.scales.x.max);
                if (maxXIndex == -1) { maxXIndex = null };
            }
            let last = null;
            let j = maxXIndex !== undefined && maxXIndex !== null && maxXIndex < meta.data.length ? maxXIndex: meta.data.length - 1;
            while (j >= 0) {
                const el = meta.data[j];
                if (el?.parsed?.y !== null) { last = el; break; }
                --j
            }
            if (!last) return;

            const text = ds[opts.labelField] ?? '';
            this._setupCanvas(ctx, this._LABEL_FONT, '#000');
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
                order: 0,
                isPinned: !!ds.pinned  // Track pinned status
            });
        });

        /* Animation handling - defer collision detection until animation completes */
        const animating =
            chart.animating ||
                (chart._animations && chart._animations.size) ||
                (chart.animations && chart.animations.size);

        if (animating) {
            chart._labelRandDone = false;
            // Clear any cached visible set built during animation - it's invalid
            chart._defaultVisibleLabels = null;
            labels.forEach(l => {
                this._setupCanvas(ctx, this._LABEL_FONT, l.colour, opts.animAlpha);
                ctx.fillText(l.text, l.x, l.y);
                ctx.restore();
            });
            return;
        }

        /* Randomise order once - but give pinned countries top priority */
        if (!chart._labelRandDone) {
            const pinnedIndices = labels.filter(l => l.isPinned).map(l => l.idx);
            const unpinnedIndices = labels.filter(l => !l.isPinned).map(l => l.idx);
            // Shuffle unpinned labels only
            for (let i = unpinnedIndices.length - 1; i > 0; --i) {
                const k = Math.floor(Math.random() * (i + 1));
                [unpinnedIndices[i], unpinnedIndices[k]] = [unpinnedIndices[k], unpinnedIndices[i]];
            }

            // Pinned countries get priority 0, 1, 2... (highest priority)
            // Unpinned countries get priority starting after pinned ones
            const orderSeq = [...pinnedIndices, ...unpinnedIndices];
            chart._labelOrder = Object.fromEntries(
                orderSeq.map((d, pos) => [d, pos])
            );
            chart._labelRandDone = true;
        }
        labels.forEach(l => {
            l.order = chart._labelOrder[l.idx] ?? 0;
        });

        /* Build default visible set with priority-based collision handling */
        labels.sort((a, b) => a.order - b.order); // Sort by random order (priority)
        // Track dataset count to detect data structure changes
        const currentDatasetCount = labels.length;
        if (chart._lastDatasetCount !== currentDatasetCount) {
            chart._defaultVisibleLabels = null; // Clear stale cache
            chart._lastDatasetCount = currentDatasetCount;
        }
        // Additional safety check: validate cached indices are still valid
        if (chart._defaultVisibleLabels && chart._defaultVisibleLabels.size > 0) {
            const cachedIndices = Array.from(chart._defaultVisibleLabels);
            const maxCachedIndex = Math.max(...cachedIndices);

            if (maxCachedIndex >= labels.length) {
                chart._defaultVisibleLabels = null;
            }
        }

        // Check if cached visible set should be rebuilt
        const shouldRebuild = !chart._defaultVisibleLabels || 
            chart._defaultVisibleLabels.size === 0 ||
            chart._needsLabelRebuild;

        if (shouldRebuild) {
            chart._defaultVisibleLabels = null;
            chart._needsLabelRebuild = false;
        }
        //
        // Throttle collision detection - only run if cooldown period has elapsed
        const now = Date.now();
        const timeSinceLastCollision = now - this._lastCollisionTime;
        const shouldRunCollisionDetection = opts.showDefaultLabels && 
            !chart._defaultVisibleLabels && 
            timeSinceLastCollision >= this._collisionCooldown;

        if (shouldRunCollisionDetection) {
            // Update timestamp before running collision detection
            this._lastCollisionTime = now;
            const spacing = opts.defaultLabelSpacing;

            // Reset occlusion flags
            labels.forEach((label, lIndex) => { label.occluded = false; label.lIndex = lIndex; });
            const pinnedLabels = labels.filter((l) => l.isPinned);
            const unpinnedLabels = labels.filter((l) => !l.isPinned);
            // Initial Sort: Always Show Pinned Labels
            let blockedIntervals = pinnedLabels.map((l) => [l.box.top - spacing, l.box.bottom + spacing])
            let visibleLabelsSet = new Set(pinnedLabels.map((l) => l.lIndex));
            let blockCount = 0;
            let unblockedLabelPool = unpinnedLabels.filter((l) => {
                for (var b = 0; b < blockedIntervals.length; b++) {
                    if (l.box.top > blockedIntervals[b][0] && l.box.top < blockedIntervals[b][1]) {
                        blockCount++
                        return false;
                    }
                    if (l.box.bottom > blockedIntervals[b][0] && l.box.bottom < blockedIntervals[b][1]) {
                        blockCount++
                        return false;
                    } 
                };
                return true;
            });
            // Select a Random Label and Remove the Others it Obstructs
            let count = 0
            while (unblockedLabelPool.length > 0 && count < 15) {
                count++
                let randomIndex = Math.floor(Math.random() * unblockedLabelPool.length);
                let randomLabel = unblockedLabelPool[randomIndex];
                visibleLabelsSet.add(randomLabel.lIndex)
                let newBlockInterval = [randomLabel.box.top - spacing, randomLabel.box.bottom + spacing]
                unblockedLabelPool = unblockedLabelPool.filter((l) => {
                    if (l.idx == randomLabel.idx) {
                        return false; // must remove the randomly drawn label itself from the unblockedList
                    }
                    if (l.box.top > newBlockInterval[0] && l.box.top < newBlockInterval[1]) {
                        l.occluded = true;
                        return false;
                    }
                    if (l.box.bottom > newBlockInterval[0] && l.box.bottom < newBlockInterval[1]) {
                        l.occluded = true;
                        return false;
                    } 
                    return true;
                });
            }
            chart._defaultVisibleLabels = visibleLabelsSet;

            // Reorder datasets so those with visible labels are drawn on top
            // this._reorderDatasetsForVisibility(chart, labels, visibleLabelsSet);
        } else if (opts.showDefaultLabels && !chart._defaultVisibleLabels) {
            // We're in cooldown period but cache is missing - skip collision detection for now
            // Labels will be drawn with default opacity until cooldown expires
        }

        /* Draw labels - draw winners last so they appear on top */

        // Separate winners and losers for proper layering
        const occludedLabels = [];
        const visibleLabels = [];

        labels.forEach((l, i) => {
            // Determine opacity based on interaction state
            let alpha, reason;
            if (isExternalHover) {
                alpha = l.idx === externalIdx ? 1 : opts.occludedAlpha;
            } else if (this._interaction.closestDatasetIdx !== null && this._interaction.mouse) {
                // Mouse interaction: highlight closest, fade others
                alpha = l.idx === this._interaction.closestDatasetIdx ? 1 : opts.occludedAlpha;
                reason = `mouse interaction: ${l.idx === this._interaction.closestDatasetIdx ? 'closest' : 'not closest'}`;
            } else if (opts.showDefaultLabels && chart._defaultVisibleLabels) {
                // No mouse interaction: show default visible set
                alpha = chart._defaultVisibleLabels.has(i) ? 1 : opts.occludedAlpha;
                reason = `default visible: ${chart._defaultVisibleLabels.has(i) ? 'in set' : 'not in set'}`;
            } else {
                // Fallback: use original behavior
                alpha = opts.occludedAlpha;
                reason = `fallback: ${opts.showDefaultLabels ? 'no default set' : 'default labels disabled'}`;
            }

            const labelInfo = { label: l, alpha, reason, arrayIdx: i };

            if (chart._defaultVisibleLabels && chart._defaultVisibleLabels.has(i)) {
                visibleLabels.push(labelInfo);
            } else {
                occludedLabels.push(labelInfo);
            }

        });

        // Draw occluded labels first (background)
        occludedLabels.forEach(({label, alpha}) => {
            this._setupCanvas(ctx, this._LABEL_FONT, label.colour, alpha);
            ctx.fillText(label.text, label.x, label.y);
            ctx.restore();
        });

        // Draw visible labels last (foreground/on top)
        visibleLabels.forEach(({label, alpha}) => {
            this._setupCanvas(ctx, this._LABEL_FONT, label.colour, alpha);
            ctx.fillText(label.text, label.x, label.y);
            ctx.restore();
        });
    },

    /* ---------- helper methods ---------------------------------------- */
    _resetProximity(chart) {
        chart.data.datasets.forEach((ds,i) => {
            const meta = chart.getDatasetMeta(i);
            if (!ds._full) return;
            ds.borderColor = ds._full.border;
            ds.backgroundColor = ds._full.bg;
            ds._isNear = ds._isHover = false;
            if (meta?.dataset) meta.dataset.options.borderColor = ds.borderColor;
            meta?.data.forEach(p => {
                p.options.backgroundColor = ds.backgroundColor;
                p.options.borderColor = ds.borderColor;
                if (p.__origR !== undefined) {
                    p.options.radius = p.__origR;
                    delete p.__origR;
                }
            });
        });
        this._interaction.tooltipItems = null;
        this._interaction.closestDatasetIdx = null;
    },

    // New method to clear all plugin state when data changes
    _clearLabelState(chart) {
        chart._defaultVisibleLabels = null;
        chart._labelRandDone = false;
        chart._labelOrder = null;
        chart._lastDatasetCount = null; // Clear dataset count tracking
    },

    // Method to force refresh of label state - called when data structure changes
    _forceRefreshLabels(chart) {
        this._clearLabelState(chart);
        // Force immediate rebuild on next draw
        chart._needsLabelRebuild = true;
    },

    // Reorder datasets so those with visible labels are drawn on top
    _reorderDatasetsForVisibility(chart, labels, visibleLabelIndices) {
        if (!chart.data?.datasets) return;

        const visibleLabelDatasetIndices = new Set();
        labels.forEach((label, labelIndex) => {
            if (visibleLabelIndices.has(labelIndex)) {
                visibleLabelDatasetIndices.add(label.idx);
            }
        });

        const datasets = chart.data.datasets;
        const datasetsWithHiddenLabels = [];
        const datasetsWithVisibleLabels = [];

        // Separate datasets based on label visibility
        datasets.forEach((ds, index) => {
            if (visibleLabelDatasetIndices.has(index)) {
                datasetsWithVisibleLabels.push({ dataset: ds, originalIndex: index });
            } else {
                datasetsWithHiddenLabels.push({ dataset: ds, originalIndex: index });
            }
        });

        // Sort visible label datasets by priority (pinned first)
        datasetsWithVisibleLabels.sort((a, b) => {
            const aPinned = !!a.dataset.pinned;
            const bPinned = !!b.dataset.pinned;
            if (aPinned && !bPinned) return 1;  // Pinned datasets last (drawn on top)
            if (!aPinned && bPinned) return -1;
            return 0;
        });

        // Reorder: hidden labels first, then visible labels (so visible are drawn on top)
        const reorderedDatasets = [
            ...datasetsWithHiddenLabels.map(item => item.dataset),
            ...datasetsWithVisibleLabels.map(item => item.dataset)
        ];

        // Only reorder if the order actually changed to avoid unnecessary updates
        const orderChanged = reorderedDatasets.some((ds, i) => ds !== datasets[i]);
        if (orderChanged) {
            chart.data.datasets = reorderedDatasets;
        }
    },

    /* ---------- comparison series drawing ----------------------------- */
    _drawComparisonSeries(chart, opts) {
        // Early exit if feature disabled
        if (!opts.comparisonEnabled) {
            return;
        }

        // Validate required components
        const ctx = chart.ctx;
        const xScale = chart.scales?.x;
        const yScale = chart.scales?.y;
        const labels = chart.data?.labels;

        if (!ctx || !xScale || !yScale || !labels) {
            // Missing critical components - fail silently
            return;
        }

        const startYear = chart.options?.scales?.x?.min;
        const endYear = chart.options?.scales?.x?.max;

        // Process each dataset that has comparison data
        chart.data.datasets.forEach((dataset) => {
            // Skip if dataset is hidden
            if (dataset.hidden) {
                return;
            }

            // Skip if no comparison data field exists (graceful handling)
            const comparisonData = dataset[opts.comparisonDataField];
            if (!comparisonData || !Array.isArray(comparisonData) || comparisonData.length === 0) {
                // No comparison data - silently skip this dataset
                return;
            }

            // Get base color for the comparison line
            const baseColor = dataset.borderColor || dataset._full?.border;
            if (!baseColor) {
                // No color available - skip this dataset
                return;
            }

            // Create ghosted version of the color
            const ghostColor = this._fade(baseColor, opts.comparisonOpacity);

            // Setup canvas for drawing
            ctx.save();
            ctx.strokeStyle = ghostColor;
            ctx.lineWidth = opts.comparisonLineWidth;
            ctx.setLineDash(opts.comparisonDashPattern);
            ctx.lineCap = 'round';
            ctx.lineJoin = 'round';

            // Build path from comparison data
            ctx.beginPath();
            let pathStarted = false;

            for (let i = 0; i < comparisonData.length; i++) {
                const value = comparisonData[i];

                // Skip null/undefined values (creates gap in line)
                if (value === null || value === undefined) {
                    pathStarted = false;
                    continue;
                }

                // Get corresponding year from labels
                const year = labels[i];
                if (year === undefined) {
                    continue;
                }

                // Filter by year range if specified
                if (startYear !== undefined || endYear !== undefined) {
                    const numericYear = typeof year === 'string' ? parseInt(year) : year;
                    const numericStartYear = typeof startYear === 'string' ? parseInt(startYear) : startYear;
                    const numericEndYear = typeof endYear === 'string' ? parseInt(endYear) : endYear;

                    if (numericStartYear !== undefined && numericYear < numericStartYear) continue;
                    if (numericEndYear !== undefined && numericYear > numericEndYear) continue;
                }

                // Calculate pixel coordinates
                const x = xScale.getPixelForValue(i);
                const y = yScale.getPixelForValue(value);

                // Skip invalid coordinates
                if (isNaN(x) || isNaN(y)) {
                    pathStarted = false;
                    continue;
                }

                // Add point to path
                if (!pathStarted) {
                    ctx.moveTo(x, y);
                    pathStarted = true;
                } else {
                    ctx.lineTo(x, y);
                }
            }

            // Draw the path if we have any valid points
            if (pathStarted) {
                ctx.stroke();
            }

            // Restore canvas state
            ctx.restore();
        });
    },

    _setupCanvas(ctx, font, color, alpha = 1) {
        ctx.save();
        ctx.font = font;
        ctx.fillStyle = color;
        ctx.globalAlpha = alpha;
        ctx.textAlign = 'left';
    },

    _fade(col, a) {
        if (col.startsWith("rgba")) return col.replace(/, *[^,]+\)$/, `, ${a})`);
        if (col.startsWith("rgb")) return col.replace("rgb","rgba").replace(")",`, ${a})`);
        if (col[0]==="#" && col.length===7)
            return col + Math.round(a*255).toString(16).padStart(2,"0");
        return col;
    },

    _yearText(chart, v) {
        const xs = chart.scales?.x;
        if (xs?.getLabelForValue) return String(xs.getLabelForValue(v));
        const lbls = chart.data?.labels;
        if (lbls && v>=0 && v<lbls.length) return String(lbls[v]);
        return String(v);
    }
};
