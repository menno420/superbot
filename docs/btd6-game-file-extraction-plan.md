# BTD6 game-file extraction — plan & handoff

> **Status:** MAPPER BUILT (PR 1) + **FIDELITY AUDIT (PR 1.5, this PR).**
> `scripts/parse_gamedata.py` maps the dump and now also self-audits
> (`--audit`) against the committed wiki data. **PR 1.5 reframes the plan** —
> see "Fidelity audit findings (PR 1.5)" below — because investigating the
> cutover surfaced that the real blocker is **mapper fidelity**, not the P1/P2
> the section further down assumed. A blind overlay would corrupt correct data.
> The revised path is: **PR 1.5 audit foundation → PR 2 safe overlay (CLEAN/
> DELTA fields only) → PR 3 per-entity gaps + new domains (Bosses/Powers).**
> This is a *roadmap* doc — when it disagrees with the source, the source wins.
>
> **Last verified:** 2026-06-03, in-sandbox, against
> `Btd6ModHelper/btd6-game-data` commit `a3348a89` (dumped 2026-06-02, v55.0).

## Fidelity audit findings (PR 1.5) — the *real* blocker

Investigating the cutover (overlay game-data numbers onto the curated wiki
files) surfaced that the P1/P2 framing below is **secondary**. The dominant
blocker is **mapper extraction fidelity**, now made measurable by
`python3.10 scripts/parse_gamedata.py --dump <clone> --audit`, which maps every
tower/hero/paragon in-memory and diffs each numeric/bool leaf against the
committed (wiki-sourced) ground truth, classifying every field:

- **CLEAN** — mapper matches the trusted data → safe to overlay.
- **DELTA** (≤20% of leaves differ) — sparse, recognizably *genuine v55
  changes* (e.g. `super_monkey` rate `0.06→0.05`, `desperado` range `28→80`,
  `boomerang` pierce `30→15`) → review then overlay.
- **SUSPECT** (>20%) — a systematic mapper/representation gap → **never overlay.**

**What the audit revealed (and PR 1.5 fixes / accounts for):**

1. **Tag damage bonus lives in `damageAddative` (sic), not `damageMultiplier`.**
   `DamageModifierForTagModel.damageMultiplier` is a neutral `1.0` in all but 2
   of 2,843 cases roster-wide; the real bonus is the *additive* in the
   misspelled `damageAddative` field (Ultra-Juggernaut Lead **+20** / Ceramic
   **+8** are right there, identical to the wiki — the mechanic was **never
   reworked**). The original mapper read only `damageMultiplier`, so it missed
   2,467 real bonuses and made it look removed. **Fixed:** read `damageAddative`
   → `damageModifierFor<Tag>`. After this the audit's `damageModifierFor*`
   fields are **CLEAN** (exact wiki match), and the four heroes re-emit with
   their **correct** bonus values restored (captain_churchill, corvus, ezili,
   pat_fusty). *(An earlier pass mistakenly dropped these as neutral `1`s before
   the real field was found.)*
2. **Float precision** — the wiki rounds (`0.3616`); the dump is full precision
   (`0.36160713`). The audit compares numbers rounded to 4 dp so this
   representation noise doesn't read as a change.
3. **Projectile / attack ordering** — the mapper flattens sub-projectiles
   depth-first; the wiki orders them differently, so an *index* diff reports
   every field as a phantom swap. The audit aligns dict-lists by `name` (and
   upgrades by `(path, tier)`); after that the whole roster is **DELTA or
   CLEAN, nothing SUSPECT** — the mapper is far more faithful than a raw diff
   count suggests. **Deep same-name sub-projectiles** still fall back to
   positional and account for most residual DELTAs; PR 2's overlay must align
   them by name **and** damage signature before writing.

**Names — the part of P1 that is *unsolvable from the dump*.** Abilities carry
`displayName` directly (100%: "Cocktail of Fire", "Firestorm"); spawned
subtowers carry `towerModel.name` ("Phoenix"). But curated names like
**"Arctic Wind"** (the `SlowBloonsZoneModel.name` is empty) and **"Reanimate"**
(the attack is internally "Attack Necromancer") are **not in the dump or
`textTable.json` at all** — they are bloonswiki-curator-supplied. So the
overlay must *preserve* curated names, never regenerate them; `textTable` is
**not** the missing link the P1 note below assumed.

