$(".widget-type-options-menu").hide()
function revealWidgetOptions() {
    $(".widget-type-options-menu").slideToggle(0.1)
}

async function addWidget(widgettype) {
    await $.get(`/widget/${widgettype}`, (data) => {
        gsId = crypto.randomUUID()
        console.log(gsId)
        grid.addWidget({w:6, h:20, minW: 4, minH: 5, content: data, id: gsId});
        revealWidgetOptions();
    }).then(() => {
        if (widgettype === "barchart") {
            setupBarChart(gsId)
        }
    });
}

function removeWidget(el) {
    widget = $(el).parents('.grid-stack-item')
    console.log(widget.attr('gs-id'))
    grid.removeWidget(widget.get(0))
}

function fullscreenWidget(el) {
    widget = $(el).parents('.grid-stack-item')
    console.log(widget.get(0))
    console.log(widget.attr('gs-id'))
    widgetW = widget.attr('gs-w')
    widgetH = widget.attr('gs-h')
    console.log(widgetW, widgetH)
    fullscreenHeight = Math.floor(0.95*window.innerHeight/25)
    grid.update(widget.get(0), {w:12, h: fullscreenHeight})
    window.scrollTo(0, widget.offset().top-10)
    fullscreenButton = widget
        .find(".fullscreen-button")
        .attr("onclick", `returnWidgetToOriginalSize(this, ${widgetW}, ${widgetH})`)
}

function returnWidgetToOriginalSize(el, widgetW, widgetH) {
    $(el).parents().eq(2).attr('gs-id')
    widget = $(`[gs-id=${widgetId}]`).get(0)
    grid.update(widget, {w:widgetW, h: widgetH})
    fullscreenButton = $(`[gs-id=${widgetId}]`)
        .find(".fullscreen-button")
        .attr("onclick", "fullscreenWidget(this)")
}

function setupBarChart(gsId) {
    let BarChartCanvas = $(`[gs-id=${gsId}]`).find(".bar-chart").get(0)
    console.log(BarChartCanvas)
    const BarChart = new Chart(BarChartCanvas, {
        type: 'bar',
        data: {},
        options: {}
    })
    makeBarChart(BarChart, "BIODIV")
}