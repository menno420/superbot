# BTD6 game-data dictionary — what the dump holds & where

> **Status:** `reference`

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
> data). Companion docs: **`btd6-gamedata-decode-status.md`** (status, lessons &
> open items — *start there to pick up the work*),
> `btd6-game-file-extraction-plan.md` (the mapper),
> `btd6-data-pipeline.md` (the wiki pipeline it augments).

## TL;DR — the source ladder

1. **Numbers** (cost, damage, pierce, rate, range, health, speed) → structured
   model fields. Reliable; refresh from the dump (gated by `--audit`).
2. **Names** → the game's own localization: `textTable.json`, reached via a
   model's `LocsKey` / `localizedNameOverride` (upgrades) or `displayName`
   (abilities). Player-facing names are all here.
3. **Descriptions / "what it grants"** → `textTable` `"<LocsKey> Description"`
   and `"<Hero> Level N Description"`. The game's own prose — authoritative and
   complete; the readable companion to the structured numbers.
4. **Semantic effect models** (buffs / zones / subtowers) → inline in the tower
   models. Real and stable, but **read the right field** — the encoding is exact
   (no rounding), the field *names* are the catch (e.g. the tag damage bonus is
   `damageAddative`, a misspelled additive, not `damageMultiplier`). Decode the
   field, confirm with `--audit`, then trust it.

## Domains (v55: 17 dirs + 5 loose files)

`✓ = we use it / should • ~ = partial • ✗ = cosmetic/out of scope`

