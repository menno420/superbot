# Titles numbers — mining Slice F (skill/milestone titles)

> **Status:** `reference` — the pinned earn-thresholds for the title catalogue.
> Tunable; change them here **and** in `utils/mining/titles.py` + its test in the
> same commit (the `gear-set-numbers-2026-06-15.md` convention). Source wins.

Titles are **derived** identity text (brainstorm §7.6) — a pure function of
progression the player already has, so nothing is granted on a mutation path.
Only the equipped *choice* persists (`mining_player_state.equipped_title`,
migration 074). A title displays on the Character card only while still earned
(`title_service.equipped_title` re-checks), so a respec silently un-displays a
mastery title without any cleanup.

## Catalogue (v1)

| id | display | earned when |
|---|---|---|
| `the_deep` | ⛏️ the Deep One | Mining branch at cap (10/10) |
| `ironclad` | ⚔️ the Ironclad | Combat branch at cap (10/10) |
| `the_lucky` | 🍀 the Lucky | Fortune branch at cap (10/10) |
| `master_smith` | 🛠️ Master Smith | Crafting branch at cap (10/10) |
| `spelunker` | 🪨 the Spelunker | Reach the Cavern (max_depth ≥ 1) |
| `deepdelver` | 💎 the Deepdelver | Reach the Deep (max_depth ≥ 2) |
| `coreborn` | 🌋 the Coreborn | Reach the Magma core (max_depth ≥ 3) |
| `veteran` | 🎖️ the Veteran | Game level ≥ 10 |
| `legend` | 👑 the Legend | Game level ≥ 25 |

Mastery thresholds = `skills.PER_BRANCH_CAP`. Depth thresholds are biome-*named*,
not absolute numbers.

## Forward note — the P6 grid

The brainstorm's **P6** arc (`docs/ideas/mining_exploration_brainstorm.md`) expands
depth from today's 4 bands into an x/y grid with N/S/E/W movement and much greater
depth. The depth titles are deliberately keyed off `max_depth >= N` against the
*current* biome bands, so when P6 deepens the world the only change is **appending
new deeper-milestone titles** to `_RULES` — nothing assumes 3 is the floor of the
world. (`test_depth_milestones_are_thresholds` pins that a deeper `max_depth`
still satisfies the shallower milestones.)
