# BTD6 game-data decode — status, lessons & open items

The living status of the effort to source BTD6 data from the **BTD Mod Helper
game-data dump** (`github.com/Btd6ModHelper/btd6-game-data`, v55.0). Start here
to pick up the work: it records what's done, **how the dump's data actually
works** (the traps we hit), and what is still un-decoded.

> Companion docs — read alongside:
> - **`btd6-gamedata-native-schema.md`** — *the game-native storage design & cutover map* (game data leads; how to store the game's structure displayably).
> - **`btd6-gamedata-dictionary.md`** — *what data exists and where* (domains, the textTable linkage).
> - **`btd6-game-file-extraction-plan.md`** — the mapper roadmap + the fidelity-audit findings.
> - **`btd6-data-pipeline.md`** — the existing bloonswiki pipeline this augments.
>
> Tooling (point `--dump` at a clone; nothing is fetched at runtime):
> - `scripts/parse_gamedata.py --audit` — per-field fidelity vs our committed data (CLEAN / DELTA / SUSPECT).
> - `scripts/btd6_gamedata_inventory.py` — domain/model-type/text-linkage discovery.

## What this effort is

The dump is the game's **complete** exported model, so for our needs (stats,
names, descriptions, what an upgrade grants) **nothing is missing** — the work
is decoding *where* each fact lives and *which field* to trust, then storing it.

