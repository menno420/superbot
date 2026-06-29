# 2026-06-29 — Fishing leaderboard provider (S1 deepening win)

> **Status:** `in-progress` — born-red (Q-0133). Run type: routine · dispatch.

**Branch:** `claude/funny-franklin-hyw1yp` (re-synced to `main` @ #1539, `2dea872c`).

## What I'm about to do (intentions)

Empty-fire scheduled dispatch — no work order. Advancing the S1 ▶ Next startable, offline
**deepening win** flagged twice in `current-state/S1-bot.md`: *"Leaderboards is missing providers for
several existing games — notably Fishing... each is one `RankProvider` class + a `utils/db` top-N read
(the headline turn-key deepening win now)."*

Fishing already has the data (`db.top_fishers(guild, known_species)` → `(user_id, caught, species)`,
used by `!fishtop`) and its own `!trophies` board, but **no provider in the unified `!leaderboard` hub /
select menu** — so it's absent from the central leaderboard surface every other game appears in. This
slice closes that gap, mirroring `CreaturesProvider` exactly.

Planned:
1. `utils/fishing/fish.py` — add `fish_names()` catalog helper (mirror `creature_names()`); export it.
   Refactor the two duplicated `[s.name for s in SPECIES]` call sites in `fishing_cog.py` onto it.
2. `services/rank_providers.py` — new `FishingProvider` (top by total caught, member_rank on/off board),
   registered + `fishlb`/`fishingleaderboard`/`anglerlb` aliases.
3. `cogs/leaderboard_cog.py` — add `fishlb` to the command alias list + the help category list.
4. `utils/card_render.py` — add a `tidal` ocean skin (the engine's "a new look = a few RGB tuples"
   property); `FishingProvider.card_theme = "tidal"` for at-a-glance visual distinction.
5. Tests: extend the canonical-category set, add FishingProvider coverage + a `fish_names()` test.

Offline, self-mergeable on green (contained, reversible, test-covered). After this, if budget remains:
the Economy `give`/`pay` deepening win or another game provider (Blackjack/Word-Chain/Farm).
