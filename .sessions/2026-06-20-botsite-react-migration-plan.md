# 2026-06-20 — Plan: make the live bot-site the React design-system app (no porting)

> **Status:** `complete`

## Arc

Continuation of the website thread (SPA wired in #1196, explainer doc in #1198). The owner asked
how it's possible for Claude Design changes to land on the live site with *less manual porting* —
they believed every change must go through Claude Code before Railway. Clarified the distinction
(commit→CI→Railway is permanent; the removable part is the *translation* between the React
`design-system/` and the vanilla live site), then the owner asked for a thorough plan to implement
later.

## Shipped (docs-only, plan)

- **`docs/planning/botsite-react-spa-migration-plan-2026-06-20.md`** (`plan`, S5) — a 2–3-PR plan to
  make `botsite/`'s live front-end **be** the built `design-system/` React app, fed by the existing
  `site.json` pipeline, so a Claude Design edit lands with **no porting**. Covers: problem framing
  (two codebases), current vs. target architecture, the **CI-build-replaces-porting** insight
  (keeps Railway Python-only), 4 owner decisions (build-in-CI vs Railway-build · `/site-data.json`
  vs `window.SBDATA` · cutover style · connector write-back), PR breakdown (foundation → serve →
  cutover/cleanup), the load-bearing invariants to preserve (no `disbot` import · secret-free ·
  single data source · no `static/` dir), risks/trade-offs, per-PR verification, and an
  implementer/routine quickstart. Also fixes the dead "Add to Discord" CTA *for free* (it's a real
  `addUrl` prop in the React pages).
- Homed in `docs/planning/README.md` (S5) → `check_plan_homing` green (40/40).

Verification: `check_plan_homing --strict` ✓ · `check_docs --strict` ✓.

## ⚑ Self-initiated

None — owner-directed (explain feasibility + write the migration plan). Planning only; no
implementation started (owner-decision gated).

## 💡 Session idea (Q-0089)

**A `check_design_data_contract` guard for the React migration:** when the live site becomes the
React app fed by `/site-data.json`, add a CI check that the page prop shapes
(`FeatureCategory`/`CommandCategoryGroup`/`BuildMeta`) stay a superset of what the data endpoint
emits — the React analogue of the `site_data` contract tests. Catches "Claude Design added a field
the data doesn't provide" before it ships a blank section. Folded into the plan (§6/§7). Lane: tooling.

## ⟲ Previous-session review (Q-0102)

The explainer-doc session (#1198) correctly surfaced the design-system↔SPA drift instead of silently
leaving it — good. **What it could have done better:** it flagged the drift but didn't yet give the
owner a *path* to resolve it; this session closes that by turning the flag into a concrete, gated
plan. **System improvement:** when a session flags a "reconcile later" drift, it should, in the same
or next step, either fix it or open a routed plan — a dangling flag with no owner-actionable next
step is how drift becomes permanent. (Done here: flag → plan.)

## 📤 Run report

- **Did:** explained why porting (not deploy) is the removable step; wrote the React-migration plan ·
  **Outcome:** shipped (docs-only, plan)
- **Run type:** `manual · owner-task (planning)`
- **⚑ Owner decisions needed:** plan §3 A–D (build-in-CI vs Railway-build · data delivery · cutover ·
  connector write-back) before implementation
- **⚑ Owner manual steps:** none (plan is implement-later)
- **↪ Next:** on owner go → execute the plan (PR1 foundation → PR2 serve → PR3 cutover); also the
  standalone "Add to Discord" wiring is subsumed by PR1