| Domain | Files | Root model | Holds | Us |
|---|---|---|---|---|
| **Towers/** | 2093 | `TowerModel` | towers, heroes (per level), paragons; per-crosspath state files; attacks/projectiles/abilities/zones/buffs/subtowers inline | ✓ |
| **Upgrades/** | 764 | `UpgradeModel` | per-upgrade `cost`/`xpCost`/`path`/`tier` + `LocsKey` (→ name & description). ~422 are player cards; the rest are hero-level internal entries | ✓ |
| **Bloons/** | 235 | `BloonModel` | every bloon **incl. bosses** (`Bloons/Bloonarius/…`, `Blastapopoulos/`, `Diamondback/` w/ Elite tiers): `maxHealth`, `speed`, `radius`, `armourMultiplier`, `isMoab/isBoss/isCamo/…`, children via `SpawnBloonsActionModel` | ✓ |
| **Powers/** | 27 | (mixed) | activated powers / placed-tower powers (Banana Farmer, Cash Drop…): `cost`, behaviors, `LocsKey` | ✓ (`--powers` → `powers.json`, 25 of 27 + effect factors) |
| **Rounds/** | 5181 | `RoundModel` | every round of **every mode** (not just standard 1–140): `BloonGroupModel` + `BloonEmissionModel` spawn timing | ~ |
| **IncomeSets/** | 7 | `IncomeSetModel` | per-round cash curves (e.g. ABR `RoundThresholdMultiplier`s) | ~ |
| **Knowledge/** | 134 | `KnowledgeModel` | Monkey Knowledge tree (meta-upgrade mods) | ✓ (`--knowledge` → `monkey_knowledge.json`, 119/134 with effect factors) |
| **Mods/** | 22 | mutator mods | per-mode rule mutators (cash/lives/rounds/cost, restrictions) | ✓ (`--modes` → `modes.json` structured `rules` blocks; taxonomy/prose stay curated) |
| **Bosses/** | 7 | `BossData` | portraits/music/icons + `LocsKey` here; boss *stats* live in **Bloons/** | ✓ (`--bosses` → `bosses.json`, reading both) |
| **Buffs/** | 91 | `BuffIndicatorModel` | **UI icons only** — buff *effects* are inline in the tower models | ✗ |
| **Maps/** | 89 files (86 player) | `MapDetails` | map metadata: `difficulty` (== folder), `hasWater`, `theme`, `IsStandard` | ✓ (`--maps` → 86 player maps; 3 non-player `IsStandard=False` filtered: Blons, Base Editor Map, Protect the Yacht) |
| **GeraldoItems/** | 16 | mods | Geraldo's shop (cash cost, unlock level, stock cadence) | ✓ (`--geraldo` → `geraldo_items.json` + effect factors) |
| **Artifacts/** | 568 | `ItemArtifactData` | Rogue Legends/Frontier artifacts+traits — real gameplay modifiers, but **spin-off-mode-only** | ✗ (out of main-game scope; pairs with `rogueData.json`) |
| **Achievements/**, **TrophyStoreItems/**, **Skins/**, **BloonOverlays/** | — | — | cosmetics / achievements | ✗ |

Loose files: **`textTable.json`** (12k+ keys — every name & description; live count
in the SHA-pinned inventory report), `paragonDegreeData.json` (degree-scaling
constants — **cross-checked exact vs our `paragon_degrees.power_for_degree`
100/100 on 2026-06-09**; the offline `paragon_math.threshold` fallback floors
where the game rounds, a known 48-boundary ×1-power edge), `frontierData.json`
(**Frontier event meta-mode balance** — no main-game boss scaling, despite the
old label), `rogueData.json` (Rogue Legends spin-off balance),
`resources.json` (GUID→asset-path lookup; zero stat content).

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

- **Tag damage bonus is in `damageAddative` (sic), not `damageMultiplier`.**
  On `DamageModifierForTagModel`, `damageMultiplier` is a neutral `1.0` in all
  but 2 of 2,843 cases; the real bonus is the *additive* in the misspelled
  `damageAddative` field. Ultra-Juggernaut "excels at crushing Ceramic,
  Fortified and Lead" = `damageAddative` **+8 / +5 / +20** — **identical to the
  wiki, never reworked**. Reading the wrong field once made it look removed.
  Lesson: when a field looks empty/neutral, the value is usually in a
  sibling field with an unexpected (or misspelled) name — find it, then
  `--audit` confirms it's CLEAN.
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

- **Buff / zone effect models** (12 zone + 37 buff `$type`s, inline in tower
  models): map the headline numeric effect fields where `--audit`-stable; lean
  on the textTable description for the rest. (`btd6_upgrade_detail_service`
  already reads `buffs[]`/`zones[]`/`subtowers[]`.)
- **textTable descriptions** → wire upgrade/ability/hero-level prose into our
  fixtures + AI grounding (the biggest untapped, authoritative win).
- **Bloons/bosses refresh** from `BloonModel` (we currently source bloons from
  the wiki).
- **Rounds (all modes) / IncomeSets** → only standard rounds come from the wiki
  today; the dump has every mode + the income curves.

## Runtime-formula facts the dump does NOT store (curated sidecars)

Some per-round quantities are **engine formulas**, not data — the dump's round
files hold only bloon *composition + spawn timing*, and `BloonModel` stores only
*base* stats. These live as curated, source-noted sidecars under
`disbot/data/btd6/` (each carries a `*_source` note stating it is absent from the
dump, mirroring the validation discipline):

- **Per-round XP / cash** → `round_xp.json` (`xp_source`); cash is derived from
  composition. Neither is a dump field.
- **MOAB-class late-game/freeplay health scaling** → `bloon_scaling.json`
  (`scaling_source`). MOAB-class bloons take a **piecewise-linear health multiplier
  `v(r)` from round 81** that **steepens sharply past round 100** (NOT a flat
  +2%/round): `v(100)=1.40`, `v(140)=5.00` — both cross-verified (BAD 28,000 @ r100;
  fortified BAD 200,000 @ r140). So a **BAD first spawns on round 100 already at
  28,000 HP** (20,000 base). `bloons.json` holds only the round-≤80 base; the ramp
  is applied at runtime by `btd6_data_service.bloon_health_at_round()`. So "where
  is the per-round health modifier in the dump?" → it isn't; it's this curve.
- **Round-scaled RBE** → same file's `freeplay` block +
  `btd6_data_service.bloon_rbe_at_round()`. Late-game RBE is the spawn tree
  recomputed with **every MOAB-class layer × `v(r)`** *and* **ceramics →
  superceramics** (RBE 68, vs base 104), which reproduces the authoritative
  **BAD @ r100 = 67,200 RBE** exactly (vs 55,760 base). It is *not* `base × v(r)`.
- **Paragon Elite-Boss damage ×2** → `paragon_degrees.ELITE_BOSS_DAMAGE_MULTIPLIER`.
  Paragons deal **double** their boss damage to **Elite** Bosses — a *global*,
  paragon-category-wide constant (NOT per-paragon: verified no `Elite` damage tag on
  the Dart/Ice paragon models, and no elite field in `paragonDegreeData.json`), flat
  across **all degrees** (Fandom *Extra Damage to Boss*: "applies … even at degree
  1"). So `elite_boss_multiplier(d) = boss_multiplier(d) × 2`. Same class as the
  freeplay/cash constants — the dump stores the base boss bonus, the engine doubles
  it for elite.

These per-round quantities are **player-queryable** via the reference commands
(prefix + slash): `/btd6ref income <start> [end]` (verified `round_cash`),
`/btd6ref rbe <start> [end]` (base + freeplay-scaled `round_rbe`), and
`/btd6ref round <n>` (composition + effective RBE). The income table deliberately
shows our audited total, which is *lower* than CyberQuincy's (it over-counts
fortified) — same divergence proven in the r100-120 cash validation.
