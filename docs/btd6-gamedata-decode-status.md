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
> - `scripts/btd6_decode_inventory_report.py` — **the SHA-pinned roll-up** of the
>   two above + the ranked zone/buff effect tail (decodable-number? /
>   has-curated-name?). Emits `docs/btd6-decode-inventory-v55.md`; validates
>   anchors first and aborts if they fail. *Re-run to refresh per patch.*

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

> **Step 0 ground-check (2026-06-03, before resuming data work).** Anchors
> re-validated at dump SHA `a3348a89…` (Dart 200, Super 2500 — PASS). The three
> post-#468 regressions were confirmed fixed in **production behavior**, not just
> green tests: (1) *enumeration over-refusal* — `deterministic_roster_reply`
> serves a costed roster for "list all heroes/towers" (answers, never refuses);
> (2) *renderer regression* — the noisy verified-data embed is deleted, answers
> render as guard-verified prose / the deterministic costed list; (3) *CT leak* —
> the resolver attaches **zero** live/CT entities to pricing questions
> (`live_entities=() ct_relics=()`), so a pricing answer's grounding cannot carry
> CT lines. Base is solid; data work proceeded.

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

- **Zones** (`zones[]`) — **0 of 28** zone model types mapped. *(Corrected
  2026-06-03: this doc previously said "0 of 12". The v55 dump carries **28**
  distinct `*ZoneModel` `$type`s inline in tower behaviors — see the SHA-pinned
  report `docs/btd6-decode-inventory-v55.md` §3a, the live ground truth. The
  old "12" was an undercount; do not inherit it.)*
- **Buffs** (`buffs[]`) — **0 of 38** buff/support model types mapped.
  *(Corrected from "37"; the dump has 38 distinct `*SupportModel`/`*BuffModel`
  `$type`s — report §3b. Close to the prior figure but not equal.)*
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

## Next steps — single ordered roadmap

