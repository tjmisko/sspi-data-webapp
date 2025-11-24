/**
 * Series Correlation Tooltip Plugin
 *
 * Custom tooltip for scatter correlation charts with:
 * - Two-column layout (labels left, values right-aligned)
 * - Smart positioning to avoid chart edges
 * - Professional typography with monospace value alignment
 * - Support for choropleth color indicators
 */

const seriesCorrelationTooltip = {
    id: 'seriesCorrelationTooltip',

    defaults: {
        enabled: true,
        tooltipBg: 'rgba(255,255,255,0.95)',
        tooltipFg: '#111',
        tooltipFgAccent: '#8BA342',
        tooltipBorder: 'rgba(0,0,0,0.25)',
        tooltipFont: '12px sans-serif',
        tooltipBoldFont: 'bold 12px sans-serif',
        tooltipMonoFont: 'bold 12px "Courier New", monospace',
        tooltipHeaderFont: 'bold 13px sans-serif',
        tooltipPad: 10,
        tooltipGap: 15,
        hoverRadius: 10,
        lineHeight: 16
    },

    // Internal state
    _mouse: null,
    _hoveredPoint: null,
    _chartInstance: null,

    /* ===== MOUSE TRACKING ===== */
    afterEvent(chart, args, opts) {
        if (!opts || !opts.enabled) return;

        const event = args.event;
        if (!event) return;

        if (event.type === 'mousemove') {
            this._mouse = { x: event.x, y: event.y };
            this._hoveredPoint = this._findNearestPoint(chart, event, opts);
            chart.draw();
        } else if (event.type === 'mouseout') {
            this._mouse = null;
            this._hoveredPoint = null;
            chart.draw();
        }
    },

    /* ===== POINT DETECTION ===== */
    _findNearestPoint(chart, event, opts) {
        const radius = opts.hoverRadius || this.defaults.hoverRadius;
        const r2 = radius * radius;
        let nearest = null;
        let minD2 = Infinity;

        chart.data.datasets.forEach((dataset, datasetIndex) => {
            if (dataset.hidden) return;

            const meta = chart.getDatasetMeta(datasetIndex);
            if (!meta || !meta.data) return;

            meta.data.forEach((point, pointIndex) => {
                if (!point) return;

                const dx = point.x - event.x;
                const dy = point.y - event.y;
                const d2 = dx * dx + dy * dy;

                if (d2 <= r2 && d2 < minD2) {
                    minD2 = d2;
                    nearest = {
                        datasetIndex,
                        pointIndex,
                        point,
                        data: dataset.data[pointIndex]
                    };
                }
            });
        });

        return nearest;
    },

    /* ===== TOOLTIP RENDERING ===== */
    afterDraw(chart, args, opts) {
        if (!opts || !opts.enabled) return;
        if (!this._mouse || !this._hoveredPoint) return;

        const ctx = chart.ctx;
        const hovered = this._hoveredPoint;
        const raw = hovered.data;

        // Get series metadata from plugin options
        const seriesX = opts.seriesX;
        const seriesY = opts.seriesY;
        const choropleth = opts.choropleth;
        const colorProvider = opts.colorProvider;

        if (!seriesX || !seriesY) return;

        // Prepare tooltip data
        const tooltipData = this._prepareTooltipData(raw, seriesX, seriesY, choropleth, colorProvider);

        // Render tooltip
        this._renderTooltip(chart, ctx, tooltipData, opts);
    },

    /* ===== DATA PREPARATION ===== */
    _prepareTooltipData(raw, seriesX, seriesY, choropleth, colorProvider) {
        const xLabel = `${seriesX.name}\u0020(${seriesX.code}):`;
        const yLabel = `${seriesY.name}\u0020(${seriesY.code}):`;
        const xValue = raw.x.toFixed(3);
        const yValue = raw.y.toFixed(3);

        return {
            country: raw.CName,
            code: raw.CCode,
            year: raw.year,
            rows: [
                { label: xLabel, value: xValue },
                { label: yLabel, value: yValue },
                { label: 'Year:', value: String(raw.year) }
            ],
            color: (choropleth && colorProvider)
                ? colorProvider.get(raw.CCode)
                : null
        };
    },

    /* ===== TOOLTIP RENDERING ===== */
    _renderTooltip(chart, ctx, data, opts) {
        const pad = opts.tooltipPad;
        const lh = opts.lineHeight;

        // Measure header dimensions (two-column: country name | year)
        ctx.font = opts.tooltipHeaderFont;
        const countryNameText = `${data.country}\u0020`;
        const openParen = '(';
        const countryCodeText = data.code;
        const closeParen = ')';
        const countryWidth = ctx.measureText(countryNameText).width +
                            ctx.measureText(openParen).width +
                            ctx.measureText(countryCodeText).width +
                            ctx.measureText(closeParen).width;
        const yearText = String(data.year);
        const yearWidth = ctx.measureText(yearText).width;
        const headerGap = 20; // Gap between country and year
        const headerWidth = countryWidth + headerGap + yearWidth;

        // Measure body columns
        ctx.font = opts.tooltipFont;
        let maxLabelWidth = 0;
        data.rows.forEach(row => {
            const w = ctx.measureText(row.label).width;
            maxLabelWidth = Math.max(maxLabelWidth, w);
        });

        ctx.font = opts.tooltipMonoFont;
        let maxValueWidth = 0;
        data.rows.forEach(row => {
            const w = ctx.measureText(row.value).width;
            maxValueWidth = Math.max(maxValueWidth, w);
        });

        const colGap = 12;
        const bodyWidth = maxLabelWidth + colGap + maxValueWidth;
        const width = Math.max(headerWidth, bodyWidth) + pad * 2;

        // Calculate height: header + body rows (excluding year row since it's in header)
        const seriesRowCount = data.rows.filter(row => row.label !== 'Year:').length;
        const height = (seriesRowCount + 1) * lh + pad * 2; // +1 for header

        // Position tooltip
        const pos = this._positionTooltip(chart, this._mouse, width, height, opts);

        // Draw background box
        ctx.save();
        ctx.fillStyle = opts.tooltipBg || this.defaults.tooltipBg;
        ctx.strokeStyle = opts.tooltipBorder || this.defaults.tooltipBorder;
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.rect(pos.x, pos.y, width, height);
        ctx.fill();
        ctx.stroke();

        // Draw header row (country name | year)
        const headerY = pos.y + pad + 0.75 * lh;

        // Draw country name and code (code colored if choropleth mode)
        ctx.font = opts.tooltipHeaderFont || this.defaults.tooltipHeaderFont;
        ctx.textAlign = 'left';

        let xPos = pos.x + pad;

        // Draw country name (normal color)
        ctx.fillStyle = opts.tooltipFg || this.defaults.tooltipFg;
        ctx.fillText(countryNameText, xPos, headerY);
        xPos += ctx.measureText(countryNameText).width;

        // Draw opening parenthesis (normal color)
        ctx.fillText(openParen, xPos, headerY);
        xPos += ctx.measureText(openParen).width;

        // Draw country code (colored if choropleth mode)
        ctx.fillStyle = data.color || (opts.tooltipFg || this.defaults.tooltipFg);
        ctx.fillText(countryCodeText, xPos, headerY);
        xPos += ctx.measureText(countryCodeText).width;

        // Draw closing parenthesis (normal color)
        ctx.fillStyle = opts.tooltipFg || this.defaults.tooltipFg;
        ctx.fillText(closeParen, xPos, headerY);

        // Draw year (right-aligned, green accent color)
        ctx.fillStyle = opts.tooltipFgAccent || this.defaults.tooltipFgAccent;
        ctx.textAlign = 'right';
        ctx.fillText(yearText, pos.x + width - pad, headerY);

        // Draw data rows (only series values, no year since it's in header)
        const rowStartY = pos.y + pad + lh;
        const seriesRows = data.rows.filter(row => row.label !== 'Year:');
        seriesRows.forEach((row, i) => {
            const rowY = rowStartY + (i + 0.75) * lh;

            // Label (left-aligned)
            ctx.font = opts.tooltipFont || this.defaults.tooltipFont;
            ctx.fillStyle = opts.tooltipFg || this.defaults.tooltipFg;
            ctx.textAlign = 'left';
            ctx.fillText(row.label, pos.x + pad, rowY);

            // Value (right-aligned, monospace)
            ctx.font = opts.tooltipMonoFont || this.defaults.tooltipMonoFont;
            ctx.textAlign = 'right';
            ctx.fillText(row.value, pos.x + width - pad, rowY);
        });

        ctx.restore();
    },

    /* ===== POSITIONING LOGIC ===== */
    _positionTooltip(chart, mouse, width, height, opts) {
        const area = chart.chartArea;
        const gap = opts.tooltipGap;
        const margin = 5;

        // Prefer right if mouse is on left half
        const preferRight = mouse.x < (area.left + area.right) / 2;
        let x = preferRight
            ? mouse.x + gap
            : mouse.x - gap - width;

        // Clamp to chart bounds
        x = Math.max(area.left + margin, Math.min(x, area.right - width - margin));

        // Prefer below if mouse is in top half
        const preferBelow = mouse.y < (area.top + area.bottom) / 2;
        let y = preferBelow
            ? mouse.y + gap
            : mouse.y - gap - height;

        // Clamp to chart bounds
        y = Math.max(area.top + margin, Math.min(y, area.bottom - height - margin));

        return { x, y };
    }
};
