# BTD6 game-data dictionary — what the dump holds & where

A map of the **BTD Mod Helper game-data dump**
(`github.com/Btd6ModHelper/btd6-game-data`, v55.0 verified) so we stop
rediscovering where each fact lives. The premise behind the BTD6 data work is
that this dump is the game's *complete* exported model — so everything we need
(stats, names, descriptions, what an upgrade grants) **is** in here; the task is
knowing where, and which encoding to trust.

> This is a **discovery / reference doc**, not a binding contract — when it
> disagrees with the dump, the dump wins. Regenerate it per patch with
> `scripts/btd6_gamedata_inventory.py` (overview / `--domain X` / `--text-link`)
> and `scripts/parse_gamedata.py --audit` (numeric fidelity vs our committed
> data). Companion docs: `btd6-game-file-extraction-plan.md` (the mapper),
> `btd6-data-pipeline.md` (the wiki pipeline it augments).

## TL;DR — the source ladder

1. **Numbers** (cost, damage, pierce, rate, range, health, speed) → structured
   model fields. Reliable; refresh from the dump (gated by `--audit`).
2. **Names** → the game's own localization: `textTable.json`, reached via a
   model's `LocsKey` / `localizedNameOverride` (upgrades) or `displayName`
   (abilities). Player-facing names are all here.
3. **Descriptions / "what it grants"** → `textTable` `"<LocsKey> Description"`
   and `"<Hero> Level N Description"`. The game's own prose — authoritative and
   complete, and steadier than the structured effect models (see Juggernaut).
4. **Semantic effect models** (buffs / zones / subtowers) → inline in the tower
   models. Real but **encoded inconsistently and reworked between patches** — do
   not treat a single field as canonical; prefer the description for meaning and
   the structured value only where `--audit` says it is stable.

## Domains (v55: 17 dirs + 5 loose files)

`✓ = we use it / should • ~ = partial • ✗ = cosmetic/out of scope`

