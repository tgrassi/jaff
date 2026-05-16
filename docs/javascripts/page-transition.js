(function () {
    let firstLoad = true;

    function init() {
        if (firstLoad) { firstLoad = false; return; }
        const content = document.querySelector(".md-content__inner");
        if (!content) return;
        content.classList.remove("jaff-page-enter");
        void content.offsetWidth; // force reflow to restart animation
        content.classList.add("jaff-page-enter");
    }

    if (typeof document$ !== "undefined") {
        document$.subscribe(init);
    } else {
        document.addEventListener("DOMContentLoaded", init);
    }
})();
