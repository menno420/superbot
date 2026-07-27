# Plan — reconciliation-routine tooling debt (a batchable collector)

> **Status:** `plan` — a **collector** of ungated, low-risk workflow-tooling ideas that the Q-0107
> reconciliation passes keep independently surfacing. Created 2026-07-27 (52nd pass, band-#2250) to close
> a loop the 49th–51st passes each *flagged but deferred*: they proposed consolidating these ideas into a
> single dispatch-session unit, but kept minting a fresh idea file each pass instead of collecting them.
> This file **is** that consolidation. Subsystem: **S4/S5** (docs-system + ops tooling).
>
> **Not owner-gated.** Every item here is a small, offline-verifiable, self-mergeable `check_*` /
> workflow change (Q-0194 friction→guard lane) — a tooling-capable dispatch/routine session can build the
> batch end-to-end. Two items touch a **workflow** (`.github/workflows/*` / `.claude/settings.json`
> adjacent), which is owner-gated per the Q-0194 split — those are flagged **⚑ owner-gated** below and
> should be *proposed* (router DISCUSS Q) rather than self-applied unless owner-directed in-session.

## Why these belong together

All four ideas below were surfaced as Q-0089 session-enders by consecutive reconciliation passes, and
three share one root cause: **the `bot/dashboard-refresh` loop's PR churn on the frozen oracle repo**
(each refresh is a full Code Quality CI run + merge + redeploy, and 25–27 of every ~30-PR band are these
regenerations). The fourth is a friction→guard on the routine's own control-plane bookkeeping. Building
them as one unit avoids four separate half-context tooling PRs and lets the executor see the shared root.

## The collected items (highest-leverage first)

1. **Coalesce/debounce the dashboard-refresh loop** — ⚑ owner-gated (touches a workflow) —
   [`ideas/dashboard-refresh-coalesce-loop-2026-07-25.md`](../ideas/dashboard-refresh-coalesce-loop-2026-07-25.md).
   The producer-side fix at the root: replace the per-change refresh PR with one rolling amend-in-place PR
   / a daily digest / skip-if-diff-is-noise, cutting the repo's dominant Actions cost at its source. This
   is the highest-value item and the one that shrinks every future band.
2. **Exclude generated PR classes from the reconciliation cadence counter** — self-mergeable `check_*`
   change — [`ideas/reconciliation-cadence-exclude-generated-prs-2026-07-19.md`](../ideas/reconciliation-cadence-exclude-generated-prs-2026-07-19.md).
   Consumer-side complement to item 1: teach `check_reconciliation_due.py` to skip
   `bot/dashboard-refresh` + Dependabot PRs so a docs-reconciliation pass (which costs owner attention)
   fires on real drift, not artifact churn. Independent of item 1 — worth doing even if the loop isn't
   coalesced.
3. **Control-plane confirmation-marker staleness guard** — self-mergeable warn-only `check_*` —
   [`ideas/control-plane-marker-staleness-guard-2026-07-27.md`](../ideas/control-plane-marker-staleness-guard-2026-07-27.md).
   Turns the ~30-pass silent staleness of the `ROUTINE_PAT` "re-confirmed through #N" marker (hand-fixed
   in the 52nd pass) into a soft check that flags when the marker falls more than one cadence-step behind
   the live reconciliation marker.
4. **`PLAN BACKLOG THIN` — distinguish standing vs. newly-raised** — self-mergeable `check_*` / doc-convention —
   [`ideas/reconcile-thin-flag-standing-vs-newly-raised-2026-07-21.md`](../ideas/reconcile-thin-flag-standing-vs-newly-raised-2026-07-21.md).
   So a *standing* THIN condition (the intentional oracle-freeze) reads differently from a *newly-raised*
   one (a genuine backlog drain the owner should act on) — the freeze makes the flag fire every pass, which
   dulls its signal.

## Suggested build order

Items 2, 3, 4 are pure stdlib `check_*` changes and can ship as **one docs-tooling PR** (all three are
warn-only / cadence hygiene, none runtime). Item 1 is the owner-gated workflow change — **propose it
separately** (router DISCUSS Q or an owner-directed session) since it alters merge/CI behavior. Splitting
this way keeps the self-mergeable batch clean and isolates the one item that needs owner sign-off.

## How new items join

When a future reconciliation pass surfaces another routine-tooling idea rooted in the same class of
friction, **add it here** (with its idea-file link) instead of leaving it to drift as a standalone
capture — that is the whole point of this collector.
