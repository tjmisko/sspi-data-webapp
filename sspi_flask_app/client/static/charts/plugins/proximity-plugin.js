/* ---------------------------------------------------------------------
 *  proximityHighlight
 *  -------------------------------------------------------------
 *  • Tooltip rows:
 *      CName (CCode):   12.345   #3 / 12
 *        - “value” (exactly 3 d.p.) is **bold**
 *        - “#rank / total” is normal weight, with spaces around “/”
 *        - Country text is ***bold italic*** if its point is within
 *          clickRadius of the cursor
 *  • Year/x-label header is bold
 *  • Points inside clickRadius grow by 60 %
 *  • Optional onDatasetClick callback fires when the user clicks
 *    on points within clickRadius
 * ------------------------------------------------------------------ */
const proximityPlugin = {
  id: "proximityHighlight",

  defaults: {
    enabled       : true,
    radius        : 20,
    clickRadius   : 5,
    fadeAlpha     : 0.1,
    circleColor   : "rgba(0,0,0,.5)",
    circleWidth   : 1,
    guideColor    : "rgba(0,0,0,.35)",
    guideWidth    : 1,
    guideDash     : [],
    tooltipBg     : "rgba(255,255,255,0.85)",
    tooltipFg     : "#000",
    tooltipFont   : "12px sans-serif",
    tooltipPad    : 6,
    tooltipGap    : 10,
    colGap        : 6,
    onDatasetClick: null
  },

  _mouse        : null,
  _tooltipItems : null,
  _nearestX     : null,
  _nearestValue : null,

  /* ---------- pointer & click tracking --------------------------- */
  afterEvent(chart, args) {
    const cfg = chart.options.plugins && chart.options.plugins.proximityHighlight;
    if (!cfg || !cfg.enabled) return;

    const ev = args.event;
    if (!ev) return;

    if (ev.type === "mousemove") {
      this._mouse = { x: ev.x, y: ev.y };
    } else if (ev.type === "mouseout") {
      this._mouse = null;
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
        catch (e) { console.error("proximityHighlight onDatasetClick:", e); }
      }
    }
    chart.draw();
  },

  /* ---------- main proximity logic ------------------------------- */
  beforeDatasetsDraw(chart, _args, opts) {
    if (!opts || !opts.enabled || !this._mouse) { resetAll(); return; }

    const pos = this._mouse, R = opts.radius, CR = opts.clickRadius;
    const cr2 = CR * CR;
    const ctx = chart.ctx, area = chart.chartArea;
    const top = area.top, bottom = area.bottom;

    /* find nearest point */
    let nearest = { d2: Infinity, x: null, idx: null, valX: null };
    chart.data.datasets.forEach((ds, di) => {
      const meta = chart.getDatasetMeta(di);
      if (ds.hidden || !meta) return;
      meta.data.forEach((pt, colIdx) => {
        const dx = pt.x - pos.x, dy = pt.y - pos.y, d2 = dx * dx + dy * dy;
        if (d2 < nearest.d2) nearest = {
          d2, x: pt.x, idx: colIdx,
          valX: pt.parsed?.x ?? colIdx
        };
      });
    });
    if (nearest.d2 > R * R) { resetAll(); return; }

    /* fade + mark near + resize + hover flag */
    let anyNear = false;
    chart.data.datasets.forEach((ds, i) => {
      const meta = chart.getDatasetMeta(i);
      if (ds.hidden || !meta) { ds._isNear = ds._isHover = false; return; }

      ds._full  = ds._full  || { border: ds.borderColor, bg: ds.backgroundColor };
      ds._faded = ds._faded || fade(ds._full.border, opts.fadeAlpha);

      const pt   = meta.data[nearest.idx];
      const d2pt = pt ? (pt.x - pos.x) ** 2 + (pt.y - pos.y) ** 2 : Infinity;
      const near = d2pt <= R * R;
      const hover= d2pt <= cr2;

      ds._isNear  = near;
      ds._isHover = hover;
      if (near) anyNear = true;

      ds.borderColor     = near ? ds._full.border : ds._faded;
      ds.backgroundColor = near ? ds._full.bg     : ds._faded;

      if (meta.dataset) meta.dataset.options.borderColor = ds.borderColor;

      meta.data.forEach(p => {
        p.options.backgroundColor = ds.backgroundColor;
        p.options.borderColor     = ds.borderColor;

        const clickNear = (p.x - pos.x) ** 2 + (p.y - pos.y) ** 2 <= cr2;
        if (clickNear) {
          if (p.__origR === undefined)
            p.__origR = p.options.radius ?? p.radius ?? 3;
          p.options.radius = p.__origR * 1.6;
        } else if (p.__origR !== undefined) {
          p.options.radius = p.__origR;
        }
      });
    });
    if (!anyNear) { resetAll(); return; }

    /* circle + guide */
    ctx.save();
    ctx.beginPath();
    ctx.arc(pos.x, pos.y, R, 0, 2 * Math.PI);
    ctx.strokeStyle = opts.circleColor;
    ctx.lineWidth   = opts.circleWidth;
    ctx.setLineDash([3,3]);
    ctx.stroke();
    ctx.beginPath();
    ctx.moveTo(nearest.x, top);
    ctx.lineTo(nearest.x, bottom);
    ctx.strokeStyle = opts.guideColor;
    ctx.lineWidth   = opts.guideWidth;
    ctx.setLineDash(opts.guideDash);
    ctx.stroke();
    ctx.restore();

    /* ranks */
    const vis = [];
    chart.data.datasets.forEach((ds, i) => {
      if (ds.hidden) return;
      const el = chart.getDatasetMeta(i).data[nearest.idx];
      const v  = el?.parsed?.y ?? el?.raw;
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
      let val  = el?.parsed?.y ?? el?.raw;
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

    this._tooltipItems = items;
    this._nearestX     = nearest.x;
    this._nearestValue = nearest.valX;

    /* helpers */
    function resetAll() {
      chart.data.datasets.forEach((ds,i) => {
        const meta = chart.getDatasetMeta(i);
        if (!ds._full) return;
        ds.borderColor = ds._full.border;
        ds.backgroundColor = ds._full.bg;
        ds._isNear = ds._isHover = false;
        if (meta?.dataset) meta.dataset.options.borderColor = ds.borderColor;
        meta?.data.forEach(p => {
          p.options.backgroundColor = ds.backgroundColor;
          p.options.borderColor     = ds.borderColor;
          if (p.__origR !== undefined) {
            p.options.radius = p.__origR;
            delete p.__origR;
          }
        });
      });
      proximityPlugin._tooltipItems = null;
    }
    function fade(col,a){
      if (col.startsWith("rgba")) return col.replace(/, *[^,]+\)$/,`, ${a})`);
      if (col.startsWith("rgb"))  return col.replace("rgb","rgba").replace(")",`, ${a})`);
      if (col[0]==="#" && col.length===7)
        return col + Math.round(a*255).toString(16).padStart(2,"0");
      return col;
    }
  },

  /* ---------- tooltip drawing ------------------------------------ */
  afterDraw(chart, _a, opts) {
    if (!opts?.enabled) return;
    const rows = this._tooltipItems;
    if (!rows?.length) return;

    const ctx      = chart.ctx;
    const pad      = opts.tooltipPad, gap = opts.colGap, lh = 14;
    const baseFont = opts.tooltipFont;
    const boldFont = "bold " + baseFont;
    const boldItal = "italic bold " + baseFont;

    /* column widths */
    let prefixW=0,valW=0,rankW=0;
    rows.forEach(r=>{
      ctx.font = r.hover ? boldItal : baseFont;
      prefixW  = Math.max(prefixW, ctx.measureText(r.prefix).width);
    });
    ctx.font = baseFont;
    rows.forEach(r=>{ rankW = Math.max(rankW, ctx.measureText(" "+r.rank).width); });
    ctx.font = boldFont;
    rows.forEach(r=>{ valW  = Math.max(valW,  ctx.measureText(r.value).width); });

    const header = headerText(chart, this._nearestValue);
    const width  = pad+12+prefixW+gap+valW+rankW+pad;
    const height = (rows.length+1)*lh + pad*2;

    /* position */
    const area = chart.chartArea;
    const right = this._nearestX < (area.left+area.right)/2;
    let x = right ? this._nearestX + opts.tooltipGap
                  : this._nearestX - opts.tooltipGap - width;
    if (x+width>area.right) x = this._nearestX - opts.tooltipGap - width;
    if (x<area.left)        x = this._nearestX + opts.tooltipGap;
    if (x+width>area.right) x = area.right - width - 2;

    const above = this._mouse.y > (area.top+area.bottom)/2;
    let y = above ? this._mouse.y - opts.radius - height - 2
                  : this._mouse.y + opts.radius + 2;
    if (y<area.top)              y = area.top + 2;
    if (y+height>area.bottom)    y = area.bottom - height - 2;

    /* box */
    ctx.save();
    ctx.fillStyle   = opts.tooltipBg;
    ctx.strokeStyle = "rgba(0,0,0,0.25)";
    ctx.beginPath();
    ctx.rect(x,y,width,height);
    ctx.fill(); ctx.stroke();

    /* header */
    ctx.font = boldFont;
    ctx.fillStyle = opts.tooltipFg;
    ctx.fillText(header, x+pad, y+pad+0.75*lh);

    /* rows */
    rows.forEach((r,i)=>{
      const rowY = y+pad+lh+(i+0.75)*lh;
      ctx.fillStyle = r.colour;
      ctx.fillRect(x+pad,rowY-8,8,8);

      const preX  = x+pad+12;
      const valX  = preX+prefixW+gap;
      const rankX = valX+valW;

      ctx.font = r.hover ? boldItal : baseFont;
      ctx.fillStyle = opts.tooltipFg;
      ctx.fillText(r.prefix, preX, rowY);

      ctx.font = boldFont;
      ctx.fillText(r.value, valX, rowY);

      ctx.font = baseFont;
      ctx.fillText(" "+r.rank, rankX, rowY);
    });
    ctx.restore();

    function headerText(ch,v){
      const xs = ch.scales?.x;
      if (xs?.getLabelForValue) return String(xs.getLabelForValue(v));
      const lbls = ch.data?.labels;
      if (lbls && v>=0 && v<lbls.length) return String(lbls[v]);
      return String(v);
    }
  }
};
