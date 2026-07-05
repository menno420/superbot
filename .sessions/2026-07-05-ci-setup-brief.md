# 2026-07-05 — CI-setup redesign brief (owner-directed prep)

> **Status:** `complete` — deliberate final flip (born-red gate). Docs-only; `check_docs --strict`
> green.

## What this session did

The owner set the *next* session's topic — **find the best-possible CI setup** (fewer separate checks
where it helps + add genuine gaps) — and asked me to confirm I understood and prime the repo. I
confirmed with a concrete grasp of the sprawl, captured the two aiming decisions via `AskUserQuestion`
(**scope = everything end-to-end; optimize for reliability + cost**), then **inventoried the CI
landscape and wrote the scoping brief** so that session starts on the redesign, not the discovery.

## Shipped (PR #1736, docs-only)

- **[`docs/planning/ci-setup-redesign-brief-2026-07-05.md`](../docs/planning/ci-setup-redesign-brief-2026-07-05.md)**
  — the brief: mission + owner aiming decisions; a full inventory (17 Actions workflows by role · the
  `code-quality` merge-gating bundle · the 40 `check_*.py` by run-context · the hooks); the reliability
  pain points (CodeQL race, dropped-`synchronize` stalls + their compensators, cancellation/born-red
  edge cases); the cost pain points (~8 workflows/push, unfiltered app-CI, push/PR duplication); the
  genuine gaps to add (Q-0238, the two checker ideas); the **method** (inventory → classify each check
  merge-gating/advisory/routine/dev-only → consolidate toward ~one required context → add gaps into the
  right class → target-state design + phased migration); and the **owner-gated guardrail** (propose
  before ripping out — CI/hooks/branch-protection are executable config).
- **S5-ops sector** now points at the brief (the next session lands on it).

## Key findings that shaped the brief

- **8 workflows fire per push, mostly unfiltered** — the cost story; path-filtering the app-CI
  workflows (botsite/dashboard/design-system) is an obvious lever.
- **Only 5 of the 40 `check_*.py` run inside the merge gate** (`code-quality`); the other ~35 run via
  hooks/routines/ad-hoc — so "what actually gates a merge" is much narrower than the checker count
  suggests, and building the what-runs-where matrix is the session's first real task.
- **`check_ci_coverage.py` + `ci-rerun-watchdog.yml` exist only to compensate** for the dropped-
  `synchronize` CI stall — a tell that the trigger topology should be fixed at the root, not papered.
- The **CodeQL merge-race** (this week's #1728→#1730) is the headline reliability defect, already
  captured as router Q-0238 — folded into the brief as a gap to close.

## Context delta

- **Needed but not pointed to:** there was no single "CI map" doc — I had to derive the
  workflow-by-role + check-by-run-context picture from the raw `.github/workflows/` + `scripts/`
  listings. The brief now *is* that map (first draft); the session will make it authoritative.
- **Decisions made alone:** none of substance — the two session-shaping forks (scope, optimize-for)
  were put to the owner via `AskUserQuestion` and answered (everything; reliability+cost). The brief's
  *method* (aim for ~one required context) is a recommendation the session/owner can revise.
- **Flagged for maintainer:** the redesign itself is **owner-gated** (executable config) — the next
  session proposes, you ratify before destructive changes. Q-0238 is the one concrete decision already
  queued.
- **🛠 Friction → guard:** n/a this session (docs-only; nothing blocked it). The CI-setup session *is*
  the systemic friction→guard for the reliability issues we've been hitting.

## ⟲ Previous-session review (Q-0102)

Previous session = the **next-session-prep / docs-banking** run (#1735). Strong: it banked every loose
finding into a proper home and answered the substrate-kit question with a real evidence base (delegated
candidate map + grounded reads) rather than a guess, correctly catching that the kit is already
finalized. **What it could have done better:** its priority doc offered "live → Stage-2 walk /
autonomous → §7.2 or A/B" but didn't anticipate that the owner might redirect to a *different* axis
entirely (CI setup) — a reminder that a priority doc is a menu, not a prediction; the owner picks the
axis. No system change needed — the menu did its job (the owner steered).

## 💡 Session idea (Q-0089)

Rolling forward the still-unbuilt idea from #1735 (**a maintained rebuild/CI gate-state readout**) —
this session reinforces it: I again had to *derive* "what actually gates a merge" from raw listings
(now for CI, last session for the rebuild phases). The generalized idea: **a single generated
`gate-state` readout** (rebuild phase gates + CI required-checks) so no session re-derives "what's
blocking / what's required." The CI half becomes concrete once the CI-setup session builds the
what-runs-where matrix — the matrix *is* the CI gate-state source. Not filing a second idea file;
noting the reinforcement so the CI-setup session can emit the readout as a byproduct.

## 🧹 Grooming (Q-0015)

Groomed the S5-ops queue: added the owner-directed CI-setup redesign as its now-top ▶ item with a
turn-key brief — moving "improve CI reliability/cost" from scattered pain points (across several
journal rules + Q-0238) into one scoped, startable plan.

## 📋 Docs audit (Q-0104)

New `plan`-badged brief + S5 pointer; `check_docs --strict` green. The aiming decisions are recorded
in this log (the `AskUserQuestion` answers); no separate router Q needed (the topic is a directed
work-item, not a product decision — Q-0238 already carries the one embedded decision).

## 📤 Run report

- **Did:** confirmed the owner's CI-setup intent, captured the two aiming decisions, and wrote the
  scoping brief (with a first-draft CI inventory) to prime the dedicated session. · **Outcome:** shipped
- **Shipped:** #1736 — docs-only (CI-setup brief + S5-ops pointer)
- **Run type:** `manual` (owner-directed)
- **⚑ Owner decisions needed:** none new here — the CI-setup session will surface proposals to
  ratify; Q-0238 (CodeQL-in-merge-hold) remains the one already-queued CI decision.
- **⚑ Owner manual steps:** none.
- **⚑ Self-initiated:** none (owner-directed).
- **↪ Next:** the dedicated **CI-setup redesign** session — start from
  `docs/planning/ci-setup-redesign-brief-2026-07-05.md` (build the what-runs-where matrix, then the
  target-state design + phased owner-gated migration).

## 📊 Telemetry

| Metric | Value |
|---|---|
| PRs merged this session | 1 (#1736, docs-only, on green) |
| CI-red rounds | 0 (docs-only; born-red gate red is the intended hold; no CodeQL surface) |
| Repo-rule trips | 0 |
| New ideas contributed | 0 new (reinforced the #1735 gate-state-readout idea) |
| Ideas groomed | 1 (S5 CI-redesign scoped into a turn-key brief) |
