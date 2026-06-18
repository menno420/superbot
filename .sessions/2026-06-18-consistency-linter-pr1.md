# 2026-06-18 — Repo consistency linter PR 1 (harness + edit-in-place rule) + ledger reconcile

> **Status:** `complete`

## What & why
Scheduled dispatch, no work order → advance the next real plan slice. The live ▶
Next action pointed at the **fishing reconciliation** as "in flight", but a sync +
`git log` check showed it **already merged** (#1039 reconcile + #1041 Codex
follow-ups). So the reconciliation is done; its remaining Phase-1 slices (loadout
presets, value/cook/sell, catch minigame) are explicitly owner-design-gated open
questions (Q-0175 — do not decide unprompted), and the open-world Explore hub it
would surface in doesn't cleanly exist yet. Fishing is **paused on owner input**,
not a live empty-fire lane.

Two pieces this run:

### 1. Bugs-first ledger reconcile (Q-0166)
The SessionStart banner flagged 4 merged PRs missing from the living ledger.
Added #1038–#1041 to `current-state.md` § Recently shipped and **repointed the
stale ▶ Next action line** (it still called the fishing reconciliation "in
flight"). `check_current_state_ledger --strict` now clean.

### 2. Repo consistency linter PR 1 (owner-directed, Q-0170)
Built the first slice of `scripts/check_consistency.py` — the owner's "CI but
specifically for UX/interaction inconsistencies" tool ([plan](../docs/planning/repo-consistency-linter-plan-2026-06-17.md)):

- **The harness** — a `Finding` model + `Rule` registry + the
  `architecture_rules/consistency_exceptions.yml` allowlist loader (path-prefix or
  `::Class.method` scoping) + a `--mode`/`--file` CLI, all modeled on
  `check_architecture.py`'s house style. Warn-only / disposable (Q-0105) with a
  provenance + reliability header.
- **Rule 1 — edit-in-place.** In a `views/` panel button/select callback, flags a
  *new ephemeral* message (`response.send_message` / `followup.send`,
  `ephemeral=True`) when the callback **never edits in place** and the send isn't
  an early-return guard (`send; return` validation toasts are excluded — the
  correct pattern). Mixed callbacks that also `edit_message`/`edit` are skipped.
- **First-run count: 45 candidates.** Allowlist left empty (warn-only — triage in
  follow-up). Confirmed genuine signal, not pure noise: e.g.
  `DiagnosticsPanel.refresh_btn` shows "Member list refreshed" as an ephemeral
  followup instead of re-rendering the panel — a real refresh-should-edit-in-place
  inconsistency. Other hits are intended ephemeral sub-panels (allowlist material).
- **Tests:** `tests/unit/scripts/test_check_consistency.py` — positive +
  edits-in-place / guard / non-ephemeral / non-callback negatives + allowlist
  (file + method) + only-scans-views + a live-tree warn-only invariant (9 tests).

Not CI-wired (warn-first per Q-0120 until it runs clean across sessions). Next
slices: rule 2 (back-button presence), rule 3 (panel base-class).

## Verification
- `python3.10 scripts/check_consistency.py` → 45 warnings, 0 errors.
- `python3.10 -m pytest tests/unit/scripts/test_check_consistency.py -q` → 9 passed.
- `python3.10 scripts/check_quality.py --full` → green (10619 passed; formatters
  clean after black/isort on the new files).
- `python3.10 scripts/check_architecture.py --mode strict` → 0 errors (pre-existing
  warnings only; new files are under `scripts/`, outside `disbot/`).
- `python3.10 scripts/check_current_state_ledger.py --strict` → clean.

## 💡 Session idea
A **`--changed-only`** flag for `check_consistency.py` (mirroring
`check_architecture.py`) so a future pre-commit / `code-quality` wire-in can lint
only a PR's touched views — that's the cheap precondition for graduating a rule
from warn-only to a gating error without a full-tree false-positive sweep on every
run. Captured for rule-2's PR rather than now (YAGNI until graduation).

## ⟲ Previous-session review
The previous run (#1040, cog-routing pagination) was a model bugs-first catch — it
noticed a *latent* registry-drift bug (the 25-option select cap silently dropping
cogs) that no single feature PR's tests would surface, and shipped a real fix plus
a replacement guard test. Its own session idea ("an invariant that every
registry-built select paginates or provably stays ≤25") is exactly the kind of
mechanical-consistency rule the linter built this run is designed to host — so the
workflow improvement is concrete: **that idea should become rule 4 of
`check_consistency.py`** (a select-options-bound rule), turning a one-off guard
into a reusable house-rule. Logged as a candidate in the plan's rule backlog.

## Context delta
- **Needed but not pointed to:** that the ▶ Next action's "RECONCILIATION in
  flight" was already merged — only a `git log --all | grep fish` revealed it. The
  living-ledger drift class (banner flags it, but the prose ▶ line lagged). The
  sync-first + verify-against-`git log` step is what caught it.
- **Pointed to but didn't need:** the long historical tail of the ▶ Next action
  callout (band-#930/#900/#870 snapshots) — the live first sentence + Recently-
  shipped were sufficient, as the doc itself says.
- **Discovered by hand:** the "Explore hub" the fishing plan names as fishing's
  home (`cogs/mining/exploration.py`) doesn't exist — exploration is
  `utils/mining/exploration.py` surfaced via the mining main panel's 🗺️ Explore
  button. The plan's hub target is aspirational, not a current seam.
- **Decisions made alone:** scoped rule 1 to `views/` only (not cogs) and to
  `ephemeral=True` sends specifically (the owner's literal example), excluding
  early-return guards — to keep first-run noise to a defensible 45, warn-only.
  Reversible (it's a read-only tool); broaden via the YAML / future rules.

## 📤 Run report
- **Did:** shipped consistency-linter PR 1 (harness + edit-in-place rule, 45
  candidates surfaced) + reconciled 4 ledger-drift PRs and repointed ▶ Next action ·
  **Outcome:** shipped
- **Shipped:** #1042 — `scripts/check_consistency.py` PR 1 (warn-only) + ledger reconcile
- **Run type:** `routine · dispatch`
- **⚑ Owner decisions needed:** none new. (Standing: fishing Phase-1 mechanics —
  loadout presets / value / minigame — are Q-0175 open questions awaiting the owner
  before fishing can advance.)
- **⚑ Owner manual steps:** none
- **⚑ Self-initiated:** none — the linter is owner-directed (Q-0170) off an
  existing executable plan; the ledger fix is mandated bugs-first work.
- **↪ Next:** consistency-linter rule 2 (back-button presence) then rule 3 (panel
  base-class); triage the 45 edit-in-place candidates into real fixes vs allowlist
  entries. Fishing stays paused on owner input (Q-0175 open questions).

## 📊 Telemetry

| Metric | Value |
|---|---|
| PRs opened | 1 (#1042) |
| New tool / rules | 1 tool, 1 rule |
| Tests added | 9 |
| Linter candidates surfaced | 45 (warn-only) |
| Ledger PRs reconciled | 4 (#1038–#1041) |
| Full suite | 10619 passed, 38 skipped |
| New arch errors | 0 |
