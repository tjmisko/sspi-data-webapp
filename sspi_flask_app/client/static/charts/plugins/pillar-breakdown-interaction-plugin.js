/* ---------------------------------------------------------------------
 *  Pillar Breakdown Interaction Plugin
 *  -------------------------------------------------------------
 *  Lightweight interaction plugin for stacked pillar breakdown charts
 *  showing a single country's score composition over time.
 *
 *  FEATURES:
 *  • Proximity-based fading for datasets
 *  • DOM-based tooltip showing pillar contributions
 *  • Shows true pillar scores and SSPI (arithmetic mean)
 *  • Visual guide line (vertical)
 *  • CSS-themed styling
 *
 *  DESIGNED FOR:
 *  • Single country, multiple pillars/items
 *  • Stacked area charts (height = 1/3 sum for SSPI average)
 *  • No country comparison or ranking
 *
 *  TOOLTIP STRUCTURE:
 *  Parallels globe.js tooltip structure with unique CSS classes
 *  Styled via pillar-breakdown-tooltip.css
 * ------------------------------------------------------------------ */
const pillarBreakdownInteractionPlugin = {
  id: "pillarBreakdownInteractionPlugin",

  defaults: {
    // Core settings
    enabled: true,

    // Proximity settings
    radius: 30,

    // Visual guide settings
    guideColor: "#bbbbbb",
    guideWidth: 1,

    // Tooltip settings (DOM-based, styled via CSS)
    showTotal: true,  // Shows SSPI (arithmetic mean of pillar scores)

    // Country details
    countryName: null,
    countryFlag: null
  },

  // Internal state
  _interaction: {
    mouse: null,
    nearest: null,
    tooltipData: null,
    tooltipElement: null
  },

  /* ---------- Mouse tracking ---------------------------------------- */
  afterEvent(chart, args) {
    const cfg = chart.options.plugins?.pillarBreakdownInteractionPlugin;
    if (!cfg || !cfg.enabled) return;

    const ev = args.event;
    if (!ev) return;

    if (ev.type === "mousemove") {
      this._interaction.mouse = { x: ev.x, y: ev.y };
    } else if (ev.type === "mouseout") {
      this._interaction.mouse = null;
    }

    chart.draw();
  },

  /* ---------- Main interaction logic -------------------------------- */
  beforeDatasetsDraw(chart, _args, opts) {
    if (!opts || !opts.enabled) {
      this._resetProximity(chart);
      return;
    }

    const pos = this._interaction.mouse;

    // If no mouse, reset everything
    if (!pos) {
      this._resetProximity(chart);
      return;
    }

    const R = opts.radius;
    const ctx = chart.ctx;
    const area = chart.chartArea;

    // Find nearest X position across all datasets (no fading)
    let nearest = { d2: Infinity, x: null, idx: null, valX: null };

    chart.data.datasets.forEach((ds, i) => {
      const meta = chart.getDatasetMeta(i);
      if (ds.hidden || !meta?.data?.length) {
        return;
      }

      // Find nearest point in this dataset
      meta.data.forEach((pt, colIdx) => {
        if (!pt) return;
        const dx = pt.x - pos.x;
        const dy = pt.y - pos.y;
        const d2 = dx * dx + dy * dy;

        if (d2 < nearest.d2) {
          nearest = {
            d2,
            x: pt.x,
            idx: colIdx,
            valX: pt.parsed?.x ?? colIdx
          };
        }
      });
    });

    if (nearest.d2 === Infinity) {
      this._resetProximity(chart);
      return;
    }

    // Store nearest info
    this._interaction.nearest = nearest;

    /* Draw vertical guide line */
    ctx.save();
    ctx.beginPath();
    ctx.moveTo(nearest.x, area.top);
    ctx.lineTo(nearest.x, area.bottom);
    ctx.strokeStyle = opts.guideColor;
    ctx.lineWidth = opts.guideWidth;
    ctx.setLineDash([]);
    ctx.stroke();
    ctx.restore();

    /* Prepare tooltip data */
    const items = [];
    let sumOfScores = 0;

    chart.data.datasets.forEach((ds, i) => {
      if (ds.hidden) return;

      const meta = chart.getDatasetMeta(i);
      const el = meta.data[nearest.idx];

      // Get the score value (not the stacked y-position)
      // Try multiple sources: scores array, score array, data array, or parsed value
      let value;
      if (ds.scores && ds.scores[nearest.idx] != null) {
        value = ds.scores[nearest.idx];
      } else if (ds.score && ds.score[nearest.idx] != null) {
        value = ds.score[nearest.idx];
      } else if (ds.data && ds.data[nearest.idx] != null) {
        value = ds.data[nearest.idx];
      } else {
        value = el?.parsed?.y ?? el?.raw;
      }

      if (value == null || isNaN(value)) return;

      // Get item name (try IName, then ICode, then generic)
      const name = ds.IName || ds.ICode || `Item ${i + 1}`;

      items.push({
        name,
        value,
        color: ds._full ? ds._full.border : ds.borderColor,
        near: ds._isNear
      });

      sumOfScores += value;
    });

    // Sort items by value (largest first)
    items.sort((a, b) => b.value - a.value);

    // SSPI is the arithmetic mean (average) of the pillar scores
    // The chart height shows this average, which is sum/count
    const sspiScore = items.length > 0 ? sumOfScores / items.length : 0;

    this._interaction.tooltipData = {
      header: this._headerText(chart, nearest.valX),
      items,
      sspi: opts.showTotal ? sspiScore : null
    };
  },

  /* ---------- DOM Tooltip Management -------------------------------- */
  afterDraw(chart, _args, opts) {
    if (!opts?.enabled) return;

    const data = this._interaction.tooltipData;

    // Remove tooltip if no data
    if (!data || !data.items.length) {
      this._removeTooltip();
      return;
    }

    // Create or update tooltip element
    this._updateTooltip(chart, data, opts);
  },

  _removeTooltip() {
    if (this._interaction.tooltipElement) {
      this._interaction.tooltipElement.remove();
      this._interaction.tooltipElement = null;
    }
  },

  _updateTooltip(chart, data, opts) {
    const canvas = chart.canvas;
    const area = chart.chartArea;

    // Create tooltip if it doesn't exist
    if (!this._interaction.tooltipElement) {
      this._interaction.tooltipElement = document.createElement('div');
      this._interaction.tooltipElement.className = 'pillar-breakdown-tooltip';
      this._interaction.tooltipElement.style.position = 'absolute';
      this._interaction.tooltipElement.style.pointerEvents = 'none';
      this._interaction.tooltipElement.style.zIndex = '1000';
      canvas.parentElement.style.position = 'relative';
      canvas.parentElement.appendChild(this._interaction.tooltipElement);
    }

    const tooltip = this._interaction.tooltipElement;

    // Build tooltip HTML following globe.js structure
    let scoresHTML = '';
    data.items.forEach(item => {
      scoresHTML += `
        <div class="pillar-breakdown-score-line">
          <span class="pillar-breakdown-item-label" style="color: ${item.color}">${item.name}:</span>
          <span class="pillar-breakdown-item-score">${item.value.toFixed(3)}</span>
        </div>
      `;
    });

    // Add SSPI total if enabled
    if (data.sspi !== null) {
      scoresHTML += `
        <div class="pillar-breakdown-score-line sspi-total">
          <span class="pillar-breakdown-item-label">SSPI:</span>
          <span class="pillar-breakdown-item-score">${data.sspi.toFixed(3)}</span>
        </div>
      `;
    }

    // Follow exact structure from globe.js
    // Build header with country info if available
    let headerHTML = '';
    if (opts.countryName) {
      const flag = opts.countryFlag || '';
      headerHTML = `<h3><span class="pillar-breakdown-country-name">${flag}\u0020${opts.countryName}</span><span class="pillar-breakdown-year">${data.header}</span></h3>`;
    } else {
      headerHTML = `<h3><span class="pillar-breakdown-year">${data.header}</span></h3>`;
    }

    tooltip.innerHTML = `
${headerHTML}
<div class="pillar-breakdown-score-container">
${scoresHTML}
</div>
`;

    // Position tooltip relative to chart area
    const canvasRect = canvas.getBoundingClientRect();
    const parentRect = canvas.parentElement.getBoundingClientRect();

    const nearestX = this._interaction.nearest.x;
    const mouseY = this._interaction.mouse.y;

    // Calculate tooltip dimensions
    tooltip.style.visibility = 'hidden';
    tooltip.style.display = 'block';
    const tooltipRect = tooltip.getBoundingClientRect();
    const tooltipWidth = tooltipRect.width;
    const tooltipHeight = tooltipRect.height;
    tooltip.style.visibility = '';

    // Position horizontally (left or right of cursor)
    const right = nearestX < (area.left + area.right) / 2;
    let x = right ? nearestX + 15 : nearestX - 15 - tooltipWidth;
    x = Math.max(area.left + 2, Math.min(x, area.right - tooltipWidth - 2));

    // Position vertically
    const above = mouseY > (area.top + area.bottom) / 2;
    let y = above ? mouseY - tooltipHeight - opts.radius - 5 : mouseY + opts.radius + 5;
    y = Math.max(area.top + 2, Math.min(y, area.bottom - tooltipHeight - 2));

    // Convert chart coordinates to parent-relative coordinates
    const offsetX = canvasRect.left - parentRect.left;
    const offsetY = canvasRect.top - parentRect.top;

    tooltip.style.left = (x + offsetX) + 'px';
    tooltip.style.top = (y + offsetY) + 'px';
  },

  /* ---------- Helper methods ---------------------------------------- */
  _resetProximity(chart) {
    this._interaction.tooltipData = null;
    this._removeTooltip();
  },

  _headerText(chart, v) {
    const xs = chart.scales?.x;
    if (xs?.getLabelForValue) return String(xs.getLabelForValue(v));
    const lbls = chart.data?.labels;
    if (lbls && v >= 0 && v < lbls.length) return String(lbls[v]);
    return String(v);
  }
};
