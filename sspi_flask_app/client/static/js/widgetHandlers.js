async function addWidget() {
    await $.get('/widget', (data) => {
        grid.addWidget({w:3, h:2, content: data})    
    })
}

function removeWidget(el) {
    grid.removeWidget(el)
}