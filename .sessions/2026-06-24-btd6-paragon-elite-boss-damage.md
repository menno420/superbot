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

## Verification update
Owner challenged whether the ×2 is **constant** across degrees or assumed from the
one (deg-35) screenshot. **Resolved:** a *second* independent search of the Fandom
*Extra Damage to Boss* / *Paragons* pages states it explicitly — *"Elite Bosses take
double damage from Paragons. This is a **flat bonus that applies to all Paragon
degrees**"* and *"applies from the very first degree."* So constant ×2 is confirmed by
two independent community sources + the screenshot — not an extrapolation. (It hits
the **total** boss damage, matching JonnyBoy `ed = 2× bd`, not just the bonus.) Full
CI mirror green (12,280 passed); the only red is the born-red gate. **Holding the
final flip for the owner's nod** since this point was explicitly contested.
