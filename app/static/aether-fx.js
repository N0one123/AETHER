/* =====================================================================
   AETHER — interface effects  (aether-fx.js)
   Purely presentational. Safe to load alongside script.js: it never
   touches forms, charts or your existing button handlers.
   ===================================================================== */
(function () {
    "use strict";

    var reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    var $ = function (sel, root) { return (root || document).querySelector(sel); };
    var $$ = function (sel, root) { return Array.prototype.slice.call((root || document).querySelectorAll(sel)); };
    var pad = function (n) { return String(n).padStart(2, "0"); };

    /* -------------------------------------------------------------
       1. Starfield background
       ------------------------------------------------------------- */
    function starfield() {
        var canvas = $("#starfield");
        if (!canvas || !canvas.getContext) return;
        var ctx = canvas.getContext("2d");
        var dpr = Math.min(window.devicePixelRatio || 1, 2);
        var stars = [], shooting = null, w = 0, h = 0, raf = null;

        function resize() {
            w = window.innerWidth; h = window.innerHeight;
            canvas.width = w * dpr; canvas.height = h * dpr;
            ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
            var count = Math.round((w * h) / 9000);
            stars = [];
            for (var i = 0; i < count; i++) {
                stars.push({
                    x: Math.random() * w,
                    y: Math.random() * h,
                    r: Math.random() * 1.15 + 0.2,
                    a: Math.random() * 0.6 + 0.2,
                    tw: Math.random() * 0.02 + 0.004,
                    ph: Math.random() * Math.PI * 2,
                    vx: (Math.random() - 0.5) * 0.04,
                    vy: Math.random() * 0.05 + 0.01,
                    hue: Math.random() < 0.15 ? 190 : 215
                });
            }
            if (reduceMotion) draw(0);
        }

        function draw(t) {
            ctx.clearRect(0, 0, w, h);
            for (var i = 0; i < stars.length; i++) {
                var s = stars[i];
                if (!reduceMotion) {
                    s.x += s.vx; s.y += s.vy;
                    if (s.y > h) { s.y = 0; s.x = Math.random() * w; }
                    if (s.x < 0) s.x = w; if (s.x > w) s.x = 0;
                }
                var alpha = s.a * (0.6 + 0.4 * Math.sin(t * s.tw * 0.06 + s.ph));
                ctx.beginPath();
                ctx.arc(s.x, s.y, s.r, 0, Math.PI * 2);
                ctx.fillStyle = "hsla(" + s.hue + ",90%,85%," + alpha + ")";
                ctx.fill();
            }
            // occasional shooting star
            if (!reduceMotion) {
                if (!shooting && Math.random() < 0.0025) {
                    shooting = { x: Math.random() * w * 0.7 + w * 0.3, y: Math.random() * h * 0.4, l: 0, life: 1 };
                }
                if (shooting) {
                    shooting.x -= 9; shooting.y += 4; shooting.l = Math.min(shooting.l + 14, 140); shooting.life -= 0.018;
                    var g = ctx.createLinearGradient(shooting.x, shooting.y, shooting.x + shooting.l, shooting.y - shooting.l * 0.44);
                    g.addColorStop(0, "rgba(200,245,255," + shooting.life + ")");
                    g.addColorStop(1, "rgba(200,245,255,0)");
                    ctx.strokeStyle = g; ctx.lineWidth = 1.4;
                    ctx.beginPath(); ctx.moveTo(shooting.x, shooting.y);
                    ctx.lineTo(shooting.x + shooting.l, shooting.y - shooting.l * 0.44); ctx.stroke();
                    if (shooting.life <= 0) shooting = null;
                }
            }
        }

        function loop(t) { draw(t); raf = requestAnimationFrame(loop); }

        resize();
        window.addEventListener("resize", resize);
        if (!reduceMotion) {
            raf = requestAnimationFrame(loop);
            document.addEventListener("visibilitychange", function () {
                if (document.hidden) cancelAnimationFrame(raf);
                else raf = requestAnimationFrame(loop);
            });
        }
    }

    /* -------------------------------------------------------------
       2. Staggered entrance (sets --i on each child)
       ------------------------------------------------------------- */
    function stagger() {
        var groups = [
            ".main-content", ".dashboard", ".core-content", ".health-overview", ".emergency-overview",
            ".metrics-grid", ".dashboard-metrics", ".dashboard-grid", ".severity-grid",
            ".incident-list", ".core-status-grid", ".symptom-grid"
        ];
        groups.forEach(function (sel) {
            $$(sel).forEach(function (group) {
                var i = 0;
                Array.prototype.forEach.call(group.children, function (child) {
                    if (child.classList.contains("topbar")) return;
                    child.style.setProperty("--i", Math.min(i++, 14));
                });
            });
        });
        $$("tbody").forEach(function (tb) {
            Array.prototype.forEach.call(tb.rows, function (row, i) { row.style.setProperty("--row", Math.min(i, 20)); });
        });
    }

    /* -------------------------------------------------------------
       3. Count-up numbers
       ------------------------------------------------------------- */
    function countUp() {
        var targets = $$(".metric-value, .severity-card strong, .health-data-item strong, .assessment-stats strong");
        targets.forEach(function (el) {
            var raw = el.textContent.trim();
            var m = raw.match(/^(-?\d[\d,]*(?:\.\d+)?)(.*)$/);
            if (!m) return;
            var end = parseFloat(m[1].replace(/,/g, ""));
            var decimals = (m[1].split(".")[1] || "").length;
            var suffix = m[2];
            if (!isFinite(end) || reduceMotion) return;
            var dur = 1200, start = null;
            el.textContent = (0).toFixed(decimals) + suffix;
            function step(ts) {
                if (!start) start = ts;
                var p = Math.min((ts - start) / dur, 1);
                var eased = 1 - Math.pow(1 - p, 4);
                var val = end * eased;
                el.textContent = val.toLocaleString(undefined, { minimumFractionDigits: decimals, maximumFractionDigits: decimals }) + suffix;
                if (p < 1) requestAnimationFrame(step);
                else el.textContent = raw;
            }
            setTimeout(function () { requestAnimationFrame(step); }, 250);
        });
    }

    /* -------------------------------------------------------------
       4. Decorative sparklines on metric cards
       ------------------------------------------------------------- */
    function sparklines() {
        var NS = "http://www.w3.org/2000/svg";
        $$(".metric-card").forEach(function (card, idx) {
            if (card.querySelector(".metric-spark")) return;
            var pts = [], n = 9, seed = (card.textContent.length * 7 + idx * 13) % 97;
            for (var i = 0; i < n; i++) {
                seed = (seed * 37 + 11) % 97;
                pts.push([i * (72 / (n - 1)), 6 + (seed / 97) * 18]);
            }
            var d = "M" + pts.map(function (p) { return p[0].toFixed(1) + " " + p[1].toFixed(1); }).join(" L");
            var svg = document.createElementNS(NS, "svg");
            svg.setAttribute("class", "metric-spark");
            svg.setAttribute("viewBox", "0 0 72 28");
            svg.setAttribute("aria-hidden", "true");
            svg.innerHTML =
                '<defs><linearGradient id="sparkFill" x1="0" y1="0" x2="0" y2="1">' +
                '<stop offset="0" stop-color="#5ee4ff" stop-opacity=".35"/><stop offset="1" stop-color="#5ee4ff" stop-opacity="0"/>' +
                "</linearGradient></defs>" +
                '<path class="area" d="' + d + ' L72 28 L0 28 Z"/><path d="' + d + '"/>';
            card.appendChild(svg);
        });
    }

    /* -------------------------------------------------------------
       5. Mouse-follow spotlight
       ------------------------------------------------------------- */
    function spotlight() {
        var sel = ".metric-card, .dashboard-panel, .content-panel, .severity-card, .incident-card, .core-status-item";
        document.addEventListener("pointermove", function (e) {
            var el = e.target.closest && e.target.closest(sel);
            if (!el) return;
            var r = el.getBoundingClientRect();
            el.style.setProperty("--mx", (e.clientX - r.left) + "px");
            el.style.setProperty("--my", (e.clientY - r.top) + "px");
        }, { passive: true });
    }

    /* -------------------------------------------------------------
       6. Button ripple
       ------------------------------------------------------------- */
    function ripples() {
        document.addEventListener("pointerdown", function (e) {
            var btn = e.target.closest && e.target.closest(".action-button");
            if (!btn || reduceMotion) return;
            var r = btn.getBoundingClientRect();
            var size = Math.max(r.width, r.height);
            var span = document.createElement("span");
            span.className = "ripple";
            span.style.width = span.style.height = size + "px";
            span.style.left = (e.clientX - r.left - size / 2) + "px";
            span.style.top = (e.clientY - r.top - size / 2) + "px";
            btn.appendChild(span);
            setTimeout(function () { span.remove(); }, 700);
        });
    }

    /* -------------------------------------------------------------
       7. Live UTC clock + session timer
       ------------------------------------------------------------- */
    function clock() {
        var clockEl = $("[data-clock]"), upEl = $("[data-uptime]");
        if (!clockEl && !upEl) return;
        var key = "aether-session-start";
        var startTs = parseInt(sessionStorage.getItem(key), 10);
        if (!startTs) { startTs = Date.now(); sessionStorage.setItem(key, String(startTs)); }
        function tick() {
            var now = new Date();
            if (clockEl) clockEl.textContent = pad(now.getUTCHours()) + ":" + pad(now.getUTCMinutes()) + ":" + pad(now.getUTCSeconds());
            if (upEl) {
                var s = Math.floor((Date.now() - startTs) / 1000);
                upEl.textContent = pad(Math.floor(s / 3600)) + ":" + pad(Math.floor(s / 60) % 60) + ":" + pad(s % 60);
            }
        }
        tick();
        setInterval(tick, 1000);
    }

    /* -------------------------------------------------------------
       8. Mobile sidebar
       ------------------------------------------------------------- */
    function sidebar() {
        var body = document.body;
        $$("[data-sidebar-toggle]").forEach(function (b) {
            b.addEventListener("click", function () { body.classList.toggle("sidebar-open"); });
        });
        $$("[data-sidebar-close]").forEach(function (b) {
            b.addEventListener("click", function () { body.classList.remove("sidebar-open"); });
        });
    }

    /* -------------------------------------------------------------
       9. Dismissible messages
       ------------------------------------------------------------- */
    function messages() {
        $$(".form-message").forEach(function (msg) {
            if (msg.querySelector(".message-close")) return;
            var btn = document.createElement("button");
            btn.type = "button";
            btn.className = "message-close";
            btn.setAttribute("aria-label", "Dismiss message");
            btn.innerHTML = "&times;";
            btn.addEventListener("click", function () { dismiss(msg); });
            msg.appendChild(btn);
            if (msg.classList.contains("success-message")) {
                setTimeout(function () { dismiss(msg); }, 7000);
            }
        });
        function dismiss(msg) {
            msg.classList.add("is-leaving");
            setTimeout(function () { msg.remove(); }, 420);
        }
    }

    /* -------------------------------------------------------------
       10. Symptom counter (evaluation page)
       ------------------------------------------------------------- */
    function symptomCounter() {
        var counter = $("[data-symptom-counter] b");
        if (!counter) return;
        var boxes = $$('.symptom-option input[type="checkbox"]');
        function update() {
            counter.textContent = boxes.filter(function (b) { return b.checked; }).length;
        }
        boxes.forEach(function (b) { b.addEventListener("change", update); });
        update();
    }

    /* -------------------------------------------------------------
       11. Command palette (Ctrl/Cmd + K, or "/")
       ------------------------------------------------------------- */
    function commandPalette() {
        var overlay = $("[data-cmdk]");
        if (!overlay) return;
        var input = $("[data-cmdk-input]", overlay);
        var list = $("[data-cmdk-list]", overlay);
        var items = [], filtered = [], active = 0;

        // build from sidebar so it always matches your navigation
        var group = "";
        $$(".navigation > *").forEach(function (node) {
            if (node.classList.contains("nav-label")) { group = node.textContent.trim(); return; }
            if (!node.matches("a.nav-item")) return;
            var icon = node.querySelector("span");
            items.push({
                group: group,
                href: node.getAttribute("href"),
                icon: icon ? icon.textContent.trim() : "•",
                label: node.textContent.replace(icon ? icon.textContent : "", "").trim()
            });
        });

        function render() {
            var q = input.value.trim().toLowerCase();
            filtered = items.filter(function (it) { return !q || it.label.toLowerCase().indexOf(q) !== -1; });
            if (active >= filtered.length) active = 0;
            if (!filtered.length) { list.innerHTML = '<li class="cmdk-empty">No matching systems</li>'; return; }
            var html = "", lastGroup = null;
            filtered.forEach(function (it, i) {
                if (it.group !== lastGroup) { html += '<li class="cmdk-group">' + it.group + "</li>"; lastGroup = it.group; }
                html += '<li class="cmdk-item' + (i === active ? " is-active" : "") + '" data-index="' + i + '">' +
                    '<span class="cmdk-icon">' + it.icon + "</span>" + it.label +
                    '<span class="cmdk-hint">Open ↵</span></li>';
            });
            list.innerHTML = html;
            var cur = list.querySelector(".is-active");
            if (cur) cur.scrollIntoView({ block: "nearest" });
        }

        function open() {
            overlay.hidden = false;
            input.value = ""; active = 0; render();
            setTimeout(function () { input.focus(); }, 10);
        }
        function close() { overlay.hidden = true; }
        function go(i) { var it = filtered[i]; if (it) window.location.href = it.href; }

        $$("[data-cmdk-open]").forEach(function (b) { b.addEventListener("click", open); });
        overlay.addEventListener("click", function (e) { if (e.target === overlay) close(); });
        list.addEventListener("mousemove", function (e) {
            var li = e.target.closest(".cmdk-item");
            if (li && +li.dataset.index !== active) { active = +li.dataset.index; render(); }
        });
        list.addEventListener("click", function (e) {
            var li = e.target.closest(".cmdk-item");
            if (li) go(+li.dataset.index);
        });
        input.addEventListener("input", function () { active = 0; render(); });

        document.addEventListener("keydown", function (e) {
            var typing = /INPUT|TEXTAREA|SELECT/.test((document.activeElement || {}).tagName || "");
            if ((e.key === "k" || e.key === "K") && (e.metaKey || e.ctrlKey)) { e.preventDefault(); overlay.hidden ? open() : close(); return; }
            if (e.key === "/" && !typing && overlay.hidden) { e.preventDefault(); open(); return; }
            if (overlay.hidden) return;
            if (e.key === "Escape") close();
            else if (e.key === "ArrowDown") { e.preventDefault(); active = (active + 1) % Math.max(filtered.length, 1); render(); }
            else if (e.key === "ArrowUp") { e.preventDefault(); active = (active - 1 + filtered.length) % Math.max(filtered.length, 1); render(); }
            else if (e.key === "Enter") { e.preventDefault(); go(active); }
        });
    }

    /* -------------------------------------------------------------
       12. Colour status pills by meaning (text-based, no backend change)
       ------------------------------------------------------------- */
    function statusTones() {
        var danger = /(alert|critical|emergency|offline|fail|error|down|danger)/i;
        var warn = /(pending|warn|degraded|standby|standing|monitor|caution|maintenance|simulat)/i;
        $$(".core-status, .mission-status, .crew-health").forEach(function (el) {
            var t = el.textContent;
            if (danger.test(t)) el.setAttribute("data-tone", "danger");
            else if (warn.test(t)) el.setAttribute("data-tone", "warn");
        });
    }

    function init() {
        statusTones();
        starfield();
        stagger();
        sparklines();
        countUp();
        spotlight();
        ripples();
        clock();
        sidebar();
        messages();
        symptomCounter();
        commandPalette();
    }

    if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
    else init();
})();
