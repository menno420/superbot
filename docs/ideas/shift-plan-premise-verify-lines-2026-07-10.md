# Idea — shift-plan / scout-report items carry a one-line `verify:` premise command

> **Status:** `ideas` — not a plan, not approval. Captured 2026-07-10 (Q-0089 session
> ender, overnight shift session D / PR #1920).
> **Subsystem:** none (agent workflow — scout reports, overnight shift plans, band plans)

## The gap (observed live this session)

The 2026-07-10 overnight shift plan's item **Q2** stated that 6 views "lack a justifying
comment" for their direct `discord.ui.View` extension and predicted "warning count drops
by up to 6". Both premises were stale/wrong by pick-up time: **all 6 views already carried
the justifying comment** (landed via #1871 on 2026-07-08, *before* the scout pass — the
scout apparently inferred "undocumented" from the checker's warning list, but the checker
never read comments at all, so the warning proved nothing about documentation). Session D
only caught this because Q-0120 forced a source check before editing; a less careful
session would have "re-added" comments that already existed or chased a warning-count drop
that could never happen.

This is a recurring class, not a one-off: a scout/plan is a **dated snapshot of claims**,
and downstream sessions consume it hours later, after parallel merges. The current defense
(re-read source before acting) is judgment-tier — exhortation, not mechanism.

## The idea

Every actionable item in a scout report / shift plan / band plan carries one cheap,
copy-pasteable **`verify:` line** — a command whose output confirms the item's premise
still holds at pick-up time, next to the existing "Verification:" (which confirms the
*fix*, not the *premise*). For Q2 it would have been:

```
verify: grep -L "discord.ui.View directly" <the 6 files>   # expect: 6 files listed
```

— which would have returned nothing and killed the item in five seconds. For a bug item
it is the repro command; for drift it is the checker line that shows the drift.

## Why it's worth having

- Converts "plan says X" into "plan says X, and here is the 5-second proof X still holds"
  — the Q-0120 verify-against-source instinct made mechanical and *cheap enough to always run*.
- Costs the scout almost nothing (it already ran a command to find each item — just paste it).
- Fits the existing template culture: the plan-band skill and scout prompts can require the
  line the way run reports require `⚑ Self-initiated:`.
- Failure mode without it repeats forever: plans age in hours in a multi-agent wave
  (Q2 aged ~2 days; the #1221 duplicate-PR class is the same staleness family).

## Cheapest first step

Add a `verify:` line requirement to the overnight-scout prompt template and
`docs/operations/autonomous-routines.md`'s plan-item conventions; graduate to the
plan-band skill template if it proves useful across a few shifts.
