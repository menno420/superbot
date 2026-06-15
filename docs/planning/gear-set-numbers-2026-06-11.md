# Gear-set numbers — V-16 phase 1 design record (Q-0092)

> **Status:** `reference` — the rationale behind the 30-item stat/economy
> tables shipped 2026-06-11. **Source of truth is the code**
> (`utils/equipment.py`, `utils/mining/items.py`, `utils/mining/market.py`,
> `data/json/recipes.json`); the **binding contract is the test suite**
> (`tests/unit/utils/test_gear_set_numbers.py` — monotonicity + duel-sim
> bands). This file explains *why* the numbers are what they are, so a
> retune session changes them deliberately. Owner mandate: Q-0092 item 3
> ("full numbers authority — simulation-sane, monotonic per tier,
> documented; a later owner round can retune").

## The model

- **9 slots** (`equipment.SLOTS`): tool · light · charm (mining) + weapon ·
  shield · helmet · chestplate · leggings · boots (combat — `SET_SLOTS`).
- **5 tiers** (`TIER_ORDER`): bronze < iron < silver < gold < diamond.
  Bronze sits before iron (Bronze Age before Iron Age), silver between iron
  and gold (real-world value order); the pre-existing repo ladder
  iron < gold < diamond is preserved.
- **Set bonus**: all six combat slots in one tier → `damage +1×tier_index`,
  `max_health +3×tier_index` (bronze +1/+3 … diamond +5/+15). Defense is
  deliberately **not** in the bonus (see the defense cliff below).
- **Legacy fold (migration 068)**: item "armor" → "iron chestplate",
  "diamond armor" → "diamond chestplate"; the old combined `armor` *slot*
  splits into `shield` (for shields) and `chestplate` (everything else).
  Starters "sword"/"shield" stay as untiered entry pieces strictly below
  bronze.

## The duel constraints (why these magnitudes)

Duel math (`cogs/deathmatch_cog.py`): attack = 15 base (30 crit, 10%)
+ attacker damage − defender defense, **flat, floored at 1**, over
100 + max_health HP.

1. **Defense cliff:** once total defense reaches the 15 base attack, every
   bare hit floors at 1 — a degenerate stone wall. Full diamond defense
   totals **14** (< 15, pinned by test), and the set bonus carries no
   defense so the cap can't creep.
2. **Per-piece edge:** one piece a tier up (no set bonuses in play) wins
   ~0.50–0.85 of always-attack duels — favoured, never guaranteed (pinned).
3. **Full-set gap is decisive on purpose:** a complete set one tier up wins
   ~0.75–0.995 (pinned). Six pieces + the bonus is the progression
   investment; with no defend-action variance the sim overstates live
   decisiveness, where defend timing + crits soften it.
4. **The set breakpoint is intentional:** the same-tier bonus outweighs any
   single next-tier piece, so swapping one piece out of a complete set is a
   net downgrade ("upgrade by batches" — the collection goal). Two seams
   absorb the UX cost: `best_loadout` is **set-aware** (Equip Best never
   breaks a profitable set) and the gear picker warns
   "⚠ breaks set bonus".
5. **Bare duels unchanged:** 100 HP / 15 damage with no gear — pinned.

## The stat tables (per tier: bronze, iron, silver, gold, diamond)

| Family | Stat(s) | Values |
|---|---|---|
| sword | damage | 4 · 6 · 7 · 8 · 10 *(iron/diamond preserved pre-set anchors)* |
| shield | defense / max_health / damage | 2/12/1 · 3/14/1 · 3/16/2 · 4/18/2 · 4/20/2 *(damage added 2026-06-15)* |
| helmet | defense / max_health | 1/2 · 1/3 · 2/4 · 2/5 · 2/6 |
| chestplate | defense / max_health | 2/6 · 2/8 · 3/10 · 3/12 · 4/15 |
| leggings | defense / max_health | 1/4 · 1/5 · 2/6 · 2/8 · 2/10 |
| boots | defense / max_health | 1/2 · 1/3 · 1/4 · 2/5 · 2/6 |

Full-set totals (set bonus included): damage 6/9/12/14/17 · defense
7/8/11/13/14 · max_health 29/39/49/60/72. Starters: sword damage 3,
shield 2 def / 10 hp (no damage).

> **2026-06-15 (owner):** tiered shields gained a gentle damage jab
> (1/1/2/2/2), so a shield is a light off-hand weapon as well as a defensive
> anchor; the starter `shield` stays defense-only. Diamond was tuned to +2 (not
> +3) to keep the one-tier-gap duel-sim band — the bands in
> `tests/unit/utils/test_gear_set_numbers.py` still hold.

## Economy ladders

- **Ores:** bronze (value 2) and silver (value 4) join the loot table —
  surface weights descend in 0.5 steps by value (stone 3 → diamond 0.5);
  with depth, bronze fades like stone (at half rate, `max(0.5, 2.5−0.5d)`)
  while silver grows like gold (`1.5+0.5d`). Both scale with mining power
  (`exploration._ORE_ITEMS`).
- **Forge recipes** (the Q-0092 smelt→forge path; every set item consumes
  its tier's ore — pinned): sword `{ore 2, wood 1}` · shield `{ore 2,
  wood 2}` · helmet `{ore 3}` · chestplate `{ore 5}` · leggings `{ore 4}` ·
  boots `{ore 2}`. A full set = 18 ore + 3 wood.
- **Shop prices:** ~5–6× material sell value (crafting stays the cheaper
  path; pinned as `price > material value`). Every wearing item has a shop
  row because **repair pricing derives from the shop knob**
  (`workshop.repair_base`) — pinned.
- **Durability** (wears 1/duel, all six families): 80 · 150 · 200 · 260 ·
  320 per tier. Item display values ≈ 2× material value, monotonic.

## UI consequences shipped with the numbers

- Market panel: one field + one buy-select **per shop section**
  (`market.shop_sections()` — 41 items vs the 25-option / 1024-char caps).
- Workshop panel: craft field shows craftable-now + a Recipe-browser
  pointer; craft select sorts craftable-first before the 25 cap.
- Recipe browser: already paginated — now actually multi-page (44 recipes).
- Gear panel: set-progress line ("🧩 Bronze set: 4/6 pieces" /
  "✨ … set complete"), stat previews per picker option, and the V-16
  paper-doll follow-up (`utils/character_render.py`).

## Retuning

Change the tables in code, keep the invariants green. If a retune
deliberately moves a sim band (e.g. softer full-set dominance), update the
band in `test_gear_set_numbers.py` **and the rationale here** in the same
commit.
