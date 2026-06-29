# 2026-06-29 — Farm leaderboard provider (completion-first deepening)

> **Status:** `in-progress`

**Run type:** routine · dispatch

## What this run is doing
Empty-fire dispatch advancing the S1 completion-first arc (Q-0209). The Leaderboards
completion assessment flagged "missing providers for several existing games"; Fishing
shipped as the worked example (#1540). This run ships the **Farm leaderboard provider**
(rank by flock size) — the remaining turn-key gap that has a persisted per-player stat.

Investigated all four named gaps: **Farm** has a per-(user,guild) `chicken_farm` row
(flock + coop level) → turn-key. **Blackjack** (in-memory game state, coins via economy
audit only), **Casino/poker** (ephemeral play-chips, no persistence), and **Word-Chain**
(per-channel `chain_count` only, no per-user tracking) lack a persisted rankable per-player
stat — each would need a migration + write-path, **not** turn-key; noted honestly in S1.

## Plan
1. `top_farmers` db primitive (`utils/db/games/farm.py`) — `[(user_id, chickens, coop_level)]`.
2. `FarmProvider` in `rank_providers.py` (mirrors Fishing/Creatures) + register + aliases.
3. `harvest` card theme (golden field) for the farm board's own look.
4. Cog docstring/help/aliases + tests.
