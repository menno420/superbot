# Plan — Usage-limit-aware routines and orchestrations

> **Status:** `plan` · structured 2026-07-08 (grooming wave-1 lane C, PR #1845) from
> [`../ideas/usage-limit-aware-routines-2026-07-07.md`](../ideas/usage-limit-aware-routines-2026-07-07.md)
> (session idea 2026-07-07, Q-0089, kit-lab founding-plan session PR #1804).
> **Sector:** S5 operations / routine fleet · kit-lab loop (founding plan §6).
> Not yet built — routing/structure only; no owner gate (all slices are reversible docs/tooling).

## Problem (observed live, 2026-07-07)

A 4-lane adversarial-review workflow died mid-flight on the account's 5-hour usage limit: all
four lanes returned `You've hit your session limit · resets 5:40pm (UTC)` and the workflow
completed "successfully" with an **empty result set**. Nothing today distinguishes
"limit-exhausted, retry after HH:MM" from a real agent failure. As the fleet moves to *more*
scheduled autonomy (dispatch, docs-reconciliation, the kit-lab loop, the trading repo's
routines), each limit collision silently wastes a firing — the owner sees a silent no-op or an
abandoned partial run, and a limit-killed lane can be miscounted as "ran clean."

## Design (three layers, from the idea — kept as-is, sequenced)

1. **Routine-prompt clause** — every saved routine prompt gains: *"if your work dies with a
   usage-limit error, do not error out or write a failure report — schedule a self check-in
   (`send_later`) at the stated reset time + 2 min, note `limit-deferred` on the run report,
   and resume there."*
2. **Orchestration rule** — coordinators treat the limit-error string as a **distinct failure
   class**: re-arm instead of diagnosing, and **never count limit-killed lanes as evidence**
   that a lane ran clean.
3. **Fleet telemetry** — a greppable `limit-deferred:` counter line in run-report footers, so
   exhausted windows become spend-planning data for the Q-0248/Q-0249 ~2-month observation
   window.

## PR breakdown (2 PRs, per the 2–3-PR rule)

### PR 1 — the conventions (docs-only, ungated, ship anytime)

- Add the layer-1 clause to every saved routine prompt in
  `docs/operations/autonomous-routines.md` (dispatch · docs-reconciliation · any newer
  routine registered there), plus one short **"Usage-limit failures"** subsection defining:
  the error signature to match, the `limit-deferred` run-report token, and the
  `send_later`-at-reset+2min re-arm recipe.
- Record the layer-2 orchestration rule in the multi-agent workflow doc the coordinators
  actually read (`docs/owner/ai-project-workflow.md` — the fan-out/synthesis section):
  limit-killed lanes are `limit-deferred`, never evidence lanes.
- Cross-link from the kit-lab founding plan §6 loop prompt so the standing A/B routine is
  born limit-aware (its firings are exactly the unattended kind a collision would waste).

### PR 2 — the counter (small stdlib tool, disposable per Q-0105)

- `scripts/count_limit_deferrals.py`: grep `.sessions/` + routine run reports for
  `limit-deferred:` tokens and emit one summary line (count · dates · routine names) —
  the feed into the Q-0248/Q-0249 spend dataset. Warn-only, provenance header, delete if
  unused after the observation window.
- Optional same-PR: one line in the reconciliation pass record template ("limit-deferred
  firings this band: N") so the number is trended per band, not re-derived.

**Not in scope:** any `.claude/settings.json` / hook wiring (none needed — this is prompt +
docs + one script); retry *caps* (covered by `executor-chain-trigger-via-workflow-2026-06-15`,
a distinct concern, dedup-verified in the idea).

## Kit portability (follow-up, rides a kit release)

The clause + failure-class rule are project-agnostic and belong in the substrate-kit's routine
templates once superbot upgrades from a real kit release — flag it in the kit-lab plan rather
than editing `substrate-kit/` templates from this lane.

## Verification

- PR 1: `python3.10 scripts/check_docs.py --strict` (links resolve); manual read of each
  edited prompt for the clause.
- PR 2: run the counter against the live `.sessions/` tree; it must find zero false positives
  on historical logs before the token exists, and find a seeded fixture token in tests.
- Ground truth (Q-0105): after the next real limit collision, confirm the routine actually
  re-armed and the counter counted it — graduate the convention only on that proof.
