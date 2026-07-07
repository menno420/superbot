# Session-1 brief — the program websites (last-Fable-day design session)

> **Status:** `plan` — the launch brief + paste-ready prompt for **program session 1 of 4**
> (re-cut by owner correction **Q-0253**: today is the last day Fable is in the subscription for
> a while, so the scarce capacity goes to the work where its edge is most visible — design).
> **Model:** Claude **Fable 5**, `/effort ultracode`. Launch index:
> [`program-three-sessions-launch-index-2026-07-07.md`](program-three-sessions-launch-index-2026-07-07.md).
> Governance: **Q-0241/Q-0240** (never-wait, decide-and-flag) · **Q-0248** telemetry from
> session one.

## 0. The owner's ask, verbatim-condensed

Use the design of the existing websites as guidance — **specifically the looks of the botsite** —
but come up with an **improved own version**; the program's websites "should not necessarily look
or function the same, but it should be clear and easy to use and feature rich, possibly also
decided by simulations etc."

## 1. Reading route (in order)

1. `.claude/CLAUDE.md` → `docs/collaboration-model.md` → `docs/current-state.md` (S1 + S3 rows).
2. **The web estate as it exists:** `botsite/README.md` (the Claude-Design SPA: neon theme,
   vanilla-JS no-build, hash-routed, everything renders from `window.SBDATA`/`site.json`; the
   Jinja fallback; **three design-owned files that must never be edited** — v2 SUPERSEDES with
   new files, keeping v1 intact as the fallback) → `docs/owner/website-explained.md` →
   `docs/planning/website-two-site-split-plan-2026-06-19.md` (public site vs dev dashboard
   topology + security model) → `dashboard/` → `scripts/export_dashboard_data.py` (the data
   pipeline: `botsite/data/site.json` + `botsite/site/data.js`).
3. **The program frame** (what these sites will serve):
   [`../ideas/multi-repo-program-kit-lab-trading-2026-07-07.md`](../ideas/multi-repo-program-kit-lab-trading-2026-07-07.md)
   — the lab's work surfaces (the **program console** is its recommended first site), the trading
   tracker's needs (Q-0251: leaderboards, decision-ledger browser, DEGIRO benchmark lane).
4. The **dataviz skill** (load it before writing any chart/stat-tile code) — the design-system
   work must produce chart/tile patterns that read as one system.

## 2. The mandate — in priority order (ship 1 fully before 2, 2 before 3)

1. **The program design system** — the compounding asset. An evolution of the botsite look
   (its neon identity is the anchor the owner likes), rebuilt as a **reusable foundation** all
   program sites share: design tokens (color/type/spacing/elevation, dark-first with a proper
   light theme), a component library (nav, cards, tables, stat tiles, charts, forms, empty/error
   states), layout patterns, accessibility (contrast, focus, keyboard), responsive rules. Keep
   the no-build vanilla discipline unless you can justify a minimal build step (decide-and-flag —
   the no-build property is why agents can iterate the site cheaply). Document it as a living
   style guide page that renders every component (the design system's own test surface).
2. **Botsite v2** — the improved public site, on the design system, over the real `site.json`
   data that exists today (485 commands / 43 features / 12 games — immediately verifiable).
   Better information architecture than v1 where you see wins (clarity, findability,
   feature-richness); v1's three design-owned files stay untouched (v2 = new files; v1 remains
   the wired fallback until the owner flips).
3. **The program console shell** — the owner's one-glance page (capture doc part 2): run
   reports + ⚑ flags, spend/model telemetry (Q-0248/Q-0249 — placeholder lanes with declared
   data contracts until the telemetry lands), the port-progress dashboard slot (gate 5's
   parity.yml when it exists), trading state slot (Q-0251's tracker later). Ship the shell +
   whatever real data is reachable today (dashboard.json export, merged-PR feed); every empty
   lane declares its future feed honestly — no fake data, the UNRENDERED-banner instinct.
4. **Sim-informed UX, pragmatically** — the owner's "possibly decided by simulations": do NOT
   build a full website-layout simulator today. Instead: (a) a **task-success checklist** as a
   repeatable check (a defined user-task list — "find command X", "check feature Y's status" —
   with max-click/nav-depth budgets, runnable via Playwright); (b) nav-coverage + perf +
   accessibility budgets in CI shape; (c) where a real layout choice is contested, a cheap
   scored comparison (two variants, the task list, pick by score) — the sim-decides instinct at
   web scale. A full navigation-simulator oracle stays a named future lab item.

**Verification (the "well functioning" half):** drive it live — run the FastAPI app locally,
Playwright/chromium is pre-installed; screenshot every page in both themes at 3 widths; run the
task-success checklist; attach the screenshots to the PR/run report. Design claims without
rendered proof don't count.

**Deployment:** botsite already deploys as its own Railway service — v2 rides the same service
behind the existing fallback switch (no new Railway needs today); the console's deploy target is
decided-and-flagged (same service as a route vs the lab's future project — recommend the former
for now, move at kit-extraction).

## 3. What NOT to do

- Never edit the three design-owned v1 files (`botsite/site/index.html` / `app.js` / `app.css`).
- No new Railway project today; no secrets work.
- Don't build the trading tracker or the full telemetry pipelines — shells with declared
  contracts only (their sessions own the real feeds).
- Don't chase pixel-parity with v1 — the owner explicitly wants an *improved own version*.

## 4. Paste-ready prompt

> You are a **Claude Fable 5** session at **`/effort ultracode`** on the SuperBot repo. Read
> `docs/planning/website-design-fable-brief-2026-07-07.md` — it is your full brief and reading
> route. Today is the last Fable day for a while: spend it on design quality. Build, in strict
> priority order: (1) the program design system (an improved evolution of the botsite's neon
> look — tokens, components, layouts, dark/light, accessibility, a living style-guide page);
> (2) botsite v2 on that system over the real site.json data (v1's three design-owned files stay
> untouched — v2 supersedes with new files, v1 stays the fallback); (3) the program-console
> shell with honest placeholder lanes; (4) the pragmatic sim-informed UX checks (task-success
> checklist with click budgets via Playwright, nav/perf/accessibility budgets). Verify
> everything live — run the app, screenshot every page both themes at 3 widths, run the task
> checklist, attach proof. Decide-and-flag; never wait for me; silence = consent.
