# BTD6 game-native storage — schema design & cutover map

**Principle (set by the maintainer):** the **game data leads**; bloonswiki is a
cross-check *reference*, not the source of truth. We store the game's **own
structure** and resolve names from the **game's own** strings — we do **not**
reshape the data to fit a wiki-derived schema. The one exception: don't fragment
data into pieces the bot can't reassemble (keep the few bot-matching keys the
dump doesn't expose — see "What stays curated").

> Why now: the wiki files are v53, lag per-tower, rename/merge the game's
> projectiles, and miss projectiles entirely. The game data is complete, v55,
> and canonical. Verified wins from going game-native: Druid Superstorm shows
> its **v55** storm (100 dmg, was a stale 150) with clean canonical ids instead
> of 8 duplicate-named entries; Super Monkey Dark Knight's **two** abilities are
> distinct again (`Legend of the Night` vs `ChampionDarkshift`); Psi's
> `DestructiveResonance` (previously dropped) is present; upgrades carry the
> game's own descriptions.
>
> Companion docs: `btd6-gamedata-decode-status.md` (status/lessons),
> `btd6-gamedata-dictionary.md` (where each fact lives),
> `btd6-game-file-extraction-plan.md` (the mapper).

## The game's tower data structure (what we mirror)

```
Towers/<Name>/<Name>-NNN.json   (one file per crosspath state; NNN = tier digits)
  └ behaviors[]
      ├ AttackModel              range; one per distinct attack
      │   └ weapons[]            rate; emission (count); ejectX/Y/Z
      │       ├ projectile       ProjectileModel — id is the game-native name
      │       │   └ behaviors[]
      │       │       ├ DamageModel               damage, immuneBloonProperties
      │       │       ├ DamageModifierForTagModel tag + damageAddative (the bonus)
      │       │       ├ Travel*Model              speed, lifespan
      │       │       ├ CreateProjectile*/Alternate/… → child projectiles
      │       │       └ Create/Slow/Freeze/Stun…  → effects
      │       └ behaviors[]      AlternateProjectileModel etc. (weapon-level spawns)
      ├ AbilityModel             displayName (player-facing!), cooldown
      ├ *ZoneModel               damage zones (Arctic Wind, DoT, …)
      ├ buff models              inline (MonkeyFanClub, village range, …)
      └ footprint / areaTypes / towerSet / targetTypes  (top-level)
```

Heroes: `<Hero> N.json` per level (same `behaviors[]` shape). Paragons:
`<Name>-Paragon.json`, a single flat node. Bloons (incl. bosses):
`Bloons/<Name>/<Name><tier>.json` `BloonModel`.

## Names — all game-sourced (no wiki labels)

| Thing | Game-native source | Status |
|---|---|---|
| Ability | `AbilityModel.displayName` ("Cocktail of Fire") | ✅ mapper does this |
| Upgrade name + **description** | `UpgradeModel.LocsKey` → `textTable[LocsKey]` / `[LocsKey + " Description"]` | ✅ mapper does this |
| Projectile | `ProjectileModel.id` (e.g. `BaseProjectile`, `LightningProj`) | ✅ canonical id |
| Spawned subtower | nested `towerModel.name` ("Phoenix") | ✅ |
| Tower / hero | catalog id + canonical | ✅ |
| Zone (e.g. "Arctic Wind") | the zone model's `name` is empty → resolve via the **owning upgrade's** name (`LocsKey`) | ⏳ cutover |
| Bloon / boss | `BloonModel.id` | ⏳ when bloons go game-native |

The tag damage bonus lives in `damageAddative` (sic), not `damageMultiplier`;
see the dictionary/decode-status docs for the field traps.

## How the bot consumes it (the "displayable" constraint)

The runtime is largely **name-agnostic**, which is what makes game-native
storage drop-in:

- **`btd6_stats_service.normal_stats`** — the glance view — picks the headline by
  **highest-damage own-attack projectile** (`_main_projectile`), *not* by a name
  like "Projectile". Reads `damage`, `damage_type`, `cannot_pop`, `pierce`,
  `rate` (cooldown), tier `range`, `filterInvisible` (camo), and scans all nodes
  (`_iter_dicts`) for specials (MOAB bonus, stun, income, ability cooldown,
  knockback). → A game-native projectile set just works (and headlines the right
  projectile).
- **Pro view** (`utils/btd6/stats_embed`) — renders the full per-tier breakdown;
  shows whatever projectiles/abilities are present.
- **`btd6_upgrade_detail_service`** — surfaces *named* attacks/projectiles/
  abilities/subtowers/buffs/zones; game-native names flow straight through.
- **Grounding** (`btd6_context_service`) — renders fact lines from the same data.

## What game-native storage requires (runtime adaptations for the cutover)

These are the only places that assume *wiki* naming and need updating when the
committed files become game-native:

