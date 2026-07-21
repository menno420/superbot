# Idea — distinguish a *standing* PLAN BACKLOG THIN from a *newly-raised* one

> **Status:** `ideas` — captured 2026-07-21 (fiftieth Q-0107 reconciliation pass, band-#2190).
> **Class:** workflow / reconciliation-routine + run-report. Small, cheap, disposable (Q-0105).
> **Routes to:** a dispatch/tooling session (touches the routine + `current-state.md` convention),
> not a docs-only reconciliation pass.

## The observation

`⚠️ PLAN BACKLOG THIN` (Q-0164) has now fired on **three consecutive reconciliation passes** — the
48th (band-#2130), 49th (band-#2160), and 50th (band-#2190) — because superbot is **intentionally
frozen as the behavioral oracle** for `superbot-next`. There is no in-repo feature band to plan, and
there is not expected to be one until the owner re-opens product work (`NEXT-TASKS.md` item 6).

Each pass "raises" THIN afresh and lists it on the run report's `⚑ Owner-decisions needed:` line. But
the flag is not a *fresh* signal on a frozen repo — it is a **standing, intentional, owner-known
condition**. Re-alerting the owner every ~30 PRs about a state they deliberately created is
alert-fatigue: the one time THIN *should* grab attention (a real feature backlog genuinely draining
unexpectedly) is buried under the recurring benign firing.

## The idea

Give the routine a way to tell **"THIN newly raised this pass"** (real signal — the backlog just
drained) apart from **"THIN standing / carried since band-#N"** (known, intentional):

- Track a small `THIN-since: band-#N` marker (in `current-state.md` near the reconciliation marker, or
  a one-line state file the routine reads/writes).
- When a pass finds THIN and the marker already says `THIN-since: band-#<earlier>`, report it as
  **carried** — "PLAN BACKLOG THIN carried since band-#<earlier> (oracle-freeze; expected)" — and keep
  it *off* the loud `⚑ Owner-decisions needed:` line, or clearly label it `standing, not urgent`.
- When a pass finds THIN and the marker is unset (or the freeze banner is absent), report it as
  **newly raised** — the real "the owner should look now" signal — and set the marker.
- Clearing the marker when a pass finds the backlog healthy again restores the fresh-signal behavior.

## Why it's worth having

- **Reduces false-urgency owner alerts** on a deliberately-frozen repo without silencing the flag —
  the *transition* into THIN stays loud, the *steady state* goes quiet.
- **Cheap + disposable** — a one-line marker + a branch in the run-report text. No new dependency.
- **Complements** the 49th pass's idea
  ([`reconciliation-cadence-exclude-generated-prs-2026-07-19.md`](reconciliation-cadence-exclude-generated-prs-2026-07-19.md)):
  that one reduces how *often* the routine fires on artifact churn; this one reduces the *alert noise*
  of what it reports when it does fire. Both attack the same root — the reconciliation machinery treats
  a stale/known count or label as if it were a fresh event on a frozen oracle repo.

## Not doing it here

This pass is docs-only (Q-0107). Recording the idea; the implementation (routine prompt + a marker
convention + the run-report branch) is a dispatch/tooling change for a later session. Delete this file
if a future session judges the recurring THIN firing is not actually costing owner attention.
