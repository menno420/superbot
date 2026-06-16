# 2026-06-16 — Night work queue for the dispatch routine

> **Status:** `in-progress`

**Arc:** Owner directive (in-session) — seed a *grounded* night-work queue so the
~4 scheduled dispatch fires overnight (`0 */2 * * *` → 00:00/02:00/04:00/06:00 UTC,
"including that from 12am") advance genuinely useful **bot-section (`disbot/`
runtime)** work instead of stalling on the thinned `ready` queue.

**What I'm about to do:** land a turn-key [night queue](../docs/planning/night-queue-2026-06-16.md)
of independent, read-only deterministic BTD6 floor builders (the proven
#946/#950/#955/#962/#975 lane) + repoint `current-state.md` ▶ Next action at it, so
each scheduled fire (which `git reset --hard origin/main` then reads ▶ Next action)
picks the topmost unbuilt slice and self-chains.
