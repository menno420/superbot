# 2026-07-07 — Program websites: design system + botsite v2 + console shell (Fable session 1/4)

> **Status:** `complete`
> **Branch:** `claude/website-design-brief-ryc3do` · **PR:** #1802 · **Model:** Fable 5 / ultracode
> **Brief:** [`docs/planning/website-design-fable-brief-2026-07-07.md`](../docs/planning/website-design-fable-brief-2026-07-07.md) (Q-0253 last-Fable-day design session; Q-0241 never-wait)

## What happened (the brief's four mandates, in order — all shipped)

1. **The program design system** (`botsite/ds/`) — semantic tokens (dark-first + a full light
   theme), the component library (nav/buttons/cards/tables/stat tiles/charts/forms/
   empty-error-pending lanes/command palette/timeline/status), `ds.js` runtime (theme manager,
   icons, dataviz-spec chart renderers, accessible ⌘K palette), and the **living style guide at
   `/design`** rendering every token + component from the real CSS. Chart/status palettes
   validated with the dataviz skill's validator against the real surfaces, both themes.
2. **Botsite v2** (`botsite/site/v2/`, served at `/v2`) — the improved public site on the system
   over the real `site.json`: full **43-feature catalogue** with per-feature pages + area hubs
   (v1 collapsed these into 9 cards), filterable commands browser (area/permission/status +
   group-by-area), global command palette, real light theme, real build provenance, suggestion
   CTAs that reach the **real `/submit` intake** (with `?about=` context carried — v1 kept
   suggestions in localStorage where nobody ever saw them), honest counts (registered vs
   documented), honest status page (fabricated latency/uptime/60-day strips REMOVED). v1's three
   design-owned files untouched; **v1 stays the default at `/` until the owner sets
   `BOTSITE_FRONTEND=v2`** on the Railway botsite service.
   SBDATA extended additively (FEATURES/BUILD/COUNTS/ADD_URL) behind the frozen v1 export line.
3. **The program console** (`/console`) — the one-glance page: REAL lanes (session run-report
   feed with ⚑ self-initiated flags + filters, ideas/bugs counters with honest open-bug states
   parsed from the bug book's verdict convention, deploys/changelog + build) and **declared**
   pending lanes (Q-0248/Q-0249 telemetry, gate-5 parity, Q-0251 trading) that name their future
   feed — no fake data anywhere, incl. feed-cap saturation disclosure ("60+ sessions, last 5d").
   New `console` export target → `botsite/data/console.json`, whitelist-by-construction
   (Q-0178-consistent: repo-public families only); the default export keeps it fresh via the
   existing dashboard-refresh routine.
4. **Sim-informed UX checks** (`tools/web_ux/`) — the Playwright task-success checklist (10
   canonical user tasks with interaction budgets), nav-coverage sweep, perf budgets, and
   rendered-page a11y budgets (landmarks/labels/contrast, both themes) + the screenshot tool.
   **ALL PASS** at close; the harness caught real bugs on its first runs (light-theme ink-4
   contrast 2.7:1, console flex overflow).

**Verification (the "well functioning" half):** live app + 72 screenshots (12 pages × 2 themes ×
3 widths) ×3 rounds; a 25-subagent **verification fleet** (5 lenses → adversarial verify) produced
40 findings, ~20 real ones fixed (hash-router crash on malformed URLs, invisible focus ring,
combobox lifecycle, full-page aria-live dump, 568px ghost page width → exact 375, fabricated
status history removed, /submit context wired, CodeQL path-injection ×3). Full record + proof:
[`docs/planning/website-v2-verification-2026-07-07.md`](../docs/planning/website-v2-verification-2026-07-07.md).

## Decide-and-flag register (⚑ vetoable, none blocking)

- ⚑ **No build step** kept for the DS + v2; React-migration plan → `historical`.
- ⚑ **Console rides the botsite service** at `/console` (brief's recommendation; moves at
  kit-extraction); its feed is a new whitelisted export, dev-value families excluded.
- ⚑ **`/` flip is owner-paced** via `BOTSITE_FRONTEND=v2` (v2 reviewable at `/v2` on deploy).
- ⚑ **Stat-tile neon values** kept (brand anchor) — deliberate dataviz deviation, documented.
- ⚑ **`/submit` GET prefills from `?about=`** (title only, escaped, capped).

## ⚑ Self-initiated

None beyond the brief's scope — all four mandates were owner-directed; the fix wave and doc
updates (README v2 section, React plan supersede note, S1 pointer refresh, status-donut idea
progress note) are contained follow-through of that scope.

## 💡 Session idea (Q-0089)

**`web-ux.yml` — a manual-dispatch CI job for the web-UX harness.** `tools/web_ux/` is
local-only today (CI doesn't install Playwright/botsite deps). A `workflow_dispatch`-only job
(install `botsite/requirements.txt` + `playwright`, run `check_web_ux.py`, upload the screenshot
set as an artifact) would give the owner one-click rendered proof on any PR touching `botsite/`
— the same pattern as the BTD6 data-refresh workflow (Q-0049). Genuine because this session's
harness caught 3 real regressions that no existing CI check would have seen.

## ⟲ Previous-session review (Q-0102)

The previous session (#1800/#1803 band — the reconciliation pass + program launch-index prep) did
its job cleanly: the launch index pointed this session at one brief with a complete reading route,
which made orientation genuinely fast (~15 min to first push). What it could have done better: the
brief's "attach screenshots to the PR/run report" instruction had no stated *mechanism* — this
session had to invent the curated-assets-in-docs pattern (`docs/planning/assets/…`).
**Workflow improvement:** briefs that demand rendered proof should name the destination
convention; the verification-record + assets-dir pattern used here is now a copyable precedent.

## Docs audit (Q-0104)

- New docs reachable: verification record ← `botsite/README.md` + S1 queue; assets under
  `docs/planning/assets/website-v2-2026-07-07/`. React plan carries a supersede pointer.
- Drift fixed on sight (Q-0166): S1's stale React-migration next-pointer → v2 rollout;
  status-donut idea gained its progress note; `check_current_state_ledger --strict` green at close
  (this PR itself is the benign newest-merge lag; the next recon adds it).
- Friction → guard (Q-0194): the two footguns this session hit are both now *enforced* — the
  data.js/site.json desync after a main merge is caught by the existing sync test (it fired,
  correctly), and front-end regressions are caught by the new `tools/web_ux` harness (checker
  tier; carries the Q-0105 provenance/kill-switch header).

## Close-out

Shipped in PR #1802 (auto-merge armed; merge = deploy). Owner's reaction surface: browse `/v2`,
`/design`, `/console` on the botsite Railway URL after merge; flip `BOTSITE_FRONTEND=v2` when
satisfied; veto anything ⚑ above by saying so.
