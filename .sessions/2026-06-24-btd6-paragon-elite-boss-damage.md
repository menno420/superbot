# 2026-06-24 — BTD6 paragon elite-boss damage multiplier

> **Status:** `in-progress`

Owner-reported gap (Discord): the bot can't answer about the **elite boss damage
multiplier** for paragons. Owner showed JonnyBoy/hemi's bot displaying `ed: elite
boss dmg` = `×2` the boss damage (`326 = 2×163`).

## What I'm about to do
- **Verified** (this session): the ×2 elite factor is **NOT in the dump** — checked
  the Dart *and* Ice Monkey paragon models (only Boss/Ceramic/Moabs damage tags, all
  multiplier 1.0) and `paragonDegreeData.json` (one boss field, no elite). It's a
  **universal runtime constant**: per the Fandom *Extra Damage to Boss* / *Paragons*
  pages, **paragons deal 2× their bonus boss damage to Elite Bosses**, paragon-category
  only, at **all degrees including degree 1**. (Same shape as the freeplay/cash
  runtime constants — curate it, the dump doesn't have it.)
- Add `ELITE_BOSS_DAMAGE_MULTIPLIER = 2.0` + `elite_boss_multiplier(degree)` (=
  `boss_multiplier(degree) × 2`) to `paragon_degrees.py`, surface it in the paragon
  degree embed and the `[btd6_paragon_stats]` grounding so the bot answers it, with
  tests pinning the anchors (deg 35 → ×2.5, deg 100 → ×4.5; ×2 vs normal boss).
