function revealWidgetOptions() {
    $(".widget-type-options-menu").slideToggle()
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
    repositionInfo = {
        widgetW: $(widget).attr('gs-w'),
        widgetH: $(widget).attr('gs-h')
    }
    fullscreenHeight = Math.floor(0.95*window.innerHeight/50)
    grid.update(widget, {w:12, h: fullscreenHeight})
    window.scrollTo(0,$(widget).offset().top-10)
    fullscreenButton = $(`[gs-id=${widgetId}]`).find(".fullscreen-button").html(
        `<button onclick="returnWidgetToOriginalSize(this, ${repositionInfo})" class="widget-controls-button fullscreen-button"><img class="fullscreen" style="width: 32px; height: 32px" src="{{ url_for('client_bp.static', filename='/svg_assets/fullscreen.svg') }}"/></button>`
    )
}

function returnWidgetToOriginalSize(el, repositionInfo) {
    $(el).parents().eq(2).attr('gs-id')
    widget = $(`[gs-id=${widgetId}]`).get(0)
    grid.update(widget, {w:repositionInfo.widgetW, h: repositionInfo.widgetH})
    fullscreenButton = $(`[gs-id=${widgetId}]`).find(".fullscreen-button").html(
        `<button onclick="fullscreenWidget(this)" class="widget-controls-button fullscreen-button">button</button>`
    )
}
