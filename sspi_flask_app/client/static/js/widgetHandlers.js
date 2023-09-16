async function addWidget() {
    await $.get('/widget', (data) => {
        grid.addWidget(data)    
    })
}