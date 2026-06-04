# BTD6 game-data decode & cutover — the deep explainer

> **Who this is for:** anyone (the maintainer, or a future session) who wants to
> *understand* — not just continue — the effort to source BTD6 data from the
> game's own files. It explains the **what**, **why**, and **how** from first
> principles, with concrete examples. For the live to-do list and current
> counts, see **`btd6-gamedata-decode-status.md`** (that doc is the status; this
> doc is the understanding behind it).

---

## 1. The problem in one paragraph

The bot answers BTD6 questions (tower stats, costs, what each upgrade does). Those
facts have to come from somewhere. Historically they came from **bloonswiki**, a
human-curated community wiki — readable, but it **lags** behind game patches and
has **gaps** (it never had stats for 11 heroes, two paragons, etc.). The game
itself ships a **complete, always-current** description of every tower/bloon/etc.
as encrypted data; a community tool (**BTD Mod Helper → "Export Game Data"**)
decrypts it and publishes it as JSON. That public dump is the ideal source: it's
complete and day-one current. The catch — it's written for the **game engine**,
not for humans: cryptic nested structures, internal code names, no friendly
labels. The whole effort is about **translating that dump into our schema
correctly**, then eventually **switching the bot over to it** (the "cutover").

---

## 2. The cast of characters (data flow)

```
 BTD Mod Helper dump            scripts/parse_gamedata.py            committed files                runtime
 (github, ~320 MB JSON)   ───►  "the mapper"                  ───►  disbot/data/btd6/stats/*.json  ───►  services + UI + AI
   Towers/ Bloons/ Maps/         walks the raw model,                 (+ maps.json, modes.json)            btd6_stats_service
   Upgrades/ textTable.json      flattens to OUR schema                                                    btd6_upgrade_detail_service
                                                                                                           btd6_context_service (AI)
```

