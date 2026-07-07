/* ============================================================================
   SuperBot public site v2 — hash router + views
   ----------------------------------------------------------------------------
   Vanilla JS, no build step. Renders into #app from window.SBDATA (/data.js)
   using the program design system (/ds/ds.js + CSS). v1 (botsite/site/) stays
   untouched and wired as the fallback front-end.

   v2 over v1 (information architecture):
   - full 43-feature catalogue with per-feature pages (v1 collapsed features
     into 9 area bullets), plus area hubs;
   - global command palette (Ctrl+K / "/") across commands, features, games
     and pages;
   - commands browser: area + permission + status filters, alias-aware search,
     grouped-by-area view, honest result counts;
   - real light theme + theme toggle; real build provenance in the footer;
   - suggestions route to the real /submit intake (v1 kept them in
     localStorage only — they never reached the maintainers);
   - status page drops the fabricated latency/uptime figures and says what the
     data actually is (editorial, per-deploy) — no fake numbers.
   ========================================================================== */
(function () {
  "use strict";
  const D = window.SBDATA;
  const S = window.SBDS;
  const app = document.getElementById("app");
  const esc = S.esc;
  const icon = S.icon;

  /* additive families may be absent if a stale data.js is loaded — degrade */
  const FEATURES = D.FEATURES || [];
  const COUNTS = D.COUNTS || {};
  const BUILD = D.BUILD || {};
  const ADD_URL = D.ADD_URL || "#/";
  const byFeature = (key) => FEATURES.find((f) => f.key === key);
  const featuresInArea = (id) => FEATURES.filter((f) => f.area === id);
  const REPO = "https://github.com/menno420/superbot";

  /* ── shared chrome ───────────────────────────────────────── */
  const statusBadge = (st) =>
    st === "in-progress"
      ? `<span class="sb-badge sb-badge-warn">${icon("clock", "currentColor", 11)} in-progress</span>`
      : st === "game"
        ? `<span class="sb-badge sb-badge-info">${icon("activity", "currentColor", 11)} game</span>`
        : `<span class="sb-badge sb-badge-ok">${icon("check", "currentColor", 11)} finished</span>`;

  const crumb = (parts) =>
    `<nav class="sb-crumb" aria-label="Breadcrumb">${icon("back", "currentColor", 15)} ${parts
      .map((p, i) => (i ? `<span class="sep" aria-hidden="true">/</span>` : "") +
        (p.href ? `<a href="${p.href}">${esc(p.label)}</a>` : `<span aria-current="page">${esc(p.label)}</span>`))
      .join(" ")}</nav>`;

  const pageHero = (eyebrow, titleHtml, lead, opts) => {
    opts = opts || {};
    return `<div class="sb-page-hero" style="--c:${opts.color || "var(--sb-brand)"}">
      <div class="glow-top" aria-hidden="true"></div>
      <div class="head-row">
        <div><span class="sb-ey"><span class="dot">▸</span> ${esc(eyebrow)}</span><h1>${titleHtml}</h1>${lead ? `<p class="sb-lead">${esc(lead)}</p>` : ""}</div>
        ${opts.more ? `<a class="sb-more" href="${opts.more.href}">${esc(opts.more.label)}</a>` : ""}
      </div>
    </div>`;
  };

  const buildDate = BUILD.committed_at ? S.fmt.date(BUILD.committed_at.slice(0, 10)) : "";
  const footer = `
    <footer class="sb-footer"><div class="sb-wrap sb-footer-in">
      <span>© 2026 SuperBot · A hobby project, built with care — and increasingly by its own agents.</span>
      <span class="right">
        <span class="v2-build">build <a href="${REPO}/commit/${esc(BUILD.commit || "")}" rel="noopener">${esc(BUILD.commit || "dev")}</a>${buildDate ? ` · ${esc(buildDate)}` : ""}</span>
        <a href="/submit">feedback</a>
        <a href="/design">design system</a>
        <a href="${REPO}" rel="noopener">github</a>
      </span>
    </div></footer>`;

  const suggestCta = (about, label, accent) => `
    <div class="sb-panel" style="--c:${accent || "var(--sb-brand)"}">
      <h3>Suggestions &amp; feedback</h3>
      <p style="margin:0 0 14px;font-size:13.5px;color:var(--sb-ink-3)">Got an idea for ${esc(label)}, found a bug, or want an alias? Reports go straight to the maintainers' review queue.</p>
      <a class="sb-btn sb-btn-soft sb-btn-sm" href="/submit?about=${encodeURIComponent(about)}">${icon("comment", "currentColor", 15)} Suggest or report — takes a minute</a>
    </div>`;

  const cmdRow = (c) => {
    if (!c) return "";
    const alias = c.aliases && c.aliases.length ? `<span class="v2-alias">a.k.a. ${esc(c.aliases.slice(0, 2).map((a) => "!" + a).join(" "))}</span>` : "";
    return `<a class="sb-cmdrow" href="#/command/${encodeURIComponent(c.name)}">
      <code>!${esc(c.name)}</code>
      <span class="desc">${esc(c.summary)}</span>
      <span class="end">${alias}${c.permissions && c.permissions !== "anyone" ? `<span class="sb-badge sb-badge-neutral">${esc(c.permissions)}</span>` : ""}${statusBadge(c.status)}<span class="chev" aria-hidden="true">${icon("chevron", "currentColor", 16)}</span></span>
    </a>`;
  };

  const featCard = (f) => {
    const a = D.byArea(f.area);
    const color = a ? a.color : "var(--sb-brand)";
    return `<a class="sb-card sb-card-hover sb-feat v2-feature-card" href="#/feature/${encodeURIComponent(f.key)}" style="--c:${color}">
      <span class="corner" aria-hidden="true"></span>
      <div class="sb-feat-top"><span class="sb-tile"><span class="emoji" aria-hidden="true">${esc(f.emoji || "✨")}</span></span><span class="sb-feat-cat">${esc(a ? a.name : f.area)}${f.is_game ? " · game" : ""}</span></div>
      <h3>${esc(f.name)}</h3>
      <p>${esc(clip(f.description, 110))}</p>
      <div class="meta">${f.tags.slice(0, 3).map((t) => `<span class="v2-tag">${esc(t)}</span>`).join("")} <span class="go">Open →</span></div>
    </a>`;
  };

  const areaCard = (a) => `
    <a class="sb-card sb-card-hover sb-feat" href="#/area/${a.id}" style="--c:${a.color}">
      <span class="corner" aria-hidden="true"></span>
      <div class="sb-feat-top"><span class="sb-tile">${icon(a.icon)}</span><span class="sb-feat-cat">${esc(a.name)}</span></div>
      <h3>${esc(a.title || a.name)}</h3>
      <p>${esc(a.tagline)}</p>
      <div class="meta">${D.commandsInArea(a.id).length} commands${featuresInArea(a.id).length ? ` · ${featuresInArea(a.id).length} features` : ""} <span class="go">Open →</span></div>
    </a>`;

  const gameCard = (g) => `
    <a class="sb-card sb-card-hover sb-feat" href="#/game/${encodeURIComponent(g.id)}" style="--c:${g.color}">
      <span class="corner" aria-hidden="true"></span>
      <div class="sb-feat-top"><span class="sb-tile">${icon(g.icon)}</span><span class="sb-feat-cat">${g.beta ? "Game · beta" : "Game"}</span></div>
      <h3>${esc(g.name)}</h3>
      <p>${esc(g.tagline)}</p>
      <div class="meta"><code class="sb-mono" style="color:var(--sb-brand-ink)">!${esc(g.command)}</code><span class="go">Play →</span></div>
    </a>`;

  function clip(s, n) {
    s = String(s || "");
    if (s.length <= n) return s;
    return s.slice(0, n).replace(/\s+\S*$/, "") + "…";
  }

  function notFound(msg) {
    return `<div class="sb-view"><section class="sb-section"><div class="sb-wrap-narrow" style="text-align:center;padding:60px 0">
      <h2 style="font-size:30px">Nothing here</h2>
      <p style="color:var(--sb-ink-3);margin-top:10px">${esc(msg || "That page doesn't exist.")}</p>
      <div class="sb-row" style="justify-content:center;margin-top:24px"><a class="sb-btn sb-btn-primary" href="#/">Back home</a><button class="sb-btn sb-btn-ghost" data-palette-open>Search instead</button></div>
    </div></section>${footer}</div>`;
  }

  /* ── home ────────────────────────────────────────────────── */
  function viewHome() {
    const areaCards = D.AREAS.map(areaCard).join("");
    const bars = S.barChart(
      D.AREAS.map((a) => ({
        label: a.name, value: D.commandsInArea(a.id).length,
        href: "#/area/" + a.id, title: `${a.name}: ${D.commandsInArea(a.id).length} commands — open the area`,
      })).sort((x, y) => y.value - x.value),
      { ariaLabel: "Commands per area" },
    );
    const featured = FEATURES.filter((f) => !f.is_game).slice(0, 6).map(featCard).join("");
    const gameStrip = D.GAMES.slice(0, 8).map(gameCard).join("");
    const latest = D.CHANGELOG[0];
    return `
      <div class="sb-view">
        <header class="v2-hero">
          <div class="sb-dots" aria-hidden="true"></div><div class="sb-glow glow-main" aria-hidden="true"></div>
          <div class="sb-wrap">
            <span class="sb-kicker"><span class="d" aria-hidden="true"></span> AI-assisted · self-improving · open hobby project</span>
            <h1>One bot for your whole <span class="sb-grad">Discord server</span>.</h1>
            <p class="sub">Games, moderation, economy and AI tools — ${S.fmt.num(COUNTS.commands || D.COMMANDS.length)} commands across ${S.fmt.num(COUNTS.features || D.AREAS.length)} features. Every one documented, searchable, and honest about its status.</p>
            <div class="cta-row">
              <a href="#/features" class="sb-btn sb-btn-primary sb-btn-lg">Explore features ${icon("arrow", "currentColor", 16)}</a>
              <a href="#/commands" class="sb-btn sb-btn-ghost sb-btn-lg">Browse commands</a>
            </div>
            <p class="hint">Press <kbd class="sb-kbd">/</kbd> or <kbd class="sb-kbd">⌘K</kbd> to search everything.</p>
            <div class="sb-statrow">
              ${S.statTile({ label: "Registered commands", value: S.fmt.num(COUNTS.commands || D.COMMANDS.length), href: "#/commands" })}
              ${S.statTile({ label: "Features", value: S.fmt.num(COUNTS.features || FEATURES.length), href: "#/features" })}
              ${S.statTile({ label: "Built-in games", value: S.fmt.num(COUNTS.games || D.GAMES.length), href: "#/games" })}
            </div>
          </div>
        </header>
        <section class="sb-section"><div class="sb-wrap">
          <div class="sb-sec-head"><div><span class="sb-ey"><span class="dot">▸</span> Capabilities</span><h2>Everything it can do</h2><p>Nine areas, ${FEATURES.length || "dozens of"} features. Open any one to see its commands.</p></div><a class="sb-more" href="#/features">All features →</a></div>
          <div class="sb-grid-3">${areaCards}</div>
        </div></section>
        <section class="sb-section"><div class="sb-wrap">
          <div class="sb-sec-head"><div><span class="sb-ey"><span class="dot">▸</span> At a glance</span><h2>Where the commands live</h2></div><a class="sb-more" href="#/commands">Browse all →</a></div>
          <div class="sb-panel" style="margin:0">${bars}<p class="sb-chart-note">Unique command names per area — from the same registry the bot runs on, regenerated every deploy.</p></div>
        </div></section>
        <section class="sb-section"><div class="sb-wrap">
          <div class="sb-sec-head"><div><span class="sb-ey"><span class="dot">▸</span> Spotlight</span><h2>Feature highlights</h2></div><a class="sb-more" href="#/features">Full catalogue →</a></div>
          <div class="sb-grid-3">${featured}</div>
        </div></section>
        <section class="sb-section"><div class="sb-wrap">
          <div class="sb-sec-head"><div><span class="sb-ey"><span class="dot">▸</span> Play</span><h2>Games, ready out of the box</h2></div><a class="sb-more" href="#/games">All ${D.GAMES.length} games →</a></div>
          <div class="sb-grid-4">${gameStrip}</div>
        </div></section>
        ${latest ? `<section class="sb-section"><div class="sb-wrap">
          <div class="sb-sec-head"><div><span class="sb-ey"><span class="dot">▸</span> Fresh</span><h2>Latest release</h2></div><a class="sb-more" href="#/changelog">Full changelog →</a></div>
          <div class="sb-panel" style="margin:0"><div class="sb-row"><strong style="font-family:var(--sb-font-display);font-size:17px">${esc(latest.title)}</strong><span class="sb-muted sb-mono" style="font-size:12px">${esc(latest.date)}</span></div>
          <ul class="sb-changes" style="margin-top:12px">${latest.changes.map((c) => `<li class="sb-ch sb-ch-${c.type}"><span class="sb-ch-tag">${c.type}</span><span>${esc(c.text)}</span></li>`).join("")}</ul></div>
        </div></section>` : ""}
        <section class="sb-section"><div class="sb-wrap">
          <div class="sb-sec-head"><div><span class="sb-ey"><span class="dot">▸</span> Setup</span><h2>Running in three steps</h2></div></div>
          <div class="sb-grid-3">
            <div class="sb-card"><div class="sb-mono" style="font-size:26px;color:var(--sb-brand-hi);margin-bottom:14px">01</div><h3>Invite the bot</h3><p>One click adds SuperBot with sensible default permissions. No dashboard wrestling.</p></div>
            <div class="sb-card"><div class="sb-mono" style="font-size:26px;color:var(--sb-brand-hi);margin-bottom:14px">02</div><h3>Pick your modules</h3><p>Toggle the areas you want — games, moderation, AI tools. Everything else stays out of the way.</p></div>
            <div class="sb-card"><div class="sb-mono" style="font-size:26px;color:var(--sb-brand-hi);margin-bottom:14px">03</div><h3>Type <span class="sb-mono" style="color:var(--sb-brand-ink);font-size:17px">!help</span></h3><p>Self-documenting commands explain themselves. Your members learn it in seconds.</p></div>
          </div>
        </div></section>
        <section class="sb-section"><div class="sb-wrap">
          <div class="sb-card" style="text-align:center;padding:64px 28px;overflow:hidden">
            <div class="sb-dots" aria-hidden="true"></div>
            <h2 style="font-size:40px;font-weight:800;letter-spacing:-0.03em;max-width:640px;margin:0 auto;position:relative">Found a bug? Got an idea?</h2>
            <p style="position:relative;font-size:17px;line-height:1.6;color:var(--sb-ink-3);margin:18px auto 0;max-width:520px">This bot grows from real feedback — reports go straight to the maintainers' review queue.</p>
            <div class="sb-row" style="justify-content:center;margin-top:30px">
              <a href="/submit" class="sb-btn sb-btn-primary sb-btn-lg">Suggest &amp; report ${icon("arrow", "currentColor", 16)}</a>
              <a href="${esc(ADD_URL)}" class="sb-btn sb-btn-ghost sb-btn-lg" rel="noopener">Add to Discord</a>
            </div>
          </div>
        </div></section>
        ${footer}
      </div>`;
  }

  /* ── features catalogue ──────────────────────────────────── */
  const fstate = { q: "", area: "" };
  function featureResults() {
    const q = fstate.q.toLowerCase();
    const rows = FEATURES.filter((f) => {
      if (fstate.area && f.area !== fstate.area) return false;
      if (!q) return true;
      return `${f.name} ${f.key} ${f.description} ${f.tags.join(" ")}`.toLowerCase().includes(q);
    });
    if (!rows.length) {
      return `<div class="sb-empty"><span class="ico">${icon("search", "currentColor", 20)}</span><h4>No features match</h4>Try a different search or clear the filter.<div class="act"><button class="sb-btn sb-btn-ghost sb-btn-sm" data-clear-filters>Clear filters</button></div></div>`;
    }
    /* group by area (in AREAS order) when unfiltered; flat grid when filtered */
    if (!fstate.area && !q) {
      return D.AREAS.map((a) => {
        const inArea = rows.filter((f) => f.area === a.id);
        if (!inArea.length) return "";
        return `<div class="v2-group-head"><span class="sb-tile" style="--c:${a.color};width:30px;height:30px;border-radius:8px">${icon(a.icon, undefined, 16)}</span><h3>${esc(a.name)}</h3><span class="n">${inArea.length}</span></div>
          <div class="sb-grid-3">${inArea.map(featCard).join("")}</div>`;
      }).join("");
    }
    return `<div class="sb-grid-3">${rows.map(featCard).join("")}</div>`;
  }
  function viewFeatures() {
    return `<div class="sb-view"><section class="sb-section sb-section-top"><div class="sb-dots" aria-hidden="true"></div><div class="sb-wrap">
      ${crumb([{ label: "Home", href: "#/" }, { label: "Features" }])}
      ${pageHero(`${FEATURES.length} features across ${D.AREAS.length} areas`, `The full <span class="sb-grad">catalogue</span>`, "Everything SuperBot ships, feature by feature — what it does, where it lives, and the commands behind it.")}
      <div class="v2-cmdbar">
        <div class="sb-search">${icon("search", "var(--sb-ink-4)", 16)}<input data-q placeholder="Search features, tags, descriptions…" aria-label="Search features" value="${esc(fstate.q)}" /></div>
      </div>
      <div class="sb-filterbar" role="group" aria-label="Filter by area">
        <button class="sb-pill" data-f="" aria-pressed="${fstate.area === ""}">all areas</button>
        ${D.AREAS.map((a) => `<button class="sb-pill" data-f="${a.id}" aria-pressed="${fstate.area === a.id}">${esc(a.name)}</button>`).join("")}
      </div>
      <div data-results>${featureResults()}</div>
    </div></section>${footer}</div>`;
  }
  function wireFeatures(root) {
    const qel = root.querySelector("[data-q]");
    const res = root.querySelector("[data-results]");
    const rewire = () => { res.innerHTML = featureResults(); wireClear(root, () => { fstate.q = ""; fstate.area = ""; render(); }); };
    if (qel) qel.addEventListener("input", () => { fstate.q = qel.value; rewire(); });
    root.querySelectorAll("[data-f]").forEach((b) =>
      b.addEventListener("click", () => {
        fstate.area = b.getAttribute("data-f");
        root.querySelectorAll("[data-f]").forEach((x) => x.setAttribute("aria-pressed", String(x === b)));
        rewire();
      }));
    wireClear(root, () => { fstate.q = ""; fstate.area = ""; render(); });
  }
  function wireClear(root, fn) {
    root.querySelectorAll("[data-clear-filters]").forEach((b) => b.addEventListener("click", fn));
  }

  /* ── feature detail ──────────────────────────────────────── */
  function viewFeature(key) {
    const f = byFeature(key);
    if (!f) {
      /* back-compat: v1-style #/feature/<areaId> links land on the area hub */
      if (D.byArea(key)) return viewArea(key);
      return notFound("That feature doesn't exist.");
    }
    const a = D.byArea(f.area);
    const color = a ? a.color : "var(--sb-brand)";
    const game = f.is_game ? D.byGame(f.key) : null;
    const areaCmds = a ? D.commandsInArea(a.id) : [];
    return `<div class="sb-view"><section class="sb-section"><div class="sb-wrap-narrow">
      ${crumb([{ label: "Home", href: "#/" }, { label: "Features", href: "#/features" }, { label: f.name }])}
      <div class="sb-card sb-detail-head" style="--c:${color}">
        <div class="sb-glow glow" aria-hidden="true"></div>
        <div class="row"><span class="sb-tile sb-tile-lg"><span class="emoji" style="font-size:26px" aria-hidden="true">${esc(f.emoji || "✨")}</span></span><h1>${esc(f.name)}</h1>${f.is_game ? statusBadge("game") : ""}</div>
        <p class="tagline">${esc(f.description)}</p>
        <div class="tags">${f.tags.map((t) => `<span class="v2-tag">${esc(t)}</span>`).join("")}</div>
      </div>
      ${game ? `<div class="sb-panel"><h3>Play it</h3><div class="sb-cmdlist">${cmdRow(D.byCommand(game.command))}</div><p style="margin:12px 0 0;font-size:13px;color:var(--sb-ink-3)">Full rules on the <a href="#/game/${encodeURIComponent(game.id)}" style="color:var(--sb-brand-ink)">game page →</a></p></div>` : ""}
      ${a ? `<div class="sb-panel"><h3>Where it lives</h3>
        <p style="margin:0 0 14px;font-size:14px;color:var(--sb-ink-2)">${esc(f.name)} is part of the <strong>${esc(a.name)}</strong> area (${areaCmds.length} commands). Feature-level command mapping isn't published yet, so browse the area for everything nearby.</p>
        <a class="sb-btn sb-btn-ghost sb-btn-sm" href="#/area/${a.id}">${icon(a.icon, "currentColor", 15)} Open the ${esc(a.name)} area</a></div>` : ""}
      ${suggestCta("feature:" + f.key, f.name, color)}
    </div></section>${footer}</div>`;
  }

  /* ── area hub ────────────────────────────────────────────── */
  function viewArea(id) {
    const a = D.byArea(id);
    if (!a) return notFound("That area doesn't exist.");
    const cmds = D.commandsInArea(id);
    const feats = featuresInArea(id);
    return `<div class="sb-view"><section class="sb-section"><div class="sb-wrap-narrow">
      ${crumb([{ label: "Home", href: "#/" }, { label: "Features", href: "#/features" }, { label: a.name }])}
      <div class="sb-card sb-detail-head" style="--c:${a.color}">
        <div class="sb-glow glow" aria-hidden="true"></div>
        <div class="row"><span class="sb-tile sb-tile-lg">${icon(a.icon)}</span><h1 style="text-transform:capitalize">${esc(a.name)}</h1></div>
        <p class="tagline">${esc(a.description)}</p>
      </div>
      ${feats.length ? `<div class="sb-panel"><h3>${feats.length} features in ${esc(a.name)}</h3><div class="sb-grid-2">${feats.map(featCard).join("")}</div></div>` : ""}
      <div class="sb-panel"><h3>${cmds.length} commands in ${esc(a.name)}</h3><div class="sb-cmdlist">${cmds.map(cmdRow).join("")}</div></div>
      ${suggestCta("area:" + a.id, a.name, a.color)}
    </div></section>${footer}</div>`;
  }

  /* ── commands browser ────────────────────────────────────── */
  const cstate = { q: "", area: "", perm: "", status: "", group: false };
  function filteredCommands() {
    const q = cstate.q.toLowerCase();
    return D.COMMANDS.filter((c) => {
      if (cstate.area && c.area !== cstate.area) return false;
      if (cstate.perm && (cstate.perm === "anyone" ? c.permissions !== "anyone" : c.permissions === "anyone")) return false;
      if (cstate.status && c.status !== cstate.status) return false;
      if (!q) return true;
      return `${c.name} ${c.aliases.join(" ")} ${c.summary} ${c.area}`.toLowerCase().includes(q);
    });
  }
  function commandResults() {
    const rows = filteredCommands();
    const count = `<span class="v2-count" aria-live="polite">${rows.length} of ${D.COMMANDS.length} commands${COUNTS.commands && COUNTS.commands !== D.COMMANDS.length ? ` (${S.fmt.num(COUNTS.commands)} registered incl. slash duplicates)` : ""}</span>`;
    if (!rows.length) {
      return count + `<div class="sb-empty"><span class="ico">${icon("search", "currentColor", 20)}</span><h4>No commands match</h4>Try a different search or clear a filter.<div class="act"><button class="sb-btn sb-btn-ghost sb-btn-sm" data-clear-filters>Clear filters</button></div></div>`;
    }
    if (cstate.group) {
      return count + D.AREAS.map((a) => {
        const inArea = rows.filter((c) => c.area === a.id);
        if (!inArea.length) return "";
        return `<div class="v2-group-head"><span class="sb-tile" style="--c:${a.color};width:30px;height:30px;border-radius:8px">${icon(a.icon, undefined, 16)}</span><h3>${esc(a.name)}</h3><span class="n">${inArea.length}</span></div>
          <div class="sb-cmdlist">${inArea.map(cmdRow).join("")}</div>`;
      }).join("");
    }
    return count + `<div class="sb-cmdlist">${rows.map(cmdRow).join("")}</div>`;
  }
  function viewCommands() {
    return `<div class="sb-view"><section class="sb-section sb-section-top"><div class="sb-dots" aria-hidden="true"></div><div class="sb-wrap">
      ${crumb([{ label: "Home", href: "#/" }, { label: "Commands" }])}
      ${pageHero(`${D.COMMANDS.length} unique · ${S.fmt.num(COUNTS.commands || D.COMMANDS.length)} registered`, `A <span class="sb-grad">command</span> for everything`, "Every command SuperBot ships, with usage, aliases, permissions and examples. Search, filter, or press ⌘K anywhere.")}
      <div class="sb-panel" style="margin:0">
        <div class="v2-cmdbar">
          <div class="sb-search">${icon("search", "var(--sb-ink-4)", 16)}<input data-q placeholder="Search commands, aliases, descriptions…" aria-label="Search commands" value="${esc(cstate.q)}" /></div>
          <select class="sb-inp" data-perm aria-label="Filter by permissions">
            <option value="">any permission</option>
            <option value="anyone"${cstate.perm === "anyone" ? " selected" : ""}>anyone</option>
            <option value="staff"${cstate.perm === "staff" ? " selected" : ""}>staff-only</option>
          </select>
          <select class="sb-inp" data-status aria-label="Filter by status">
            <option value="">any status</option>
            <option value="finished"${cstate.status === "finished" ? " selected" : ""}>finished</option>
            <option value="in-progress"${cstate.status === "in-progress" ? " selected" : ""}>in-progress</option>
          </select>
          <button class="sb-pill" data-group aria-pressed="${cstate.group}">group by area</button>
        </div>
        <div class="sb-filterbar" role="group" aria-label="Filter by area">
          <button class="sb-pill" data-f="" aria-pressed="${cstate.area === ""}">all</button>
          ${D.AREAS.map((a) => `<button class="sb-pill" data-f="${a.id}" aria-pressed="${cstate.area === a.id}">${esc(a.name)}</button>`).join("")}
        </div>
        <div data-results>${commandResults()}</div>
      </div>
    </div></section>${footer}</div>`;
  }
  function wireCommands(root) {
    const res = root.querySelector("[data-results]");
    const rewire = () => { res.innerHTML = commandResults(); wireClear(root, clearAll); };
    const clearAll = () => { cstate.q = ""; cstate.area = ""; cstate.perm = ""; cstate.status = ""; render(); };
    const qel = root.querySelector("[data-q]");
    if (qel) qel.addEventListener("input", () => { cstate.q = qel.value; rewire(); });
    root.querySelector("[data-perm]").addEventListener("change", (e) => { cstate.perm = e.target.value; rewire(); });
    root.querySelector("[data-status]").addEventListener("change", (e) => { cstate.status = e.target.value; rewire(); });
    const g = root.querySelector("[data-group]");
    g.addEventListener("click", () => { cstate.group = !cstate.group; g.setAttribute("aria-pressed", String(cstate.group)); rewire(); });
    root.querySelectorAll("[data-f]").forEach((b) =>
      b.addEventListener("click", () => {
        cstate.area = b.getAttribute("data-f");
        root.querySelectorAll("[data-f]").forEach((x) => x.setAttribute("aria-pressed", String(x === b)));
        rewire();
      }));
    wireClear(root, clearAll);
  }

  /* ── command detail ──────────────────────────────────────── */
  function viewCommand(name) {
    const c = D.byCommand(name);
    if (!c) return notFound("That command doesn't exist.");
    const a = D.byArea(c.area);
    const color = a ? a.color : "var(--sb-brand)";
    const aliasHtml = c.aliases.length
      ? c.aliases.map((al) => `<span class="sb-chip">!${esc(al)}</span>`).join(" ")
      : `<span class="sb-muted">none yet — <a href="/submit?about=${encodeURIComponent("command:" + c.name)}" style="color:var(--sb-brand-ink)">suggest one</a></span>`;
    const planHtml = c.planned.length
      ? `<div class="sb-panel"><h3>What's planned</h3><div class="sb-stack">${c.planned.map((p) => `<div class="sb-row" style="align-items:flex-start"><span class="sb-badge sb-badge-flag">${esc(p.status)}</span><span style="font-size:14px;color:var(--sb-ink-2)">${esc(p.title)}</span></div>`).join("")}</div></div>`
      : "";
    const related = a ? D.commandsInArea(a.id).filter((x) => x.name !== c.name).slice(0, 4) : [];
    return `<div class="sb-view"><section class="sb-section"><div class="sb-wrap-narrow">
      ${crumb([{ label: "Home", href: "#/" }, { label: "Commands", href: "#/commands" }, { label: "!" + c.name }])}
      <div class="sb-card sb-detail-head" style="--c:${color}">
        <div class="sb-glow glow" aria-hidden="true"></div>
        <div class="row"><span class="sb-cmd-name">!${esc(c.name)}</span>${statusBadge(c.status)}</div>
        <p class="tagline">${esc(c.description)}</p>
        <div class="tags"><a class="sb-badge sb-badge-neutral" href="#/area/${c.area}">${icon(a ? a.icon : "info", "currentColor", 12)} ${esc(a ? a.name : c.area)}</a></div>
      </div>
      <div class="sb-panel"><h3>Usage</h3><div class="sb-example">${esc(c.usage)}</div></div>
      <div class="sb-panel"><h3>Details</h3><div class="sb-kv-grid">
        <dl class="sb-kv"><dt>Aliases</dt><dd>${aliasHtml}</dd></dl>
        <dl class="sb-kv"><dt>Permissions</dt><dd>${esc(c.permissions)}</dd></dl>
        <dl class="sb-kv"><dt>Cooldown</dt><dd>${esc(c.cooldown || "—")}</dd></dl>
      </div></div>
      ${c.examples.length ? `<div class="sb-panel"><h3>Examples</h3><div class="sb-stack">${c.examples.map((ex) => `<div class="sb-example">${esc(ex)}</div>`).join("")}</div></div>` : ""}
      ${planHtml}
      ${related.length ? `<div class="sb-panel"><h3>More in ${esc(a.name)}</h3><div class="sb-cmdlist">${related.map(cmdRow).join("")}</div></div>` : ""}
      ${suggestCta("command:" + c.name, "!" + c.name, color)}
    </div></section>${footer}</div>`;
  }

  /* ── games ───────────────────────────────────────────────── */
  function viewGames() {
    return `<div class="sb-view"><section class="sb-section sb-section-top"><div class="sb-dots" aria-hidden="true"></div><div class="sb-wrap">
      ${crumb([{ label: "Home", href: "#/" }, { label: "Games" }])}
      ${pageHero(`${D.GAMES.length} to play`, `<span class="sb-grad">Games</span>`, "Casual games your members can play right in chat — solo or head-to-head, each one earning XP.", { color: "var(--sb-brand-hi)", more: { href: "#/area/games", label: "Games area →" } })}
      <div class="sb-grid-3">${D.GAMES.map(gameCard).join("")}</div>
    </div></section>${footer}</div>`;
  }

  function viewGame(id) {
    const g = D.byGame(id);
    if (!g) return notFound("That game doesn't exist.");
    const c = D.byCommand(g.command);
    const f = byFeature(g.id);
    return `<div class="sb-view"><section class="sb-section"><div class="sb-wrap-narrow">
      ${crumb([{ label: "Home", href: "#/" }, { label: "Games", href: "#/games" }, { label: g.name }])}
      <div class="sb-card sb-detail-head" style="--c:${g.color}">
        <div class="sb-glow glow" aria-hidden="true"></div>
        <div class="row"><span class="sb-tile sb-tile-lg">${f && f.emoji ? `<span class="emoji" style="font-size:26px" aria-hidden="true">${esc(f.emoji)}</span>` : icon(g.icon)}</span><h1>${esc(g.name)}</h1>${g.beta ? statusBadge("in-progress") : statusBadge("game")}</div>
        <p class="tagline">${esc(g.description)}</p>
      </div>
      <div class="sb-panel"><h3>How to play</h3><ol class="sb-bullets">${g.howTo.map((s2) => `<li>${esc(s2)}</li>`).join("")}</ol></div>
      <div class="sb-panel"><h3>Command</h3><div class="sb-cmdlist">${cmdRow(c)}</div></div>
      ${suggestCta("game:" + g.id, g.name, g.color)}
    </div></section>${footer}</div>`;
  }

  /* ── changelog ───────────────────────────────────────────── */
  const lstate = { kind: "" };
  function changelogEntries() {
    const rels = D.CHANGELOG
      .map((rel) => ({ ...rel, changes: lstate.kind ? rel.changes.filter((c) => c.type === lstate.kind) : rel.changes }))
      .filter((rel) => rel.changes.length);
    if (!rels.length) return `<div class="sb-empty"><span class="ico">${icon("doc", "currentColor", 20)}</span><h4>No entries of this type yet</h4><div class="act"><button class="sb-btn sb-btn-ghost sb-btn-sm" data-clear-filters>Show everything</button></div></div>`;
    return `<div class="sb-timeline">${rels.map((rel) => `
      <div class="sb-rel">
        <div class="sb-rel-aside">
          <span class="ver">v${esc(rel.version)}</span>
          <span class="when">${esc(rel.date)}</span>
          <a class="build" href="${REPO}/commit/${esc(rel.build)}" rel="noopener">${esc(rel.build)}</a>
        </div>
        <div class="sb-rel-body">
          <span class="sb-rel-node" aria-hidden="true"></span>
          <h3>${esc(rel.title)}</h3>
          <ul class="sb-changes">${rel.changes.map((c) => `<li class="sb-ch sb-ch-${c.type}"><span class="sb-ch-tag">${c.type}</span><span>${esc(c.text)}</span></li>`).join("")}</ul>
        </div>
      </div>`).join("")}</div>`;
  }
  function viewChangelog() {
    const total = D.CHANGELOG.reduce((n, r) => n + r.changes.length, 0);
    const kinds = ["added", "improved", "fixed", "removed"];
    return `<div class="sb-view"><section class="sb-section sb-section-top"><div class="sb-dots" aria-hidden="true"></div><div class="sb-wrap-narrow">
      ${crumb([{ label: "Home", href: "#/" }, { label: "Changelog" }])}
      ${pageHero(`${D.CHANGELOG.length} releases · ${total} changes`, `What's <span class="sb-grad">new</span>`, "SuperBot ships in the open — follow along as features land, get polished and occasionally retire.")}
      <div class="sb-filterbar" role="group" aria-label="Filter by change type">
        <button class="sb-pill" data-k="" aria-pressed="${lstate.kind === ""}">all</button>
        ${kinds.map((k) => `<button class="sb-pill" data-k="${k}" aria-pressed="${lstate.kind === k}">${k}</button>`).join("")}
      </div>
      <div data-results>${changelogEntries()}</div>
    </div></section>${footer}</div>`;
  }
  function wireChangelog(root) {
    const res = root.querySelector("[data-results]");
    const clearAll = () => { lstate.kind = ""; render(); };
    root.querySelectorAll("[data-k]").forEach((b) =>
      b.addEventListener("click", () => {
        lstate.kind = b.getAttribute("data-k");
        root.querySelectorAll("[data-k]").forEach((x) => x.setAttribute("aria-pressed", String(x === b)));
        res.innerHTML = changelogEntries();
        wireClear(root, clearAll);
      }));
    wireClear(root, clearAll);
  }

  /* ── status ──────────────────────────────────────────────── */
  const ST = {
    operational: { label: "Operational", token: "var(--sb-ok)", tick: "ok", ico: "check" },
    degraded: { label: "Degraded", token: "var(--sb-warn)", tick: "warn", ico: "clock" },
    maintenance: { label: "Maintenance", token: "var(--sb-info)", tick: "info", ico: "info" },
    outage: { label: "Outage", token: "var(--sb-danger)", tick: "danger", ico: "alert" },
  };
  function viewStatus() {
    const s = D.STATUS;
    const allOk = s.systems.every((x) => x.state === "operational");
    const banner = ST[s.overall] || ST.operational;
    const sysRows = s.systems.map((sys) => {
      const m = ST[sys.state] || ST.operational;
      return `<div class="sb-sys">
        <div class="sb-sys-head">
          <div class="sb-sys-id">
            <span class="sb-dot" style="--c:${m.token}" aria-hidden="true"></span>
            <div><div class="sb-sys-name">${esc(sys.name)}</div><div class="sb-sys-desc">${esc(sys.desc)}</div></div>
          </div>
          <span class="sb-sys-state" style="color:${m.token}">${icon(m.ico, "currentColor", 13)} ${esc(m.label)}</span>
        </div>
        ${sys.note ? `<div class="sb-error" style="margin-top:12px">${icon("alert")}<span>${esc(sys.note)}</span></div>` : ""}
        ${S.tickStrip(sys.history.map((h) => (ST[h] || ST.operational).tick), { ariaLabel: `${sys.name} status, last ${sys.history.length} days` })}
      </div>`;
    }).join("");
    return `<div class="sb-view"><section class="sb-section sb-section-top"><div class="sb-dots" aria-hidden="true"></div><div class="sb-wrap-narrow">
      ${crumb([{ label: "Home", href: "#/" }, { label: "Status" }])}
      ${pageHero("How things are running", `System <span class="sb-grad">status</span>`, null)}
      <div class="sb-status-banner" style="--c:${banner.token}">
        <span class="sb-pulse" aria-hidden="true"></span>
        <div><strong>${allOk ? "All systems operational" : "Some systems need attention"}</strong>
        <span class="sub">as of build ${esc(BUILD.commit || "dev")}${buildDate ? ` · ${esc(buildDate)}` : ""}</span></div>
        <span style="margin-left:auto" aria-hidden="true">${icon("activity", banner.token, 26)}</span>
      </div>
      <div class="sb-panel" style="padding:8px 8px 4px">${sysRows}</div>
      <p class="v2-honesty">${icon("info", "currentColor", 14)} <span>Honesty note: these states are editorial, refreshed with each deploy — SuperBot doesn't publish live telemetry yet. When the ops feed lands, this page will read from it directly (declared feed: per-system state + incident history).</span></p>
    </div></section>${footer}</div>`;
  }

  /* ── palette registration ────────────────────────────────── */
  function registerPalette() {
    const items = [];
    [["Home", "#/"], ["Features", "#/features"], ["Commands", "#/commands"], ["Games", "#/games"],
     ["Changelog", "#/changelog"], ["Status", "#/status"], ["Design system", "/design"], ["Suggest & report", "/submit"]]
      .forEach(([label, href]) => items.push({ group: "Pages", label, href, sub: "page" }));
    FEATURES.forEach((f) => items.push({ group: "Features", label: f.name, sub: f.area, href: "#/feature/" + encodeURIComponent(f.key), keywords: f.tags.join(" ") }));
    D.GAMES.forEach((g) => items.push({ group: "Games", label: g.name, sub: "!" + g.command, href: "#/game/" + encodeURIComponent(g.id) }));
    D.COMMANDS.forEach((c) => items.push({ group: "Commands", code: "!" + c.name, label: clip(c.summary, 60), sub: c.area, href: "#/command/" + encodeURIComponent(c.name), keywords: c.aliases.join(" ") }));
    S.palette.register(items);
  }

  /* ── nav chrome (status chip + install links) ────────────── */
  function initNavChrome() {
    const chip = document.querySelector("[data-status-chip]");
    if (chip) {
      const ok = D.STATUS.systems.every((x) => x.state === "operational");
      chip.innerHTML = `<span class="sb-pulse" aria-hidden="true"${ok ? "" : ' style="background:var(--sb-warn);box-shadow:0 0 8px var(--sb-warn)"'}></span> ${ok ? "All systems operational" : "Some systems degraded"}`;
    }
    document.querySelectorAll("[data-add-url]").forEach((el) => { el.href = ADD_URL; el.setAttribute("rel", "noopener"); });
  }

  /* ── router ──────────────────────────────────────────────── */
  const TITLES = {
    home: "SuperBot — one bot for your whole Discord server",
    features: "Features — SuperBot", commands: "Commands — SuperBot",
    games: "Games — SuperBot", changelog: "Changelog — SuperBot", status: "Status — SuperBot",
  };
  function parse() {
    const h = (location.hash || "#/").replace(/^#/, "");
    const seg = h.split("/").filter(Boolean);
    return { name: seg[0] || "home", param: seg[1] ? decodeURIComponent(seg[1]) : null };
  }
  function setNav(name) {
    document.querySelectorAll("[data-nav]").forEach((a) => {
      if (a.getAttribute("data-nav") === name) a.setAttribute("aria-current", "page");
      else a.removeAttribute("aria-current");
    });
  }
  let firstRender = true;
  function render() {
    const r = parse();
    let html, navKey = r.name, title = TITLES[r.name];
    switch (r.name) {
      case "home": html = viewHome(); break;
      case "features": html = viewFeatures(); break;
      case "feature": html = viewFeature(r.param); navKey = "features";
        title = (byFeature(r.param) || {}).name ? `${byFeature(r.param).name} — SuperBot` : title; break;
      case "area": html = viewArea(r.param); navKey = "features";
        title = D.byArea(r.param) ? `${D.byArea(r.param).name} — SuperBot` : title; break;
      case "commands": html = viewCommands(); break;
      case "command": html = viewCommand(r.param); navKey = "commands";
        title = D.byCommand(r.param) ? `!${r.param} — SuperBot` : title; break;
      case "games": html = viewGames(); break;
      case "game": html = viewGame(r.param); navKey = "games";
        title = D.byGame(r.param) ? `${D.byGame(r.param).name} — SuperBot` : title; break;
      case "changelog": html = viewChangelog(); break;
      case "status": html = viewStatus(); break;
      default: html = notFound(); navKey = "";
    }
    app.innerHTML = html;
    document.title = title || TITLES.home;
    setNav(navKey);
    if (r.name === "commands") wireCommands(app);
    if (r.name === "features") wireFeatures(app);
    if (r.name === "changelog") wireChangelog(app);
    app.querySelectorAll("[data-palette-open]").forEach((b) => b.addEventListener("click", S.palette.open));
    window.scrollTo(0, 0);
    /* a11y: move focus to the page content on SPA navigation (not initial load) */
    if (!firstRender) app.focus({ preventScroll: true });
    firstRender = false;
  }

  window.addEventListener("hashchange", render);
  if (!location.hash) location.replace("#/");
  registerPalette();
  initNavChrome();
  S.initChrome();
  render();
})();
