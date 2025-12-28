document.addEventListener("DOMContentLoaded", function() {
    var title = document.querySelector(".md-header__title");
    if (title) {
        title.innerHTML = title.innerHTML.replace("YAML", '<span style="color: #09cbcc;">YAML</span>');
    }
});
