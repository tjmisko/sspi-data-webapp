async function addWidget() {
    await $.get('/widget', (data) => {
        $('#add-widget-button').before(data);
        grid.addWidget(data)    
    })
}