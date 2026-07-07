/* ============================================================================
   SuperBot program design system — living style guide renderer
   Renders every token + component from the real CSS/JS. If a specimen here
   looks wrong, the SYSTEM is wrong — fix tokens/components, never this page's
   private styles. Sections auto-index into the sticky TOC.
   ========================================================================== */
(function () {
  "use strict";
  const S = window.SBDS;
  const root = document.getElementById("specimens");
  const toc = document.querySelector(".sg-toc");

  const spec = (id, title, code, bodyHtml) => `
    <section class="sg-spec" id="${id}" aria-labelledby="${id}-h">
      <div class="sg-spec-head"><h3 id="${id}-h">${title}</h3><code>${code}</code></div>
      <div class="sg-spec-body">${bodyHtml}</div>
    </section>`;

  const swatch = (name, varName) => `
    <div class="sg-swatch"><div class="c" style="background:var(${varName})"></div>
      <div class="m">${name}<br>${varName}</div></div>`;

  const sections = [];

  /* ── tokens: color ── */
  sections.push(["colors", "Color tokens", "tokens.css", `
    <p class="sb-muted" style="margin:0;font-size:13px">Semantic tokens — values swap per theme. Components never use raw hex.</p>
    <div class="sg-swatches">
      ${swatch("Canvas", "--sb-bg")}${swatch("Canvas deep", "--sb-bg-2")}${swatch("Surface", "--sb-surface")}
      ${swatch("Well", "--sb-well")}${swatch("Line", "--sb-line")}${swatch("Line strong", "--sb-line-2")}
      ${swatch("Ink 1", "--sb-ink-1")}${swatch("Ink 2", "--sb-ink-2")}${swatch("Ink 3", "--sb-ink-3")}${swatch("Ink 4", "--sb-ink-4")}
      ${swatch("Brand", "--sb-brand")}${swatch("Brand hi", "--sb-brand-hi")}${swatch("Brand ink", "--sb-brand-ink")}${swatch("Brand tint", "--sb-brand-tint")}
      ${swatch("Sky", "--sb-sky")}${swatch("Amber", "--sb-amber")}${swatch("Pink", "--sb-pink")}${swatch("Indigo", "--sb-indigo")}${swatch("Rose", "--sb-rose")}
      ${swatch("OK", "--sb-ok")}${swatch("Warn", "--sb-warn")}${swatch("Info", "--sb-info")}${swatch("Danger", "--sb-danger")}
      ${swatch("Chart mark", "--sb-chart-mark")}${swatch("Chart track", "--sb-chart-track")}${swatch("Focus", "--sb-focus")}
    </div>`]);

  /* ── tokens: type ── */
  sections.push(["type", "Typography", "tokens.css — --sb-font-*, --sb-text-*", `
    <div>
      <div class="sg-type-row"><code>display / hero</code><span style="font-family:var(--sb-font-display);font-size:var(--sb-text-5xl);font-weight:800;letter-spacing:var(--sb-track-tight)">One bot, whole server</span></div>
      <div class="sg-type-row"><code>display / 3xl · 800</code><span style="font-family:var(--sb-font-display);font-size:var(--sb-text-3xl);font-weight:800">Section heading</span></div>
      <div class="sg-type-row"><code>display / xl · 700</code><span style="font-family:var(--sb-font-display);font-size:var(--sb-text-xl);font-weight:700">Card heading</span></div>
      <div class="sg-type-row"><code>body / base</code><span style="font-size:var(--sb-text-base)">Body text — system sans, 1.6 line height, ink-2 on surfaces.</span></div>
      <div class="sg-type-row"><code>mono / eyebrow</code><span class="sb-ey" style="margin:0"><span class="dot">▸</span> Mono eyebrow label</span></div>
      <div class="sg-type-row"><code>mono / code</code><span class="sb-mono" style="color:var(--sb-brand-ink)">!command --flag</span></div>
    </div>`]);

  /* ── tokens: spacing & radii ── */
  const spaceBar = (n) => `<div class="sg-row" style="gap:8px"><code class="sb-mono sb-muted" style="width:70px;font-size:11px">--sb-s-${n}</code><span style="display:block;height:10px;background:var(--sb-brand-tint);border:1px solid var(--sb-brand-line);border-radius:3px;width:var(--sb-s-${n})"></span></div>`;
  sections.push(["space", "Spacing & radii", "tokens.css — --sb-s-*, --sb-r-*", `
    <div class="sb-stack" style="gap:6px">${[1,2,3,4,5,6,7,8,9].map(spaceBar).join("")}</div>
    <div class="sg-row">${["xs","sm","md","lg","xl"].map((r) => `<div style="width:72px;height:48px;border:1.5px solid var(--sb-brand-line);border-radius:var(--sb-r-${r});display:grid;place-items:center" class="sb-mono sb-muted">${r}</div>`).join("")}</div>`]);

  /* ── buttons ── */
  sections.push(["buttons", "Buttons", ".sb-btn (-primary -ghost -soft -danger, -sm -lg)", `
    <div class="sg-row">
      <button class="sb-btn sb-btn-primary">Primary action</button>
      <button class="sb-btn sb-btn-ghost">Ghost</button>
      <button class="sb-btn sb-btn-soft">Soft</button>
      <button class="sb-btn sb-btn-danger">Danger</button>
      <button class="sb-btn sb-btn-primary" disabled>Disabled</button>
    </div>
    <div class="sg-row">
      <button class="sb-btn sb-btn-primary sb-btn-lg">Large ${S.icon("arrow", "currentColor", 16)}</button>
      <button class="sb-btn sb-btn-ghost sb-btn-sm">Small</button>
      <button class="sb-iconbtn" title="Icon button" aria-label="Icon button">${S.icon("search", "currentColor", 17)}</button>
      <button class="sb-iconbtn sb-searchbtn" data-palette-open>${S.icon("search", "currentColor", 15)} search <kbd class="sb-kbd">⌘K</kbd></button>
    </div>`]);

  /* ── badges & pills ── */
  sections.push(["badges", "Badges, pills & chips", ".sb-badge / .sb-pill / .sb-chip / .sb-kbd", `
    <div class="sg-row">
      <span class="sb-badge sb-badge-ok">${S.icon("check", "currentColor", 11)} finished</span>
      <span class="sb-badge sb-badge-warn">${S.icon("clock", "currentColor", 11)} in-progress</span>
      <span class="sb-badge sb-badge-info">${S.icon("activity", "currentColor", 11)} game</span>
      <span class="sb-badge sb-badge-danger">${S.icon("alert", "currentColor", 11)} outage</span>
      <span class="sb-badge sb-badge-flag">${S.icon("flag", "currentColor", 11)} self-initiated</span>
      <span class="sb-badge sb-badge-neutral">neutral</span>
    </div>
    <div class="sb-filterbar" role="group" aria-label="Example filters">
      <button class="sb-pill" aria-pressed="true">all</button>
      <button class="sb-pill" aria-pressed="false">games</button>
      <button class="sb-pill" aria-pressed="false">moderation</button>
      <button class="sb-pill" aria-pressed="false">economy</button>
    </div>
    <div class="sg-row"><span class="sb-chip">!rank @user</span><kbd class="sb-kbd">esc</kbd></div>`]);

  /* ── cards ── */
  sections.push(["cards", "Cards", ".sb-card / .sb-feat / .sb-tile / .sb-panel / .sb-kv", `
    <div class="sb-grid-3">
      <a class="sb-card sb-card-hover sb-feat" href="#cards" style="--c:var(--sb-brand)">
        <span class="corner" aria-hidden="true"></span>
        <div class="sb-feat-top"><span class="sb-tile">${S.icon("gamepad")}</span><span class="sb-feat-cat">games</span></div>
        <h3>Games, ready to play</h3>
        <p>Quick, replayable fun that keeps members coming back.</p>
        <div class="meta">106 commands <span class="go">Open →</span></div>
      </a>
      <a class="sb-card sb-card-hover sb-feat" href="#cards" style="--c:var(--sb-sky)">
        <span class="corner" aria-hidden="true"></span>
        <div class="sb-feat-top"><span class="sb-tile">${S.icon("shield")}</span><span class="sb-feat-cat">moderation</span></div>
        <h3>Keep the peace</h3>
        <p>Automatic and manual moderation with a full audit trail.</p>
        <div class="meta">21 commands <span class="go">Open →</span></div>
      </a>
      <a class="sb-card sb-card-hover sb-feat" href="#cards" style="--c:var(--sb-amber)">
        <span class="corner" aria-hidden="true"></span>
        <div class="sb-feat-top"><span class="sb-tile">${S.icon("coins")}</span><span class="sb-feat-cat">economy</span></div>
        <h3>A living economy</h3>
        <p>Currency, inventory and mining to keep members engaged.</p>
        <div class="meta">50 commands <span class="go">Open →</span></div>
      </a>
    </div>
    <div class="sb-panel" style="margin-bottom:0"><h3>Key–value grid</h3>
      <div class="sb-kv-grid">
        <dl class="sb-kv"><dt>Aliases</dt><dd><span class="sb-chip">!21</span></dd></dl>
        <dl class="sb-kv"><dt>Permissions</dt><dd>anyone</dd></dl>
        <dl class="sb-kv"><dt>Cooldown</dt><dd>5s</dd></dl>
      </div>
    </div>`]);

  /* ── stat tiles & charts ── */
  sections.push(["charts", "Stat tiles & charts", "SBDS.statTile / barChart / sparkline / tickStrip / .sb-meter", `
    <div class="sb-statrow">
      ${S.statTile({ label: "Registered commands", value: "485", href: "#charts" })}
      ${S.statTile({ label: "Sessions this week", value: "23", delta: { text: "+4 vs last week", dir: "up" }, spark: [3, 5, 2, 6, 4, 8, 7, 9, 6, 10, 8, 11] })}
      ${S.statTile({ label: "Open bugs", value: "7", delta: { text: "−2 vs last week", dir: "up" } })}
    </div>
    <div class="sb-panel" style="margin-bottom:0"><h3>Commands per area — single-hue magnitude, direct end labels</h3>
      ${S.barChart([
        { label: "games", value: 106 }, { label: "other", value: 68 }, { label: "economy", value: 50 },
        { label: "admin", value: 44 }, { label: "management", value: 29 },
      ], { ariaLabel: "Commands per area" })}
      <p class="sb-chart-note">Marks carry the single chart hue; every value is directly labeled in ink tokens (dataviz rule: text never wears the series color).</p>
    </div>
    <div class="sb-panel" style="margin-bottom:0"><h3>Status ticks & meter</h3>
      ${S.tickStrip(Array.from({ length: 60 }, (_, i) => (i === 41 ? "warn" : i === 42 ? "danger" : "ok")), { ariaLabel: "Example 60-day status history" })}
      <div style="margin-top:16px" class="sb-stack">
        <div class="sb-meter" role="img" aria-label="Capacity 62%"><span class="fill" style="width:62%"></span></div>
        <div class="sb-meter warn" role="img" aria-label="Capacity 84%"><span class="fill" style="width:84%"></span></div>
      </div>
    </div>`]);

  /* ── forms ── */
  sections.push(["forms", "Forms & search", ".sb-field / .sb-inp / .sb-search", `
    <div class="sb-search" style="max-width:480px">${S.icon("search", "var(--sb-ink-4)", 16)}<input placeholder="Search commands, aliases, descriptions…" aria-label="Search" /></div>
    <div class="sb-grid-2">
      <div class="sb-field" style="margin:0"><label class="sb-label" for="sg-in1">Your name</label>
        <input id="sg-in1" class="sb-inp" placeholder="Optional" /></div>
      <div class="sb-field" style="margin:0"><label class="sb-label" for="sg-in2">Type</label>
        <select id="sg-in2" class="sb-inp"><option>Bug report</option><option>Idea</option></select></div>
    </div>
    <div class="sb-field" style="margin:0"><label class="sb-label" for="sg-in3">Details</label>
      <textarea id="sg-in3" class="sb-inp" rows="3" placeholder="Be specific — it helps the maintainers."></textarea>
      <span class="sb-hint">Markdown not required.</span></div>
    <div class="sb-field" style="margin:0"><label class="sb-label" for="sg-in4">Invalid state</label>
      <input id="sg-in4" class="sb-inp" aria-invalid="true" value="!!" aria-describedby="sg-in4-err" />
      <span class="sb-field-error" id="sg-in4-err">${S.icon("alert", "currentColor", 13)} Add a few more words first.</span></div>`]);

  /* ── tables ── */
  sections.push(["tables", "Tables", ".sb-table (-scroll wrapper)", `
    <div class="sb-table-scroll"><table class="sb-table">
      <thead><tr><th scope="col">Command</th><th scope="col">Area</th><th scope="col">Permissions</th><th scope="col" style="text-align:right">Aliases</th></tr></thead>
      <tbody>
        <tr><td class="sb-mono" style="color:var(--sb-brand-ink)">!blackjack</td><td>games</td><td>anyone</td><td class="num">1</td></tr>
        <tr><td class="sb-mono" style="color:var(--sb-brand-ink)">!warn</td><td>moderation</td><td>Staff</td><td class="num">0</td></tr>
        <tr><td class="sb-mono" style="color:var(--sb-brand-ink)">!rank</td><td>progression</td><td>anyone</td><td class="num">2</td></tr>
      </tbody>
    </table></div>`]);

  /* ── command rows ── */
  sections.push(["rows", "Command rows & code", ".sb-cmdrow / .sb-example", `
    <div class="sb-cmdlist">
      <a class="sb-cmdrow" href="#rows"><code>!blackjack</code><span class="desc">Play a hand of blackjack against the dealer.</span><span class="end"><span class="sb-badge sb-badge-info">game</span><span class="chev">${S.icon("chevron", "currentColor", 16)}</span></span></a>
      <a class="sb-cmdrow" href="#rows"><code>!warn</code><span class="desc">Warn a member; auto-escalates at the configured threshold.</span><span class="end"><span class="sb-badge sb-badge-ok">finished</span><span class="chev">${S.icon("chevron", "currentColor", 16)}</span></span></a>
    </div>
    <div class="sb-example">!blackjack 250 &nbsp;<span class="sb-muted"># bet 250 coins</span></div>`]);

  /* ── timeline ── */
  sections.push(["timeline", "Timeline (changelog)", ".sb-timeline / .sb-rel / .sb-ch-*", `
    <div class="sb-timeline">
      <div class="sb-rel">
        <div class="sb-rel-aside"><span class="ver">v2026.07.07</span><span class="when">Jul 7, 2026</span><a class="build" href="#timeline">5c16701</a></div>
        <div class="sb-rel-body"><span class="sb-rel-node" aria-hidden="true"></span><h3>Example release</h3>
          <ul class="sb-changes">
            <li class="sb-ch sb-ch-added"><span class="sb-ch-tag">added</span><span>New fishing coral structures with reef bonuses.</span></li>
            <li class="sb-ch sb-ch-improved"><span class="sb-ch-tag">improved</span><span>Reaction roles get a slimmer builder flow.</span></li>
            <li class="sb-ch sb-ch-fixed"><span class="sb-ch-tag">fixed</span><span>Tournament payouts settle exactly once.</span></li>
            <li class="sb-ch sb-ch-removed"><span class="sb-ch-tag">removed</span><span>The legacy !hub alias.</span></li>
          </ul>
        </div>
      </div>
    </div>`]);

  /* ── status ── */
  sections.push(["status", "Status", ".sb-status-banner / .sb-sys / .sb-dot", `
    <div class="sb-status-banner" style="--c:var(--sb-ok);margin-bottom:0">
      <span class="sb-pulse" aria-hidden="true"></span>
      <div><strong>All systems operational</strong><span class="sub">as of the last deploy · build 5c16701</span></div>
      <span style="margin-left:auto">${S.icon("activity", "var(--sb-ok)", 26)}</span>
    </div>
    <div class="sb-panel" style="padding:8px 8px 4px;margin-bottom:0">
      <div class="sb-sys"><div class="sb-sys-head">
        <div class="sb-sys-id"><span class="sb-dot" style="--c:var(--sb-ok)" aria-hidden="true"></span><div><div class="sb-sys-name">Core gateway</div><div class="sb-sys-desc">Command routing &amp; Discord connection</div></div></div>
        <span class="sb-sys-state" style="color:var(--sb-ok)">${S.icon("check", "currentColor", 13)} Operational</span>
      </div></div>
      <div class="sb-sys"><div class="sb-sys-head">
        <div class="sb-sys-id"><span class="sb-dot" style="--c:var(--sb-warn)" aria-hidden="true"></span><div><div class="sb-sys-name">AI platform</div><div class="sb-sys-desc">Provider-backed answers</div></div></div>
        <span class="sb-sys-state" style="color:var(--sb-warn)">${S.icon("clock", "currentColor", 13)} Degraded</span>
      </div></div>
    </div>`]);

  /* ── empty / error / pending ── */
  sections.push(["empty", "Empty, error & pending lanes", ".sb-empty / .sb-error / .sb-lane-pending / .sb-skel", `
    <div class="sb-panel" style="margin-bottom:0"><div class="sb-empty">
      <span class="ico">${S.icon("search", "currentColor", 20)}</span>
      <h4>No commands match</h4>
      Try a different search or clear a filter.
      <div class="act"><button class="sb-btn sb-btn-ghost sb-btn-sm">Clear filters</button></div>
    </div></div>
    <div class="sb-error">${S.icon("alert")}<span><strong>Couldn't load live data.</strong> Showing the committed fallback — refresh to retry.</span></div>
    <div class="sb-lane-pending">
      <div class="head">${S.icon("inbox")}<h4>Model &amp; spend telemetry</h4></div>
      <p>No data yet — this lane renders once per-session telemetry lands (Q-0248). Declared feed:</p>
      <code class="feed">telemetry/model-usage.json → [{ session, date, model, effort, task_class, tokens_out, outcome }]</code>
    </div>
    <div class="sb-stack" aria-hidden="true" style="max-width:340px">
      <span class="sb-skel" style="width:70%"></span><span class="sb-skel" style="width:100%"></span><span class="sb-skel" style="width:45%"></span>
    </div>`]);

  /* ── palette ── */
  sections.push(["palette", "Command palette", "SBDS.palette — ⌘K / Ctrl-K / “/”", `
    <p class="sb-muted" style="margin:0;font-size:13px">Global fuzzy search over commands, features, games and pages. Fully keyboard-driven (↑↓ ↵ esc), focus-trapped, ARIA combobox.</p>
    <div class="sg-row"><button class="sb-btn sb-btn-ghost" data-palette-open>${S.icon("search", "currentColor", 15)} Open the palette <kbd class="sb-kbd">⌘K</kbd></button></div>`]);

  root.innerHTML = sections.map(([id, t, c, b]) => spec(id, t, c, b)).join("");
  toc.innerHTML = sections.map(([id, t]) => `<a href="#${id}">${t}</a>`).join("");

  /* demo data for the palette */
  S.palette.register([
    { group: "Pages", label: "Colors", href: "#colors", sub: "section" },
    { group: "Pages", label: "Buttons", href: "#buttons", sub: "section" },
    { group: "Pages", label: "Charts", href: "#charts", sub: "section" },
    { group: "Commands", label: "blackjack — play a hand", code: "!blackjack", href: "#rows", sub: "demo" },
    { group: "Commands", label: "warn — warn a member", code: "!warn", href: "#rows", sub: "demo" },
  ]);
  S.initChrome();
})();
