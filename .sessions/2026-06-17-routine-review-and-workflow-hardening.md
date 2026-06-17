# 2026-06-17 — Routine review + autonomous-workflow hardening

> **Status:** `in-progress`
> Owner-live session. Reviewing the **first full unattended-routine day** (~20h, ~#1017–#1025
> + the band-#1020 reconciliation pass), then routing the owner's observations to their durable
> homes and applying the contained workflow fixes he steered in-session (`AskUserQuestion`,
> 2026-06-17). Born-red per Q-0133; flip to `complete` after the owner reviews the governance-doc
> edits.

## Goal

The owner's first full day back. He let the two-routine fleet run unattended from ~02:00 with no
interference and gave a brain-dump of observations. This session: **review** what the routines did,
and **map** the useful points to the repo (ideas / router decisions / config fixes), per his ask.

## Review of the 20h run (the headline finding)

The fleet did **high-quality, self-auditing work** — every log verifies CI, reviews its predecessor,
contributes an idea, and writes a run report; the reconciliation pass even pruned a self-inflicted
~2,000-word drift surface. **The one real systemic problem is exactly the one the owner spotted:**
reconciliation fires every **30** PRs but only plans the next **~9**, so the buildable queue drains
and dispatch fires start hitting "exhausted lane / plan-first / owner-paced" walls (the BTD6 floor
lane is now fully consumed). "Running out of plans" is real and has a precise, fixable cause.

## Plan (what this session ships)

- **Planning depth** — reconciliation plans the FULL band (depth ≥ the 30-PR cadence, as larger
  initiatives or more slices) + a **low-backlog flag** so a thin idea backlog triggers a dedicated
  planning session instead of filler. → `CLAUDE.md` + both routine prompts. (Q-0164)
- **Routine self-labeling** — each session log declares its run type (`routine` / `manual`);
  surfaced as a badge on the dashboard updates feed so the owner can see routine work at a glance.
  (Q-0165)
- **Drift-on-sight** — spotted ledger/docs drift is fixed immediately, not deferred to the
  reconciliation failsafe (bugs-first applies to docs). (Q-0166)
- **Updates freshness** — `dashboard.json` regenerates on every source-touching merge to `main`, so
  the updates feed stops lagging ~30 PRs behind. (Q-0167)
- **Hermes plain-language house style** — ONE sample report drafted for owner review (preview-first,
  then roll out). (Q-0168)
- **Owner review-inbox / communication website** — captured as idea + plan (build later). (Q-0169)
- **Claude skills + automation shortlist** — captured as idea. (Q-0170)

## 📤 Run report

- **Did:** reviewed the first unattended-routine day + routed the owner's observations to durable homes + applied the steered workflow fixes (planning depth · drift-on-sight · routine labels · updates freshness) · **Outcome:** shipped (merge held born-red pending owner review)
- **Shipped:** #1026 — this PR (4 applied fixes + Q-0164…Q-0171 + 4 idea / 2 plan / 1 proposal docs)
- **Run type:** manual (owner-live)
- **⚑ Owner decisions needed:** react to the Hermes house-style sample (Q-0168) · pick the next agent-tooling builds (Q-0170) · review-inbox phasing (Q-0169) is captured · Codex-review (Q-0171) needs research before a decision
- **⚑ Owner manual steps:** re-paste the two updated routine prompts (dispatch + reconciliation) into their console configs — CLAUDE.md/prompt edits only take effect once pasted
- **↪ Next:** the **repo-consistency linter** is the flagged top buildable lane (turn-key plan, one rule per PR — feeds the now-fixed plan backlog); then roll out the approved Hermes style + pick agent-tooling skills

## 💡 Session idea (Q-0089)

**Make the planning horizon and the reconciliation cadence one source of truth, with an assertion.**
This whole session's root cause was that "30" (the cadence, Q-0134) and "~9 slices" (the band-doc
planning horizon) lived in *different docs* and silently diverged for many sessions. A tiny check —
assert the reconciliation planning horizon ≥ the cadence constant, both read from one place — would
have caught the 9-vs-30 drift mechanically, the way `check_reconciliation_due.py` reads the marker.
It's the verified-signal cousin of the `check_plan_backlog.py` proposed in the agent-tooling
shortlist (Q-0170 §B). Disposable per Q-0105.

## ⟲ Previous-session review (Q-0102)

The previous workflow run — the **band-#1020 reconciliation pass** (#1020) — did its hard job well:
it reconciled five genuinely-missing ledger entries and *killed a self-inflicted ~2,000-word
bookkeeping tally* (a real durable win). **But it is also the clearest illustration of the gap this
session fixes:** it explicitly wrote "the buildable-now ungated `ready` queue is genuinely thin" and
*still planned only ~9 slices* against the 30-PR cadence — treating the drought as normal instead of
escalating it. It **observed** the running-low signal the owner later raised but had no instruction
to **flag it loudly to him** — exactly the `⚠️ PLAN BACKLOG THIN` escalation Q-0164 now adds. The
self-auditing loop worked: the predecessor surfaced the symptom; this session found the root cause.

## Doc audit (Q-0104)

`check_docs --strict` green · `check_current_state_ledger --strict` green · `check_session_log`
green · the four new ideas indexed in `ideas/README.md` · Q-0164…Q-0171 recorded in the router with
provenance · no new runtime bugs (BUG-0009 slice 3 / BUG-0011 stay OPEN — untouched).

## 📊 Telemetry

| Metric | Value |
|---|---|
| PRs merged this session | 0 (held born-red for owner review) |
| CI-red rounds | 1 (the intended born-red gate; clears on flip-to-complete) |
| Repo-rule trips | 2 (skill-builder picked up the proposal draft · invalid `proposal` badge — both fixed) |
| New ideas contributed | 1 (Q-0089, above) + 4 captured from the owner brain-dump |
| Ideas groomed | 2 promoted to executable plans (review-inbox · consistency-linter) |
