$(".data-download-reveal").click(() => {
    $(".data-download-form").slideDown(() => {
        $(".data-download-reveal").slideUp();
    });
}
)

$(".data-download-close").click(() => {
    $(".data-download-form").slideUp();
    $(".data-download-reveal").slideDown();
})