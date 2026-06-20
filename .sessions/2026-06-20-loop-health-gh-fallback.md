# Session — `check_loop_health.py` gh-absent REST fallback + plan-homing guard

> **Status:** `complete`
> **Branch:** `claude/funny-franklin-3m7tvn`
> **Run type:** `routine · dispatch`
> **PR:** #1174

## Arc

Scheduled dispatch fire, no work order → advanced the next ungated plan slices from current-state
▶ Next action (band-#1170 queue). Shipped two cohesive ungated stdlib-guard slices in one PR.

## What I did

**Slice 1 — `check_loop_health.py` gh-absent REST fallback** (executes
[`planning/loop-health-gh-fallback-plan-2026-06-20.md`](../docs/planning/loop-health-gh-fallback-plan-2026-06-20.md),
candidate (a) in ▶ Next action):
- Refactored the issue fetch behind a `fetch_issues()` provider seam: `_fetch_via_gh()` (renamed,
  unchanged) → `_fetch_via_rest()` (new, stdlib `urllib`, authed `GITHUB_TOKEN`/`GH_TOKEN`) →
  actionable SKIP that names the manual MCP read. Pure `classify()` core untouched.
- Labels the verdict source (`via gh` / `via REST` / `SKIP`) in both prose and `--json`.
- So the control-plane ROUTINE_PAT row becomes **script-verifiable in the routine container**
  (where `gh` is absent but a token may be set), not only a manual MCP read no checker can see.
- Tests: +6 cases covering the selection seam (mocked, no live network) and the REST `user.login`
  field mapping.

**Slice 2 — `scripts/check_plan_homing.py`** (promotes idea
[`ideas/plan-homing-guard-2026-06-19.md`](../docs/ideas/plan-homing-guard-2026-06-19.md),
candidate (b); **⚑ self-initiated** idea→build, Q-0172):
- Asserts every live `plan`-badged doc under `docs/planning/` is linked from a **routing** doc
  (roadmap / a folio / current-state / the plan index) — the *routing* complement to
  `check_docs`'s *reachability* (which a sibling-plan-only link already satisfies, the gap that let
  the dashboard cluster drift ~30 PRs).
- Report-only default; `--strict` for the reconciliation cadence; wired into the routine prompt
  STEP 2 (after replanning) + the `## See also` tooling list.
- First run: **all 36 live plans already homed** → the guard is now the preventive regression net.
- Tests: 7 cases (helpers + tmp-tree homed/unhomed split + a real-tree guard that all live plans
  stay homed).

**Drift fixed on sight (Q-0166):** rebadged the loop-health plan + the plan-homing idea to
`historical`/✅SHIPPED in place (plan-index ship convention); updated `ideas/README.md`; noted the
REST fallback in the routine prompt's CONTROL-PLANE step.

## Verification
- `python3.10 scripts/check_quality.py --full` → green (10968 passed, 44 skipped).
- `python3.10 scripts/check_architecture.py --mode strict` → 0 errors (warnings pre-existing).
- `check_plan_homing.py --strict`, `check_docs.py --strict`, `check_current_state_ledger.py
  --strict` → all green.

## Handoff (↪ next dispatch)
current-state ▶ Next action is sharpened: candidate (a) loop-health fallback **SHIPPED**, (b) now
has one of four guards built (`plan-homing`). Remaining ungated startables: the other three small
guards (`band-pr-merge-status-helper` · `public-data-contract-field-snapshot` ·
`governance-files-presence-guard`), or a substantial `needs-hermes-review` lane (consistency-linter
AI-nav PR 1 · procedures→skills Batch 2). **Honest caveat carried forward:** in *this* dispatch
container both `gh` and `GITHUB_TOKEN` are absent, so `check_loop_health.py` still SKIPs *here* — the
REST fallback only produces a verdict where a token is present (Actions / a token-provisioned routine
container). That's the Q-0089 idea below.

## 💡 Session idea (Q-0089)
**`scripts/check_env_capabilities.py` — a one-line routine-container capability probe.** This run
surfaced that the dispatch container has neither `gh` nor `GITHUB_TOKEN`, so even the new REST
fallback SKIPs here; a session only learns this by trial. A tiny stdlib probe reporting which of
`{gh, GITHUB_TOKEN/GH_TOKEN, outbound-network}` are present would let a session (and the routine
prompt) know up-front whether control-plane reads will produce a verdict or a SKIP — turning a
silent capability gap into a one-glance readout. Cheap, read-only, disposable (Q-0105). Captured as
a forward idea (not built this run; dedup-grep of `docs/ideas/` found no existing
env-capability-probe idea — `scan_env_usage.py`/#969 maps *where env vars are used in source*, a
different axis from *what's present in this container at runtime*).

## ⟲ Previous-session review (Q-0102)
Reviewed `2026-06-19-website-split-next-steps-handoff.md` (docs-only handoff persisting the website
rollout state). **Did well:** it correctly recognised that a *verbal* handoff evaporates and made it
a durable, `check_docs`-reachable doc anchored from current-state — exactly the anti-drift instinct
the system rewards. **Could improve / system note:** it captured three forward ideas (web-CI matrix,
MCP-PR conflict-guard gap, per-command status granularity) *in the handoff doc* rather than as
`docs/ideas/` files — which means they're reachable but **not in the idea backlog the grooming pass
and `check_plan_backlog` count**. The system improvement this surfaces: forward ideas dropped in an
ops/handoff doc should be cross-filed into `docs/ideas/` (or the handoff doc indexed by
`ideas/README.md`) so they enter the idea→plan pipeline instead of resting in a doc only that lane
reads. (Today's run is the mirror of the good half: the plan-homing idea *was* in `docs/ideas/`, so
it was visible as a buildable candidate and got built.)

## 📋 Doc audit (Q-0104)
- Ledger: `check_current_state_ledger.py --strict` green (no new merged PRs to record yet; #1174
  records on merge).
- Reachability/badges: `check_docs.py --strict` green; new idea/plan badges valid (`historical`).
- New tooling reachable: both guards listed in `autonomous-routines.md` `## See also` + STEP 2.
- No owner decision taken this run (router untouched).

## 📤 Run report
- **Did:** shipped 2 ungated stdlib guards — `check_loop_health` REST fallback + `check_plan_homing`. · **Outcome:** shipped
- **Shipped:** #1174 — loop-health gh→REST fallback (control-plane row script-verifiable) + plan-homing guard (every live plan on a routing doc); both stdlib/disposable, full CI green.
- **Run type:** `routine · dispatch`
- **⚑ Owner decisions needed:** `none`
- **⚑ Owner manual steps:** `none`
- **⚑ Self-initiated:** `check_plan_homing.py` — promoted [`ideas/plan-homing-guard-2026-06-19.md`](../docs/ideas/plan-homing-guard-2026-06-19.md) → build with no dispatch/owner ask (Q-0172). (Slice 1 was an already-promoted plan, not self-initiated.)
- **↪ Next:** remaining (b) small guards (`band-pr-merge-status-helper` · `public-data-contract-field-snapshot` · `governance-files-presence-guard`) or a substantial `needs-hermes-review` lane; OR build the Q-0089 `check_env_capabilities.py` probe.

## 📊 Telemetry
| metric | value |
|---|---|
| PRs | 1 (#1174) |
| slices shipped | 2 |
| new scripts | 1 (`check_plan_homing.py`) |
| new tests | +13 cases (6 loop-health + 7 homing) |
| bugs fixed | 0 (no OPEN bug was an ungated slice) |
| self-initiated | 1 (plan-homing guard) |
| CI mirror | green (10968 passed) |