1. **`_main_projectile` reanimated-minion skip-list** (`_REANIMATED_MINION_NAMES`)
   — hard-coded wiki names; re-key to the game ids/names so a reanimated blimp
   still can't masquerade as the headline.
2. **`_collect_specials`** keys on `"Stun" in name` and on `cashPerRound` etc. —
   confirm the game-native node names still trip stun detection (the mapper's
   effect nodes carry game names like `"Stun…"`); adjust if needed.
3. **Curated prose** — tower/hero `description` (deliberately empty today) and
   `paragon_descriptions.json` can be **superseded by `textTable` descriptions**
   (game-authored, no CC concern). Decide per-entity; keep paragon overviews if
   preferred.
4. **Value-pinned tests** (~25) — update to the v55 numbers.

## What stays curated (the bot-matching keys the dump doesn't expose)

- **Paragon `cost` / `canonical` / `xp`** — the dump's `-Paragon.json` `cost` is
  the base monkey's placement cost, not the paragon price; keep the curated
  metadata (the mapper already preserves it).
- **Catalog `towers.json` / `heroes.json`** — ids, aliases, the resolver
  vocabulary the bot matches user text against.
- **Bloon aliases** and any synthesized modifier entries used for matching.

These are *keys for matching*, not game stats — exactly the "don't fragment what
the bot can't reassemble" exception.

## Structural completeness — subtowers / zones / buffs (the cutover gate)

The curated files carry `subtowers[]`, `zones[]`, `buffs[]` (read by
`btd6_upgrade_detail_service`). **The mapper must produce all of these before a
towers cutover, or it silently regresses them.** Complete map of where each
lives + status:

**Subtowers** — a nested `TowerModel` (mapped like a tier). 3 spawn models cover
the common cases; 2 mechanisms remain tower-specific.

| Spawn model | Field | Examples | Status |
|---|---|---|---|
| `AbilityCreateTowerModel` | `towerModel` | Wizard Phoenix, Adora Ball of Light | ✅ mapped |
| `CreateTowerModel` | `tower` | Engineer Sentry, Etienne UAV, hero totems, Super Monkey Spectre/Sun-Avatar | ✅ mapped |
| `MorphTowerModel` (embedded) | `towerModel` | Druid Masqued Macaque | ✅ mapped |
| `MorphTowerModel` (**named ref**) | name → other file | **Alchemist** "Transformed Monkey" | ⏳ needs file resolution |
| `BeastHandlerPetModel` | tower-specific | **Beast Handler** beasts | ⏳ tower-specific |

**Zones** (`*ZoneModel`, ~18 types) — ⏳ **not yet mapped.** Headline ones to
extract: `SlowBloonsZoneModel` (`zoneRadius`, `speedScale`→slow, `filters`),
`DamageOverTimeZoneModel` (damage, interval), `NecromancerZoneModel`,
`MoabShoveZoneModel`, `WindyZoneModel`; the cash/discount zones
(`DiscountZoneModel`, `CollectCashZoneModel`, `CashbackZoneModel`) are economy.
The zone model's own `name` is empty → resolve via the owning upgrade (`LocsKey`).

**Buffs** (`*SupportModel` / `*BuffModel`, ~40 types) — ⏳ **not yet mapped.** A
common core covers most: `RangeSupportModel` (10 towers), `PierceSupportModel`
(8), `VisibilitySupportModel` (8, camo), `RateSupportModel` (7),
`ProjectileSpeed`/`AbilityCooldown`/`Damage` support — all share
`multiplier`/`additive` + **`buffLocsName`** (→ `textTable` for the name). The
long tail is tower-specific (`ObynBuffModel`, `EziliSupportModel`,
`MonkeyFanClubModel`, `TradeEmpireBuffModel`, …) — map the common core well,
emit a name-only node (via `buffLocsName`) for the tail.

## Cutover plan (phased)

1. **Game-native names + descriptions in the mapper** — ability `displayName`,
   upgrade `LocsKey` → name/description. ✅ Generated heroes re-emitted with real
   ability names.
2. **Subtowers** — common spawn models → minion stats. ✅ **(this PR)** Generated
   heroes (obyn/etienne/ezili) re-emitted with their totems/UAV.
3. **Zones + buffs** — map per the table above (+ the alchemist/beast subtower
   tail). This *completes the structural map* and unblocks the cutover.
4. **Towers cutover** — adopt `parse_gamedata.py --all` output as the committed
   tower stats (game-native ids/structure/values), do the runtime adaptations
   above, update value-pinned tests. Audit (`--audit`) gates the numbers.
3. **Heroes + paragons cutover** + wire `textTable` descriptions into grounding
   and the detail UI (answers "what does upgrade/ability X do?" from the game).
4. **Bloons / bosses** from `BloonModel`; then the other domains as needed.

Until a phase lands, the conservative overlay (`--overlay`) keeps the
uniquely-keyed numbers (cost/range/xp) current without touching the wiki
structure.