**Direction (set by the maintainer): the game data leads.** We store the game's
**own structure** and names (`displayName` / `LocsKey` → `textTable` / projectile
ids), with bloonswiki as a cross-check *reference* only — see
`btd6-gamedata-native-schema.md`. The end state is a **game-native cutover**
(adopt the mapper's output as the committed stats). The conservative
`--overlay` (uniquely-keyed numbers only) is an *interim* safe refresh that
keeps the curated files current without regressing them until the cutover's
prerequisites (full subtower/zone/buff mapping) are done. *(An earlier framing
in this doc — "numeric overlay, not a rebuild" — was superseded by that
direction.)*

## Completion status (verified)

Only items confirmed **100% complete** are marked ✅. Anything partial is 🟡 and
must not be treated as done. Verified against the v55 dump on 2026-06-03.

### ✅ Complete & verified

| Item | Where | Evidence |
|---|---|---|
| Fidelity-audit harness | `parse_gamedata.py --audit` | #464; tested; CLEAN/DELTA/SUSPECT per field |
| Discovery / inventory tool | `btd6_gamedata_inventory.py` | #465; tested |
| Data-domain dictionary (17 domains *identified*) | `btd6-gamedata-dictionary.md` | #465 |
| **`damageAddative`** tag-bonus extraction | mapper | #465; `damageModifierFor*` now audit-CLEAN (exact wiki match) |
| Conservative numeric **overlay engine** (uniquely-keyed only) | `parse_gamedata.py --overlay` | #466; tested. *Engine* complete; scope intentionally limited |
| Ability names via **`displayName`** | mapper | #466; 87/87 abilities carry it |
| Upgrade **descriptions** via `LocsKey`→`textTable` (extraction) | mapper | #466; extracts wherever the game localizes one (≈422 player upgrade cards) |
| Core per-tier numeric extraction: base_cost, category, upgrade cost/xp/path/tier, damage, pierce, rate, range, radius, speed, lifespan, immunities→type | mapper | audit: roster is DELTA/CLEAN, nothing SUSPECT |

### 🟡 Partial — NOT complete

| Item | Done | Missing |
|---|---|---|
| **Subtowers** (`subtowers[]`) | 3 spawn models: `AbilityCreateTower`/`CreateTower`/`MorphTower`(embedded) → Phoenix, Sentry, Spectre, totems, UAV | `MorphTowerModel` **named-ref** (Alchemist "Transformed Monkey") + `BeastHandlerPetModel` (Beast Handler) — 2 of ~4 mechanisms |
| **Projectile flattening completeness** | spawn-model coverage (under-emission 177→111) | 111 attacks still differ in projectile count vs wiki; flattening *style* (naming/grouping) differs |
| **Numeric overlay applied** | 3 files (Desperado range, mermonkey xp, ace cost), uniquely-keyed only | per-projectile/ability values cannot be safely overlaid (wiki↔dump name mismatch) |

### 🔴 Not started

- **Zones** (`zones[]`) — **0 of 12** zone model types mapped.
- **Buffs** (`buffs[]`) — **0 of 37** buff/support model types mapped.
- **Economy-tower attack suppression** (Banana Farm shows a nominal AttackModel).
- **The towers cutover itself** — blocked on zones + buffs + the subtower tail.
- **Descriptions consumed by the runtime** — extracted into upgrade data, but
  not yet wired into grounding / the detail UI.
- **Bloons / bosses game-native ingestion** (still wiki-sourced).
- **Powers / Knowledge / Rounds (all modes) / IncomeSets ingestion.**
- **Paragon overlay / cutover** (combat in a `base` node, not `tiers`/`levels`).

## Two extraction bugs found & fixed this program

**Both the same failure mode: the data was always present; the mapper read the
wrong field or the wrong place.**

1. **Tag damage bonus** (Juggernaut "+20 vs Lead") read from the wrong field.
   `DamageModifierForTagModel.damageMultiplier` is a neutral `1.0` in all but 2
   of 2,843 cases; the real bonus is the **additive** in the misspelled
   **`damageAddative`** field. Fixing it made `damageModifierFor*` audit-CLEAN
   (exact wiki match) and restored correct bonuses on 4 heroes. *(It was never
   "reworked between patches" — that was a misread on my part.)*
2. **Projectiles silently dropped.** Flattening only followed `CreateProjectile*`
   behaviors off `weapon.projectile`, missing ~13 other spawn models
   (`AlternateProjectileModel`, `ProjectileOverTimeModel`,
   `UnstableConcoctionSplashModel`, `PrinceOfDarknessEmissionModel`,
   `PhoenixRebirthModel`, …) under varied field names, on both projectile and
   **weapon** behaviors — under-emitting in 177 attacks (**Psi's whole damage
   projectile "DestructiveResonance" was missing**). Fixed by structural
   detection (by `ProjectileModel` `$type`, any field) + de-dupe. Parity:
   exact 1269→1348, under 177→111, duplicate-name attacks 192→72.

## How the dump's data works (lessons — read before extending the mapper)

- **The recurring trap: a field that looks empty/neutral usually means the value
  is in a sibling with an unexpected — or *misspelled* — name.** Both bugs above
  were this. When a stat reads `0`/`1.0`/absent but the game clearly has it, dump
  the **full** node (all fields) and look for the real carrier before concluding
  anything is "missing" or "reworked".
- **Source ladder** (which encoding to trust for what):
  1. **Numbers** (damage, pierce, rate, range, cost, health) → structured model
     fields; trust per `--audit` (CLEAN/DELTA).
  2. **Names** → `textTable.json` via a model's **`LocsKey`** /
     `localizedNameOverride` (upgrades) or **`displayName`** (abilities, 100%
     coverage); spawned subtowers use `towerModel.name`.
  3. **Descriptions / "what it grants"** → `textTable` `"<LocsKey> Description"`
     and `"<Hero> Level N Description"` — game-authored prose, authoritative
     (e.g. *Ezili L11 → "+50% pierce to reanimated Bloons"*).
- **`damageAddative` (sic)** is the additive tag bonus; `damageMultiplier` is a
  separate, near-always-`1.0` field.
- **Float precision**: the wiki rounds (`0.3616`); the dump is full precision
  (`0.36160713`). Compare/treat as equal at 4 dp.
- **List ordering differs**: the mapper flattens sub-projectiles depth-first;
  the wiki groups/names them its own way. Align by `name` (+ damage signature),
  never by index. Same-name sub-projectiles are the main residual audit DELTAs.
- **Projectile / ability *names* are NOT reliable keys across wiki↔dump** — the
  single most dangerous thing for *writing* (overlay). The wiki calls a
  projectile `"Projectile"` where the dump uses the id `"BaseProjectile"`, and
  `"Projectile"`/`"Ability"` are reused for distinct nodes. Matching by name
  therefore writes onto the **wrong** node: it would put Druid Superstorm's 100
  dmg on the base dart, and Dark Knight's *Legend of the Night* 180s cooldown
  on its *other* ability. So the overlay only touches **uniquely-keyed** values
  (cost/category, upgrades by `(path,tier)`, tier-level `range`/`footprint`) and
  leaves all per-projectile/ability stats curated. The audit may *report* a
  per-projectile DELTA, but it is never safe to auto-*write* it.
- **`immuneBloonProperties`** is a bitmask with bits we don't decode (9 vs 73
  can decode to the *same* type+immunity) — compare the *decoded* type, not the
  raw int.