- **The dump** is *not* committed to our repo (it's huge). You point the mapper
  at a local clone: `git clone --depth 1 https://github.com/Btd6ModHelper/btd6-game-data /tmp/btd6gd`.
- **The mapper** (`scripts/parse_gamedata.py`) is the translator. Run it with
  `--dump /tmp/btd6gd` plus a mode flag (see §9).
- **The committed files** are what the bot actually reads. Today **maps** and the
  **11 gap heroes** are game-data-sourced; **towers, rounds, bloons** are still
  wiki-sourced.
- **The runtime** never touches the dump — it only reads the committed files.

**Key consequence:** producing good mapper output is *not* the same as the bot
using it. The bot uses a file only once we **commit** the mapper's output over
the old one — and that final switch, for towers, is "the cutover" (§7).

---

## 3. What the raw dump actually looks like

Every tower is a folder of JSON files: a base file (`DartMonkey.json`) plus one
file per crosspath state (`DartMonkey-205.json` = top-path 2, mid-path 0,
bottom-path 5). Each file is a `TowerModel` whose guts live in a `behaviors`
array. Every behavior is tagged with a `$type`:

```json
{
  "behaviors": [
    { "$type": "…Behaviors.AttackModel, Assembly-CSharp",
      "range": 32.0,
      "weapons": [ { "rate": 0.95,
                     "projectile": { "behaviors": [
                        { "$type": "…DamageModel, Assembly-CSharp", "damage": 1.0,
                          "immuneBloonProperties": 17 } ] } } ] },
    { "$type": "…Behaviors.RateSupportModel, Assembly-CSharp",
      "multiplier": 0.75, "buffLocsName": "EliteSniperBuff" }
  ]
}
```

Three things make this hard, and they recur everywhere:

1. **Deep nesting.** A tower's *damage* isn't a field on the tower; it's on a
   `DamageModel` inside a `projectile` inside a `weapon` inside an `AttackModel`
   inside `behaviors`. The mapper walks down to find it.
2. **`$type` discrimination.** You find things by their model class name (the bit
   before the comma in `$type`). `_short_type()` extracts `"AttackModel"`,
   `"RateSupportModel"`, etc.
3. **Internal names, not player names.** `buffLocsName: "EliteSniperBuff"` — the
   player sees "Attack speed buff"; the dump has no friendly label at all. Some
   names live in `textTable.json` (e.g. ability `displayName`s resolve there),
   but many curated names (zone/buff labels like "Arctic Wind") are **not in the
   dump anywhere** — bloonswiki editors invented them.

---

## 4. The mapper, layer by layer

`parse_gamedata.py` flattens the raw model into our clean per-tier shape. Roughly
inside-out:

| Layer | Function | What it pulls from the raw model |
|---|---|---|
| Projectile | `_clean_projectile` | `pierce`/`radius` off the projectile; `damage` + damage-type off its `DamageModel`; speed/lifespan off its travel model |
| Sub-projectiles | `_collect_projectiles` / `_spawned_projectiles` | a bomb's *explosion* is a child projectile spawned on contact — flattened to a sibling, de-duped by signature |
| Attack | `_clean_attack` | `rate` (cooldown), `range`, and the list of projectiles |
| Ability | `_clean_ability` | activated-ability cooldown + its projectiles |
| Sub-towers | `_subtowers` | minions the tower spawns (Phoenix, Sentry, Sub Commander's…), themselves mapped like a mini-tier |
| **Zones** | `_zones` | area effects (`*ZoneModel`) — e.g. Ice Monkey's Arctic Wind slow |
| **Buffs** | `_buffs` | tower-buffs-other-towers effects (`*SupportModel`/`*BuffModel`) |
| Placement / category / cost / upgrades | `_placement`, `map_tower`, `_upgrades_for` | `towerSet` bit-flag → category; `areaTypes` → land/water; per-upgrade cost/xp from `Upgrades/<name>.json` |

The first chunk (combat numbers) is **done and proven faithful**. The last
two highlighted rows — **zones** and **buffs** — are the in-progress "effect
tail," and they're hard for the same reason: each sub-type speaks its own dialect.

---

## 5. Buffs — the hard part, in depth

### 5.1 What a buff is
A **buff** is one tower improving *other nearby* towers. Concrete examples:
- **Village** → range/speed to nearby monkeys.
- **Druid "Poplust"** → +15% attack speed and +15% pierce to nearby towers.
- **Sub Commander** → +4 pierce and ×2 damage to nearby subs.
- **Ninja "Shinobi Tactics"**, **Buccaneer "Trade Empire"**, **Sniper Elite Defender**, etc.

In our schema each buff is a small record the runtime renders:
```json
{ "name": "Poplust buff", "ratePercentage": 0.15, "piercePercentage": 0.15 }
```

### 5.2 Why it's hard: every buff type is a different dialect
There is **no single "buff" shape** in the dump. There are ~38 *distinct* buff
model `$type`s, each with its own field names and its own meaning:

| Player sees | Raw model `$type` | Raw field → our field |
|---|---|---|
| Sniper speed buff | `RateSupportModel` | `multiplier` 0.75 → `rateMultiplier` |
| Poplust | `PoplustSupportModel` | `ratePercentIncrease` → `ratePercentage` |
| Sub Commander | `SubCommanderSupportModel` | `pierceIncrease`→`pierceAdditive`, `damageScale`→`damageMultiplier` |
| Mermonkey pierce | `PiercePercentageSupportModel` | `percentIncrease` → `pierceMultiplier` |
| Trade Empire | `TradeEmpireBuffModel` | `damageBuff`→`damageAdditive`, `ceramicDamageBuff`→`damageAdditiveForCeramic`, … |
| Engineer/Spike start-of-round | `StartOfRoundRateBuffModel` | `modifier`→`rateMultiplier`, `duration`→`lifespan` |
| Wizard undead | `PrinceOfDarknessZombieBuffModel` | `damageIncrease`→`damageAdditive`, `distanceMultiplier`→`lifespanMultiplier` |

So "decode the buffs" = **reverse-engineer, type by type, which cryptic raw field
maps to which clean field.** That mapping table lives in `_BUFF_FIELD_MAP` in the
mapper. There is no shortcut — each type is its own little puzzle.

A second twist: buff *names* are internal (`PoplustBuff`, not "Poplust buff").
The friendly names aren't in the dump, so we extract the **numbers** from the dump
and keep the **names** from the wiki.

### 5.3 How we prove a mapping is right (the arbiter rule)
We don't trust a guess. We have an **answer key**: the trusted wiki numbers
already sit in the committed `stats/*.json`. So for a candidate mapping we:

1. Find a tower that has this buff (Sniper for `RateSupportModel`).
2. Read the raw dump value (`multiplier: 0.75`).
3. Read the committed wiki value for that exact tower (`rateMultiplier: 0.75`).
4. **Only if they match exactly** do we add the mapping to `_BUFF_FIELD_MAP`.

This is the **binding discipline**: *the committed value is the arbiter, not
your intuition.* A vivid example — `PrinceOfDarknessZombieBuffModel` has a field
`distanceMultiplier: 1.5`. Mapping "distance" to "lifespan" *looks* wrong. But the
trusted wiki buff says `lifespanMultiplier: 1.5`, and 1.5 appears on no other raw
field — so the game really does store the zombie's lifespan as "distance," and the
mapping is **correct**. The data overruled the gut. (It cuts the other way too:
a value that coincidentally matches but is semantically absurd must be rejected —
so single-value, single-tower "matches" get extra scrutiny.)

### 5.4 Why it stopped at 8 of 38 (this is a boundary, not a quota)
The 8 confirmed types are the ones where the answer-key method *works*. The
remaining ~30 can't be confirmed this way, for one of two reasons:

- **No answer key.** For many buffs the wiki *never recorded* a buff entry, so
  there's nothing trustworthy to compare against. Example: the dump gives Monkey
  Village a `RateSupportModel 0.85`, but our committed Village file has **no**
  matching buff row. Mapping it would be an unverifiable guess.
- **Transformed values.** Some dumps store a raw multiplier (`1.1`) where the
  wiki stores a percentage (`0.1`) or an additive. The values don't match
  directly, so confirming the *transformation* requires more than value-equality.

Under the maintainer's standing rule (**correctness over speed**), writing an
unconfirmable number is worse than leaving it out — a wrong number silently
corrupts grounding the AI then states as fact. So the honest stopping point is 8.
The rest need **per-model analysis** (read the model's purpose, find any tower
with a matching committed value, or accept that it can only be validated *after*
the cutover when the dump itself becomes the source of truth).

### 5.5 Why adding buffs to the mapper is *safe* even before the cutover
The mapper now emits `buffs[]` on every tier, but towers aren't cut over, so does
that pollute anything? No — because of how the **audit** (§6) compares. Buff
entries carry the **internal** name (`PoplustBuff`); the committed wiki entries
carry the **curated** name ("Poplust buff"). The audit aligns lists **by name**,
the names never match, so our buff entries are simply *ignored* by the audit. That
keeps the audit "nothing-SUSPECT" while we build the mapping up incrementally.

---

## 6. The audit — how we know the mapper is faithful

`parse_gamedata.py --audit` is the safety instrument. It maps every
tower/hero/paragon **in memory** and diffs each numeric/bool leaf against the
committed (trusted) value, bucketing every field:

- **CLEAN** — mapper matches the trusted data exactly → safe.
- **DELTA** — a few values differ, and they're recognizably *real v55 changes*
  (e.g. a tower that got rebalanced) → review, then accept.
- **SUSPECT** — >20% of a field's values differ → a *systematic mapper bug* →
  never trust until fixed.

The whole roster currently audits as **CLEAN/DELTA, nothing SUSPECT** — that's the
evidence the mapper is trustworthy. Two design details make the audit fair:
- It aligns lists **by name** (and upgrades by `(path,tier)`), so a different
  ordering doesn't show up as fake diffs.
- It only compares leaves present in **both** trees, so fields the mapper
  deliberately omits aren't counted as differences.

This audit is *why* the buff work can be incremental and safe: every step is
checked against the trusted answer key automatically.

---

## 7. The cutover — what it is and what gates it

### 7.1 Definition
**The cutover** is the moment we replace the committed *tower* files (currently
wiki-sourced) with **game-data-sourced** content. Today the mapper *can* produce
tower files, but we haven't committed them over the wiki ones, so the bot still
reads wiki data for towers. The cutover flips that switch — making the dump the
source of truth for towers, the way it already is for maps and the 11 gap heroes.

### 7.2 Two ways to do it
- **Numeric overlay (conservative, partial).** Keep the curated wiki files;
  copy in *only* trustworthy game-data numbers, field by field. This is what
  `--overlay` does today, and it's deliberately tiny — `_OVERLAY_FIELDS` is
  currently just `{"range", "footprintRadius"}` plus upgrade cost/xp, because
  only uniquely-keyed, unambiguous fields are safe to overlay by name. It's the
  "keep everything, freshen a few numbers" approach.
- **Game-native cutover (the end goal).** Adopt the mapper's full output as the
  committed files — the dump's *structure and numbers* lead, with wiki only as a
  cross-check. This is the real destination; it needs the effect tail finished.

### 7.3 The three blockers (all about *not regressing*)
1. **Buffs/zones aren't fully decoded.** If we cut a tower over today, any buff or
   zone we haven't mapped yet would come out **empty or wrong** — the bot would
   know *less* about Village/Druid/Ninja than it does now. So buff/zone decoding
   is the gate.
2. **The name-downgrade trap.** The dump only has internal names. A naïve cutover
   would replace "Cocktail of Fire" with "WallOfFire" — a visible regression.
   There is a hard guard: `NameDowngradeError` + `assert_names_preserved` /
   `overlay_payload` — the cutover must **keep the curated names and take only the
   numbers**. (PR-1.5 proved a naïve refresh regresses names; that's why the guard
   exists and must run before any ability-bearing cutover.)
3. **Economy towers look like attackers.** The dump gives Banana Farm a nominal
   `AttackModel`, which would make the bot think a farm is a combat tower. Needs a
   "no real damage ⇒ not combat" filter first. (Also: tower files must carry
   `paragon_cost`/`paragon_name`, which aren't cleanly in the dump and must be
   preserved like the paragon metadata.)

### 7.4 The nice property
For buff types with **no wiki answer key**, the cutover itself becomes the
validation: once towers are game-sourced, the dump *is* the truth, so those
numbers are correct by definition rather than something to cross-check. So the
sequence is: **decode buffs/zones far enough → satisfy the guards → cut over →
the remaining unverifiable types resolve by becoming the source.**

---

## 8. A buff, end to end (worked example: Druid Poplust)

**In the dump** (`Towers/Druid/Druid-015.json`, a `behaviors[]` entry):
```json
{ "$type": "…Behaviors.PoplustSupportModel, Assembly-CSharp",
  "ratePercentIncrease": 0.15, "piercePercentIncrease": 0.15,
  "buffLocsName": "PoplustBuff", "name": "" }
```
**The committed wiki truth** (`disbot/data/btd6/stats/druid.json`, tier `005`):
```json
{ "name": "Poplust buff", "ratePercentage": 0.15, "piercePercentage": 0.15 }
```
**Confirmation:** raw `ratePercentIncrease 0.15` == wiki `ratePercentage 0.15`,
and `piercePercentIncrease 0.15` == `piercePercentage 0.15`. Exact → safe. So
`_BUFF_FIELD_MAP` gains:
```python
"PoplustSupportModel": {
    "ratePercentIncrease": "ratePercentage",
    "piercePercentIncrease": "piercePercentage",
},
```
**What the mapper now emits** (audit-safe — internal `name`):
```json
{ "kind": "PoplustSupport", "name": "PoplustBuff",
  "ratePercentage": 0.15, "piercePercentage": 0.15 }
```
At cutover, the merge keeps the wiki `name` ("Poplust buff") and takes these
numbers — best of both.

---

## 9. How to make progress next session (concrete loop)

1. **Clone + anchor-gate.** Clone the dump; run
   `python3.10 scripts/parse_gamedata.py --dump /tmp/btd6gd --validate-anchors`.
   If Dart≠200 / Super≠2500, the dump moved — **stop**.
2. **Pick a buff/zone type** from the worklist in `btd6-gamedata-decode-status.md`
   / the SHA-pinned `btd6-decode-inventory-v55.md` (it ranks every type by
   "decodable-number?" and "has-curated-name?").
3. **Confirm it** against the committed value on a matching tier (the arbiter
   rule, §5.3). A quick discovery harness can *suggest* candidates by value
   coincidence, but it produces false positives — **always hand-vet**.
4. **Write only confirmed mappings** into `_BUFF_FIELD_MAP` (buffs) or extend
   `_zones`; for `SCHEMA_FIRST` types (the number exists but the runtime renderer
   `btd6_upgrade_detail_service._BUFF_FIELDS` has no field for it — e.g.
   projectile speed/radius, freeze duration), **extend the renderer first**.
5. **Re-run `--audit`** — it must stay nothing-SUSPECT — and add a hermetic test
   in `tests/unit/scripts/test_parse_gamedata.py`.
6. **Gate** with `python3.10 scripts/check_quality.py --full`, then PR.
7. When buffs+zones are complete enough: do the **cutover** (numeric overlay
   widening, or game-native), gated on the name guard + economy filter.

---

## 10. Glossary

- **Dump** — the BTD Mod Helper game-data export (the game's own model JSON).
- **Mapper** — `scripts/parse_gamedata.py`; translates dump → our schema.
- **Tier** — one crosspath state of a tower (e.g. `205`); our per-state stat node.
- **Buff** — a tower improving other nearby towers (`*SupportModel`/`*BuffModel`).
- **Zone** — an area effect (`*ZoneModel`), e.g. a slow field or damage-over-time.
- **Sub-tower / minion** — a tower the tower spawns (Phoenix, Sentry, …).
- **`_BUFF_FIELD_MAP`** — the per-type "raw field → our field" table; the heart of
  buff decode; only **confirmed** mappings live here.
- **Audit** — `--audit`; per-field CLEAN/DELTA/SUSPECT fidelity check vs the
  committed wiki truth.
- **Cutover** — switching committed tower files from wiki-sourced to game-sourced.
- **Overlay** — the conservative "keep curated files, freshen a few numbers"
  refresh (`--overlay`, `_OVERLAY_FIELDS`).
- **Name-downgrade guard** — `NameDowngradeError`; forbids replacing a curated
  name with an internal one during overlay/cutover.
- **Arbiter rule** — confirm every mapping against the committed value, not
  against semantic intuition.
