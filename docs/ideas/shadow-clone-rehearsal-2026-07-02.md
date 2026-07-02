# Shadow-clone rehearsal — stand up the current bot's twin, agent-operated (2026-07-02)

> **Status:** `ideas` — session idea (Q-0089, owner-requested harvest). Not approved for
> implementation (creates Railway resources → flag before running; creation is additive and
> tear-down-able, but it is real spend).

## The idea

Under the Q-0213 grant, an agent can stand up the **entire Phase-5 shadow topology today, on the
current bot**: a Railway `shadow` environment (or scratch project) running `worker` from `main`
with the **Galaxy Bot** token + a Postgres restored from the newest backup artifact — a live,
production-shaped twin serving a test guild, created/verified/torn down entirely by agents.

## Why it's worth having

One rehearsal, four birds — each currently scheduled to be proven for the first time *during* the
rebuild, when the stakes are highest:

1. **Proves the restore path end-to-end** (the backup artifact actually boots a working bot, not
   just a schema).
2. **Rehearses the §5 cutover choreography** (restored-snapshot shadow · exactly-one-bot-writes-prod
   · token-swap flip · teardown) with zero production risk, months before Phase 5 needs it.
3. **Gives the golden harness a capture target** that is production-shaped but consequence-free —
   captures that would be intrusive against the live guild (moderation actions, provisioning,
   destructive confirms) run here.
4. **Exercises the wire-level live-bot loop** (sibling idea) against real production data shapes.

Cost is bounded (Hobby usage for one small worker + Postgres for the rehearsal window; sleep or
tear down after) and the whole thing is a dry run of the new-project bootstrap script (plan §6 R-3).

## Route

S3/S5 · pairs with `wire-level-live-bot-loop`, `continuously-verified-backups`, and the Railway
plan §5. Natural sequencing: after the restore-verify workflow is green once.