| Domain | Files | Root model | Holds | Us |
|---|---|---|---|---|
| **Towers/** | 2093 | `TowerModel` | towers, heroes (per level), paragons; per-crosspath state files; attacks/projectiles/abilities/zones/buffs/subtowers inline | ✓ |
| **Upgrades/** | 764 | `UpgradeModel` | per-upgrade `cost`/`xpCost`/`path`/`tier` + `LocsKey` (→ name & description). ~422 are player cards; the rest are hero-level internal entries | ✓ |
| **Bloons/** | 235 | `BloonModel` | every bloon **incl. bosses** (`Bloons/Bloonarius/…`, `Blastapopoulos/`, `Diamondback/` w/ Elite tiers): `maxHealth`, `speed`, `radius`, `armourMultiplier`, `isMoab/isBoss/isCamo/…`, children via `SpawnBloonsActionModel` | ✓ |
| **Powers/** | 27 | (mixed) | activated powers / placed-tower powers (Banana Farmer, Cash Drop…): `cost`, behaviors, `LocsKey` | ~ |
| **Rounds/** | 5181 | `RoundModel` | every round of **every mode** (not just standard 1–140): `BloonGroupModel` + `BloonEmissionModel` spawn timing | ~ |
| **IncomeSets/** | 7 | `IncomeSetModel` | per-round cash curves (e.g. ABR `RoundThresholdMultiplier`s) | ~ |
| **Knowledge/** | 134 | `KnowledgeModel` | Monkey Knowledge tree (meta-upgrade mods) | ✗ |
| **Bosses/** | 7 | `BossData` | **cosmetic only** — portraits/music/icons + `LocsKey`. Boss *stats* are in **Bloons/**, not here | ✗ |
| **Buffs/** | 91 | `BuffIndicatorModel` | **UI icons only** — buff *effects* are inline in the tower models | ✗ |
| **Maps/** | 89 | `MapDetails` | map metadata | ✗ |
| **Artifacts/**, **GeraldoItems/** | 568, 16 | `ItemArtifactData` / mods | Rogue Legends artifacts, Geraldo's shop | ✗ |
| **Achievements/**, **TrophyStoreItems/**, **Skins/**, **BloonOverlays/**, **Mods/** | — | — | cosmetics / achievements / game-mode mods | ✗ |

Loose files: **`textTable.json`** (12,127 keys — every name & description),
`paragonDegreeData.json` (degree-scaling constants; we already derive these),
`frontierData.json` (Boss/Legends scaling), `rogueData.json` (Rogue Legends),
`resources.json` (asset refs).

## Where each thing we need lives

### Stats
- **Towers/heroes/paragons** → `Towers/<Name>/…` `behaviors[AttackModel → weapons[] → projectile → DamageModel]` etc. Mapped by `parse_gamedata.py`; trust per `--audit` (CLEAN/DELTA only).
- **Bloons incl. bosses** → `Bloons/<Name>/<Name><tier>.json` `BloonModel.maxHealth/speed/radius/armourMultiplier`; children via `SpawnBloonsActionModel`. (Bloonarius skulls: 20k / 75k / 350k …)

### Names (player-facing — all present)
- **Upgrades** → `UpgradeModel.LocsKey` → `textTable[LocsKey]` (or `localizedNameOverride`).
- **Abilities** → `AbilityModel.displayName` directly (already English: "Cocktail of Fire", "Firestorm"). 100% coverage.
- **Spawned subtowers** → nested `towerModel.name` ("Phoenix").
- **Towers/heroes/bloons** → the entity's own `name`/`id` + `textTable`.
- **Not present:** *editorial* labels the wiki invented for unnamed internal
  parts (e.g. "Reanimate" for the necromancer attack — internally "Attack
  Necromancer"; the word appears in *descriptions* but never as that attack's
  name). These stay curated.

### Descriptions / "what an upgrade grants"
- `textTable["<LocsKey> Description"]` per upgrade (422 cards), per ability
  (`"<Ability> Ability Description"`), per hero level
  (`"<Hero> Level N Description"`, e.g. *Ezili Level 11 → "Increases pierce of
  reanimated Bloons by 50%."*). Game-authored prose — cleaner and more reliable
  than reverse-engineering the effect models, and not CC-encumbered (factual
  game strings). **Currently unused** by our pipeline — a clear gap to fill.

## Keystone decodes / lessons (don't relearn these)

- **`DamageModifierForTagModel` is a uniform `1.0` in v55** even where a tower
  really does bonus a tag. Ultra-Juggernaut's "excels at crushing Ceramic,
  Fortified and Lead" (per its own description) is **not** a `damageMultiplier`
  in v55 — the wiki's `Lead ×20 / Ceramic ×8` was the **v53** encoding, since
  reworked. Lesson: bonus-vs-tag is a *reworked* mechanic; trust the
  **description** for meaning, never a lone multiplier. The mapper now omits the
  `1.0` so it can't overwrite curated data.
- **`LocsKey` is the localization join** from a model to `textTable` — the
  reliable name + description link (not a key-by-internal-name lookup, which
  fails). `localizedNameOverride` overrides it on some upgrades.
- **Float precision**: the wiki rounds (`0.3616`); the dump is full precision
  (`0.36160713`). Compare at 4 dp (the `--audit` does).
- **List ordering**: the mapper flattens sub-projectiles depth-first; the wiki
  orders them differently. Align attacks/projectiles by `name` (and upgrades by
  `(path, tier)`) before diffing or overlaying — never by index.
- **Bosses live in Bloons/** (recursive), **not** `Bosses/` (cosmetic);
  **Buffs/** is icons, not effects.

## Open decode items (for the overlay / gaps PRs)

- **Buff / zone effect models** (~30 zone + ~25 buff `$type`s, inline in tower
  models): map the headline numeric effect fields where `--audit`-stable; lean
  on the textTable description for the rest. (`btd6_upgrade_detail_service`
  already reads `buffs[]`/`zones[]`/`subtowers[]`.)
- **textTable descriptions** → wire upgrade/ability/hero-level prose into our
  fixtures + AI grounding (the biggest untapped, authoritative win).
- **Bloons/bosses refresh** from `BloonModel` (we currently source bloons from
  the wiki).
- **Rounds (all modes) / IncomeSets** → only standard rounds come from the wiki
  today; the dump has every mode + the income curves.
