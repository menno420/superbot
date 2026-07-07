/* ============================================================================
   SuperBot program design system — shared runtime (window.SBDS)
   ----------------------------------------------------------------------------
   Vanilla JS, no build step, no dependencies. Loads after tokens/components CSS.
   Provides: theme manager (dark-first + persisted light), icon helper, escaping,
   formatting, chart renderers (single-hue bars, sparkline, status ticks) per the
   dataviz mark specs, an accessible command palette, and mobile-nav wiring.
   Living reference: /design.
   ========================================================================== */
(function () {
  "use strict";

  const esc = (s) =>
    String(s == null ? "" : s).replace(/[&<>"']/g, (c) => ({
      "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
    }[c]));

  /* ── theme ───────────────────────────────────────────────
     Dark is the brand-native default. SBDS.theme.init() runs inline in <head>
     (before first paint) to avoid a theme flash; toggle persists to localStorage. */
  const THEME_KEY = "sb:theme";
  const theme = {
    get() {
      try { const t = localStorage.getItem(THEME_KEY); if (t === "light" || t === "dark") return t; } catch (e) { /* private mode */ }
      return "dark";
    },
    set(t) {
      document.documentElement.setAttribute("data-theme", t);
      try { localStorage.setItem(THEME_KEY, t); } catch (e) { /* private mode */ }
      document.querySelectorAll("[data-theme-toggle]").forEach((btn) => {
        btn.setAttribute("aria-pressed", t === "light" ? "true" : "false");
        btn.innerHTML = icon(t === "light" ? "moon" : "sun", "currentColor", 17);
        btn.setAttribute("title", t === "light" ? "Switch to dark theme" : "Switch to light theme");
        btn.setAttribute("aria-label", btn.getAttribute("title"));
      });
    },
    toggle() { theme.set(theme.get() === "light" ? "dark" : "light"); },
    init() { document.documentElement.setAttribute("data-theme", theme.get()); },
  };

  /* ── icons ───────────────────────────────────────────────
     DS-owned chrome icons; merged under any SBDATA.ICONS so data-declared
     icon names keep working. 24×24, 2px stroke, round caps (v1 vocabulary). */
  const DS_ICONS = {
    gamepad: '<line x1="6" y1="11" x2="10" y2="11"/><line x1="8" y1="9" x2="8" y2="13"/><line x1="15" y1="12" x2="15.01" y2="12"/><line x1="18" y1="10" x2="18.01" y2="10"/><rect x="2" y="6" width="20" height="12" rx="6"/>',
    shield: '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>',
    sun: '<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/>',
    moon: '<path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z"/>',
    menu: '<path d="M4 7h16M4 12h16M4 17h16"/>',
    x: '<path d="M6 6l12 12M18 6L6 18"/>',
    flag: '<path d="M5 3v18M5 4h11l-2 4 2 4H5"/>',
    external: '<path d="M14 4h6v6M20 4l-9 9"/><path d="M19 14v5a1 1 0 0 1-1 1H6a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1h5"/>',
    inbox: '<path d="M3 13l3-8h12l3 8v5a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><path d="M3 13h5l1.5 2h5L16 13h5"/>',
    alert: '<path d="M12 3l10 18H2L12 3z"/><path d="M12 10v5M12 18v.5"/>',
    info: '<circle cx="12" cy="12" r="9"/><path d="M12 11v5M12 8v.5"/>',
    bot: '<rect x="4" y="8" width="16" height="11" rx="3"/><path d="M12 8V4M8 3v2M16 3v2"/><circle cx="9" cy="13" r="1"/><circle cx="15" cy="13" r="1"/>',
    search: '<circle cx="11" cy="11" r="7"/><path d="M21 21l-4-4"/>',
    chevron: '<path d="M9 6l6 6-6 6"/>',
    arrow: '<path d="M5 12h14M13 6l6 6-6 6"/>',
    back: '<path d="M19 12H5M11 6l-6 6 6 6"/>',
    check: '<path d="M20 6L9 17l-5-5"/>',
    plus: '<path d="M12 5v14M5 12h14"/>',
    clock: '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    activity: '<path d="M22 12h-4l-3 9L9 3l-3 9H2"/>',
    comment: '<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>',
    doc: '<path d="M6 2h9l5 5v15H6z"/><path d="M14 2v6h6"/>',
    coins: '<circle cx="12" cy="12" r="9"/><path d="M12 7v10M9.5 9.5h3a2 2 0 0 1 0 4H10a2 2 0 0 0 0 4h3.5"/>',
    chart: '<path d="M4 20V10M10 20V4M16 20v-7M22 20H2"/>',
    layers: '<path d="M12 3l9 5-9 5-9-5 9-5z"/><path d="M3 13l9 5 9-5"/>',
  };
  function iconSet() {
    const data = (window.SBDATA && window.SBDATA.ICONS) || {};
    return Object.assign({}, data, DS_ICONS);
  }
  function icon(name, color, size) {
    const body = iconSet()[name] || DS_ICONS.info;
    const s = size || 22;
    return `<svg width="${s}" height="${s}" viewBox="0 0 24 24" fill="none" stroke="${color || "currentColor"}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${body}</svg>`;
  }

  /* ── formatting ──────────────────────────────────────────── */
  const fmt = {
    num(n) {
      n = Number(n) || 0;
      if (Math.abs(n) >= 1e6) return (n / 1e6).toFixed(1).replace(/\.0$/, "") + "M";
      if (Math.abs(n) >= 1e4) return (n / 1e3).toFixed(1).replace(/\.0$/, "") + "K";
      return n.toLocaleString("en-US");
    },
    date(iso) {
      if (!iso) return "";
      const d = new Date(iso + (iso.length === 10 ? "T00:00:00Z" : ""));
      if (isNaN(d)) return iso;
      return d.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric", timeZone: "UTC" });
    },
  };

  /* ── charts (dataviz specs: thin marks, direct labels, ink-token text) ── */

  /* Horizontal single-hue bar list. items: [{label, value, href?, title?}].
     Rows may be links, so the container is a plain group (never role="img" —
     interactive descendants inside a presentational role are an ARIA violation
     and read as garbage); each row carries its own complete accessible name. */
  function barChart(items, opts) {
    opts = opts || {};
    const max = Math.max(1, ...items.map((i) => Number(i.value) || 0));
    const rows = items.map((i) => {
      const v = Number(i.value) || 0;
      const w = Math.max(0.5, (v / max) * 100);
      const tag = i.href ? "a" : "div";
      const href = i.href ? ` href="${esc(i.href)}"` : "";
      const name = i.title || `${i.label}: ${v}`;
      return `<${tag} class="sb-bar-row"${href} title="${esc(name)}" aria-label="${esc(name)}">
        <span class="lbl" aria-hidden="true">${esc(i.label)}</span>
        <span class="track" aria-hidden="true"><span class="bar" style="width:${w}%"></span></span>
        <span class="val" aria-hidden="true">${fmt.num(v)}</span>
      </${tag}>`;
    }).join("");
    return `<div class="sb-bars" role="group" aria-label="${esc(opts.ariaLabel || "Bar chart")}">${rows}</div>`;
  }

  /* 12-point sparkline for stat tiles (de-emphasis wash + 2px line). */
  function sparkline(values, opts) {
    opts = opts || {};
    const w = opts.width || 120, h = opts.height || 28, pad = 2;
    if (!values || values.length < 2) return "";
    const max = Math.max(1, ...values), min = Math.min(0, ...values);
    const span = max - min || 1;
    const pts = values.map((v, i) => {
      const x = pad + (i / (values.length - 1)) * (w - pad * 2);
      const y = h - pad - ((v - min) / span) * (h - pad * 2);
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    });
    const fill = `${pad},${h - pad} ${pts.join(" ")} ${w - pad},${h - pad}`;
    return `<svg class="spark" width="${w}" height="${h}" viewBox="0 0 ${w} ${h}" role="img" aria-label="${esc(opts.ariaLabel || "trend")}">
      <polygon class="fill" points="${fill}"></polygon>
      <polyline points="${pts.join(" ")}"></polyline>
    </svg>`;
  }

  /* Status tick strip. history: ["ok"|"warn"|"info"|"danger", …].
     The accessible name carries the SUMMARY (counts per state), so the data
     is never hue-only for screen readers; per-day detail rides the tooltips. */
  const TICK_LABEL = { ok: "operational", warn: "degraded", info: "maintenance", danger: "outage" };
  function tickStrip(history, opts) {
    opts = opts || {};
    const days = history.length;
    const counts = {};
    const ticks = history.map((s, i) => {
      const cls = TICK_LABEL[s] ? s : "ok";
      counts[cls] = (counts[cls] || 0) + 1;
      const ago = days - 1 - i;
      const when = ago === 0 ? "today" : `${ago}d ago`;
      return `<span class="sb-tick t-${cls}" title="${esc(when)}: ${esc(TICK_LABEL[cls])}"></span>`;
    }).join("");
    const summary = Object.entries(counts)
      .map(([k, n]) => `${n} ${TICK_LABEL[k]}`)
      .join(", ");
    return `<div class="sb-ticks" role="img" aria-label="${esc(opts.ariaLabel || `status, last ${days} days`)}: ${esc(summary)}">${ticks}</div>
      <div class="sb-tick-legend" aria-hidden="true"><span>${days} days ago</span><span>today</span></div>`;
  }

  /* Stat tile. {label, value, delta?: {text, dir: up|down|flat}, spark?: [..], href?} */
  function statTile(t) {
    const tag = t.href ? "a" : "div";
    const href = t.href ? ` href="${esc(t.href)}"` : "";
    const delta = t.delta ? `<span class="d ${esc(t.delta.dir || "flat")}">${esc(t.delta.text)}</span>` : "";
    const spark = t.spark ? sparkline(t.spark, { ariaLabel: `${t.label} trend` }) : "";
    return `<${tag} class="sb-stat"${href}><span class="v">${esc(t.value)}</span><span class="l">${esc(t.label)}</span>${delta}${spark}</${tag}>`;
  }

  /* ── command palette (accessible: combobox/listbox, roving selection) ──
     SBDS.palette.register(items) with [{group, label, sub?, code?, href, keywords?}]
     SBDS.palette.open() / close(); bound to Ctrl/Cmd-K + "/" and [data-palette-open]. */
  const palette = (() => {
    let items = [], overlay = null, input = null, listbox = null, emptyEl = null, sel = 0, results = [], lastFocus = null;

    function register(newItems) { items = newItems || []; }

    function score(item, q) {
      const hay = `${item.label} ${item.code || ""} ${item.sub || ""} ${item.keywords || ""}`.toLowerCase();
      if (!q) return 1;
      const idx = hay.indexOf(q);
      if (idx < 0) return -1;
      /* prefix boost compares against the command name itself, so "warn"
         boosts "!warn" without the user typing the bang */
      const codeBody = (item.code || "").replace(/^!/, "").toLowerCase();
      const boost = codeBody && codeBody.startsWith(q.replace(/^!/, "")) ? 500 : 0;
      return 1000 - idx - hay.length * 0.001 + boost;
    }

    function filter(q) {
      q = q.trim().toLowerCase();
      const scored = items
        .map((it) => ({ it, s: score(it, q) }))
        .filter((r) => r.s >= 0)
        .sort((a, b) => b.s - a.s)
        .slice(0, 40)
        .map((r) => r.it);
      /* regroup: keep score order INSIDE a group, but emit each group once
         (in order of its best hit) so headers never repeat down the list */
      const groups = [];
      const byGroup = new Map();
      scored.forEach((it) => {
        if (!byGroup.has(it.group)) { byGroup.set(it.group, []); groups.push(it.group); }
        byGroup.get(it.group).push(it);
      });
      return groups.flatMap((g) => byGroup.get(g));
    }

    function renderList(q) {
      results = filter(q);
      sel = 0;
      if (!results.length) {
        /* the empty state lives OUTSIDE the listbox (a bare div is not a valid
           listbox child), the combobox collapses, and the pointer dangles */
        listbox.innerHTML = "";
        emptyEl.innerHTML = `<div class="sb-empty" style="padding:28px 16px">No matches for “${esc(q)}” — try a command name, feature or page.</div>`;
        input.setAttribute("aria-expanded", "false");
        input.removeAttribute("aria-activedescendant");
        announce(`No matches for ${q}`);
        return;
      }
      emptyEl.innerHTML = "";
      input.setAttribute("aria-expanded", "true");
      let html = "", lastGroup = null;
      results.forEach((r, i) => {
        if (r.group !== lastGroup) { html += `<div class="sb-palette-group" role="presentation">${esc(r.group)}</div>`; lastGroup = r.group; }
        html += `<button class="sb-palette-item" role="option" id="sb-pal-${i}" aria-selected="${i === sel}" data-i="${i}">
          <span class="t">${r.code ? `<code>${esc(r.code)}</code> ` : ""}${esc(r.label)}</span>
          <span class="sub">${esc(r.sub || "")}</span>
        </button>`;
      });
      listbox.innerHTML = html;
      listbox.querySelectorAll(".sb-palette-item").forEach((b) => {
        b.addEventListener("click", () => go(Number(b.dataset.i)));
        b.addEventListener("mousemove", () => setSel(Number(b.dataset.i)));
      });
      setSel(0); /* writes aria-selected AND aria-activedescendant every render */
      announce(`${results.length} result${results.length === 1 ? "" : "s"}`);
    }

    function setSel(i) {
      sel = Math.max(0, Math.min(results.length - 1, i));
      listbox.querySelectorAll(".sb-palette-item").forEach((b, j) => b.setAttribute("aria-selected", String(j === sel)));
      const el = listbox.querySelector(`#sb-pal-${sel}`);
      if (el) el.scrollIntoView({ block: "nearest" });
      if (input) input.setAttribute("aria-activedescendant", `sb-pal-${sel}`);
    }

    function announce(text) {
      const live = overlay && overlay.querySelector("[data-pal-live]");
      if (live) live.textContent = text;
    }

    function go(i) {
      const r = results[i];
      if (!r) return;
      close();
      if (r.href.charAt(0) === "#") location.hash = r.href.slice(1);
      else location.href = r.href;
    }

    function open() {
      if (overlay) return;
      lastFocus = document.activeElement;
      overlay = document.createElement("div");
      overlay.className = "sb-palette-overlay";
      overlay.innerHTML = `
        <div class="sb-palette" role="dialog" aria-modal="true" aria-label="Site search">
          <div class="sb-search">${icon("search", "var(--sb-ink-4)", 16)}
            <input type="text" role="combobox" aria-expanded="true" aria-controls="sb-pal-list" aria-autocomplete="list" placeholder="Search commands, features, games, pages…" aria-label="Search the site" />
          </div>
          <div class="sb-palette-results">
            <div id="sb-pal-list" role="listbox" aria-label="Results"></div>
            <div data-pal-empty></div>
          </div>
          <div class="sb-palette-foot"><span><kbd class="sb-kbd">↑↓</kbd> navigate</span><span><kbd class="sb-kbd">↵</kbd> open</span><span><kbd class="sb-kbd">esc</kbd> close</span><span class="sb-visually-hidden" data-pal-live aria-live="polite"></span></div>
        </div>`;
      document.body.appendChild(overlay);
      document.body.style.overflow = "hidden";
      input = overlay.querySelector("input");
      listbox = overlay.querySelector("#sb-pal-list");
      emptyEl = overlay.querySelector("[data-pal-empty]");
      renderList("");
      input.focus();
      input.addEventListener("input", () => renderList(input.value));
      overlay.addEventListener("mousedown", (e) => { if (e.target === overlay) close(); });
      overlay.addEventListener("keydown", (e) => {
        if (e.key === "Escape") { e.preventDefault(); close(); }
        else if (e.key === "ArrowDown") { e.preventDefault(); setSel(sel + 1); }
        else if (e.key === "ArrowUp") { e.preventDefault(); setSel(sel - 1); }
        else if (e.key === "Enter") { e.preventDefault(); go(sel); }
        else if (e.key === "Tab") { e.preventDefault(); } /* focus stays in the dialog */
      });
    }

    function close() {
      if (!overlay) return;
      overlay.remove();
      overlay = input = listbox = emptyEl = null;
      document.body.style.overflow = "";
      if (lastFocus && lastFocus.focus) lastFocus.focus();
    }

    function bindGlobal() {
      document.addEventListener("keydown", (e) => {
        const inField = /^(INPUT|TEXTAREA|SELECT)$/.test((e.target && e.target.tagName) || "");
        if ((e.key === "k" || e.key === "K") && (e.metaKey || e.ctrlKey)) { e.preventDefault(); overlay ? close() : open(); }
        else if (e.key === "/" && !inField && !overlay) { e.preventDefault(); open(); }
      });
      document.querySelectorAll("[data-palette-open]").forEach((b) => b.addEventListener("click", open));
    }

    return { register, open, close, bindGlobal };
  })();

  /* ── chrome wiring (mobile drawer + theme toggles) ───────── */
  function initChrome() {
    theme.set(theme.get()); /* normalizes toggle buttons' state/icon */
    document.querySelectorAll("[data-theme-toggle]").forEach((btn) =>
      btn.addEventListener("click", theme.toggle));
    const menuBtn = document.querySelector("[data-menu-toggle]");
    const drawer = document.querySelector("[data-drawer]");
    if (menuBtn && drawer) {
      const setMenu = (open) => {
        drawer.classList.toggle("open", open);
        menuBtn.setAttribute("aria-expanded", String(open));
        menuBtn.setAttribute("aria-label", open ? "Close menu" : "Open menu");
        menuBtn.innerHTML = icon(open ? "x" : "menu", "currentColor", 17);
      };
      menuBtn.setAttribute("aria-label", "Open menu");
      menuBtn.addEventListener("click", () => setMenu(!drawer.classList.contains("open")));
      drawer.addEventListener("click", (e) => { if (e.target.closest("a")) setMenu(false); });
      document.addEventListener("keydown", (e) => {
        if (e.key === "Escape" && drawer.classList.contains("open")) { setMenu(false); menuBtn.focus(); }
      });
    }
    palette.bindGlobal();
  }

  window.SBDS = { esc, icon, fmt, theme, barChart, sparkline, tickStrip, statTile, palette, initChrome };
})();
