function addWidget() {
    $("widget-menu")
}

async function addWidget() {
    await $.get('/widget', (data) => {
        grid.addWidget({w:6, h:10, minW: 4, minH: 5, content: data, id: crypto.randomUUID()})    
    })
}

function removeWidget(el) {
    widgetId = $(el).parents().eq(4).attr('gs-id')
    grid.removeWidget($(`[gs-id=${widgetId}]`).get(0))
}