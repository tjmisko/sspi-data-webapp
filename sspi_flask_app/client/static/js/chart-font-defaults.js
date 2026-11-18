// Put the flag font ahead of Chart.js's default family so country flags in
// chart titles, labels, and tooltips render as flags rather than letter pairs
// on Linux and Windows. Canvas text does not trigger web font loading, so load
// the face explicitly and redraw any chart drawn before it arrived.
(function () {
    if (typeof Chart === 'undefined') {
        return;
    }
    const flagFamily = "'Twemoji Country Flags'";
    const defaultFamily = Chart.defaults.font.family;
    if (defaultFamily.indexOf(flagFamily) === -1) {
        Chart.defaults.font.family = flagFamily + ', ' + defaultFamily;
    }
    if (!document.fonts || !document.fonts.load) {
        return;
    }
    document.fonts.load('1em ' + flagFamily, '\u{1F1FA}\u{1F1F8}').then(function () {
        Object.values(Chart.instances).forEach(function (chart) {
            chart.update('none');
        });
    }).catch(function () {});
})();
