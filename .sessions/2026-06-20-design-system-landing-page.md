# 2026-06-20 — Design-system: full landing-page composition + hybrid edit loop

> **Status:** `complete`

## Arc

Owner is trying out **Claude Design** and kept hitting *"Can't save this edit — element
isn't from project source"* when editing the hero. Root cause: after #1168 only the 6 atomic
components from `design-system/` are source-backed; the hero / nav / section layout are
generated canvas content with **nowhere in source to save to**. Owner chose **Path 1** —
expand the design-system so the **whole landing page** is real, source-backed components, and
tighten the **hybrid Claude Code + Claude Design workflow** (Claude Code as porter/reviewer;
preview without merge+redeploy each iteration).

Owner directive this session: *"anything documented in the repo is based on the situation when
we documented it — good guidelines, not 100% strict rules. Do what's best for the vision:
correctness over temporary fixes, stability first."*

## What shipped (this PR — #1175)

New `design-system/src/` components, all faithful to `botsite/` (same Tailwind palette):

- **Layout / chrome (mirror `base.html`):** `PageShell` (dark canvas + centered `<main>`),
  `SiteHeader` (sticky nav · logo · links · status dot · Add-to-Discord), `SiteFooter`
  (generated/as-of-last-deploy badge + source link).
- **Sections (mirror `index.html`):** `Hero`, `CapabilityBand` (3 × `StatTile`), `Section`
  (title + action link, or centered), `StepCard` (how-it-works).
- **`ButtonLink`** — an anchor styled as a button (how the live site actually renders CTAs);
  `Button` refactored to share its style via an exported `buttonClasses` (output identical).
- **`LandingPage`** — the whole `index.html` composed from the parts, with sample-data
  defaults so it renders standalone. **The canonical surface Claude Design edits**, mapping
  1:1 onto the live page → every region now has somewhere in source to save to.
- A **Storybook story per new component** + a full-page `Pages/LandingPage` story (the
  `/design-sync` preview source).
- **`design-system/README.md`**: regrouped components table + a new "hybrid loop" section
  (Claude Design canvas ⇄ Claude Code porter/reviewer) and **preview-without-redeploy**
  guidance (Storybook for the design layer; `uvicorn` for the real Jinja site).
- **`.github/workflows/design-system-ci.yml`** — the JS CI leg the #1168 session flagged:
  `npm ci` + `typecheck` + `build`, path-scoped to `design-system/**`, twin of
  `botsite-ci` / `dashboard-ci`. Uses the runner's preinstalled Node (only the SHA-pinned
  `actions/checkout`, no unpinned `setup-node`). Non-required check.

**Production stays Jinja.** This library feeds Claude Design; canvas output is ported back
into `botsite/` by Claude Code. Additive + isolated — nothing imports `design-system/`,
Python CI untouched.

## Verification (in-container)

- `npm run typecheck` (`tsc --noEmit`) → **clean**.
- `npm run build` (tsup + tailwind) → **exit 0**; `dist/index.js` 3.5 KB → **13.5 KB**
  (new components), `dist/index.d.ts` 10 KB, `styles.css` rebuilt.
- `check_docs --strict` → pass (377 docs reachable); `check_current_state_ledger --strict`
  → pass (last 15 merged PRs present). Arch checker not applicable (no `disbot/` change).
- `design-system-ci.yml` runs on this PR (path match) — **UNVERIFIED first run**; mirrors the
  local typecheck+build, which are green.

## Decisions made alone (ratify if wrong)

- **`ButtonLink` + `buttonClasses`** — added an anchor-button rather than make `Button`
  polymorphic; the live site renders CTAs as `<a>`, so this is the faithful element. `Button`
  output is byte-identical (pure refactor to share the class string).
