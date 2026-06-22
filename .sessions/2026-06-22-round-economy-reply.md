# 2026-06-22 — Unified round economy NL reply (RBE + cash + XP)

> **Status:** `in-progress`

Owner-directed (the maintainer approved the round-economy consolidation idea
filed in the #1324 session: "Yes that's a good idea you can implement that").
Round economy data (RBE, cash, cumulative cash, XP) is now answered by three
separate paths — cash via `ai_round_cash_workflow`, XP via the new
`deterministic_round_xp_reply`, RBE via none. Adding one
`deterministic_round_economy_reply` that gives all of them in a single grounded
answer ("what's the economy of round 95?"), matching the round embed's Economy
field.

## Shipped

_(filling in)_
