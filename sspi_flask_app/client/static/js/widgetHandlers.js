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
    console.log(grid.margin)
    console.log(widgetId)
}