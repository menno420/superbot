# 2026-06-21 — Creature collector leaderboard provider (central hub integration)

> **Status:** `in-progress` — second slice of this dispatch run. Registers a
> `CreaturesProvider` in `services/rank_providers.py` so the creature game joins the
> unified `!leaderboard` / `!rank` hub (the documented "new category = register a
> provider" pattern). Additive; no migration; reuses the existing `top_collectors` read.

> **Run type:** `routine · dispatch`

## Plan (about to do)

The creature game (#1208/#1213/#1230) has a standalone `!dextop` top-collectors command
but is **absent from the central `!leaderboard` hub** — every other game (xp/coins/mining/
gamexp/crafting/deathmatch/rps/counting) is a registered `RankProvider`. This slice closes
that gap:

1. `CreaturesProvider` in `rank_providers.py` — `top` + `member_rank` over the existing
   `db.top_collectors(guild.id, creature_names())` read (caught count + species).
2. Registers it in `_PROVIDERS` (auto-wires the dropdown, `!leaderboard creatures`, `!rank`).
3. Tests: registry membership, select metadata, top/member_rank rows, empty-state.

The ▶ Next startable (a) from current-state ("creature leaderboards slice"). Independent of
this run's slice 1 (#1242, role_grants) — different files.
