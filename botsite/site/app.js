/* ============================================================================
   SuperBot prototype — app: hash router, views, suggestion system
   Vanilla JS, no build step. Renders into #app; nav is static in index.html.
   ========================================================================== */
(function () {
  const D = window.SBDATA;
  const app = document.getElementById("app");

  /* ── helpers ─────────────────────────────────────────── */
  const esc = (s) => String(s == null ? "" : s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  function icon(name, color, size) {
    const s = size || 22;
    return `<svg width="${s}" height="${s}" viewBox="0 0 24 24" fill="none" stroke="${color || "currentColor"}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">${D.ICONS[name] || ""}</svg>`;
  }
  const statusBadge = (st) =>
    st === "in-progress" ? `<span class="badge b-wip">in-progress</span>`
    : st === "game" ? `<span class="badge b-game">game</span>`
    : `<span class="badge b-fin">finished</span>`;

  /* ── suggestion store (localStorage) ─────────────────── */
  const SKEY = "superbot:suggestions:v1";
  function allSug() { try { return JSON.parse(localStorage.getItem(SKEY)) || {}; } catch (e) { return {}; } }
  function sugFor(key) { return allSug()[key] || []; }
  function saveSug(key, list) { const all = allSug(); all[key] = list; localStorage.setItem(SKEY, JSON.stringify(all)); }
  function addSug(key, entry) { const list = sugFor(key); list.unshift(entry); saveSug(key, list); }
  function delSug(key, id) { saveSug(key, sugFor(key).filter((s) => s.id !== id)); }

  const TYPE_META = {
    alias:   { label: "Alias",   color: "var(--g)" },
    idea:    { label: "Idea",    color: "var(--indigo)" },
    bug:     { label: "Bug",     color: "#fb7185" },
    general: { label: "Comment", color: "var(--t-3)" },
  };
  function relTime(ts) {
    const d = Math.floor((Date.now() - ts) / 1000);
    if (d < 60) return "just now";
    if (d < 3600) return Math.floor(d / 60) + "m ago";
    if (d < 86400) return Math.floor(d / 3600) + "h ago";
    return Math.floor(d / 86400) + "d ago";
  }

  /* ── suggestion box (HTML + wiring) ──────────────────── */
  function suggestBox(key, label, types, accent) {
    const list = sugFor(key);
    const typeBtns = types.map((t, i) =>
      `<button class="type-opt${i === 0 ? " active" : ""}" data-type="${t}" style="--c:${TYPE_META[t].color}"><span class="dot"></span>${TYPE_META[t].label}</button>`
    ).join("");
    const placeholder = types[0] === "alias"
      ? `Suggest an alias for ${esc(label)} — e.g. "add !21 as an alias", or share an idea…`
      : `Share an idea or comment about ${esc(label)}…`;
    return `
      <div class="suggest" data-suggest="${esc(key)}" style="--c:${accent}">
        <div class="head">
          ${icon("comment", "var(--g-bright)", 20)}
          <h3>Suggestions &amp; feedback</h3>
          <span class="count" data-count>${list.length} so far</span>
        </div>
        <p class="sub">Got an idea for ${esc(label)}? Suggest an alias, float a feature, or flag a bug. Saved on this device.</p>
        <div class="type-row" data-types>${typeBtns}</div>
        <div class="field">
          <input class="inp author" data-author placeholder="Your name (optional)" maxlength="40" />
          <textarea class="inp" data-text rows="3" placeholder="${esc(placeholder)}" maxlength="500"></textarea>
        </div>
        <div class="actions">
          <button class="btn btn-primary btn-sm" data-submit>${icon("plus", "currentColor", 15)} Post suggestion</button>
          <span class="hint" data-hint>Be specific — it helps the maintainers.</span>
        </div>
        <div class="sug-list" data-list>${list.map((s) => sugItem(s)).join("")}</div>
      </div>`;
  }
  function sugItem(s) {
    const m = TYPE_META[s.type] || TYPE_META.general;
    return `
      <div class="sug" data-id="${s.id}">
        <div class="top">
          <span class="ttag" style="background:color-mix(in oklab, ${m.color} 16%, transparent); color:${m.color}">${m.label}</span>
          <span class="who">${esc(s.author || "Anonymous")}</span>
          <span class="when">${relTime(s.ts)}</span>
          <button class="del" data-del="${s.id}" title="Remove">✕</button>
        </div>
        <div class="text">${esc(s.text)}</div>
      </div>`;
  }
  function wireSuggest(root) {
    const box = root.querySelector("[data-suggest]");
    if (!box) return;
    const key = box.getAttribute("data-suggest");
    let type = (box.querySelector(".type-opt.active") || {}).dataset ? box.querySelector(".type-opt.active").dataset.type : "general";
    box.querySelectorAll(".type-opt").forEach((b) =>
      b.addEventListener("click", () => {
        box.querySelectorAll(".type-opt").forEach((x) => x.classList.remove("active"));
        b.classList.add("active");
        type = b.dataset.type;
      })
    );
    const textEl = box.querySelector("[data-text]");
    const authorEl = box.querySelector("[data-author]");
    const hintEl = box.querySelector("[data-hint]");
    function refreshList() {
      const list = sugFor(key);
      box.querySelector("[data-list]").innerHTML = list.map((s) => sugItem(s)).join("");
      box.querySelector("[data-count]").textContent = list.length + " so far";
      wireDeletes();
    }
    function wireDeletes() {
      box.querySelectorAll("[data-del]").forEach((d) =>
        d.addEventListener("click", () => { delSug(key, d.getAttribute("data-del")); refreshList(); })
      );
    }
    box.querySelector("[data-submit]").addEventListener("click", () => {
      const text = textEl.value.trim();
      if (!text) { textEl.focus(); textEl.style.borderColor = "#fb7185"; hintEl.textContent = "Add a few words first."; hintEl.style.color = "#fb7185"; return; }
      addSug(key, { id: "s" + Date.now().toString(36) + Math.random().toString(36).slice(2, 6), type, author: authorEl.value.trim(), text, ts: Date.now() });
      textEl.value = ""; textEl.style.borderColor = "";
      hintEl.innerHTML = "✓ Thanks — your suggestion was saved."; hintEl.style.color = "var(--g-bright)";
      refreshList();
      setTimeout(() => { hintEl.textContent = "Be specific — it helps the maintainers."; hintEl.style.color = ""; }, 2600);
    });
    wireDeletes();
  }

  /* ── shared bits ─────────────────────────────────────── */
  function pageHero(eyebrow, titleHtml, lead, opts) {
    opts = opts || {};
    return `<div class="page-hero" style="--c:${opts.color || "var(--g)"}">
      <div class="glow-top"></div>
      <div class="head-row">
        <div><span class="ey">${esc(eyebrow)}</span><h1>${titleHtml}</h1>${lead ? `<p class="lead">${esc(lead)}</p>` : ""}</div>
        ${opts.more ? `<a class="more" href="${opts.more.href}">${esc(opts.more.label)}</a>` : ""}
      </div>
    </div>`;
  }

  const crumb = (parts) =>
    `<div class="crumb">${icon("back", "currentColor", 15)} ${parts.map((p, i) =>
      (i ? `<span class="sep">/</span>` : "") + (p.href ? `<a href="${p.href}">${esc(p.label)}</a>` : `<span>${esc(p.label)}</span>`)
    ).join(" ")}</div>`;

  const footer = `
    <footer class="site"><div class="wrap foot-in">
      <span>© 2026 SuperBot · A hobby project, built with care.</span>
      <span class="right">build <a href="https://github.com/menno420/superbot">1f26d13</a> · menno420/superbot</span>
    </div></footer>`;

  /* ── views ───────────────────────────────────────────── */
  function viewHome() {
    const featCards = D.AREAS.map((a) => `
      <a class="feat-card" href="#/feature/${a.id}" style="--c:${a.color}">
        <span class="corner"></span>
        <div class="feat-top"><span class="ico-tile">${icon(a.icon)}</span><span class="feat-cat">${esc(a.name)}</span></div>
        <h3>${esc(a.title || a.name)}</h3>
        <div class="meta">${D.commandsInArea(a.id).length} commands <span class="go">Open →</span></div>
      </a>`).join("");
    const cmdPreview = ["blackjack", "warn", "summarise", "rank"].map((n) => cmdRow(D.byCommand(n))).join("");
    return `
      <div class="view">
        <header class="hero">
          <div class="tex-dots"></div><div class="glow glow-main"></div>
          <div class="wrap">
            <span class="kicker"><span class="d"></span> AI-assisted · self-improving · open hobby project</span>
            <h1>One bot for your whole <span class="grad">Discord server</span>.</h1>
            <p class="sub">Games, moderation, AI tools and more — ${D.COMMANDS.length} commands across ${D.AREAS.length} feature areas. Click into any feature, game or command to see exactly what it does.</p>
            <div class="cta-row">
              <a href="#/features" class="btn btn-primary btn-lg">Explore features →</a>
              <a href="#/commands" class="btn btn-ghost btn-lg">Browse commands</a>
            </div>
            <div class="stats">
              <a class="stat" href="#/commands"><div class="v">${D.COMMANDS.length}</div><div class="l">Commands</div></a>
              <a class="stat" href="#/features"><div class="v">${D.AREAS.length}</div><div class="l">Feature areas</div></a>
              <a class="stat" href="#/games"><div class="v">${D.GAMES.length}</div><div class="l">Built-in games</div></a>
            </div>
          </div>
        </header>
        <section class="section"><div class="wrap">
          <div class="sec-head"><div><span class="ey"><span class="dot">▸</span> Capabilities</span><h2>Everything it can do</h2><p>Grouped by area. Open any one to see its commands.</p></div><a class="more" href="#/features">All features →</a></div>
          <div class="grid-3">${featCards}</div>
        </div></section>
        <section class="section"><div class="wrap">
          <div class="sec-head"><div><span class="ey"><span class="dot">▸</span> Reference</span><h2>A command for everything</h2></div><a class="more" href="#/commands">Browse all →</a></div>
          <div class="cmd-panel"><div class="cmd-list">${cmdPreview}</div></div>
        </div></section>
        ${footer}
      </div>`;
  }

  function viewFeatures() {
    const cards = D.AREAS.map((a) => `
      <a class="feat-card" href="#/feature/${a.id}" style="--c:${a.color}">
        <span class="corner"></span>
        <div class="feat-top"><span class="ico-tile">${icon(a.icon)}</span><span class="feat-cat">${esc(a.name)}</span></div>
        <h3>${esc(a.title || a.name)}</h3>
        <p>${esc(a.tagline)}</p>
        <div class="meta">${D.commandsInArea(a.id).length} commands <span class="go">Open →</span></div>
      </a>`).join("");
    return `<div class="view"><section class="section top"><div class="tex-dots"></div><div class="wrap">
      ${crumb([{ label: "Home", href: "#/" }, { label: "Features" }])}
      ${pageHero(`${D.AREAS.length} subsystems`, `Features &amp; <span class="grad">subsystems</span>`, "Six connected subsystems — games, moderation, AI, utility, leveling and music. Open any one to see exactly what it does.", { color: "var(--g)" })}
      <div class="grid-3">${cards}</div>
    </div></section>${footer}</div>`;
  }

  function viewFeature(id) {
    const a = D.byArea(id);
    if (!a) return notFound("That feature doesn't exist.");
    const cmds = D.commandsInArea(id);
    return `<div class="view"><section class="section"><div class="wrap-narrow">
      ${crumb([{ label: "Home", href: "#/" }, { label: "Features", href: "#/features" }, { label: a.name }])}
      <div class="detail-head" style="--c:${a.color}">
        <div class="glow"></div><div class="glow-2"></div>
        <div class="row"><div class="ico-tile lg">${icon(a.icon, "var(--ink)", 30)}</div><h1 style="text-transform:capitalize">${esc(a.name)}</h1></div>
        <p class="tagline">${esc(a.description)}</p>
      </div>
      <div class="panel"><h3>What you get</h3><ul class="bullets">${a.points.map((p) => `<li>${esc(p)}</li>`).join("")}</ul></div>
      <div class="panel"><h3>${cmds.length} commands in ${esc(a.name)}</h3><div class="related">${cmds.map((c) => cmdRow(c)).join("")}</div></div>
      ${suggestBox("area:" + a.id, a.name, ["idea", "bug", "general"], a.color)}
    </div></section>${footer}</div>`;
  }

  function cmdRow(c) {
    if (!c) return "";
    return `<a class="cmd-row" href="#/command/${c.name}">
      <code>!${esc(c.name)}</code>
      <span class="desc">${esc(c.summary)}</span>
      ${statusBadge(c.status)}
      <span class="chev">${icon("chevron", "currentColor", 16)}</span>
    </a>`;
  }

  // commands list view state
  const cstate = { q: "", filter: "" };
  function viewCommands() {
    return `<div class="view"><section class="section top"><div class="tex-dots"></div><div class="wrap">
      ${crumb([{ label: "Home", href: "#/" }, { label: "Commands" }])}
      ${pageHero(`${D.COMMANDS.length} and counting`, `A <span class="grad">command</span> for everything`, "Every command SuperBot ships, with usage, aliases, permissions and examples. Search or filter to find one fast.", { color: "var(--g)" })}
      <div class="cmd-panel">
        <div class="cmd-search">${icon("search", "var(--t-4)", 16)}<input data-q placeholder="Search commands, aliases, descriptions…" value="${esc(cstate.q)}"/></div>
        <div class="filters" data-filters>
          <button class="pill${cstate.filter === "" ? " active" : ""}" data-f="">all</button>
          ${D.AREAS.map((a) => `<button class="pill${cstate.filter === a.id ? " active" : ""}" data-f="${a.id}">${esc(a.name)}</button>`).join("")}
        </div>
        <div class="cmd-list" data-results>${commandResults()}</div>
      </div>
    </div></section>${footer}</div>`;
  }
  function commandResults() {
    const q = cstate.q.toLowerCase();
    const rows = D.COMMANDS.filter((c) => {
      if (cstate.filter && c.area !== cstate.filter) return false;
      if (!q) return true;
      return (c.name + " " + c.aliases.join(" ") + " " + c.summary + " " + c.area).toLowerCase().includes(q);
    });
    if (!rows.length) return `<div class="empty">No commands match — try a different search or filter.</div>`;
    return rows.map((c) => cmdRow(c)).join("");
  }
  function wireCommands(root) {
    const qel = root.querySelector("[data-q]");
    const res = root.querySelector("[data-results]");
    if (qel) qel.addEventListener("input", () => { cstate.q = qel.value; res.innerHTML = commandResults(); });
    root.querySelectorAll("[data-f]").forEach((b) =>
      b.addEventListener("click", () => {
        cstate.filter = b.getAttribute("data-f");
        root.querySelectorAll("[data-f]").forEach((x) => x.classList.toggle("active", x === b));
        res.innerHTML = commandResults();
      })
    );
  }

  function viewCommand(name) {
    const c = D.byCommand(name);
    if (!c) return notFound("That command doesn't exist.");
    const a = D.byArea(c.area);
    const aliasHtml = c.aliases.length ? c.aliases.map((al) => `<span class="code-chip">!${esc(al)}</span>`).join(" ") : `<span style="color:var(--t-4)">none yet</span>`;
    const planHtml = c.planned.length
      ? `<div class="panel"><h3>What's planned</h3><div class="flow-list">${c.planned.map((p) => `<div class="plan-item"><span class="tag">${esc(p.status)}</span><span>${esc(p.title)}</span></div>`).join("")}</div></div>`
      : "";
    return `<div class="view"><section class="section"><div class="wrap-narrow">
      ${crumb([{ label: "Home", href: "#/" }, { label: "Commands", href: "#/commands" }, { label: "!" + c.name }])}
      <div class="detail-head" style="--c:${a ? a.color : "var(--g)"}">
        <div class="glow"></div><div class="glow-2"></div>
        <div class="row"><span class="cmd-name">!${esc(c.name)}</span>${statusBadge(c.status)}</div>
        <p class="tagline">${esc(c.description)}</p>
        <div class="tags">
          <a class="badge b-game" href="#/feature/${c.area}" style="background:rgba(255,255,255,0.05);color:var(--t-2)">${icon(a ? a.icon : "spark", "var(--t-2)", 12)} ${esc(a ? a.name : c.area)}</a>
        </div>
      </div>
      <div class="panel"><h3>Usage</h3><div class="example">${esc(c.usage)}</div></div>
      <div class="panel"><h3>Details</h3><div class="kv-grid">
        <div class="kv"><dt>Aliases</dt><dd>${aliasHtml}</dd></div>
        <div class="kv"><dt>Permissions</dt><dd>${esc(c.permissions)}</dd></div>
        <div class="kv"><dt>Cooldown</dt><dd>${esc(c.cooldown || "—")}</dd></div>
      </div></div>
      <div class="panel"><h3>Examples</h3><div class="flow-list">${c.examples.map((ex) => `<div class="example">${esc(ex)}</div>`).join("")}</div></div>
      ${planHtml}
      ${suggestBox("command:" + c.name, "!" + c.name, ["alias", "idea", "bug", "general"], a ? a.color : "var(--g)")}
    </div></section>${footer}</div>`;
  }

  function viewGames() {
    const cards = D.GAMES.map((g) => `
      <a class="feat-card" href="#/game/${g.id}" style="--c:${g.color}">
        <span class="corner"></span>
        <div class="feat-top"><span class="ico-tile">${icon(g.icon)}</span><span class="feat-cat">${g.beta ? "Game · beta" : "Game"}</span></div>
        <h3>${esc(g.name)}</h3>
        <p>${esc(g.tagline)}</p>
        <div class="meta"><code style="font-family:var(--font-mono);color:var(--g-soft)">!${esc(g.command)}</code><span class="go">Play →</span></div>
      </a>`).join("");
    return `<div class="view"><section class="section top"><div class="tex-dots"></div><div class="wrap">
      ${crumb([{ label: "Home", href: "#/" }, { label: "Games" }])}
      ${pageHero(`${D.GAMES.length} to play`, `<span class="grad">Games</span>`, "Casual games your members can play right in chat — solo or head-to-head, each one earning XP.", { color: "var(--g-bright)", more: { href: "#/feature/games", label: "Games subsystem →" } })}
      <div class="grid-3">${cards}</div>
    </div></section>${footer}</div>`;
  }

  function viewGame(id) {
    const g = D.byGame(id);
    if (!g) return notFound("That game doesn't exist.");
    const c = D.byCommand(g.command);
    return `<div class="view"><section class="section"><div class="wrap-narrow">
      ${crumb([{ label: "Home", href: "#/" }, { label: "Games", href: "#/games" }, { label: g.name }])}
      <div class="detail-head" style="--c:${g.color}">
        <div class="glow"></div><div class="glow-2"></div>
        <div class="row"><div class="ico-tile lg">${icon(g.icon, "var(--ink)", 30)}</div><h1>${esc(g.name)}</h1>${g.beta ? statusBadge("in-progress") : statusBadge("game")}</div>
        <p class="tagline">${esc(g.description)}</p>
      </div>
      <div class="panel"><h3>How to play</h3><ol class="bullets">${g.howTo.map((s) => `<li>${esc(s)}</li>`).join("")}</ol></div>
      <div class="panel"><h3>Command</h3><div class="related">${cmdRow(c)}</div></div>
      ${suggestBox("game:" + g.id, g.name, ["idea", "bug", "general"], g.color)}
    </div></section>${footer}</div>`;
  }

  /* ── status helpers ──────────────────────────────────── */
  const ST_META = {
    operational: { label: "Operational", color: "var(--g-bright)", cls: "operational" },
    degraded:    { label: "Degraded performance", color: "var(--amber)", cls: "degraded" },
    maintenance: { label: "Maintenance", color: "var(--sky)", cls: "maintenance" },
    outage:      { label: "Outage", color: "var(--rose)", cls: "outage" },
    monitoring:  { label: "Monitoring", color: "var(--amber)", cls: "degraded" },
    resolved:    { label: "Resolved", color: "var(--g-bright)", cls: "operational" },
  };

  function viewChangelog() {
    const entries = D.CHANGELOG.map((rel, i) => `
      <div class="rel">
        <div class="rel-aside">
          <span class="ver">v${esc(rel.version)}</span>
          <span class="rel-date">${esc(rel.date)}</span>
          <a class="rel-build" href="https://github.com/menno420/superbot">${esc(rel.build)}</a>
        </div>
        <div class="rel-body">
          <div class="rel-node"></div>
          <h3>${esc(rel.title)}</h3>
          <ul class="changes">
            ${rel.changes.map((c) => `<li class="ch ch-${c.type}"><span class="ch-tag">${c.type}</span><span class="ch-text">${esc(c.text)}</span></li>`).join("")}
          </ul>
        </div>
      </div>`).join("");
    const total = D.CHANGELOG.reduce((n, r) => n + r.changes.length, 0);
    return `<div class="view"><section class="section top"><div class="tex-dots"></div><div class="wrap-narrow">
      ${crumb([{ label: "Home", href: "#/" }, { label: "Changelog" }])}
      ${pageHero(`${D.CHANGELOG.length} releases · ${total} changes`, `What's <span class="grad">new</span>`, "Every release, smallest to largest. SuperBot ships in the open — follow along as features land, get polished and occasionally retire.", { color: "var(--g)" })}
      <div class="changelog">${entries}</div>
    </div></section>${footer}</div>`;
  }

  function uptimeStrip(history) {
    return `<div class="uptime"><div class="ticks">${history.map((s) =>
      `<span class="tick t-${ST_META[s] ? ST_META[s].cls : "operational"}"></span>`).join("")}</div>
      <div class="up-legend"><span>60 days ago</span><span>today</span></div></div>`;
  }

  function viewStatus() {
    const s = D.STATUS;
    const allOk = s.systems.every((x) => x.state === "operational");
    const banner = ST_META[s.overall];
    const sysRows = s.systems.map((sys) => {
      const m = ST_META[sys.state];
      return `<div class="sys">
        <div class="sys-head">
          <div class="sys-id">
            <span class="sys-dot" style="--c:${m.color}"></span>
            <div><div class="sys-name">${esc(sys.name)}</div><div class="sys-desc">${esc(sys.desc)}</div></div>
          </div>
          <div class="sys-meta">
            <span class="sys-num">${esc(sys.latency)}<small>latency</small></span>
            <span class="sys-num">${esc(sys.uptime)}<small>90-day</small></span>
            <span class="sys-state" style="color:${m.color}">${esc(m.label)}</span>
          </div>
        </div>
        ${sys.note ? `<div class="sys-note">${esc(sys.note)}</div>` : ""}
        ${uptimeStrip(sys.history)}
      </div>`;
    }).join("");
    const incidents = s.incidents.map((inc) => {
      const m = ST_META[inc.state];
      const area = inc.area ? D.byArea(inc.area) : null;
      return `<div class="inc">
        <div class="inc-top">
          <span class="inc-state" style="--c:${m.color}">${esc(m.label)}</span>
          <span class="inc-title">${esc(inc.title)}</span>
          ${area ? `<a class="inc-area" href="#/feature/${area.id}">${esc(area.name)}</a>` : ""}
          <span class="inc-date">${esc(inc.date)}</span>
        </div>
        <div class="inc-updates">${inc.updates.map((u) =>
          `<div class="inc-u"><span class="inc-at">${esc(u.at)}</span><span>${esc(u.text)}</span></div>`).join("")}</div>
      </div>`;
    }).join("");
    return `<div class="view"><section class="section top"><div class="tex-dots"></div><div class="wrap-narrow">
      ${crumb([{ label: "Home", href: "#/" }, { label: "Status" }])}
      ${pageHero("Live system status", `System <span class="grad">status</span>`, null, { color: "var(--g)" })}
      <div class="status-banner ${banner.cls}" style="--c:${banner.color}">
        <span class="sb-pulse"></span>
        <div class="sb-text">
          <strong>${allOk ? "All systems operational" : "Some systems are degraded"}</strong>
          <span>${esc(s.uptime90)} uptime over the last 90 days · updated just now</span>
        </div>
        ${icon("activity", "var(--c)", 26)}
      </div>
      <div class="panel" style="padding:8px 8px 4px"><div class="sys-list">${sysRows}</div></div>
      <div class="sec-head" style="margin:34px 0 18px"><div><span class="ey"><span class="dot">▸</span> History</span><h2 style="font-size:24px">Recent incidents</h2></div></div>
      <div class="inc-list">${incidents}</div>
    </div></section>${footer}</div>`;
  }

  function notFound(msg) {
    return `<div class="view"><section class="section"><div class="wrap-narrow" style="text-align:center;padding:60px 0">
      <h2 style="font-size:30px">Nothing here</h2>
      <p style="color:var(--t-3);margin-top:10px">${esc(msg || "That page doesn't exist.")}</p>
      <div class="cta-row" style="justify-content:center;margin-top:24px"><a class="btn btn-primary" href="#/">Back home</a></div>
    </div></section>${footer}</div>`;
  }

  /* ── router ──────────────────────────────────────────── */
  function parse() {
    const h = (location.hash || "#/").replace(/^#/, "");
    const seg = h.split("/").filter(Boolean); // ["feature","games"]
    return { name: seg[0] || "home", param: seg[1] ? decodeURIComponent(seg[1]) : null };
  }
  function setNav(name) {
    document.querySelectorAll(".nav [data-nav]").forEach((a) =>
      a.classList.toggle("active", a.getAttribute("data-nav") === name)
    );
  }
  function render() {
    const r = parse();
    let html, navKey = r.name;
    switch (r.name) {
      case "home": html = viewHome(); break;
      case "features": html = viewFeatures(); break;
      case "feature": html = viewFeature(r.param); navKey = "features"; break;
      case "commands": html = viewCommands(); break;
      case "command": html = viewCommand(r.param); navKey = "commands"; break;
      case "games": html = viewGames(); break;
      case "game": html = viewGame(r.param); navKey = "games"; break;
      case "changelog": html = viewChangelog(); break;
      case "status": html = viewStatus(); break;
      default: html = notFound(); navKey = "";
    }
    app.innerHTML = html;
    setNav(navKey);
    if (r.name === "commands") wireCommands(app);
    if (["feature", "command", "game"].includes(r.name)) wireSuggest(app);
    window.scrollTo(0, 0);
  }

  window.addEventListener("hashchange", render);
  if (!location.hash) location.replace("#/");
  render();
})();
