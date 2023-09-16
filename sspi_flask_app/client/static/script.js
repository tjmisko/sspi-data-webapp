$(".data-download-reveal").click(()=>{$(".data-download-form").slideDown();$(".data-download-reveal").slideUp();})
$(".data-download-close").click(()=>{$(".data-download-reveal").slideDown();$(".data-download-form").slideUp();})
async function addWidget(){await $.get('/widget',(data)=>{$('#add-widget-button').before(data);grid.addWidget(data)})}