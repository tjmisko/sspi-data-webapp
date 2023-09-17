$(".data-download-reveal").click(()=>{$(".data-download-form").slideDown();$(".data-download-reveal").slideUp();})
$(".data-download-close").click(()=>{$(".data-download-reveal").slideDown();$(".data-download-form").slideUp();})
async function addWidget(){await $.get('/widget',(data)=>{grid.addWidget({w:3,h:2,content:data})})}
function removeWidget(el){grid.removeWidget($(el).parent().parent())}