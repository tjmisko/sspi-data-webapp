function revealWidgetOptions() {
    $("widget-type-options-menu").slideIn()
}

async function addWidget(widgettype) {
    await $.get(`/widget/${widgettype}`, (data) => {
        grid.addWidget({w:6, h:10, minW: 4, minH: 5, content: data, id: crypto.randomUUID()})    
    })
}

function removeWidget(el) {
    widgetId = $(el).parents().eq(4).attr('gs-id')
    grid.removeWidget($(`[gs-id=${widgetId}]`).get(0))
}