- **`design-system-ci.yml` uses the runner's preinstalled Node** (no `setup-node`) — chosen
  because the GitHub API was rate-limited (couldn't fetch a pin-able `setup-node` SHA) and the
  repo's hygiene is SHA-pinned actions only. Keeps the only action (`checkout`) pinned.
- **`LandingPage` defaults** mirror the *current* indigo `botsite/` (not the owner's green
  canvas exploration) and use sample counts (308/36/8) — the live site overrides via props.

## Context delta (reflection interview)

- **Needed but not pointed to:** `design-system/README.md` is the canonical contract for the
  Claude Design loop, but it's package-local — not in `docs/`, the AGENT_ORIENTATION route, or
  `current-state`'s "where to read next". Found it by glob. Also reverse-engineered that
  `code-quality.yml` has **no `paths` filter** (always runs + reports green for non-Python
  PRs) and runs the session gate — so a design-system-only PR *can* reach green.
- **Pointed to but didn't need:** the three binding docs (architecture/ownership/runtime) +
  CodeGraph stats — all Python-layer, inert for a `design-system/` (JS) change.
- **Discovered by hand:** `pull_request` workflows **do** fire on the MCP-created PR here
  (Code Quality/CodeQL ran on commit 1) — the "app-token PR doesn't trigger workflows" worry
  did not apply to required checks; only the auto-merge *enabler* needs the manual
  `enable_pr_auto_merge` (Q-0127), which I did.
- **Weak point / known limits:** `design-system-ci.yml` is UNVERIFIED (confirm green a few
  times). LandingPage defaults are sample data, not live counts. Components mirror today's
  indigo site by design; the owner's new look gets ported when finalized.
- **Most-helpful change:** route web/site/Claude-Design tasks to `design-system/README.md`
  from orientation (below).

## ⟲ Previous-session review (Q-0102)

Reviewing #1168 (the session that built the 6-component library). **Did well:** diagnosed
*why* `/design-sync` no-op'd (no JS library) before building, and left a precise follow-up
list — "port canvas output back into Jinja" + "add a JS CI leg" — which made *this* session a
straight execution. **Missed:** it shipped only atoms, so the page chrome the owner actually
clicks (hero/nav) wasn't editable — the exact "can't save" wall the owner hit. The atoms were
necessary but not sufficient for the stated goal (edit the page). **Concrete system
improvement (done-adjacent):** add a one-line pointer from `docs/AGENT_ORIENTATION.md` (web /
site task route) to `design-system/README.md` so the next agent is *routed* to the Claude
Design contract instead of discovering it by glob — captured as a groom item; small enough to
land next session.

## 💡 Session idea (Q-0089)

**A `botsite/` ⇄ `design-system/` parity guard.** The README's rule "keep the components in
sync with the templates so designs stay shippable" is enforced by nothing — drift between a
component's Tailwind classes and the Jinja it mirrors silently makes a ported design wrong. A
small test/script (e.g. assert each documented component↔template mapping exists, or compare
the canonical class strings) would turn that rule into a guard, protecting the hybrid loop.
Dedup-checked: no existing `docs/ideas/` entry mentions design-system / Claude Design / parity.
(File under `docs/ideas/` next grooming pass if not built sooner.)

## 📊 Doc audit (Q-0104)

- Hybrid workflow + components durable in `design-system/README.md`; owner Path-1 decision in
  this log + the active-work claim. `check_docs --strict` + `check_current_state_ledger
  --strict` green. The merged-PR ledger entry for #1175 lands via the next reconciliation/
  grooming pass (the PR isn't merged at log-write time — strict ledger check correctly doesn't
  require an unmerged entry).

## 📤 Run report

- **Did:** expanded `design-system/` so the whole bot-site landing page is source-backed
  components Claude Design can edit (`LandingPage` + chrome + sections), documented the hybrid
  Claude Design ⇄ Claude Code loop + preview-without-redeploy, and added the design-system CI
  leg. · **Outcome:** built + verified (typecheck/build green); PR #1175 open, auto-merge armed
  on green.
- **Shipped:** #1175 — design-system full landing-page composition + hybrid edit loop + JS CI.
- **Run type:** `manual` (owner-directed, interactive — Path 1).
- **⚑ Owner decisions needed:** `none`.
- **⚑ Owner manual steps:** optional — run `/design-sync` to upload the expanded components to
  Claude Design, then design against the full `LandingPage`; tell Claude Code to port the
  result into `botsite/`.
- **⚑ Self-initiated:** `design-system-ci.yml` — promoted the #1168 session's flagged JS-CI-leg
  idea to implementation without a separate dispatch (within the owner's "stability first / do
  what's best" latitude). No `docs/ideas/` file; provenance is the #1168 log + this one.
- **↪ Next:** confirm `design-system-ci` green in CI; route AGENT_ORIENTATION → design-system
  README; build the botsite⇄design-system parity guard.

## 📊 Telemetry

| Metric | Value |
|---|---|
| PRs merged this session | 0 at log-write (auto-merge fires on green; #1175) |
| CI-red rounds | 0 real (the only `code-quality` reds were the intended born-red session gate) |
| Repo-rule trips | 0 |
| New ideas contributed | 1 (botsite⇄design-system parity guard) |
| Ideas groomed | 1 (executed #1168's flagged JS CI leg → shipped) |
