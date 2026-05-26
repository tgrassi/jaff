(function () {
    function createElements(containerEl) {
        containerEl.querySelector(".jaff-nav-indicator")?.remove();
        containerEl.querySelector(".jaff-nav-track")?.remove();

        const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
        svg.classList.add("jaff-nav-track");
        svg.setAttribute("aria-hidden", "true");
        const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
        svg.appendChild(path);
        containerEl.appendChild(svg);

        const indicator = document.createElement("div");
        indicator.className = "jaff-nav-indicator";
        containerEl.appendChild(indicator);

        return { indicator, svg };
    }

    function updateTrack(containerEl, navEl, svg) {
        const links = [...navEl.querySelectorAll(".md-nav__link")];
        if (!links.length) return;

        const cRect = containerEl.getBoundingClientRect();
        const OFFSET = 10;
        const TILT = 7;
        const half = 0.75;

        const pts = links.map(link => {
            const r = link.getBoundingClientRect();
            return {
                x:   r.left   - cRect.left + half - OFFSET,
                top: r.top    - cRect.top,
                bot: r.bottom - cRect.top,
            };
        });

        const segs = pts.map((p, i) => {
            const prev = pts[i - 1];
            const next = pts[i + 1];
            const vertStart = (prev && Math.abs(p.x - prev.x) > 1) ? p.top + TILT : p.top;
            const vertEnd   = (next && Math.abs(p.x - next.x) > 1) ? p.bot - TILT : p.bot;
            return { x: p.x, top: p.top, vertStart, vertEnd };
        });

        let d = `M${segs[0].x},${segs[0].top}`;
        for (let i = 0; i < segs.length; i++) {
            const s = segs[i];
            const next = segs[i + 1];
            d += ` L${s.x},${s.vertEnd}`;
            if (next && Math.abs(next.x - s.x) > 1) {
                d += ` L${next.x},${next.vertStart}`;
            }
        }

        svg.querySelector("path").setAttribute("d", d);
        svg.style.height = containerEl.offsetHeight + "px";
    }

    function updateIndicator(containerEl, navEl, indicator, animate) {
        const active = navEl.querySelector(".md-nav__link--active");
        if (!active) {
            indicator.style.opacity = "0";
            return;
        }

        const cRect = containerEl.getBoundingClientRect();
        const activeRect = active.getBoundingClientRect();
        const itemH = activeRect.height;
        const barH = itemH * 0.55;
        const top  = activeRect.top  - cRect.top  + (itemH - barH) / 2;
        const PILL_WIDTH = 3.5;
        const left = activeRect.left - cRect.left + 0.75 - 10 - PILL_WIDTH / 2;

        if (!animate) {
            indicator.style.transition = "none";
            indicator.style.opacity = "0";
        }

        requestAnimationFrame(() => {
            indicator.style.top    = top  + "px";
            indicator.style.left   = left + "px";
            indicator.style.height = barH + "px";

            if (!animate) {
                requestAnimationFrame(() => {
                    indicator.style.transition = "";
                    indicator.style.opacity = "1";
                });
            } else {
                indicator.style.opacity = "1";
            }
        });
    }

    function setup(sidebarSelector, navSelector) {
        const sidebar = document.querySelector(sidebarSelector);
        if (!sidebar) return;

        const navEl = sidebar.querySelector(navSelector);
        if (!navEl) return;

        // Attach to sidebar (not nav) — avoids scrollwrap overflow clipping
        const { indicator, svg } = createElements(sidebar);

        function refresh(animate) {
            updateTrack(sidebar, navEl, svg);
            updateIndicator(sidebar, navEl, indicator, animate);
        }

        refresh(false);

        const observer = new MutationObserver(() => refresh(true));
        observer.observe(navEl, {
            subtree: true,
            attributes: true,
            attributeFilter: ["class"],
        });

        // Recompute on scroll since viewport-relative rects change
        const scrollwrap = sidebar.querySelector(".md-sidebar__scrollwrap");
        if (scrollwrap) {
            scrollwrap.addEventListener("scroll", () => refresh(false));
        }
    }

    function setupHighlight(sidebarSelector, navSelector) {
        const sidebar = document.querySelector(sidebarSelector);
        if (!sidebar) return;

        const navEl = sidebar.querySelector(navSelector);
        if (!navEl) return;

        const highlight = document.createElement("div");
        highlight.className = "jaff-nav-highlight";
        highlight.style.opacity = "0";
        sidebar.appendChild(highlight);

        let initialized = false;

        function refresh(animate) {
            const active = navEl.querySelector(".md-nav__link--active");
            if (!active) return; // keep last position — never hide mid-navigation

            const cRect = sidebar.getBoundingClientRect();
            const aRect = active.getBoundingClientRect();
            const top    = aRect.top    - cRect.top;
            const left   = aRect.left   - cRect.left;
            const height = aRect.height;
            const width  = aRect.width;

            if (!initialized) {
                highlight.style.transition = "none";
                requestAnimationFrame(() => {
                    highlight.style.top    = top    + "px";
                    highlight.style.left   = left   + "px";
                    highlight.style.width  = width  + "px";
                    highlight.style.height = height + "px";
                    requestAnimationFrame(() => {
                        highlight.style.transition = "";
                        highlight.style.opacity = "1";
                        initialized = true;
                    });
                });
            } else {
                highlight.style.top    = top    + "px";
                highlight.style.left   = left   + "px";
                highlight.style.width  = width  + "px";
                highlight.style.height = height + "px";
            }
        }

        refresh(false);

        const observer = new MutationObserver(() => refresh(true));
        observer.observe(navEl, {
            subtree: true,
            attributes: true,
            attributeFilter: ["class"],
        });

        const scrollwrap = sidebar.querySelector(".md-sidebar__scrollwrap");
        if (scrollwrap) {
            scrollwrap.addEventListener("scroll", () => refresh(false));
        }
    }

    function setupNavSlide() {
        const sidebar = document.querySelector(".md-sidebar--primary");
        if (!sidebar) return;

        sidebar.addEventListener("click", (e) => {
            const link = e.target.closest("a.md-nav__link");
            if (!link || !link.href || !sidebar.contains(link)) return;

            // Collect ancestor nested items of the clicked link (sections to keep/expand)
            const newAncestors = new Set();
            let cur = link.parentElement;
            while (cur && sidebar.contains(cur)) {
                if (cur.classList && cur.classList.contains("md-nav__item--nested")) {
                    newAncestors.add(cur);
                }
                cur = cur.parentElement;
            }

            // Find all currently-active nested items that are NOT ancestors → collapse them
            const toCollapse = [];
            sidebar.querySelectorAll(".md-nav__item--nested.md-nav__item--active").forEach(item => {
                if (newAncestors.has(item)) return;
                const cb = item.querySelector(":scope > input.md-nav__toggle");
                if (cb && cb.checked) toCollapse.push(cb);
            });

            // Find ancestors that need expanding
            const toExpand = [];
            newAncestors.forEach(item => {
                const cb = item.querySelector(":scope > input.md-nav__toggle");
                if (cb && !cb.checked) toExpand.push(cb);
            });

            if (!toCollapse.length && !toExpand.length) return;

            // Block instant navigation so sidebar isn't replaced mid-animation
            e.preventDefault();
            e.stopImmediatePropagation();

            toCollapse.forEach(cb => { cb.checked = false; });
            toExpand.forEach(cb => { cb.checked = true; });

            // Wait for slide transition (250ms) then navigate
            setTimeout(() => {
                window.location.href = link.href;
            }, 280);
        }, true); // capture phase: run before instant-nav's handler
    }

    function init() {
        setup(".md-sidebar--secondary", ".md-nav--secondary");
        setupNavSlide();
    }

    if (typeof document$ !== "undefined") {
        document$.subscribe(init);
    } else {
        document.addEventListener("DOMContentLoaded", init);
    }
})();
