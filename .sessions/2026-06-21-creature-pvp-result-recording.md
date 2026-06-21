# 2026-06-21 — Creature PvP: result recording + win/loss records + battle leaderboard

> **Status:** `in-progress` — born-red HOLD; flips to `complete` as the final step.

> **Run type:** `routine · dispatch`

## What I'm about to do

Empty scheduled dispatch fire. The ▶ Next action queue's startable lane (a) is the creature-game
**leaderboards slice (reuse `game_xp`, additive)** — #1230 shipped the read-only PvP flow, and both
the plan §4 and `creature_battle_service`'s own docstring point at the deferred **audited-write half**
("the moment a battle records a result, this is where that transaction will live").

This slice ships that half:

- migration **082** `creature_battle_record` — per-(user, guild) win/loss tally.
- `utils/db/games/creature_battles.py` — transaction-aware CRUD (record outcome · get record · top
  battlers), exported through `utils/db`.
- `game_xp_service` — a new `battle_win` award (`GAME_CREATURE`, 6 XP), through the one central award
  policy + daily soft-cap (PvP itself stays level-normalized, so this XP is prestige only, never P2W).
- `creature_battle_service.resolve_and_record_pvp` — resolve, then in ONE `db.transaction()` record
  the W/L + award the winner's XP; emit the game-XP events post-commit (mirrors `creature_workflow`).
- the challenge view + renderer show each fighter's updated record and any level-up note.
- `!cbattletop` / `!pvptop` leaderboard in `creature_battle_cog` (mirrors `!dextop`).

`needs-hermes-review` (runtime, substantial plan step — not an autonomous self-merge), per the plan's
framing of the creature-PvP runtime lane.