> **Reconciled 2026-06-03 (post-#468)** against source — `parse_gamedata.py`
> (real flags: `--validate-anchors` / `--audit` / `--overlay` / `--all` /
> `--tower` / `--hero` / `--dry-run`; *there is no `--audit-faithful`*),
> `btd6_gamedata_inventory.py`, the committed `stats/*.json`, and the runtime
> (`btd6_context_service`, `btd6_upgrade_detail_service`). Tags: **[done]**,
> **[planned-existing]** (already scoped — in `--overlay`, the cutover, or a
> table above), **[new]** (not previously scoped). A reviewer's candidate a–e
> sequence is folded in by letter and **re-ordered by value-per-effort** within
> the hard safety constraints below.

**End goal (maintainer):** a complete **v55** dataset where every committed stat
shows v55 and is correct for v55; every special attack / ability carries **both**
its in-game description **and** its decoded stat-based effect; and every
curator-supplied name is preserved, never regressed to an internal model string.

**What now exists (shipped this cycle):**
- *Decode track* (tables above): `--audit` harness (#464); inventory tool +
  17-domain dictionary (#465); `damageAddative` fix (#465); the conservative
  `--overlay` **engine**, ability `displayName` names, and upgrade-description
  **extraction** (#466); subtowers (2 of 4 mechanisms); 11 wiki-missing heroes.
- *AI-answer track* — **#468**: the answer-faithfulness **verifier** (a model
  reply can no longer state a BTD6 name/number absent from the grounded payload —
  reject → regenerate-once → version-stamped refusal), the `btd6_list_roster`
  enumeration tool, and a deterministic verified-data embed. This is why step
  **2** is now pure upside (descriptions wired into grounding are guarded the
  moment they land) and why answer-caching **(7)** is unblocked.

**Hard safety constraints (not preferences):**
- Re-validate anchors (`--validate-anchors`: Dart 200, Super 2500) before any
  decode step; if they fail the dump moved — **stop**.
- Wiki↔dump projectile/ability *names* are not stable keys, so **never overlay a
  per-projectile/ability value by name**, and **never** let an overlay/cutover
  downgrade a curated name to an internal string. Hence the name guard **(3)**
  must precede any overlay/cutover touching ability-bearing entities (PR-1.5
  proved a naïve refresh regresses names), and it is the join key for **(5)**.

**Ordered next steps**

1. **SHA-pinned inventory/audit report** — ✅ **done (2026-06-03).**
   `scripts/btd6_decode_inventory_report.py` → `docs/btd6-decode-inventory-v55.md`,
   pinned to dump SHA `a3348a89c28b9db204f6f30776c5b072510584bc` (v55.0). One
   re-runnable artifact: per domain — present? / extracted? / ingest verdict
   (now/later/skip); the full `--audit` field table (verified **33 CLEAN · 15
   DELTA · 0 SUSPECT** — nothing is a systematic gap, so the whole extracted set
   is overlay-eligible); and the ranked zone/buff effect tail with the two
   effect-work columns **decodable-number?** / **has-curated-name?** (3/28 zone +
   11/38 buff `$type`s carry a decodable effect number; the rest fall back to the
   textTable description). The anchor gate runs first and aborts on failure.
   *This sizes steps 3–5 and turns the model-type tail into a worklist.*

2. **Wire `textTable` upgrade descriptions into fixtures + grounding** —
   ✅ **done (2026-06-03).** The game-authored prose (`LocsKey` →
   `textTable "<key> Description"`) is now written **inline** into the committed
   `stats/*.json` `upgrades[]` (**373/375** cards — the 2 gaps are a pre-existing
   mapper under-emission of one Ace/Wizard upgrade node, *not* a missing string)
   via `parse_gamedata.py --descriptions` (`apply_upgrade_descriptions` /
   `overlay_descriptions`), kept **separate from the numeric overlay** so the
   data diff is descriptions-only, and **names-frozen** by the same
   `assert_names_preserved` guard. The runtime surfaces it:
   `btd6_upgrade_detail_service` carries `UpgradeDetail.description` (joined by
   `(path, tier)`) and `render_upgrade_grounding` emits a
   `[btd6_upgrade] … (source: BTD6 in-game description)` line right after the
   identity line, so it grounds through the existing Pass-3c
   `grounding_for_query` seam — and #468 guards it automatically.
   - *Storage note:* inline (not a `paragon_descriptions.json`-style sidecar) on
     purpose — these are **verbatim, derived** game strings that SHOULD refresh
     on every dump re-pull, unlike the curated/paraphrased paragon prose the
     sidecar exists to protect.
   - *Follow-on (not done):* **ability descriptions** are effectively covered
     because abilities are granted by upgrade tiers (the `AbilityModel.description`
     field is empty in the dump). **Hero-level descriptions**
     (`"<Hero> Level N Description"` in `textTable`, e.g. *Ezili L11 → "+50%
     pierce to reanimated Bloons"*) are a **separate** extraction the mapper does
     not yet do — a clean next slice.

3. **Name-preservation guard** — ✅ **done (2026-06-03).** `parse_gamedata.py`
   now carries `collect_names` / `name_downgrades` / `assert_names_preserved`
   (+ `NameDowngradeError`). `overlay_payload` snapshots every curated `name` /
   `displayName` before mutating and hard-stops if any was emptied or altered —
   the numeric overlay is names-frozen by construction. The guard catches both
   PR-1.5 regression modes (tested): "Arctic Wind" → `""` *(emptied)* and
   "Reanimate" → "Attack Necromancer" *(internal model string)*. The future
   cutover passes the dump's internal-id set as `internal_names` to catch
   curated→internal swaps while still allowing deliberate curated→curated
   renames. This is the precondition for widening the overlay (4) and the join
   key for (5). *(The maintainer's binding ordering numbers this **step 2**,
   ahead of textTable; the doc's roadmap kept textTable at 2 because it keys off
   the reliable `LocsKey` and doesn't depend on the name match — both land
   before any ability-bearing overlay, so the order between them is moot.)*

4. **Numeric overlay expansion** — *[engine done #466 → expansion
   planned-existing]* *(reviewer c).* Widen `--overlay` from the 3 uniquely-keyed
   files to all `--audit` CLEAN/DELTA leaves, aligning nested lists by **name +
   damage signature** (never index), stamping v55. Stays in the safe envelope
   (cost/category, upgrades by `(path,tier)`, tier-level range/footprint);
   per-projectile/ability numbers stay curated. Delivers **stats show v55** for
   the safe set. *Rationale: after (1) sizes the CLEAN/DELTA set and (3) guards
   the names it touches.*

5. **Zones / buffs / subtower-tail effect decoding → towers cutover** —
   *[planned-existing — the cutover track; largest build]* *(reviewer e).* The
   **decoded-effect half** of the end goal. Each sub-step: decode the headline
   numeric where `--audit`-stable, else fall back to description-only (flagged).
   In order:
   a. **Zones** — 12 `*ZoneModel` types (`SlowBloonsZone`, `DamageOverTimeZone`,
      shove/windy/necromancer + economy); the zone's own `name` is empty →
      resolve via the owning upgrade's `LocsKey`.
   b. **Buffs** — 37 `*SupportModel`/`*BuffModel` types; a common core
      (Range/Pierce/Visibility/Rate/Speed/Cooldown/Damage support sharing
      `multiplier`/`additive` + `buffLocsName`→name) covers most; tail towers get
      a name-only node.
   c. **Subtower tail** — `MorphTowerModel` named-ref (Alchemist) +
      `BeastHandlerPetModel` (the 2 remaining mechanisms).
   d. **Economy-tower attack suppression**, then the **towers cutover** (`--all`,
      runtime name-adaptations, update the ~25 value-pinned tests), gated by
      `--audit` and (3). *Rationale: largest effort and the cutover blocker; uses
      (1) sizing and (3) name-joins.*

**Lower priority — post-#468 AI-answer enhancements (not roadmap-critical)**

6. **Audit-schema version column** — *[new]* the §5 observability item deferred
   from #468: a per-answer `game_version`/`data_version` column on
   `ai_decision_audit` so stale/disputed answers are queryable in-table (today the
   version is structured-logged only).
7. **Answer-caching** — *[new]* unblocked by #468's verifier: cache grounded BTD6
   answers keyed on (question, dataset version) — a served answer is now
   guaranteed faithful — and invalidate on a dataset-version bump.

**Smaller standing notes:** `count` has no exact dump field (stays curated); the
2 roster-wide `damageMultiplier != 1` tag cases aren't emitted (we read the
additive); bloons/bosses, Powers/Knowledge/Rounds/IncomeSets, and the paragon
overlay/cutover remain wiki-sourced / un-ingested (see the 🔴 table).

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