**Bottom line for PR 2 (the safe overlay):** refresh **only audit-CLEAN/DELTA
numeric leaves** (`damage`, `range`, `rate`, `pierce`, `cost`, `xp`,
`cooldown`, `speed`, `immuneBloonProperties`, …) onto the curated tree, align
nested lists by name+signature, resolve ability names via `displayName`, and
leave every curated name/description/zone/buff label untouched. The fields the
audit flags as systematically divergent stay curated.

## Build-session results (PR 1)

**Done & validated in-sandbox:**
- `scripts/parse_gamedata.py` — clones-agnostic mapper (`--dump <clone>`,
  `--tower`/`--hero`/`--all`/`--validate-anchors`/`--dry-run`). Hermetic tests in
  `tests/unit/scripts/test_parse_gamedata.py` (synthetic `TowerModel` fixtures,
  no vendored dump).
- **`dart_monkey` round-trips exactly** to the committed wiki-sourced file
  (15 upgrades, 64 crosspath tiers, every projectile value identical).
- **11 wiki-missing heroes now have per-level stats** (`stats/heroes/*.json`):
  admiral_brickell, benjamin, captain_churchill, corvus, etienne, ezili,
  obyn_greenfoot, pat_fusty, psi, rosalia, silas. Runtime/UI/AI pick them up
  with no code change (file-presence driven). Tests that asserted the old gap
  (obyn "no module") were flipped to assert the closed gap.

**Verified source→target derivations (mapper internals):**
- `towerSet` is a **bit-flag** enum: `1=primary, 2=military, 4=magic, 8=support`.
- `areaTypes` entries: `1=water, 2=land, 4=track` → `placeableOn*`.
- `footprint` is a **top-level** model (not in `behaviors[]`) → `footprintRadius`.
- Combat damage often lives on a **child** projectile, not the thrown one
  (bomb → `CreateProjectileOnContactModel` → "Explosion"). The mapper recurses
  `CreateProjectile*Model` and flattens children as sibling projectiles
  (depth-capped), matching the wiki's "Projectile" + "Explosion" shape.
- Upgrades: each tower-state file lists only the upgrades reachable from it, so
  the full 15 are the **union across all crosspath files**; cost/xp/path/tier
  come from `Upgrades/<name>.json` (`path`/`tier` 0-indexed → +1).
- Version stamp = the dump's git **commit message** (`55.0`).
- Names: model names are `"<Class>_<Display>_"` → strip prefix + trailing `_`.

**Deferred to PR 2 (the tower cutover):** three mapper features are needed
before replacing the tower files without regression —
1. **Subtowers / minions** — `subtowers[]` (alchemist Transformed Monkey, wizard
   Reanimate/Prince of Darkness). Read by `btd6_upgrade_detail_service`; the
   spawn mechanism is a separate tower model referenced from an attack — not yet
   mapped.
2. **Damage zones** — `zones[]` (wizard wall of fire, etc.), also read by the
   upgrade-detail service.
3. **Economy-tower attack suppression** — the raw model gives Banana Farm a
   nominal `AttackModel`, so `has_combat_stats` trips true; needs a "no real
   damage ⇒ not combat" filter so the Pro button/embed stay off.
   Also: tower files must carry `paragon_cost`/`paragon_name` (catalog metadata,
   not cleanly in the dump) — preserve like the paragon `cost`/`canonical`.

### ⚠ Two hard prerequisites the v55 cutover is BLOCKED on (verified PR 2 session)

Attempting the hero/paragon refresh surfaced two blockers that make *any*
wholesale v55 cutover regress trusted, human-facing data unless solved first.
**Do these before re-running `--all` for committed data.**

**P1 — display-name localization (`textTable.json`).** The raw model names
features with **internal identifiers**, not the player-facing names the wiki
curated. Verified regressions a naïve refresh causes:
- Gwendolin ability: wiki `"Cocktail of Fire"` → raw `"WallOfFire"`.
- Wizard 0-0-5 necro attack: wiki `"Reanimate"` → raw `"Attack Necromancer"`.
- Many tower/hero/paragon abilities, zones, buffs, and even some attack labels.

