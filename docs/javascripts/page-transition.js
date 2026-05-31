(function () {
    function animate() {
        const content = document.querySelector(".md-content__inner");
        if (!content) return;
        content.classList.remove("jaff-page-enter");
        void content.offsetWidth; // force reflow to restart animation
        content.classList.add("jaff-page-enter");
    }

    // Run on full page loads (we navigate via window.location for sidebar slide animation).
    // Also subscribe to document$ for any remaining instant-nav transitions.
    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", animate);
    } else {
        animate();
    }
    if (typeof document$ !== "undefined") {
        let first = true;
        document$.subscribe(() => {
            if (first) { first = false; return; }
            animate();
        });
    }
})();
