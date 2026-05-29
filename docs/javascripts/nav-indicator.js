(function () {
    // Listeners from the previous page (instant navigation re-runs init).
    let tocCleanup = null;

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

    function updateIndicator(containerEl, active, indicator, animate) {
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
            // Snap to position with no slide, and crucially without flashing
            // opacity (that caused a visible blink on every TOC auto-scroll).
            indicator.style.transition = "none";
            indicator.style.top    = top  + "px";
            indicator.style.left   = left + "px";
            indicator.style.height = barH + "px";
            indicator.style.opacity = "1";
            requestAnimationFrame(() => {
                indicator.style.transition = "";
            });
        } else {
            indicator.style.top    = top  + "px";
            indicator.style.left   = left + "px";
            indicator.style.height = barH + "px";
            indicator.style.opacity = "1";
        }
    }

    function setup(sidebarSelector, navSelector) {
        const sidebar = document.querySelector(sidebarSelector);
        if (!sidebar) return;

        const navEl = sidebar.querySelector(navSelector);
        if (!navEl) return;

        // Tear down the previous page's listeners and clear any stale highlight.
        if (tocCleanup) tocCleanup();
        navEl.querySelectorAll(".jaff-toc-active")
            .forEach(el => el.classList.remove("jaff-toc-active"));

        // Attach to sidebar (not nav) — avoids scrollwrap overflow clipping
        const { indicator, svg } = createElements(sidebar);

        // Map each TOC link to the heading it points at, in document order.
        const entries = [...navEl.querySelectorAll("a.md-nav__link[href*='#']")]
            .map(link => {
                const id = decodeURIComponent((link.hash || "").slice(1));
                const heading = id ? document.getElementById(id) : null;
                return { link, heading };
            })
            .filter(e => e.heading);

        // Clicking a TOC link pins it active until the next manual scroll, so
        // the clicked link wins even if the page lands at the bottom.
        let locked = null;

        // Active section by scroll position.
        //  - top (scrollY 0): no heading passed the trigger → first link
        //  - middle: the section currently under the trigger line
        //  - bottom: trailing headings too short to ever reach the trigger are
        //    distributed across the remaining scroll, so the last link becomes
        //    active exactly at the page bottom — without skipping the others.
        const TRIGGER = 130; // px from viewport top (clears header + tabs)
        function resolveActive() {
            if (!entries.length) return null;

            const scrollY = window.scrollY;
            const maxScroll = document.documentElement.scrollHeight - window.innerHeight;
            // Absolute doc scroll at which each heading reaches the trigger line.
            const targets = entries.map(
                e => e.heading.getBoundingClientRect().top + scrollY - TRIGGER);

            // Last heading that has reached the trigger at the current scroll.
            let idx = 0;
            for (let i = 0; i < targets.length; i++) {
                if (targets[i] <= scrollY + 1) idx = i; else break;
            }

            // Trailing headings whose target exceeds maxScroll can never reach
            // the trigger. Spread them over the leftover scroll past the last
            // reachable heading so they still light up on the way to the bottom.
            if (maxScroll > 0) {
                let lastReach = 0;
                for (let i = 0; i < targets.length; i++) {
                    if (targets[i] <= maxScroll + 1) lastReach = i; else break;
                }
                if (lastReach < entries.length - 1) {
                    const startScroll = targets[lastReach];
                    const span = maxScroll - startScroll;
                    if (span > 0 && scrollY > startScroll) {
                        const frac = Math.min(1, (scrollY - startScroll) / span);
                        const remaining = (entries.length - 1) - lastReach;
                        idx = Math.max(idx, lastReach + Math.round(frac * remaining));
                    }
                }
            }
            return entries[Math.min(idx, entries.length - 1)].link;
        }

        function refresh(animate) {
            updateTrack(sidebar, navEl, svg);
            const active = locked || resolveActive();
            // Clear any stale highlight anywhere, then mark the single active.
            document.querySelectorAll(".jaff-toc-active")
                .forEach(el => { if (el !== active) el.classList.remove("jaff-toc-active"); });
            if (active) active.classList.add("jaff-toc-active");
            updateIndicator(sidebar, active, indicator, animate);
        }

        refresh(false);

        // Recompute on scroll/resize since viewport-relative rects change.
        let ticking = false;
        const onScroll = () => {
            if (ticking) return;
            ticking = true;
            requestAnimationFrame(() => {
                refresh(true);
                ticking = false;
            });
        };

        const controller = new AbortController();
        const { signal } = controller;
        // Capture phase catches scroll from whichever element actually scrolls
        // the page (window, body, or an inner wrapper) — scroll doesn't bubble.
        document.addEventListener("scroll", onScroll, { capture: true, passive: true, signal });
        window.addEventListener("resize", onScroll, { passive: true, signal });

        // Pin the clicked link; release on the next manual scroll input so the
        // programmatic smooth-scroll doesn't immediately unlock it.
        navEl.addEventListener("click", (e) => {
            const link = e.target.closest("a.md-nav__link[href*='#']");
            if (link && entries.some(en => en.link === link)) {
                locked = link;
                refresh(true);
            }
        }, { signal });
        const release = () => { if (locked) { locked = null; onScroll(); } };
        window.addEventListener("wheel", release, { passive: true, signal });
        window.addEventListener("touchmove", release, { passive: true, signal });
        window.addEventListener("keydown", release, { signal });

        tocCleanup = () => controller.abort();
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