`textTable.json` **does** contain the display strings (`"Cocktail of Fire"`,
`"Reanimate"`, `"Arctic Wind"` are all present), but it is **not keyed by the
internal model name** (`"WallOfFire"` is absent as a key). The mapper must find
the model→textTable link — likely a `displayName`/`nameKey`/`*Description`
reference on the model or the owning upgrade — and resolve names through it.
Until then, refreshing any entity with abilities/zones/buffs/subtowers
**downgrades** its names from curated to internal.

**P2 — subtower / zone / buff model mapping (~10 model types).** The mapper as
built (PR 1) flattens attacks/projectiles and nested sub-projectiles only. It
does **not** yet produce `subtowers[]`, `zones[]`, or `buffs[]`, which the
runtime (`btd6_upgrade_detail_service`) reads. Affected entities are widespread:
- **subtowers** (nested `TowerModel`, e.g. via `MorphTowerModel`): alchemist
  Total Transformation, wizard Necromancer minions, Adora (lvl 10+), paragons
  Master Builder / Navarch of the Seas.
- **zones** (`NecromancerZoneModel`, DoT-zone projectiles): ice_monkey Arctic
  Wind, druid Thorn zones, heli MOAB Shove, striker_jones, paragon Mega Massive.
- **buffs** (various buff models → `damageAdditive`/`rateMultiplier`/… fields):
  village, ninja Shinobi, sniper, mermonkey, sub, buccaneer, engineer, druid
  Poplust, mortar, spike, desperado Nomad, wizard Undead, several paragons.

Because of P1+P2, the **only** entities that refresh cleanly today are those
with pure attack/projectile stats and **no** abilities/zones/buffs/subtowers
(`geraldo`, `apex_plasma_master`) — negligible value. So the cutover is
deliberately **not** shipped yet; PR 1's gap-closure (the 11 wiki-missing
heroes) stands as the delivered increment.

**PR 2 (cutover), once P1+P2 land:** run `--all`, replace every tower + refresh
the 6 module heroes and 13 paragons (incl. upgrading the 2 prose paragons to
module-exact), preserve `paragon_cost`/`paragon_name`, suppress economy
non-combat attacks, and update the ~25 value-pinned tests for the v55 numbers.

---

## TL;DR for the next session

