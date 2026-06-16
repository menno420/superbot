# Idea: close the idea-spotlight loop — track the owner's verdicts

> **Status:** `ideas` — **session idea (2026-06-16, Q-0089, from the idea-spotlight skill PR #959).**
> Not approved, not a plan. Source + the binding contracts win.

## The gap

The new `superbot-idea-spotlight` skill surfaces one active idea per day and asks the owner to
**report a verdict** (build / roadmap / discuss / drop / expand). But the **selection** side
(`scripts/hermes/idea_spotlight.py`) only knows "active vs terminal" — it has **no memory of what
the owner already decided**. So an idea the owner routed to *roadmap Later* (still `ideas`-badged,
not `historical`) can resurface as the spotlight a few days later, and there's no measure of whether
the daily ritual is actually **draining** the backlog.

## The idea

Give the spotlight a tiny **verdict ledger** so the loop closes and is measurable:

1. **Record** each owner verdict (the `intake` route the EOD reply takes) to a small append-only
   log — e.g. `docs/owner/idea-spotlight-log.md` (or a `.jsonl`): `date · idea-file · verdict ·
   one-line note`. The reply already flows through `intake`; this just persists the outcome.
2. **Bias selection** in `idea_spotlight.py`: deprioritise (or skip for N days) any idea with a
   recent verdict, so the daily pick favours **un-decided** ideas — the backlog actually drains
   instead of re-offering settled ones.
3. **Measure** it: a weekly line in the morning briefing — "ideas decided this week: N · backlog:
   M active" — the human mirror of the grooming drain-rate (gap-analysis §4 telemetry theme).

## Why it matters / sizing

It turns a one-way "here's an idea" notification into a **self-draining decision queue** with a
visible trend — the same compounding the session-chain enders give the agent loop, for the owner's
idea backlog. **Small/decided-lane:** one log file + a selection filter + a briefing line; read-only
on the bot. Sequence it after a few real spotlight cards confirm the daily ritual lands.

→ relates `scripts/hermes/idea_spotlight.py` · `docs/operations/hermes-skills/{idea-spotlight,intake,morning-briefing}.md`
