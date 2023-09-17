$(".data-download-reveal").click(()=>{$(".data-download-form").slideDown();$(".data-download-reveal").slideUp();})
$(".data-download-close").click(()=>{$(".data-download-reveal").slideDown();$(".data-download-form").slideUp();})
async function addWidget(){await $.get('/widget',(data)=>{grid.addWidget({w:6,h:10,minW:4,minH:5,content:data})})}
function removeWidget(el){grid.removeWidget(el.parenElement.parentElement.parentElement)
console.log("hello")}