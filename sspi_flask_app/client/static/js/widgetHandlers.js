$(".widget-type-options-menu").hide()
function revealWidgetOptions() {
    $(".widget-type-options-menu").slideToggle(0.1)
}

async function addWidget(widgettype) {
    await $.get(`/widget/${widgettype}`, (data) => {
        grid.addWidget({w:6, h:10, minW: 4, minH: 5, content: data, id: crypto.randomUUID()});
        revealWidgetOptions();
    })
}

function removeWidget(el) {
    widgetId = $(el).parents().eq(2).attr('gs-id')
    grid.removeWidget($(`[gs-id=${widgetId}]`).get(0))
}

function fullscreenWidget(el) {
    widgetId = $(el).parents().eq(2).attr('gs-id')
    widget = $(`[gs-id=${widgetId}]`).get(0)
    // console.log(widgetId)
    widgetW = $(widget).attr('gs-w')
    widgetH =$(widget).attr('gs-h')
    fullscreenHeight = Math.floor(0.95*window.innerHeight/50)
    grid.update(widget, {w:12, h: fullscreenHeight})
    window.scrollTo(0,$(widget).offset().top-10)
    fullscreenButton = $(`[gs-id=${widgetId}]`)
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