1. The hard part (decrypting BTD6's encrypted Unity assets) is **already done
   for us** by a public dump. Just read it.
2. **Build `scripts/parse_gamedata.py`** that maps the dump's raw `TowerModel`
   JSON → our `disbot/data/btd6/stats/<id>.json` schema. Start with
   `dart_monkey` (anchors proven) + `benjamin` (a wiki-missing hero, proves
   the gap closes), validate against anchors, then expand.
3. The **mapping spec is below** — exact source→target fields, the combat-stat
   nesting, the cost model, the name allowlist, all verified.
4. Claude does the build **in-sandbox** (data is reachable here). The **user's
   role is light** — decisions + a bot sanity-check + (optionally, later) a PC
   self-export for day-one freshness. *No tablet/Termux/UnityPy needed.*

---

## Why this exists (the problem)

The BTD6 cog's structured stats (`disbot/data/btd6/stats/*.json`) come from
**bloonswiki.com** via `scripts/fetch_bloonswiki.py`. Two weaknesses:

1. **Timing lag.** bloonswiki updates *per-tower, over hours-to-days* after a
   patch. Verified 2026-06-03: with v55 released that day, **zero** towers on
   the wiki were at `55.0` (newest `54.0`; many still `53.0`/`52.2`).
2. **Coverage gaps — the wiki simply lacks the data.**
   - **Only 6 of 17 heroes** have stat modules: `adora`, `geraldo`,
     `gwendolin`, `quincy`, `sauda`, `striker_jones`. The **11 missing**:
     `admiral_brickell`, `benjamin`, `captain_churchill`, `corvus`,
     `etienne`, `ezili`, `obyn_greenfoot`, `pat_fusty`, `psi`, `rosalia`,
     `silas`.
   - **2 of 13 paragons** are hand-transcribed from prose
     (`is_prose_sourced`): **Root of all Nature** (Druid) and **Herald of
     Everfrost** (Ice Monkey).

Patch notes can't fix this — they're **deltas, not full state** (a hero that
isn't rebalanced appears in zero notes). **Source accuracy ranking: game files
> bloonswiki > patch notes.** Game data is the only **complete** *and*
**day-one** source.

## What already shipped (interim / maintenance layer — merged)

- **PR #459:** Steam `GetNewsForApp` ingestion (appid `960090`, no key) →
  `btd6_patch_notes` + `btd6.version_detected` event → `btd6_version_announce`
  posts to a channel (`!btd6ops announcechannel`). Prose notes + "new version"
  signal.
- **PR #460:** `scripts/btd6_patch_diff.py` — verifies patch-note `old > new`
  lines against on-disk stats, buckets them (CLEAN/LIKELY/STALE/REVIEW/…).
  *Also useful to verify a fresh game-data dump's currency.*

These stay current *between* dumps; they don't replace a complete source.

---

## The data source (VERIFIED)

**Repo:** `https://github.com/Btd6ModHelper/btd6-game-data` — the committed
output of **BTD Mod Helper**'s built-in **"Export Game Data"** button
(decrypts the game's internal model and dumps it to plain JSON). This is *not*
something we extract; we **consume a public dump**.

**Verified facts (commit `a3348a89`, dumped 2026-06-02, message "55.0"):**

| Check | Result |
|---|---|
| Anchor — Dart Monkey base cost | `200.0` ✅ |
| Anchor — Super Monkey base cost | `2500.0` ✅ |
| All 11 wiki-missing heroes present | ✅ (40-48 files each; Benjamin base lvl `cost=1200`) |
| Both prose paragons present | ✅ `Towers/Druid/Druid-Paragon.json`, `Towers/IceMonkey/IceMonkey-Paragon.json` (cost 400) |
| Freshness | **v55.0**, dumped the day before — *ahead of bloonswiki* |
| Size | ~9,900 files, ~320 MB |

### How to read it reliably (next session)

The REST API is rate-limited on the shared sandbox IP — **don't** use it. Use
the git protocol or raw content:

```bash
# Option A — full shallow clone (~320 MB, simplest, gives every file):
git clone --depth 1 https://github.com/Btd6ModHelper/btd6-game-data /tmp/btd6gd

# Option B — partial clone for the TREE only (cheap), then raw-fetch files:
git clone --depth 1 --filter=blob:none --no-checkout -q \
    https://github.com/Btd6ModHelper/btd6-game-data /tmp/btd6gd
git -C /tmp/btd6gd ls-tree --name-only HEAD:Towers          # dir listings work
# NOTE: lazy `git cat-file -p HEAD:<path>` was FLAKY (returned empty). Prefer
# raw content for file bodies (sha-pinned = reproducible):
curl -s "https://raw.githubusercontent.com/Btd6ModHelper/btd6-game-data/a3348a89c28b9db204f6f30776c5b072510584bc/Towers/DartMonkey/DartMonkey.json"
```

### Layout

```
Towers/<Name>/<Name>.json            # base tower, tiers [0,0,0]; .cost = PLACEMENT cost
Towers/<Name>/<Name>-PPP.json        # one file per crosspath state (PPP = tier digits)
Towers/<Name>/<Name>-Paragon.json    # paragon (single flat node)
Towers/<Hero>/<Hero> N.json          # heroes: one file per level N (2..20)
Upgrades/<Upgrade Name>.json         # per-upgrade cost/xp/path/tier  ← upgrade costs live HERE
paragonDegreeData.json               # universal degree-scaling constants (we already derive these)
textTable.json                       # display-name localization (likely optional for us)
Bloons/ Rounds/ Bosses/ Powers/ ...  # other game data (future scope)
```

---

## The mapping spec (VERIFIED source → target)

**Schema lineage:** our `stats/*.json` were produced by
`scripts/parse_bloonswiki.py` parsing the wiki's *copy of the game model*, so
field names already align with the game model. The new mapper walks the
**raw** model (`behaviors[]` with `$type`s) and flattens it to the same shape.

**Mirror these existing producers / sample files for the target shape:**
- Towers → `parse_bloonswiki.parse_stats_json` + `disbot/data/btd6/stats/dart_monkey.json`
- Heroes → `parse_bloonswiki.parse_hero_stats_json` + `stats/heroes/adora.json`
  (shape: `{hero_id, canonical, game_version, source, base_cost, cost_chimps, levels:{1..20:{range, attacks, targetType*, …}}}`)
- Paragons → `parse_bloonswiki.parse_paragon_stats_json` + `stats/paragons/glaive_dominus.json`
  (shape: `{paragon_id, tower_id, canonical, …, cost, cost_chimps, xp, base}`)
- Reuse helpers: `utils/btd6/damage_types.py` (decodes `immuneBloonProperties`),
  `utils/btd6/paragon_degrees.py` (derives the degree table — keep deriving),
  `utils/btd6/difficulty_costs.py` (Medium→other difficulties).

**Field sources (verified against DartMonkey):**

| Target | Source in the dump |
|---|---|
| base placement cost | `Towers/<Name>/<Name>.json` → `cost` (**flat across crosspaths — NOT cumulative**) |
| category | base file → `towerSet` (Primary/Military/Magic/Support) |
| per-upgrade `name/cost/xp` | `Upgrades/<Upgrade Name>.json` → `name`, `cost`, `xpCost`, `path`, `tier` (**`path`/`tier` are 0-indexed** → +1 for our schema) |
| per-tier **damage** | crosspath file → `behaviors[AttackModel].weapons[].projectile.behaviors[DamageModel].damage` |
| per-tier **pierce** | `…weapons[].projectile.pierce` (and `maxPierce`) |
| per-tier **rate/cooldown** | `…weapons[].rate` (seconds; Dart base `0.95`) |
| per-tier **range** | `behaviors[AttackModel].range` |
| damage type / immunities | `DamageModel.immuneBloonProperties` (bitmask) → `utils/btd6/damage_types.py` |
| paragon base node | `<Name>-Paragon.json` (degree-independent; degrees derived) |

The deep `behaviors[]` walk (multiple attacks/weapons per tier, AoE radius,
abilities, cash income) is the **bulk of the effort** — the skeleton above is
proven; the per-tower variations are what the build session works through.

---

## Name mapping (IMPORTANT — allowlist, don't auto-convert)

`Towers/` has **~90 folders**, most of which are **not player towers**
(`AmbushBot`, `Drone`, `Sentry*`, `Phoenix*`, `SpectreA/C`, `*Totem`,
`BananaFarmerPro`, `SuperMonkeyBeacon`, `TechBotPrime`, sub-towers from
abilities, etc.). The mapper must use an **explicit allowlist** of the 24
towers + 17 heroes, not a blind PascalCase→snake_case over every folder.

For the allowlisted entries the rule is **PascalCase → snake_case** and it maps
cleanly: `DartMonkey`→`dart_monkey`, `BombShooter`→`bomb_shooter`,
`IceMonkey`→`ice_monkey`, `EngineerMonkey`→`engineer_monkey`,
`MonkeyVillage`→`monkey_village`, `CaptainChurchill`→`captain_churchill`,
`ObynGreenfoot`→`obyn_greenfoot`, `PatFusty`→`pat_fusty`,
`AdmiralBrickell`→`admiral_brickell`, `StrikerJones`→`striker_jones`, etc.
Build the map from our catalog ids (`towers.json`, `heroes.json`) and assert
every id resolves to exactly one dump folder (fail loudly otherwise).

---

## Roles (REVISED — the device path is gone)

| Claude (this is the bulk) | User |
|---|---|
| Clone/read the dump **in-sandbox** | Decide: replace bloonswiki, or run both with precedence? |
| Build + test `parse_gamedata.py` (real files here) | Run the bot once to sanity-check a mapped tower/hero |
| Validate against anchors + diff vs committed files | (Later/optional) PC self-export for day-one freshness |
| Wire in as a source w/ provenance; PR | Approve scope of the first slice |

**The user does NOT need the tablet, Termux, UnityPy, the AES key, or root.**
Those were for the superseded path (see appendix).

---

## Open items to check / decide in the build session

- [ ] **Upgrade XP/cost**: confirm `Upgrades/*.json` covers all upgrades incl.
      Paragon upgrades; confirm `xpCost`/`path`/`tier` semantics across a few
      towers (sampled Sharp Shots = cost 140 / xpCost 0 / path 0 / tier 0).
- [ ] **Combat `behaviors[]` variations**: towers with multiple attacks
      (e.g. Super Monkey, Druid, Mortar), AoE (`projectile.radius`), abilities
      (`ActivateAttackModel` / ability behaviors), and **cash income**
      (banana farm / village / Geraldo) — find where income lives.
- [ ] **Crosspath scope**: the dump has *every* crosspath file, so we can store
      true crosspath tiers directly (bloonswiki needed reconstruction). Decide:
      ingest all ~64, or the 16 single-path tiers our schema/AI grounding uses?
- [ ] **Damage types**: confirm `immuneBloonProperties` bitmask values match
      `utils/btd6/damage_types.py` expectations (it was built for the same field).
- [ ] **Paragon degrees**: keep deriving via `paragon_degrees.py`; optionally
      cross-check the constants against `paragonDegreeData.json`.
- [ ] **Display names**: confirm whether `textTable.json` is needed, or whether
      `Upgrades/*.json` `name` + our existing catalog canonical names suffice.
- [ ] **Precedence/provenance**: how to stamp `source` and `game_version`, and
      whether game-data overrides bloonswiki per-field or wholesale.
- [ ] **Integration seam**: tower costs currently flow CSV → `import_btd6_data_from_csv.py`
      → `towers.json`; stats files are written directly. Decide where
      `parse_gamedata.py` plugs in (see `docs/btd6-data-pipeline.md`).
- [ ] **Don't vendor the 320 MB dump** — read it from a clone at runtime of the
      script; commit only derived `stats/*.json`.

## Phased plan (revised)

- **Phase 1 — scaffold + validate:** `parse_gamedata.py` reads a clone,
  **validates anchors as a hard gate** (Dart 200, Super 2500), builds the
  name allowlist (assert all ids resolve).
- **Phase 2 — one tower end-to-end:** map `dart_monkey` (base cost, category,
  upgrades from `Upgrades/`, per-tier combat from crosspath files) → diff
  against the committed `dart_monkey.json` to validate the mapping.
- **Phase 3 — one gap hero:** map `benjamin` → produce `stats/heroes/benjamin.json`
  (proves the wiki gap closes). Then the other 10 heroes + 2 prose paragons.
- **Phase 4 — full roster + integrate:** all 24 towers, stamp provenance, wire
  in above bloonswiki; tests (synthetic fixtures, not vendored dump files).
- **Phase 5 — freshness:** document re-pull per patch; optional PC self-export
  (Mod Helper + MelonLoader) for day-one when the public dump lags. Use the
  patch-notes feed (#459) as the "time to re-pull" signal.

## Legal / licensing stance

- Bot is **free, non-commercial, mostly private servers**; any future
  monetization is unrelated commissioned work — **not** this BTD6 data.
- We **consume a public dump of factual numbers** (lowest-risk category — same
  as how the wiki sources its data); we are not extracting/decrypting anything.
- Raw stat **numbers are facts** (not copyrightable). **Commit only derived
  stat values** in our schema with a `source` provenance note; **never** vendor
  the raw dump, and there's no key/decryption routine to worry about anymore.

## Pick-up checklist for the fresh session

1. Read this doc + `docs/btd6-data-pipeline.md` (the pipeline this augments).
2. Clone the dump (Option A or B above). Re-validate anchors first thing
   (Dart 200, Super 2500) — if they fail, the dump moved; stop and re-check.
3. Build Phase 1 → 2 → 3 per above. Mirror `parse_bloonswiki.parse_*_json`
   for the target shape; reuse `damage_types.py` / `paragon_degrees.py`.
4. Tests on **synthetic** TowerModel-shaped fixtures (hermetic; no vendored
   dump). Gate with `python3.10 scripts/check_quality.py --full`.
5. Open a PR; keep the raw dump out of the repo.

---

## Appendix — original Android/UnityPy extraction path (SUPERSEDED)

Kept only for context. This was the plan **before** we found the public dump;
it is no longer needed because the dump already publishes decrypted data.

The idea was: BTD6 is Unity/IL2CPP with AES-encrypted JSON `TextAsset`s; the
user would run **Termux + Python + UnityPy** on their **Galaxy Tab S11 Ultra**
(BTD6 installed, **not rooted**) to extract from the APK, decrypt with the
community AES key (the one uncertain step), and feed samples back. Risks were
scoped storage (Android 11+), Termux native deps, and key currency — **all
moot now**. If the public dump ever dies, the lightest revival is the **PC**
self-export (Mod Helper + MelonLoader), not this Android path.
