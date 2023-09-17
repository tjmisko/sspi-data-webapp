async function addWidget() {
    await $.get('/widget', (data) => {
        grid.addWidget({w:6, h:10, minW: 4, minH: 5, content: data, id: crypto.randomUUID()})    
    })
}

function removeWidget(el) {
    widgetId = $(el).parent().parent().parent().attr('id')
    grid.removeWidget()
    console.log("Removed widget" + widgetID)
}