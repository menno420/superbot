<!-- badge: historical -->
# Plan — make the live bot-site the React design-system app (kill the porting step)

> **Status:** `historical` — **superseded 2026-07-07 by botsite v2 on the program design system**
> (the last-Fable-day design session, brief
> [`website-design-fable-brief-2026-07-07.md`](website-design-fable-brief-2026-07-07.md)): the owner's
> "improved own version" ask was fulfilled as a **no-build vanilla SPA** (`botsite/site/v2/` on
> `botsite/ds/`), keeping the iterate-cheaply property this React path would have traded away. The
> §9 count-honesty goal shipped in v2 (unique-vs-registered counts labeled); the React
> `design-system/` library remains the Claude-Design working surface only. Original plan below,
> unchanged.
> **Original status:** `plan` · **Sector:** S5 (web tier) · **Created:** 2026-06-20 · **Size:** 2–3 PRs
> **Provenance:** owner-requested 2026-06-20, follow-up to the SPA-wiring work (PR #1196) and the
> plain-language explainer ([`docs/owner/website-explained.md`](../owner/website-explained.md)).
> **Related:** [`website-two-site-split-plan`](website-two-site-split-plan-2026-06-19.md) ·
> [`web-tier-centralization-proposal`](web-tier-centralization-proposal-2026-06-19.md) ·
> [`design-system/README.md`](../../design-system/README.md)
>
> Planning only — no implementation until the owner (or a routine) starts it. Source wins over this doc.

---

## 1. The problem this removes

The website's UI currently exists in **two separate codebases that look the same**:

| Form | Tech | Edited by |
|---|---|---|
| `design-system/` | **React + Tailwind** components (the design source of truth) | Claude Design (GitHub connector) |
| `botsite/site/` (live) + `botsite/templates/` (Jinja fallback) | **vanilla JS SPA** + Jinja | served to users |

When you design in Claude Design (React), the result has to be **re-implemented** in the live
site's *different* technology. That re-implementation — **porting** — is the manual Claude-Code
step that makes Claude Code feel mandatory before every deploy.

**Key distinction (the owner's question):** deployment *always* needs a commit → CI → Railway. That
pipeline never goes away (it is the test/rollback safety net). What this plan removes is the
**translation between two codebases**, not the commit/deploy. After this, the thing Claude Design
edits **is** the thing that ships — so the "Claude Code at the end" step becomes (at most) "review &
merge a PR," and can even be an **automated CI build** rather than a human re-implementation.

### Goal

Make `botsite/`'s live front-end **be the built `design-system/` React app**, fed by the existing
`site.json` → data pipeline, so a Claude Design edit lands on the live site with **no porting**.

### Non-goals

- **Not** introducing SSR / Next.js. The site stays a static client-rendered SPA — that preserves
  `botsite/`'s decoupled, secret-free posture (see §5) and keeps Railway simple.
- **Not** changing the data pipeline's source of truth (`disbot/ → site.json` stays exactly as is).
- **Not** removing the commit → CI → Railway pipeline (it stays; only *porting* is removed).
- **Not** building production UI inside `dashboard/` (separate service, out of scope).

---

## 2. Current vs. target architecture

**Today (two representations, manual port):**

```
Claude Design ──edits──▶ design-system/ (React)         ··· design reference only
                                                          (PORT by Claude Code) ─┐
disbot/ ─export─▶ site.json ─site_data.py─▶ /data.js ──▶ botsite/site/ vanilla SPA ◀┘ ··· LIVE
```

**Target (one representation, no port):**

```
Claude Design ──edits──▶ design-system/ (React)  ──CI builds──▶ static bundle ─┐
                                                                                ├─▶ served by botsite ··· LIVE
disbot/ ─export─▶ site.json ─▶ /site-data.json (or /data.js) ───fetched by─────┘
```

The React `LandingPage` / `FeaturesPage` / `CommandsPage` / `ChangelogPage` / `StatusPage`
components **already exist** and already take props (with sample defaults so they render standalone
on the Claude Design canvas). The work is to (a) make them a runnable, routable app, (b) feed them
the real data at runtime, and (c) serve the built output from `botsite/`.

### The insight that keeps Railway unchanged

`botsite/`'s Railway service installs **Python only** (Root Directory = `botsite`). Rather than make
Railway build React (which would add a Node buildpack), a **GitHub Action builds the React app and
commits/uploads the compiled static bundle into `botsite/site/`** — exactly the pattern already used
for the generated `data.js`. Then Railway keeps doing what it does now: serve static files +
the dynamic `/data.js`/`/site-data.json` route. **The CI build replaces the manual port.** (Decision
A below offers the Railway-builds alternative if preferred.)

---

## 3. Decisions the owner/routine should make first

| # | Decision | Options | Recommendation |
|---|---|---|---|
| **A** | Who runs the React build? | (a) **CI builds + commits** the static bundle to `botsite/site/` → Railway stays Python-only; (b) Railway builds (add Node/nixpacks buildpack) | **(a)** — keeps the proven Python-only Railway service and mirrors the existing `data.js` generation pattern |
| **B** | How does the React app get data? | (a) add a pure **`/site-data.json`** endpoint the app `fetch()`es; (b) reuse `/data.js`'s `window.SBDATA` via a TS adapter | **(a)** — cleaner contract for React; keep `/data.js` during transition for the legacy SPA |
| **C** | Cutover style | (a) flip `/` to React, keep vanilla SPA + Jinja as fallback for one band, then remove; (b) hard cutover | **(a)** — reversible, low-risk |
| **D** | Connector write-back | Does Claude Design's GitHub connector have **write** access (can it open its own PRs)? | **RESOLVED (owner-confirmed 2026-06-20): READ-ONLY.** GitHub grants the connector read access only and exposes no write toggle, so Claude Design **cannot** open its own PRs. The loop therefore keeps a **Claude Code step**: design → manual export (handoff zip) → Claude Code commits + opens the PR → CI → Railway. (Still no *porting* once the React migration lands — the export is the built app, not a re-implementation.) |

None of these blocks starting PR 1 except as noted; A/B can default to the recommendation.

---

## 4. PR breakdown (2–3 PRs)

### PR 1 — Foundation: make `design-system/` a buildable, data-fed app (additive, live site untouched)

Everything here is additive — the live site keeps serving the vanilla SPA until PR 2.

- **App shell + routing.** Add `design-system/src/app/` with `main.tsx` (React root) and a router
  matching the SPA's pages: Home / Features / Commands / Games / Changelog / Status. Use a **hash
  router** (`/#/commands`) to match the current URL scheme and keep `botsite/` serving a single
  shell (no server-side route changes). `react-router-dom` or a tiny custom hash switch — either is fine.
- **Data adapter.** `design-system/src/app/data.ts`: `fetch()` the site data (per Decision B) and map
  it onto the page props (`FeatureCategory[]`, `CommandCategoryGroup[]`, `BuildMeta`, counts, the
  install URL). The pages keep their sample defaults for the canvas; production passes real props.
- **Install URL = real prop (fixes the dead "Add to Discord").** The pages already accept `addUrl`;
  wire it from the data so the live CTA works — this also closes the placeholder follow-up *without*
  editing the handoff SPA's protected files (it's a different, React, codebase).
- **Build target.** Add `build:app` (Vite — already a devDependency; `@vitejs/plugin-react` present)
  producing a static `dist-app/` (HTML + hashed JS/CSS). Keep the existing `build` (tsup library +
  Storybook) untouched — the canvas/connector still consume the component library exactly as today.
- **Data delivery (Decision B(a)):** add a `botsite/` route `GET /site-data.json` returning the same
  data `site_data.py` produces, as pure JSON (reuse `build_prototype_data`; emit JSON not JS).
- **Tests/CI:** typecheck the app (`tsc --noEmit` already wired); a smoke test that the data adapter
  maps a sample `site.json` to valid page props; `design-system-ci.yml` runs the new `build:app`.

*End state:* a runnable React site exists and builds, but visitors still see the vanilla SPA.

### PR 2 — Serve the built React app from `botsite/`

- **CI build-and-publish (Decision A(a)):** a workflow step builds `design-system` `build:app` and
  writes the static bundle into `botsite/site/` (replacing the hand-authored `index.html`/`app.js`/
  `app.css` with the React build output). Mirror the `data.js` generation: a committed artifact +
  a check that it is in sync with source (a `test_react_bundle_in_sync`-style guard, or build-in-CI).
  - **Gotcha:** never put the bundle in a dir literally named `static/` (gitignored — the #970
    deploy crash). `botsite/site/` is proven safe.
- **Serve it:** `botsite/app.py` `/` serves the React `index.html`; the hashed asset files are served
  from `botsite/site/`; `/data.js` (legacy) and `/site-data.json` (new) both stay live during transition.
- **Keep fallbacks:** the Jinja routes (`/commands` …) remain as the no-JS fallback for one band.
- **Verify:** `botsite-tests` updated — `/` serves the React shell; `/site-data.json` is truthful
  (real command names, honest counts, no server/user totals — same guards as today's `/data.js` test).

*End state:* visitors see the React app, fed by live data; Claude Design edits → CI build → live.

### PR 3 — Cutover & cleanup (retire the duplication)

- Remove the vanilla handoff SPA source (`botsite/site/{index.html,app.js,app.css}` as *hand-authored*
  files — they're now CI build output) and, once confident, the Jinja `templates/` + their routes.
- Retire `site_data.py`'s JS-emitting half if `/site-data.json` fully replaces `/data.js`; keep the
  `build_prototype_data` transform (still the data contract).
- **Docs reconcile (the flagged drift):** update `design-system/README.md` (it currently says
  "production stays Jinja; port into Jinja" — now false), `docs/owner/website-explained.md`, and
  `docs/AGENT_ORIENTATION.md` website route to describe the unified React-is-the-site model.
- Fold into [`web-tier-centralization-proposal`](web-tier-centralization-proposal-2026-06-19.md) if
  that lands around the same time (shared `web-ci.yml`).

---

## 5. Invariants that MUST be preserved

These are load-bearing and a reviewer should check them on every PR:

- **`botsite/` never imports `disbot/`.** The React app is a static client; it reads only the public
  `site-data.json`/`data.js` built from `site.json`. No new coupling.
- **Secret-free public surface.** The React bundle is static and carries no secrets; data is the same
  public subset (redaction-by-construction whitelist in `export_dashboard_data.py`). A compromise of
  the public site still cannot reach the bot, its DB, or any token.
- **Single source of truth for data** stays `disbot/ → site.json`. The React app does not introduce a
  second data path.
- **No `static/` directory** (the gitignore #970 gotcha). Built assets live under `botsite/site/`.
- **CI parity / Python 3.10** unchanged for the Python side; the JS side keeps its own CI leg.

---

## 6. Risks & trade-offs

| Risk | Mitigation |
|---|---|
| **A build step is now required** (React must compile; the current SPA is no-build) | Build in CI, commit the bundle → Railway service unchanged (Decision A(a)). The cost is CI time + a build config, not new runtime infra. |
| Committed build output churns (hashed filenames) on every design change | Acceptable (same model as committed `data.js`); or gitignore the bundle and let Railway build (Decision A(b)) if churn is annoying |
| Hard cutover breaks the live site | Decision C(a): keep vanilla SPA + Jinja fallback for one band; flip `/` last; reversible via git |
| Claude Design connector may be **read-only** in this setup | Decision D: if read-only, Claude Code stays as the trivial merge step (still no porting). The win holds either way. |
| Page prop shapes drift from `site-data.json` | A TS adapter + a smoke test (PR 1) that maps sample `site.json` → page props; fail CI on a missing field (the design↔data contract guard, the same idea as today's `site_data` tests) |
| Parallel work on `design-system/` (active claim) | Coordinate via `docs/owner/active-work.md` before starting; PR 1 is additive (`src/app/`), low collision with component edits |

---

## 7. Verification (per PR)

- **PR 1:** `npm --prefix design-system run build:app` produces `dist-app/`; `tsc --noEmit` clean;
  data-adapter smoke test green; `/site-data.json` returns truthful data (real command names, honest
  counts, no server/user totals).
- **PR 2:** `botsite-tests` green — `/` serves the React shell, assets load, `/site-data.json` live;
  manual `uvicorn botsite.app:app` + browser click-through of all pages, zero console errors.
- **PR 3:** docs checks (`check_docs --strict`, `check_plan_homing`) green; `design-system/README`,
  `website-explained.md`, `AGENT_ORIENTATION` reconciled; no dead references to the removed Jinja/SPA.

---

## 8. For the implementer (or a routine) — quickstart checklist

1. Read this plan + [`design-system/README.md`](../../design-system/README.md) +
   [`docs/owner/website-explained.md`](../owner/website-explained.md).
2. Confirm Decisions A–D (defaults: A(a), B(a), C(a), D = check settings).
3. Claim the lane in `docs/owner/active-work.md` (`botsite/` + `design-system/src/app/`).
4. PR 1 → PR 2 → PR 3 as above; keep each invariant in §5 green.
5. On cutover, update the three docs in §4 PR 3 so the "two codebases" story is gone for good.

**Definition of done:** a Claude Design edit to a `design-system/` page, once merged, appears on the
live Railway site **without any hand-written port** — the only human step is review/merge (or none,
if the connector writes its own PR).

---

## 9. Command-count reconciliation (owner-reported, fold into PR 1) — BUG-0023

The bot's status embed shows **354 (283 prefix · 71 slash)**; the website shows **~280**;
`site.json` says **308**. These are three *different metrics*, not a data error (full analysis:
[`bug-book.md` BUG-0023](../health/bug-book.md)):

- **Bot** = live registry, per surface, **incl. subcommands**, a dual command counted on both
  surfaces (`webhook_reporter._command_counts`).
- **Website** = **unique command names** (the SPA dedupes 308 → 280 because each command has one
  `#/command/<name>` page).
- Source scan = **283 prefix + 25 slash = 308**; the prefix figure matches the bot **exactly**.

Two deliverables for this migration:

1. **Display parity (PR 1).** The React app should show the **same `prefix · slash` breakdown the
   bot reports**, sourced from the data — not a bare deduped length that matches nothing the owner
   sees elsewhere. Add the counts to the public data (`site_data` / `/site-data.json`) and render
   them on the landing capability band + `/status`. This is the part that actually resolves the
   owner's confusion, and it needs the React pages (can't edit the handoff `app.js`).
2. **Slash under-coverage (scoped INVESTIGATE, not in this plan's happy path).** The static scan
   finds 25 slash vs 71 live — the website under-documents slash commands. Root cause is almost
   certainly **dynamically-registered app commands / context menus** the AST can't see, so the fix is
   runtime-aware counting (or a documented approximation), **not** a one-line `scan_commands.py` tweak.
   Track via BUG-0023; give it a focused session, never an unattended wide-blast data regen.