- **Bosses live in `Bloons/`** (recursive: `Bloons/Bloonarius/Bloonarius1.json`
  = 20k HP); `Bosses/` is cosmetic. **`Buffs/`** is UI icons, not effects —
  buff/zone/subtower effects are inline in the tower models.
- **Names the wiki *invented*** (e.g. "Reanimate" for the internal "Attack
  Necromancer") are editorial and not in the dump — keep them curated. (The
  *word* may still appear in description prose; the *label-on-that-object* does
  not.)

## Next increments (toward the cutover)

The towers cutover is **gated** on completing the structural map. In order:

1. **Zones** — map the 12 `*ZoneModel` types (`SlowBloonsZone` slow, `Damage
   OverTimeZone` damage/interval, shove/windy/necromancer + economy). The zone's
   own `name` is empty → resolve via the owning upgrade's `LocsKey`.
2. **Buffs** — map the 37 `*SupportModel`/`*BuffModel` types: a common core
   (`Range`/`Pierce`/`Visibility`/`Rate`/`Speed`/`Cooldown`/`Damage` support, all
   sharing `multiplier`/`additive` + `buffLocsName`→name) covers most; tail
   towers get a name-only node.
3. **Subtower tail** — `MorphTowerModel` named-ref (Alchemist) + `BeastHandler
   PetModel`.
4. **Economy-tower attack suppression**, then the towers **cutover** (adopt
   `--all`, runtime name-adaptations, update value-pinned tests), gated by
   `--audit`.

Smaller open notes: `count` has no exact dump field (stays curated); the 2
roster-wide `damageMultiplier != 1` tag cases aren't emitted (we read the
additive); `textTable` descriptions are extracted but not yet *consumed* by
grounding/UI.

## Dump areas NOT yet examined (be honest about coverage)

Verified **deeply**: `Towers/` (attacks, projectiles, abilities, subtowers,
damage modifiers, costs/upgrades) and `Upgrades/` + `textTable.json` linkage.

**Not examined / only counted — do not assume:**
- **Domains never opened:** `Achievements/`, `Artifacts/`, `BloonOverlays/`,
  `GeraldoItems/`, `Knowledge/`, `Maps/`, `Mods/`, `Skins/`, `TrophyStoreItems/`.
- **Only counted / single-sample (structure not mapped):** `Rounds/` (5181
  files, counted), `IncomeSets/` (7, counted), `Powers/` (1 sampled), `Bloons/`
  (Bloonarius sampled + the `BloonModel` field list seen via the inventory tool;
  not all 235 bloons verified, children/immunity decode unverified).
- **Loose files unread:** `frontierData.json`, `rogueData.json`, `resources.json`.
  `paragonDegreeData.json` is *referenced* (we derive degrees) but never
  cross-checked against the dump's constants.
- **Within `Towers/` (examined domain) still undecoded:** the 12 **zone** + 37
  **buff** model types (identified, fields not extracted); status-effect /
  targeting / income behavior models beyond what `_map_tier` reads.

## Freshness
- Re-pull the dump per patch; re-validate anchors (Dart 200, Super 2500) and
  re-run `--audit`. Use the Steam patch-notes feed (#459) as the "time to
  re-pull" signal.
