# BTD6 game-data decode — status, lessons & open items

The living status of the effort to source BTD6 data from the **BTD Mod Helper
game-data dump** (`github.com/Btd6ModHelper/btd6-game-data`, v55.0). Start here
to pick up the work: it records what's done, **how the dump's data actually
works** (the traps we hit), and what is still un-decoded.

---

## ⭐ Next session — start here (updated 2026-06-04, end of v55 session)

### Operating lesson (binding — survives the session boundary)

**Green tests are not the verdict; live Discord behavior is.** "Done" means
**extracted + reachable + answerable live, verified** — not committed, not
test-green. **`extracted ≠ reachable ≠ answerable`** are three different states,
and *most of this session's bugs lived in the gaps between them*: data was in a
committed file (extracted) but a renderer dropped it or the resolver couldn't
reach the entity (not reachable), or it reached the model but was mislabeled /
the model asserted a false negative (not answerable). Verify the user-facing
answer, not the unit test.

### Session log — 2026-06-04 (reachability + absence-claim diagnosis)

Picked up the v55 hand-off. The build sandbox **cannot reach Discord and has no
game-data dump clone**, so this session did the work that is verifiable here and
*led the maintainer to the live checks* for the rest.

- **Absence-claim diagnosis (Task 1) — settled with evidence, not priors.** Ran
  the Bomb Shooter middle-path MOAB case through the real service paths. The
  named tiers ground perfectly — MOAB Mauler `+15`, Assassin `+30`, Eliminator
  `+99` *damage vs MOAB-Class* — but `resolve_upgrade("bomb shooter middle
  path")` → `none`, **0 grounding lines**. So the live refusal was the
  **false-negative / absence-claim hole** (data sitting unqueried because the
  path-level phrasing doesn't resolve), **not** an extraction gap. Design
  proposal written: **`btd6-absence-claim-guard-design.md`** (design only, for
  ChatGPT/Analysis review — no guard merged).
- **Derived-value false-"no" (sibling bug) — diagnosed from the live audit log
  + first fix shipped.** The maintainer pulled `recent_audit` for the Tack
  Shooter "total cost to reach every upgrade" refusal: `denied` ·
  `grounding_failed` · provider=anthropic/haiku ⇒ **generated-then-rejected**.
  The guard rejected a total it could not see was *summed from grounded prices*
  (provenance doesn't flow through arithmetic). This is **distinct from** the
  absence-claim hole. Fix shipped (the maintainer's preferred option a): a
  deterministic **`btd6_cumulative_cost`** tool — the total is now a tool output,
  grounded by construction. Verified vs the live screenshot (Tack Shooter top →
  Inferno Ring = $50,310 Medium / $42,760 Easy, the per-item-rounding case).
  Finding written up: **`btd6-derived-value-groundedness-finding.md`**.
- **Refined after two more live tests (post-#482).** Asked "list the damage
  multipliers of the MOAB Mauler," the bot now **answers correctly** (resolves
  0-3-0, +15 vs MOAB-class, base stats, flat-bonus-not-multiplier) — so MOAB is
  **downgraded** as the canonical failing case. A *pure* absence-claim ("X has no
  Y", no answer) has **not** been reproduced; live failures keep landing on two
  narrower modes: derived-value rejection (severe, fixed) and **deny-then-answer**
  (mild — the model prepends a false "I don't have a 'multiplier' figure" then
  answers, because the user's word isn't a literal field; seen ×3). So the
  **absence-claim guard is deprioritized to a backstop** and the **deny-then-
  answer framing fix** (a prompt change, live-verify next session) becomes the
  milder concrete item. Captured in the evidence-update section of
  `btd6-absence-claim-guard-design.md`.
- **Capability-surface verification (vs the bot's live self-report).** The bot
  was asked to "list all your tools" and another reviewer flagged possible
  doc/code drift. Verified against the real registry (`build_registry`):
  **17 tools at USER scope, 22 at ADMIN** (with guild+member). Findings:
  - **`btd6_relic_lookup` + `btd6_bloon_filter` + `btd6_cumulative_cost` ARE in
    the live registry** — i.e. **this session's #482 work is registered and the
    model sees it**, not pre-existing and not doc drift. The status doc already
    lists them; **docs are current**, correcting the "docs undercount what's
    shipped" read (that reviewer pre-dated #482).
  - **Self-knowledge ≠ registry (over-claim):** the bot listed `lookup_member`
    and `list_all_members`, which are gated behind `ai_server_member_lookup_
    enabled` (**default False**) and were **NOT** in its toolset. There is **no
    deterministic "list my tools" path** — the self-report is model-generated, so
    it can (and did) name tools it doesn't currently hold. *(If that guild has the
    member flag ON, the list is accurate — maintainer to confirm the flag.)*
  - **Buccaneer pricing `grounding_failed` is NOT a data gap.** Verified
    `btd6_context_service.build("pricing of monkey buccaneer")` → **found, 27
    facts** incl. base 400 and upgrade prices ($275/$425/$3350…), identical shape
    to sub/tack. So it is **not** "the general lookup grounds some towers and not
    others" (correcting that reviewer's hypothesis). The medium prices are
    groundable; the live refusal is **tool-invocation / derived-difficulty-price
    grounding** — same family as total-cost (either the lookup wasn't invoked that
    turn, or the model emitted Easy/Hard/Impoppable prices without calling
    `btd6_difficulty_cost`, so the *scaled* numbers were ungrounded → rejected).
    **Discriminator owed:** the buccaneer turn's tool-call trace. **Proposed fix:**
    a deterministic all-difficulties tower-pricing tool (1 call → the full
    per-upgrade × 4-difficulty table, grounded by construction), the same pattern
    as `btd6_cumulative_cost`, replacing the fragile lookup + N×difficulty_cost
    stitch. *Not built yet — pending the tool-trace so we fix the real mechanism.*
- **Round "heaviest waves" ranker — FIXED.** `round_composition` now returns a
  pre-ranked `heaviest` (by count, with a bloon) / `heaviest_by_rbe` (by RBE,
  without), ranked over the **full** range before the detail cap, so the model
  never re-sorts and a wide range can't truncate a heavy late round. Verified vs
  ground truth: ceramics r30–80 → `[(78,147),(74,135),(63,122),(76,60),(65,50),
  (69,50),(55,45),(72,38)]` (was naming r55/r50 and skipping r76/r78/r74).
- **Reachability sweep (Task 2) — both tools added.** `btd6_relic_lookup`
  (CT-relic roster + category filter + named lookup) and `btd6_bloon_filter`
  (trait / category / immunity filter). The bloon filter **distinguishes
  inherently-tagged bloons from the `modifier` pseudo-entries** (camo / fortified
  / regrow), so "which bloons are camo" answers "DDT — and Camo is also a
  modifier other bloons can gain", not a misleading closed set. Both registered
  in `BTD6_GROUNDING_TOOL_NAMES`; pin tests updated. *Code + local output
  confirmed; live confirmation owed (see table).*
- **⚠ Provenance trigger observed.** A successful upgrade answer surfaces
  `(source: bloonswiki 54.0)` — a **user-facing per-file 54.0 source label**,
  the exact condition the provenance note named as the trigger to revisit (the
  refusal stamps 55.0; a hit stamps 54.0 → the user sees both). Not acted on
  unilaterally; see the provenance section below for the proposed fix.
- **Deferred with reason:** Task 3 (numeric slice 2) and Task 4 (subtower tail)
  both require the **game-data dump** (absent in this sandbox) *and* live
  numeric verification (impossible here). Teed up, not half-done — see tasks.

### Prioritized tasks

1. **Absence-claim guard — DESIGN FIRST, do NOT implement blind.** *The session's
   most important discovery and the faithfulness mission's real frontier.* The
   verifier catches ungrounded **numbers/names** but **not absence claims** — the
   bot can fluently, version-stampedly say *"Ultra-Juggernaut has no damage
   multipliers"* when it does, and nothing stops it. A fluent false "no" is worse
   than a refusal: it looks authoritative. **Why next:** it is the core of the
   faithfulness mission and currently wide open in *every* domain (auto-grounding
   from #478 only mitigates the upgrade-modifier path). **How:** a design-doc +
   Decisions task *before any code* — verifying a negative generally means
   forcing a lookup before an absence assertion is allowed, which has latency and
   false-positive costs that need a deliberate decision. **Definition of done:** a
   written design proposal reviewed on the ChatGPT/Analysis side — **not** a
   merged guard.
   **Status (2026-06-04):** diagnosis done with evidence (path-level resolve →
   `none`, named tiers ground fine ⇒ absence-claim hole, not extraction);
   proposal written in `btd6-absence-claim-guard-design.md`. **Owed:** maintainer
   reads `recent_audit` for the live MOAB turn to confirm the reason code, then
   reviews the design. No guard code this stage, as specified.
   **Update (post-#482):** MOAB now answers when named, and no *pure*
   absence-claim has reproduced live → this guard is **deprioritized to a
   backstop**. The live failures are two narrower modes (derived-value rejection
   — fixed; deny-then-answer preamble — framing fix next). See the evidence-update
   section of `btd6-absence-claim-guard-design.md`.

2. **Finish the reachability sweep while the pattern is hot.** Two tool-gaps over
   already-committed data, same shape as the rounds/maps/modes fixes that worked:
   a **CT-relic roster/filter** tool (only named lookup today) and a
   **bloon-property filter** ("which bloons are camo / lead / fortified?").
   **Why next:** cheap, proven pattern, closes live refusals. **How:** read-only
   service fn + tool spec/handler + add to `BTD6_GROUNDING_TOOL_NAMES`, each with
   a **live** Discord confirmation of its example question. **Definition of done:**
   reachable by tool **and answerable live** — not test-green.
   **Status (2026-06-04):** ✅ code — `btd6_relic_lookup` + `btd6_bloon_filter`
   landed, registered, pin-tested; the bloon filter handles the
   camo/fortified/regrow modifier nuance faithfully. **Owed:** the three live
   confirmations in the verification table.

3. **Step 5 numeric slice 2 — registry-gated, one `$type` at a time. Never
   bulk-write.** Use the **Decode-class** registry now in the inventory report
   (`btd6-decode-inventory-v55.md` §3 / `_DECODE_CLASS`). Order: start with
   `SAFE_WRITE` additive types (`PierceSupport`, `RateSupport`); do `SCHEMA_FIRST`
   for `ProjectileSpeed` / `Visibility` etc. (extend the buff schema + dataclasses
   + renderers + tests **before** writing any data); **DEFER** the ambiguous
   `RangeSupport.multiplier` until examples prove its semantics. **Why next:** the
   decoded-effect half of the end goal, now de-risked by the classification.
   **How:** per `$type` — verify its number individually vs a committed example,
   write additively (never clobber curated buffs), wire through the existing
   `buffs[]`/`zones[]` grounding. **Definition of done per slice:** extracted +
   committed + retrievable by tool + **verified live** + the per-`$type` number
   verified individually + schema changes conform to the architecture /
   registry-snapshot invariants (expect one to bite — conform, don't fight).
   **Status (2026-06-04):** ⛔ **blocked in this sandbox** — needs the game-data
   dump clone (`--dump`, absent here) to source any number, *and* live numeric
   verification (impossible here). Not started; the registry in
   `btd6-decode-inventory-v55.md` §3 is ready for the next dump-equipped session.

4. **Subtower tail** — `MorphTowerModel` named-ref (Alchemist "Transformed
   Monkey") + `BeastHandlerPetModel` (Beast Handler pets), still missing. **Why:**
   required before any game-native tower cutover. **Definition of done:** both
   spawn mechanisms emit subtowers, answerable live.
   **Status (2026-06-04):** ⛔ **blocked** — same as Task 3 (the mapper needs the
   dump to emit these subtowers). Deferred to a dump-equipped session.

### Verification status (live backlog)

> **The build sandbox still cannot reach Discord** — every "live" check below is
> the maintainer's to run. Two carried-over items are now **✅ LIVE-CONFIRMED**
> (maintainer); the rest remain **UNVERIFIED-live** and rest on code paths.

**Carried over from the v55 session:**

| Item | Code-confirmed | Live status — exact manual check |
|---|---|---|
| Refusal stamps v55 | `_btd6_game_version()` → `55.0` | **✅ LIVE-CONFIRMED** (maintainer): refusal reads "(55.0)". |
| Round-composition math | `round_composition(30,80,'ceramic')`→873, 22 rounds | **✅ LIVE-CONFIRMED** (maintainer): 873 ceramics r30–80, reconciles. |
| Damage modifiers ground | `grounding_for_query("ultra jug")` → "+20 damage vs Lead, +8 vs Ceramic, +5 vs Fortified" | UNVERIFIED — ask "Ultra-Juggernaut bonus vs Lead/Ceramic/Fortified"; must return those, not "no multipliers". |
| Poplust % render | `_buff_text({ratePercentage:0.15})` → "15% attack speed" | UNVERIFIED — ask about Druid Poplust's buff; must read **+15%**, not +0.15%. |
| Map / mode tools | Logs→Beginner; CHIMPS→cash 650 | UNVERIFIED — ask "which maps are beginner", "CHIMPS restrictions". |
| 2 recovered upgrade cards | Ace "Operation: Dart Storm", Wizard "Necromancer: Unpopped Army" extract a description | UNVERIFIED — ask each; the description must render and **not** be invented. |

**New this session (code + local output confirmed; live owed):**

| Item | Local confirmation | UNVERIFIED-live — exact manual check |
|---|---|---|
| Heaviest-waves ranker fix | `heaviest` = `[(78,147),(74,135),(63,122),(76,60),(65,50),(69,50),(55,45),(72,38)]` | Ask "which rounds have the most ceramics in 30–80 / heaviest ceramic waves" — top should be r78/r74/r63, **not** r55/r50. |
| `btd6_relic_lookup` | `category=economy` → 5 relics (Air and Sea, Box of Monkeys, El Dorado, Rounding Up, Starting Stash) | Ask "which CT relics are economy / list the relics / what does Super Monkey Storm do". |
| `btd6_bloon_filter` | `property=camo` → DDT + "Camo property" modifier note; `category=moab_class` → 5 | Ask "which bloons are camo / lead", "list the MOAB-class bloons" — camo must note DDT **and** the broad modifier. |
| `btd6_cumulative_cost` (derived-value fix) | Tack Shooter top → Inferno Ring = $50,310 Medium / $42,760 Easy | **Re-ask the refused turn:** "total cost to reach every Tack Shooter upgrade, base + all earlier costs" — must now answer with totals, not refuse (`grounding_failed`). |
| MOAB bonus (named) | named tiers ground +15/+30/+99; generic "middle path"→`none` | **✅ LIVE (maintainer):** "list the MOAB Mauler's multipliers" now answers (+15, flat-bonus-not-multiplier). Caveat: it prepends a false "I don't have a multiplier figure" — the deny-then-answer mild bug, tracked separately. |

### Provenance decision (recorded, not auto-applied)

Top-level fixtures stamp **55.0** (the user-facing dataset version, read by the
refusal). The per-file `stats/*.json` `game_version` stays **mixed** (v46.3–55.0)
on purpose — it is the *source vintage* (when those numbers were last sourced by
the overlay), not a correctness claim. A blanket re-stamp to 55.0 was **declined**:
the `--audit` is per-**field**, not per-file, so there is no clean per-file gate,
and re-stamping unchanged bloonswiki files would falsely claim re-sourcing. A file
is re-stamped only when `--overlay`/`--all` actually re-sources it. *(Open nit: 2
economy files have an empty stamp — decide a value on the next real re-source.)*

> **⚠ Trigger fired (2026-06-04).** The "watch for it" condition has occurred: a
> *successful* upgrade answer surfaces the per-file vintage as a user-facing
> source label — `render_upgrade_grounding` emits `(source: bloonswiki
> {game_version})`, and `bomb_shooter`'s stats file is stamped **54.0**, so a
> live answer reads "MOAB Mauler … (source: bloonswiki **54.0**)" while a refusal
> stamps **55.0**. A user can see both and reasonably ask "54 or 55?". This is a
> *label* problem, not a re-stamp trigger — the 54.0 vintage is honest. **Proposed
> minimal fix (maintainer to decide, not applied here):** make the user-facing
> source label not read as a bare version that contradicts the dataset stamp —
> e.g. `(source: bloonswiki, sourced v54.0)` or drop the version from the source
> bit and let the dataset stamp own "what version is this". Do **not** blanket
> re-stamp `stats/*.json`.

---

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

> **Retrieval-surface + version-stamp fixes (2026-06-03, from live Discord
> testing).** Two issues surfaced that were *not* data gaps:
> 1. *Damage modifiers were extracted but unreachable.* The committed stats carry
>    per-projectile `damageModifierFor*` (e.g. Juggernaut +3 vs Ceramic, +2 vs
>    Fortified) and the Discord embed renders them, but the **AI grounding
>    renderer** (`btd6_upgrade_detail_service`) only emitted `moab_bonus`, so the
>    model couldn't ground "bonus vs Lead/Ceramic/Fortified" and refused.
>    Fixed: `ProjectileSpec.modifiers` now carries all bonuses (shared
>    `utils.btd6.damage_types.DAMAGE_MODIFIER_LABELS`, deduped with the embed) and
>    `_projectile_bits` emits them. *Lesson: extracted ≠ reachable ≠ answerable —
>    a tool/renderer must surface a field, not just the file containing it.*
> 2. *Stale dataset version stamp.* The refusal stamped "54.0" — read from the
>    dataset `game_version` (`towers/heroes/bloons.json`), the single source. Bumped
>    to **55.0**, justified by the audit (committed numbers are 0-SUSPECT /
>    overwhelmingly CLEAN vs the v55 dump, i.e. already v55-accurate).

> **More reachability fixes (2026-06-04, live testing).** Same "extracted ≠
> reachable" lesson, two more instances:
> 3. *`Ultra-Juggernaut` resolved as ambiguous*, so its damage modifiers (+20
>    Lead / +8 Ceramic / +5 Fortified) never reached the model — it confabulated
>    "no multipliers". Root cause: the upgrade resolver matched both the full name
>    and the embedded `Juggernaut` substring → two name-hits → ambiguous. (The
>    #476 test masked this by resolving the raw id, bypassing the resolver.)
>    Fixed: `_absorb_subname_hits` drops a name-hit whose surface is a contiguous
>    sub-run of a longer matching name, so the full name wins while genuinely
>    distinct names ("X vs Y") stay ambiguous; added `ultra jug`/`ujug` aliases.
> 4. *Per-round bloon composition is unreachable, not missing.* `rounds.json`
>    already carries each round's `groups[]` (`bloon_id` + `count`), but there is
>    **no tool** to answer a range aggregation ("how many purples r35–r70"), so
>    the bot refuses. **Fixed:** `btd6_round_composition` tool
>    (`btd6_data_service.round_composition`) — "purples r35–70" → 290.
> 5. *Maps & modes were committed + seeded but had no grounding render AND no
>    tool* — "which maps are beginner?" / "CHIMPS restrictions?" refused.
>    **Fixed:** `btd6_map_lookup` / `btd6_mode_lookup` (single + roster), which
>    bypass the missing render via the grounding-tool ledger.
> 6. *Damage modifiers were mislabeled in grounding.* `_projectile_bits` emitted
>    "+20 vs Lead" right after "210 pierce", and the model read it as bonus
>    *pierce*. Now "+20 **damage** vs Lead" — unambiguous.
>
> **Tool-use-discipline note (open):** the model sometimes asserts a confident
> *false negative* ("Ultra-Juggernaut has no damage multipliers") **without**
> calling the lookup. The faithfulness guard catches ungrounded *numbers/names*
> but NOT *absence* claims, so these slip through. Mitigations now in place:
> (a) #478 makes the upgrade resolve so its modifiers auto-ground (Pass 3c) — the
> data is in context without a tool call; (b) the clearer "+N damage vs X" label.
> A guard that catches absence claims is a larger, separate change.

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
   - **Ability descriptions** are effectively covered because abilities are
     granted by upgrade tiers (the `AbilityModel.description` field is empty in
     the dump).
   - **Hero-level descriptions** — ✅ **done (2026-06-03).** `map_hero` now reads
     `textTable "<InternalHero> Level N Description"` per level; the same
     `--descriptions` writer (`apply_hero_descriptions`) populates all **340**
     committed hero levels (17 heroes × 20), names-frozen. The runtime grounds
     them via `btd6_context_service._render_hero_descriptions` →
     `[btd6_hero_level] <Hero> Level N: <prose> (source: BTD6 in-game
     description)`, surfaced per named hero (all defined levels, so e.g. *Ezili
     L11 → "+50% pierce to reanimated Bloons"* is answerable). The renderer
     budgets the prose so the provenance suffix is never truncated by the
     240-char fact cap.

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
   a. **Zones** — **28** `*ZoneModel` types (`SlowBloonsZone`, `DamageOverTimeZone`,
      shove/windy/necromancer + economy); the zone's own `name` is empty →
      resolve via the owning upgrade's `LocsKey`. *(28, not 12 — see report §3a.)*
   b. **Buffs** — **38** `*SupportModel`/`*BuffModel` types; a common core
      (Range/Pierce/Visibility/Rate/Speed/Cooldown/Damage support sharing
      `multiplier`/`additive` + `buffLocsName`→name) covers most; tail towers get
      a name-only node. *(38, not 37 — see report §3b.)*
   c. **Subtower tail** — `MorphTowerModel` named-ref (Alchemist) +
      `BeastHandlerPetModel` (the 2 remaining mechanisms).
   d. **Economy-tower attack suppression**, then the **towers cutover** (`--all`,
      runtime name-adaptations, update the ~25 value-pinned tests), gated by
      `--audit` and (3). *Rationale: largest effort and the cutover blocker; uses
      (1) sizing and (3) name-joins.*

   > **Definition of done (binding, from the #476/#478 lessons).** A step-5 slice
   > is done only when each effect is **extracted + committed + retrievable by a
   > tool + the per-`$type` number verified individually** (never a bulk write).
   > "Extracted ≠ reachable ≠ answerable": the data being in a committed file is
   > not enough — a renderer/tool must surface it *and* the resolver must reach
   > the entity (Ultra-Juggernaut's modifiers existed and grounded but were
   > unreachable because the resolver read the name as ambiguous; #478). The
   > schema extension for effects the current buff schema can't hold
   > (`projectileSpeed`, `visibility`) **alters shape**, so expect an
   > architecture / registry-snapshot invariant to bite — conform to it.
   >
   > **Ordering vs step 3:** the numeric-overlay envelope (`_OVERLAY_FIELDS =
   > {range, footprintRadius}` + upgrade `cost`/`xp`) and step 5's
   > `buffs[]`/`zones[]` are **field-disjoint**, and `overlay_payload` edits in
   > place without stripping unrelated keys (verified) — so the two are
   > order-safe on the same tower file (no half-populated entities); either may
   > land first.

   > **Decode analysis (2026-06-04, slice 1).** Deep investigation before any
   > buff/zone *write*, with three inconsistencies flagged:
   > - **Render bug FIXED.** Percentage buff fields are stored as fractions
   >   (`0.15` = 15%, faithful to the dump's `*PercentIncrease`) but the renderer
   >   read them literally → Poplust showed *"+0.15% pierce"* (≈100× too small).
   >   `_buff_text` now scales `*Percentage` fields ×100 (61 committed buffs were
   >   affected). This is the only *answerable* change in slice 1.
   > - **The buff *prose* is already answerable** via the upgrade descriptions
   >   (step 2) — `buffLocsName` does **not** resolve in `textTable` (it is a
   >   buff-icon key), so step 5's only *added* value over step 2 is the
   >   structured *numbers*.
   > - **The numbers have mixed, per-`$type` semantics — not a uniform decode.**
   >   Verified `PoplustSupportModel.ratePercentIncrease 0.15` == committed
   >   `ratePercentage 0.15` (identity). But across types: `PierceSupport.pierce`
   >   → `pierceAdditive` (clear); `RateSupport.multiplier 0.85` → `rateMultiplier`
   >   (faithful ×-cooldown); `RangeSupport.multiplier 0.1` is an **ambiguous**
   >   fraction (×0.1 is absurd, so it must mean +10% → `rangePercentage`); and
   >   `ProjectileSpeedSupport` / `VisibilitySupport` have **no field in the
   >   committed buff schema at all**. Crosspath files also list **cumulative**
   >   buffs (need tier-diffing to attribute the granting tier) and contain
   >   **duplicates** (need de-dupe). A bulk write would ship wrong numbers under
   >   the faithfulness guard, so the numeric write is deferred to a per-`$type`,
   >   verified slice (extend the buff schema for speed/visibility; map only
   >   semantics proven against a committed example or an unambiguous field name).
   >   *(The "37 buff / 12 zone" counts here are superseded by the SHA-pinned
   >   report's 38 / 28 — see `btd6-decode-inventory-v55.md` §3.)*
   > - **Schema-coverage gap (slice-2 input).** Several committed buff fields are
   >   already present but NOT in `_BUFF_FIELDS`, so they render as a bare
   >   "buff": economy effects (`cashPerRoundPerFavouredTrades`,
   >   `heroXpMultiplier`, `cashbackZoneMultiplier`, …). Slice 2 should widen the
   >   schema to surface these too, not just speed/visibility.
   >
   > **Slice 1 shipped (#477):** the ×100 render fix only — **no buff/zone
   > numbers were written**, so the 🔴 "0 of 28 / 0 of 38" below still stands for
   > the *write*; only the rendering of the already-committed buffs is corrected.

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
