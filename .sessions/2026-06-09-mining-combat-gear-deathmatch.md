# Combat gear → deathmatch (Wave 1 cross-game stat seam)

**Branch:** `claude/mining-combat-gear` · **Date:** 2026-06-09

Second slice of the same session (after #607 "The Descent" merged). The maintainer
picked **"Combat gear → deathmatch"** from a 3-way next-slice question. This is the
brainstorm's flagship "prove the platform" milestone: a second game reading the shared
`EffectiveStats` block.

## Two commits (foundation → feature)
**1. `refactor(equipment)` — promote the stat model to a shared seam.** Moved the pure
`EffectiveStats` / gear catalogue / `compute_stats` from `cogs/mining/equipment.py` →
**`utils/equipment.py`** (stdlib-only, fits the utils layer), zero behaviour change.
*Why now:* deathmatch can't depend on *mining's* internals, and a future `services/` stat
resolver can't import `cogs/` at all — so the cross-game seam had to leave `cogs/`. This is
the brainstorm §7.4 relocation, extracted the moment the 2nd game needed it (the §7.7
"extract the platform from its first concrete use" principle). Updated 6 importers + moved
the test to `tests/unit/utils/test_equipment.py`; the mining hub's lazy equipment import
became a clean module-level `from utils import equipment`.

**2. `feat(deathmatch)` — combat gear reads through to duels.**
- Added **WEAPON/ARMOR slots** + combat gear to `utils/equipment.py`: `sword` (dmg+3),
  `iron sword` (dmg+6), `shield` (def+2, hp+10), `armor` (def+4, hp+20). Small/fair.
- `_Duel` now takes optional `p1_stats`/`p2_stats` (default all-zero → identical to the
  historical 100 HP / 15 dmg duel, so every existing caller/test is unaffected). HP =
  `BASE_HP + max_health`; attack = `base + attacker.damage`; armor = flat `-defense`
  floored at 1; the active "defend" halving stacks on top.
- Threaded stats into both construction sites: PvP (`_ChallengeView.btn_accept`) fetches
  both players' gear; bot duel (`btn_fight_bot` → `_BotDuelView`) fetches the player's
  (bot fights bare). Both via `from utils import equipment` (cog→utils / view→utils — clean,
  no new layer debt).
- `sword`/`armor` recipes added (`iron sword`/`shield` were already craftable) → closes the
  mine→craft→equip→duel loop. Duel embeds show `HP/maxHP`; Rules embed documents gear.

## Verification
- `check_quality.py --full`: **8228 passed**, 0 fail. `check_architecture --mode strict`:
  **0 errors** (relocation removed a lazy import; added none).
- **Live boot:** clean — equipment relocation resolves, all cogs load (Mining, Deathmatch,
  ServerManagement…), recipes parse, 0 ERROR/CRITICAL/Traceback.

## Learnings / gotchas
- **The relocation was the real work; combat was easy on top of it.** Doing combat via a
  lazy `deathmatch → cogs.mining.equipment` import would've "worked" but enshrined a
  cross-*subsystem* coupling (worse than the mining-internal lazy imports). Promoting the
  pure model to `utils/` is the root-cause fix and unblocks a future stat *service* too.
- **`_classify_button` (help actionability test) runs button callbacks.** Adding a
  `db.get_equipment` call to `btn_fight_bot` broke `test_deathmatch_panel_fight_bot_spawns_new_view`
  — the classifier caught the uninitialised-pool raise *before* `edit_message`, so it scored
  UNKNOWN. Fix: patch `db.get_equipment` in that test. Any new DB read inside a panel button
  needs a stub there.
- **Backward-compat via defaulted stat kwargs** kept `test_deathmatch_guild_scope`'s
  `_Duel(p1, p2)` and every other caller green — additive, not a signature break.
- **isort orders `cogs` before `utils`** even for in-function imports (caught in the Descent
  PR when test imports flipped); `python3.10 -m isort <file>` fixes it. Note `check_quality`'s
  isort scope flagged a `tests/` file even though CLAUDE.md says CI excludes tests/ — just
  fix the order, it's correct anyway.

## Next steps (Wave 1, each its own slice)
- **Sell-ore / buy-gear market** — the cross-domain leg through `economy_service` (closes the
  mine→sell→upgrade→descend economic loop). The one slice that genuinely warrants an audited
  service (unlike the rest of direct-lane mining). Has product calls (prices).
- Audited Workshop + durability (durability is the keystone ore/coin sink, §7.5).
- Mother-panel live overview (§6.3): the hub embed is still static.
- **Open product question (deferred, §7.8):** how hard should gear swing PvP? Shipped
  conservative; the maintainer can tune `_GEAR` or redesign the PvP shape (arena/wager).

## Context delta
- **Well-pointed:** brainstorm §6.5/§6.6 (the stat-contract design) + §7.4 (relocate-to-shared
  step) named exactly this move; the equipment module's own docstring already said "cross-game
  read model", confirming the relocation was always intended.
- **Found by hand:** that `iron sword` + `shield` were *already* in `recipes.json` (so only
  `sword`/`armor` needed adding); and that the help-actionability test drives button callbacks
  (so a new DB read in a button breaks it). Neither was documented.
- **Reaffirmed gap:** still no folio note on "a panel button that does a DB read needs a stub
  in the actionability/help tests." Two sessions running have hit view-test friction; worth a
  short "testing Discord views/panels" note in the games folio if a third session does.
