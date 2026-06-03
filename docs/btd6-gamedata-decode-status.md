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

## What this effort is (and isn't)

The dump is the game's **complete** exported model, so for our needs (stats,
names, descriptions, what an upgrade grants) **nothing is missing** — the work
is decoding *where* each fact lives and *which field* to trust. The plan is a
**numeric overlay onto the curated wiki files** (refresh audit-trusted numbers
+ resolve names), **not** a wholesale rebuild (which would lose curated names
and the wiki's clean structure). See the dictionary's "source ladder".

## Done this session

| PR | What |
|---|---|
| **#464** (merged) | **Fidelity-audit foundation.** `parse_gamedata.py --audit` maps every tower/hero/paragon in-memory and diffs each numeric/bool leaf vs the committed wiki data, classifying each field CLEAN / DELTA / SUSPECT. Float-tolerant (4 dp), aligns dict-lists by `name` and upgrades by `(path, tier)`. |
| **#465** (merged) | **Discovery tooling + dictionary + two mapper bug fixes**: `btd6_gamedata_inventory.py`, `docs/btd6-gamedata-dictionary.md`, the `damageAddative` fix, and the spawn-model projectile fix. |
| **(this PR)** | **Conservative numeric overlay** (`parse_gamedata.py --overlay`, `--dry-run`): refreshes only the *unambiguously-keyed* v55 values onto the curated files — top-level cost/category, upgrade cost/xp by `(path, tier)`, and **tier-level** `range`/`footprintRadius`. Found a real wiki bug (Desperado mid-path range 28, *below* its base 60 — corrected to v55's 80) plus mermonkey xp / ace cost. **Per-projectile/ability stats are deliberately NOT overlaid** (see the naming lesson below). |

Two extraction bugs were found and fixed — **both the same failure mode: the
data was always present; the mapper read the wrong field or the wrong place.**

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

## Decoded & trusted now

- **Towers/heroes/paragons**: base cost, category, upgrade cost/xp/path/tier,
  per-tier/level damage, pierce, rate, range, radius, speed, lifespan,
  `immuneBloonProperties` → damage type, and **tag damage modifiers** (via
  `damageAddative`). Ability names via `displayName`.
- After the fixes the whole roster is **DELTA or CLEAN — nothing SUSPECT**; the
  DELTAs are explained: genuine v55 changes (the dump is newer than the v53
  wiki), benign representation differences, or flattening *style*.

## Not yet added / decoded (open items)

**Mapper / data completeness**
- **The overlay is applied, but only for uniquely-keyed fields** (cost/category,
  upgrade cost/xp, tier-level `range`/`footprint`). **Expanding it to
  per-projectile/ability stats is blocked** on reconciling wiki↔dump names (a
  `"Projectile"` ↔ `"BaseProjectile"` map, or a signature match on the
  *un*-changed fields), or restricting to provably-unambiguous tiers (exactly
  one attack × one projectile). Until then those stats stay curated — the audit
  shows them mostly CLEAN, so little is lost; the DELTAs are the risky ones.
- **Paragons not yet overlaid** (their combat lives in a `base` node, not
  `tiers`/`levels`; metadata is curated). Easy follow-up once the per-projectile
  story is settled.
- **Descriptions are unused.** Wiring `textTable` upgrade/ability/hero-level
  prose into our fixtures + AI grounding is the biggest untapped, authoritative
  win (would answer "what does Ezili L11 do?" from the game itself).
- **Buff / zone / subtower *effect* models** (~30 zone + ~25 buff `$type`s,
  inline in tower models): map headline numeric effects where `--audit`-stable;
  lean on the description for the rest. `btd6_upgrade_detail_service` already
  reads `buffs[]`/`zones[]`/`subtowers[]`.
- **`count`** (projectiles per shot): no single exact dump field
  (`len(weapons)` and `emission.count` both diverge ~1/3 of tiers); stays
  curated, never overlaid.
- **Residual projectile flattening style**: 111 attacks still differ in
  projectile count vs the wiki and 72 have duplicate names — the wiki
  names/groups sub-projectiles differently. Data is present; only grouping/names
  differ. Closing it fully means matching the wiki's naming, low priority.
- **The 2 `damageMultiplier != 1` cases** roster-wide are not emitted (we only
  read the additive). Negligible; revisit if a tower needs a multiplicative tag
  bonus.

**New domains (in the dump, not yet ingested)**
- **Bloons incl. bosses** from `BloonModel` (`maxHealth`/`speed`/`radius`/
  `armourMultiplier`/children) — we currently source bloons from the wiki.
- **Powers** (`Powers/`: Banana Farmer, Cash Drop…), **Knowledge** (Monkey
  Knowledge), **Rounds for all modes + IncomeSets** (the dump has every mode +
  income curves; we have only standard wiki rounds).

**Freshness**
- Re-pull the dump per patch; re-validate anchors (Dart 200, Super 2500) and
  re-run `--audit`. Use the Steam patch-notes feed (#459) as the "time to
  re-pull" signal.
