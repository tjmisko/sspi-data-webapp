const shiftRotatedTicksPlugin = {
  id: 'shiftRotatedTicks',
  afterDraw(chart) {
    const xScale = chart.scales['x'];
    if (!xScale) return;

    const ctx = chart.ctx;
    const ticks = xScale.ticks;
    const options = xScale.options.ticks;
    const rotation = options.maxRotation || 0;
    const rad = rotation * Math.PI / 180;
    const shift = 20; // Adjust as needed

    ctx.save();
    ctx.font = Chart.helpers.toFont(options.font).string;
    ctx.textAlign = 'left';
    ctx.textBaseline = 'middle';

    ticks.forEach((tick, i) => {
      const x = xScale.getPixelForTick(i);
      const y = xScale.bottom + options.padding;
      ctx.save();
      ctx.translate(x, y - shift);
      ctx.rotate(-rad);
      ctx.fillStyle = typeof options.color === 'function' ? options.color({ chart, tick, index: i }) : options.color || '#666';
      ctx.fillText(tick.label, 0, 0);
      ctx.restore();
    });

    ctx.restore();
  }
};
