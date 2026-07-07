/* ============================================================================
   SuperBot program console — the owner's one-glance page
   ----------------------------------------------------------------------------
   Renders from /console/data.json (the whitelisted console feed exported by
   scripts/export_dashboard_data.py). Honest-lane rule: real feeds render real
   data; a feed that doesn't exist yet renders as a PENDING lane that names its
   declared contract — never placeholder numbers (the UNRENDERED-banner
   instinct). Lanes:

     REAL today   — session run reports (⚑ self-initiated flags, Q-0172) ·
                    ideas & bugs counters · deploys/changelog + build provenance
     DECLARED     — model/spend telemetry (Q-0248/Q-0249) · rebuild port
                    progress (gate-5 parity feed) · trading tracker (Q-0251)
   ========================================================================== */
(function () {
  "use strict";
  const S = window.SBDS;
  const esc = S.esc;
  const icon = S.icon;
  const app = document.getElementById("console-app");
  const metaLine = document.getElementById("console-meta");

  const statusBadge = (st) => {
    const s = String(st || "").toLowerCase();
    if (/(complete|done|ready|final|merged|shipped)/.test(s)) return `<span class="sb-badge sb-badge-ok">${icon("check", "currentColor", 11)} ${esc(s)}</span>`;
    if (/(progress|hold)/.test(s)) return `<span class="sb-badge sb-badge-warn">${icon("clock", "currentColor", 11)} ${esc(s)}</span>`;
    return `<span class="sb-badge sb-badge-neutral">${esc(s || "—")}</span>`;
  };

  const pendingLane = (title, why, feed, wide) => `
    <section class="sb-lane-pending${wide ? " co-lane-wide" : ""}" aria-label="${esc(title)} (no data yet)">
      <div class="head">${icon("inbox")}<h4>${esc(title)}</h4><span class="sb-badge sb-badge-neutral" style="margin-left:auto">declared</span></div>
      <p>${esc(why)}</p>
      <code class="feed">${esc(feed)}</code>
    </section>`;

  const lane = (title, bodyHtml, opts) => `
    <section class="sb-panel${(opts && opts.wide) ? " co-lane-wide" : ""}" style="margin:0" aria-label="${esc(title)}">
      <h3>${esc(title)}</h3>${bodyHtml}
    </section>`;

  /* the three declared-contract lanes (render identically with or without data.json) */
  const declaredLanes = () =>
    pendingLane(
      "Model & spend telemetry",
      "No data yet — per-session `model · effort · task-class · outcome` telemetry starts with the program kickoff sessions (Q-0248) and budget data shares the same dataset (Q-0249, observe-first window). This lane renders the cost-quality frontier once the feed lands.",
      "telemetry/model-usage.json → [{ session, date, model, effort, task_class, tokens_out, outcome }]",
    ) +
    pendingLane(
      "Rebuild port progress",
      "No data yet — gate 5 of the rebuild plan defines the per-surface parity feed; this lane becomes the port-progress dashboard (surfaces green/red against the pinned goldens) when superbot-next starts reporting.",
      "parity/parity.yml → { surface: { goldens, passing, verdict } } per rebuild step",
    ) +
    pendingLane(
      "Trading tracker",
      "No data yet — the trading research repo is program session 3 (Q-0251). Declared v1 product: the decision-ledger forward-test log with leaderboards (gain% per time and per trade count + honesty columns: drawdown, sample size, exposure) and the owner's DEGIRO benchmark lane.",
      "trading: strategy registry + decision ledger → leaderboard rows (tamper-evident via git timestamps)",
    );

  function render(data) {
    const build = (data.meta && data.meta.build) || {};
    metaLine.innerHTML = `Session run reports, flags and program state — generated ${esc(S.fmt.date((data.meta.generated_at || "").slice(0, 10)) || "recently")} at build <a href="https://github.com/menno420/superbot/commit/${esc(build.commit || "")}" rel="noopener" style="color:var(--sb-brand-ink)">${esc(build.commit || "?")}</a>.`;

    const sessions = data.sessions || [];
    const last7 = sessions.filter((s2) => daysAgo(s2.date) < 7);
    const flagged = sessions.filter((s2) => s2.self_initiated);
    const inProgress = sessions.filter((s2) => /progress|hold/.test(String(s2.status || "").toLowerCase()));

    /* sessions/day sparkline over the last 14 days (oldest → newest) */
    const perDay = [];
    for (let i = 13; i >= 0; i--) perDay.push(sessions.filter((s2) => daysAgo(s2.date) === i).length);

    const statRow = `<div class="sb-statrow sb-statrow-4">
      ${S.statTile({ label: "Run reports in feed", value: String(sessions.length), spark: perDay })}
      ${S.statTile({ label: "Sessions, last 7 days", value: String(last7.length) })}
      ${S.statTile({ label: "⚑ self-initiated in feed", value: String(flagged.length) })}
      ${S.statTile({ label: "Open bugs", value: String((data.bugs && data.bugs.open || []).length) })}
    </div>`;

    const sessionRows = (list) => list.slice(0, 14).map((s2) => `
      <div class="co-session">
        <span class="when">${esc(s2.date || "")}</span>
        <span class="t" title="${esc(s2.title || s2.file)}">${esc(cleanTitle(s2))}</span>
        <span class="end">${s2.self_initiated ? `<span class="sb-badge sb-badge-flag" title="self-initiated (Q-0172)">${icon("flag", "currentColor", 11)} self</span>` : ""}${s2.run_type ? `<span class="sb-badge sb-badge-neutral">${esc(s2.run_type)}</span>` : ""}${statusBadge(s2.status)}</span>
      </div>`).join("");

    const runLane = lane("Run reports — the session feed", `
      <div class="sb-filterbar" role="group" aria-label="Filter run reports">
        <button class="sb-pill" data-rf="all" aria-pressed="true">all</button>
        <button class="sb-pill" data-rf="flagged" aria-pressed="false">⚑ self-initiated</button>
        <button class="sb-pill" data-rf="progress" aria-pressed="false">in-progress</button>
      </div>
      <div data-run-list>${sessionRows(sessions) || emptyList("No run reports in the feed.")}</div>
      <p class="sb-chart-note">From <code class="sb-mono">.sessions/</code> run reports — the ⚑ flag marks work agents started on their own initiative (Q-0172 accountability line).</p>
    `, { wide: true });

    const ideas = data.ideas || { total: 0, by_status: {} };
    const bugs = data.bugs || { total: 0, by_status: {}, open: [] };
    const ideasBars = S.barChart(
      Object.entries(ideas.by_status).sort((a, b) => b[1] - a[1]).slice(0, 6)
        .map(([k, v]) => ({ label: k, value: v })),
      { ariaLabel: "Ideas by status" },
    );
    const ideasLane = lane(`Ideas — ${ideas.total} captured`, ideasBars +
      `<p class="sb-chart-note">The idea pipeline (capture → route → build); every idea eventually becomes implemented or discussed, never orphaned.</p>`);

    const bugRows = (bugs.open || []).map((b) => `
      <div class="co-bug"><span class="id">${esc(b.id || "")}</span><span>${esc(b.title || "")}</span><span style="margin-left:auto">${statusBadge(b.status)}</span></div>`).join("");
    const bugsLane = lane(`Bugs — ${(bugs.open || []).length} open of ${bugs.total} tracked`,
      bugRows ? `<div class="co-buglist">${bugRows}</div>` : emptyList("No open bugs — the book is clean."));

    const changelog = (data.bot_changelog || []).slice(0, 5).map((e) => `
      <div class="co-session"><span class="when">${esc(e.date || "")}</span><span class="t">${esc(e.title || "")}</span><span class="end"><span class="sb-badge sb-badge-neutral">${esc(e.kind || "update")}</span></span></div>`).join("");
    const deployLane = lane("Deploys & user-facing changelog", (changelog || emptyList("No changelog entries.")) +
      `<p class="sb-chart-note">Merging to main IS deploying (Q-0193) — Railway redeploys each service on merge; build above is the live provenance.</p>`);

    app.innerHTML = statRow + `<div class="co-lanes">${runLane}${ideasLane}${bugsLane}${deployLane}${declaredLanes()}</div>`;

    /* run-report filter pills */
    const listEl = app.querySelector("[data-run-list]");
    app.querySelectorAll("[data-rf]").forEach((b) =>
      b.addEventListener("click", () => {
        app.querySelectorAll("[data-rf]").forEach((x) => x.setAttribute("aria-pressed", String(x === b)));
        const mode = b.getAttribute("data-rf");
        const list = mode === "flagged" ? flagged : mode === "progress" ? inProgress : sessions;
        listEl.innerHTML = sessionRows(list) || emptyList("Nothing matches this filter.");
      }));
  }

  function renderUnavailable(reason) {
    metaLine.textContent = "The console feed hasn't been exported yet — real lanes are dormant, declared lanes below say what will fill them.";
    app.innerHTML = `
      <div class="sb-error" style="margin-bottom:16px">${icon("alert")}<span><strong>No console feed.</strong> ${esc(reason)} Regenerate with <code class="sb-mono">python3.10 scripts/export_dashboard_data.py --targets console</code> and redeploy.</span></div>
      <div class="co-lanes">${pendingLane("Run reports — the session feed", "Renders the .sessions/ run-report feed (dates, titles, status, ⚑ self-initiated flags) once console.json is exported.", "botsite/data/console.json → sessions[]", true)}${declaredLanes()}</div>`;
  }

  const emptyList = (msg) => `<div class="sb-empty" style="padding:20px 8px">${esc(msg)}</div>`;
  const cleanTitle = (s2) => String(s2.title || s2.file || "").replace(/^\d{4}-\d{2}-\d{2}\s*[—-]\s*/, "");
  function daysAgo(iso) {
    if (!iso) return 9999;
    const d = new Date(iso + "T00:00:00Z");
    if (isNaN(d)) return 9999;
    return Math.floor((Date.now() - d.getTime()) / 86400000);
  }

  S.initChrome();
  fetch("/console/data.json", { cache: "no-cache" })
    .then((r) => (r.ok ? r.json() : Promise.reject(new Error("HTTP " + r.status))))
    .then(render)
    .catch((e) => renderUnavailable(String(e.message || e)));
})();
