# Idea — a staleness guard on the Control-plane "re-confirmed through #N" marker

> **Status:** `ideas` — capture only. **Not a plan, not approval.** Session idea (2026-07-27, Q-0089,
> from the fifty-second band-#2250 reconciliation pass). Workflow/tooling. Quick-win, disposable (Q-0105).
>
> **▶ COLLECTED (2026-07-27, 52nd pass) → [`planning/routine-debt.md`](../planning/routine-debt.md) item 3**
> (self-mergeable warn-only `check_*`; ships in the batch's docs-tooling PR).

## The observation

`docs/operations/autonomous-routines.md` § "Control-plane state" row 1 (`ROUTINE_PAT`) carries a manual
running list — *"Re-confirmed every reconciliation pass since: … #1264 (band-#1260 pass, 2026-06-21)"*.
The routine's STEP 2 control-plane step asks each pass to keep that row current. In practice the list
**silently stalled at #1264 and went ~30 passes (#1260 → #2250) without an update**, even though the
loop demonstrably kept self-firing every band (each auto-opened `reconcile` issue stayed
`menno420`-authored). The table did not *lie* — the loop never actually drifted — but the row's freshness
claim did, and nothing caught it. This pass fixed it by capping the list with a "continuously
re-confirmed through #2251" note.

This is exactly the Q-0194 *friction → guard* shape: a manual "keep this marker current" instruction
that depends on every agent remembering is the failure mode the doctrine says to convert into an
enforcing check.

## The idea

Add a tiny stdlib checker (or fold into `check_reconciliation_due.py` / `check_docs.py`) that asserts the
Control-plane confirmation marker is **not more than one band stale**: parse the highest `#N (band-#M
pass, …)` token in the `ROUTINE_PAT` row and warn (soft, like the supersede-banner warnings) when the
live reconciliation marker (`Last reconciliation pass: PR #X`) is a full cadence-step (30) ahead of it.
That way the drift I hand-fixed today becomes self-catching: the next pass that forgets to re-confirm
gets a visible nudge instead of a silently-aging freshness claim.

Scope note: keep it **warn-only** (never a CI red) — the underlying fact (loop self-fires) is verified
elsewhere and a stale *note* is a docs-hygiene issue, not a control-plane failure. Complements, not
duplicates, `loop-health-gh-unavailable-fallback-2026-06-19.md` (that idea is about *probing* the live
control-plane when `gh` is absent; this one is about *the doc marker's freshness* regardless of probe
availability).

## Why it's worth having

Turns a recurring "did anyone update the marker?" manual step into an enforcing guard — one less thing
the reconciliation routine relies on an agent to remember, which is the whole point of the
self-improving loop.
