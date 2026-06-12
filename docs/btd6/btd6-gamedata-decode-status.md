# BTD6 game-data decode — status, lessons & open items

> **Status:** `living-ledger`

The living status of the effort to source BTD6 data from the **BTD Mod Helper
game-data dump** (`github.com/Btd6ModHelper/btd6-game-data`, **v55.1** at the
cutover SHA `4e22e586` — header corrected from v55.0, 2026-06-12 P2 sweep).
Start here
to pick up the work: it records what's done, **how the dump's data actually
works** (the traps we hit), and what is still un-decoded.

> **Where this sits in the bot:** SuperBot is a Discord server-setup/management
> bot; the BTD6 knowledge base is *one* feature. This subsystem migrates every
> curated/wiki BTD6 value to **reproducible, game-sourced** data
> (`disbot/data/btd6/*.json` ← `parse_gamedata.py` overlays ← the dump), each
> mirrored by a `*Entry` dataclass in `services/btd6_data_service.py` and surfaced
> through AI lookup tools + the `cogs/btd6/` embeds.

> **New to this effort? Read `btd6-gamedata-decode-explainer.md` first** — a
> from-first-principles deep explanation of the what/why/how (buffs, the audit,
> the cutover), with worked examples. *This* doc is the live status + to-do list.

---

## ⭐ Next session — start here (updated 2026-06-10 — **cutover DONE (#649) · VERIFIED (#655) · carry-forwards DECODED (#653+#655) · Ask parity + dark renders (#658) · items 6a–c + the Navarch routing fix (#662) · item 7 slice 1 + zero-fact sweep (#668; probe tool #666); next = item 3 (demand-driven) + item 4 (maintainer spot-check)**)

> **2026-06-10 (PR #662 — the Navarch live miss + items 6a–c):** the first
> *demand-driven* item-3-style question arrived via screenshot ("does the
> navarch of seas paragon make coins" → bot said NO) — and the diagnosis is
> the important part: **the data was never missing; the routing was.**
> Committed `navarch_of_the_seas.json` carried `cashPerRound: 3200`
> (the dump's `PerRoundCashBonusTowerModel` = end-of-round cash) + the Trade
> Empire/Flagship/sellback buffs since the cutover. Three routing layers
> failed: (1) "navarch of **seas**" (article dropped) failed the exact
> substring match in `_paragon_name_facts` → **zero grounding facts** → the
> model freelanced a confident "no income"; (2) even named exactly, the
> curated description's income sentence is its LAST sentence and the 240-char
> fact cap truncates precisely it; (3) the paragon grounding rendered only
> the primary-attack headline — no income line, no effect lines (towers
> ground income via specials, heroes via `[btd6_hero_buff]`; paragons had no
> leg). Fixed end-to-end: article-tolerant + "paragon"-keyword-gated
> shorthand name matching (via `paragon_math.resolve_paragon` — "boat
> paragon" works), a dedicated `[btd6_paragon_stats normal] … income` line,
> per-effect `[btd6_paragon_stats effect]` lines via `tier_effect_lines`,
> `Income $X/round` on the `_stat_node_embed` head (Pro tier / hero level /
> paragon base menu views were all income-dark), `income_per_round` on the
> `btd6_paragon_stats_at_degree` AI tool, and `(affects paragons only)` for
> the structural `onlyAffectParagon` aura split. **Known remaining gap (not
> this PR):** the follow-up turn "does **it** make coins…" grounds nothing —
> grounding is per-message; conversation-entity carryover is its own idea
> (routed below as backlog item 7).

> **2026-06-10 (PR #655 continuation — in parallel, #653's wave 1 decoded
> thorn rings / 4-x-x sentries / banana economy; reconciled at the merge):
> `_CUTOVER_CARRYFORWARD` is EMPTY — every #649 carry-forward is now
> mapper-decoded, and the audit reads 91 CLEAN · 0 DELTA · 0 SUSPECT** (was
> 76/9/0; the mapper now reproduces 100% of every committed file). Decoded,
> each committed-identity-verified at the decode site in `parse_gamedata.py`:
> druid thorn rings (`SpiritOfTheForestModel` nested DoT zones — incl. **new**
> Root-of-All-Nature paragon rings 10/15/30 dmg the wiki never had), engineer
> typed sentries (`CreateTypedTowerModel`; paragon
> `CreateSequencedTypedTowerCurrentIndexModel` towers[] + deduped deployed
> child — sentries gained real per-type combat + 25s/19s lifespans), sub
> Energizer/paragon (`SubmergeModel` neutral-filtered local/global/paragon
> split + `MonkeySubParagonSupportModel` whose `*Bonus*` fields are **additive
> +1 == committed totals**), bucc sellback (`CashbackZoneModel` decoded as the
> committed-schema buff + **new** `cashbackMaxPercent` 0.95; the value-less
> zone husk is gone), striker's two hero auras (`RateSupportExplosiveModel` /
> `RateSupportBombExpertModel` — the dump also **fills committed holes**:
> attack-speed on L7–17, Bomb-Shooter on L18+), and Magus' phoenix
> (`TowerCreateParagonTowerModel` — five combat-identical skins dedupe to
> one). The bucc-paragon Flagship carried-duplicate collapsed into two honest
> entries split by the new structural `onlyAffectParagon` flag. The druid
> "150/250 staleness" note below was itself stale — committed already carried
> the correct 0-immune-props split, re-verified against the dump. *(Found
> during the pass, pre-existing, routed to item 6: hero-level `buffs` and
> paragon `subtowers` render on no AI/menu surface yet — the new sentry/thorn
> data DOES surface via tower-upgrade facts.)*

> **2026-06-10 (PR #655, the post-cutover verification session): everything
> re-verified against the dump at the cutover SHA** (`4e22e586`, v55.1) —
> anchors PASS · audit 76 CLEAN / 9 DELTA / 0 SUSPECT (DELTAs = the
> carry-forwards) · **full regeneration byte-identical** (every flag, idempotent)
> · default-rounds parity re-proven **140/140** · all **2,022** menu embeds
> (towers×tiers, heroes×levels, paragons, crosspaths, lists) render in-limits ·
> 43-probe deterministic AI-tool battery green · clean live boot (36 cogs, 0
> errors). Fixed in the same PR: the **mode `rules` block was dark data**
> (now serialized by `btd6_mode_lookup` + rendered by the modes embed via the
> shared `utils/btd6/mode_rules.py` — the modes-cutover "teed-up follow-up" is
> closed); **`!btd6 diagnostics` 400'd** (the 86-map field hit Discord's
> 1024-char cap — counts-only now, every-field-≤1024 pinned by test); the
> **stale `game_version` stamp class** (root cause: overlays only re-stamped on
> a value change — they now re-stamp on every verified run; `towers`/`heroes`/
> `rounds` bumped to 55.1 on audit/parity evidence, so `btd6_answerability` now
> reports 55.1, matching the stats labels); and the **absolute-container-path
> leak** in `data_source_label()` (now `local:disbot/data/btd6`). Session log
> below; new answerability gaps routed into the backlog (items 5–6).

> **2026-06-10 (PR #649, the Q-0066 dedicated cutover session): every committed
> stats file is game-native v55.1** — 25 towers, 17 heroes, 13 paragons,
> regenerated by `parse_gamedata.py --all` writing through a new **cutover merge
> layer** (curated-name renames + internal-name stripping + carry-forwards +
> scalar transplants + a set-level name guard across all 55 entities). Q-0067
> (Farm/Village full tiers, nominal attacks suppressed, income auras decoded)
> and Q-0068 (per-tier beast names from the path's upgrade names) executed in
> the same pass. Mapper recoveries along the way: base-tower
> `AttackAirUnitModel` (Monkey Ace had mapped with **zero** attacks),
> PoD's reanimated BFB under `weapon.emission`, `PushBackModel` knockback,
> `AbilityDamageAllModel` (Bomb Blitz), `ActivateAttackModel` ability attacks +
> `CashModel` crates (Supply Drop $1,100), stun-as-`SlowModel` semantic names,
> `SupportStackingRangeModel` (Echosense) + `FlagshipAttackSpeedIncreaseModel`
> identities. User-facing source labels now read "BTD6 game data {version}"
> (the 54.0-vs-55.0 label trap below is closed). Full CI mirror green
> (8543 passed); post-cutover `--audit` is 76 CLEAN · 9 DELTA · 0 SUSPECT (the
> DELTAs are the deliberate carry-forward entries). Session log below.

### Post-cutover decode backlog (the new "do next", ordered)

> **Wave 1 executed 2026-06-10 (#653, the parallel same-day session):** druid
> thorn rings + engineer tier-4 typed sentries + the **banana economy**
> (tier-level `bananaValue`/`bananaValueMax`/`bananaSalvageValue`/
> `bananaBonusMultiplier` + `bankCapacity`/`bankInterest`, lifted off the
> suppressed banana attack's `CashModel` + the `BankModel`, surfaced as
> specials — "Bananas worth $300", "Bank $7,000 capacity, +15%
> interest/round"). The #655 pass then decoded the rest (below) and the two
> thorn/sentry implementations were reconciled at the merge (mutatorId-keyed
> ring names, committed far/middle/close order, the Ceramic+Moabs tag gate).

1. ~~**Decode the carried-forward mechanisms**~~ — **DONE 2026-06-10 (#653
   wave 1 + the #655 completion)**: druid thorn rings (+ the paragon's, new),
   engineer typed sentries (4-x-x) **and** the paragon roster
   (Green/Red/Blue + the deduped "Modified" child), sub Energizer + paragon
   support, bucc sellback (as the committed-schema buff, husk removed) +
   paragon Flagship dedup, striker's two hero auras (+ dump fills the
   committed L7–17 / L18+ holes), Magus' phoenix (5 skins → 1).
   `_CUTOVER_CARRYFORWARD` is empty; audit 91 CLEAN · 0 DELTA · 0 SUSPECT.
   Evidence comments live at each decode site.
2. ~~**Banana-economy decode**~~ — **DONE 2026-06-10 (#653 wave 1)**, see
   above; answers "how much is a banana / BRF crate / bank capacity".
3. **Remaining buff/zone `$type` tail** — the pre-cutover "unconfirmable"
   blocker is gone in a new sense: committed data *is* the dump now, so new
   decodes are confirmed by **upgrade-prose / owner gameplay knowledge**, not a
   committed diff. Pick from the SHA-pinned report §3 ranking as questions
   surface.
4. **Maintainer live spot-check** of the new surfaces (no sandbox Discord):
   per-tier beast names ("what does the Orca do?"), Farm/Village answers
   (Wall Street income, discounts, MIB), Spectre/Mini Sun Avatar minions, and
   the "BTD6 game data 55.1" source label. *(+ from #655: the modes panel's
   new 📋 rules lines, and `!btd6 diagnostics` — previously failed to send.)*
5. ~~**Deterministic-Ask domain gaps (menu answerability)**~~ — **DONE
   2026-06-10 (PR #658, merged)**: `deterministic_answer` gained the missing
   bloon branch (`for_bloon`, lowest precedence); powers/MK/bosses ground via
   the new context-service **Pass 3e** (MK keyword-gated); no-intent answers
   lead with the facts (`for_reference_facts` via `UNRESOLVED_TITLE`) instead
   of the refusal. Round-range cash stays AI-tool-only (the one deliberate
   remainder — a deterministic range-cash intent is its own small slice if
   ever wanted).
6. **Resolution/label polish — a–c DONE 2026-06-10 (PR #662, with the
   Navarch routing fix above):**
   ~~(a) minion *names* don't resolve directly~~ — **DONE**: the scouted
   `_subtower_name_facts` pass (context-service Pass 3b2) over a cached
   {folded minion name → (kind, owner, code)} index of every stats file's
   `subtowers` (tower tiers + hero levels + paragon bases). Both scouted
   guards held: entity/upgrade-vocabulary collisions skip (beast names ARE
   their tier's upgrade cards since the cutover, so "Orca" stays Pass-3c's;
   "Spectre" is the Ace upgrade), generic English words are stoplisted
   ("Plane"/"Marine"/"Sentry"/"Tree"/"Beast"). "Mini Sun Avatar" now grounds
   Sun Temple 4-0-0 (was mis-landing on Sun Avatar); "Crushing Sentry" + the
   typed sentries ground Sentry Expert; Etienne's UAV renders its buff
   effect ("grants Camo detection" — a support minion has no attack, so the
   hero-minion line renders `tier_effect_lines` too). **Bonus root-cause
   find:** "Pouākai" was unmatchable typed EITHER way — the upgrade
   tokenizer split the non-ASCII letter into `pou|kai`; `_tokens` now
   NFKD-folds diacritics on both index and query sides.
   ~~(b) the internal-ish `fixture/btd6_data` label~~ — **DONE**: one lazy
   `_dataset_label()` helper → "BTD6 dataset, game v55.1" across all 18
   sites; eval mock pins updated.
   ~~(c) `source_summary` claims "data.ninjakiwi.com (Tier 1)" on
   fixture-only answers~~ — **DONE**: `build()` branches on whether any
   NK-sourced DB rows actually grounded (sharper than the scouted
   `live_rows` check — stored `fetch_for_intent` rows are NK-sourced too);
   fixture-only answers summarise as "local BTD6 dataset (game data +
   curated)". ~~(d)
   hero-level `buffs` and paragon `subtowers` render on no surface~~ —
   **DONE 2026-06-10 (the #658 session)**: `tier_effect_lines` + the buff/zone
   renderers moved to `utils/btd6/effect_lines.py` (helper-policy: needed by
   services AND utils), the shared Pro body (`_stat_node_embed`) now renders
   **🌀 Effects + 🤖 Minions** on tower/hero/paragon views (whole-bullet
   truncation, ∞-sentinel reads "permanent"), and the hero grounding emits
   change-only `[btd6_hero_buff]` aura lines. Found + fixed in the same pass:
   Striker's Bomb-buff fractions carried the dump's misleading `*Multiplier`
   names and rendered as ×0.25/×0.05 *reductions* — remapped to the
   `*Percentage` family (+25% pierce, +5% range) with transplant-skips.
7. ~~**Conversation-entity grounding for follow-up turns**~~ — **slice 1
   SHIPPED 2026-06-10 in PR #668** (same day it was planned; the
   `btd6_probe.py` triage tool + the plan itself landed in **#666**:
   [`../planning/btd6-conversation-grounding-plan-2026-06-10.md`](../planning/btd6-conversation-grounding-plan-2026-06-10.md)):
   a zero-fact `build()` with channel identity (the NL mention path) grounds
   the newest recent conversation turn that resolves entities — typically
   the bot's own previous answer — labeled `[btd6_carryover]`; reads the
   conversation buffer's default floor only (never more history than the
   model prompt sees); Ask/tool callers byte-identical. The screenshot's
   turn-2 "does **it** make coins at the end of round" is the regression
   pin. **Same-pass sweep fixes:** ranking questions ("best paragon",
   "strongest tower") now ground the verified rosters (they grounded ZERO —
   the model ranked from memory), and hyper-distinctive bare shorthand
   ("navarch", "doomship", "everfrost", "magus", "mmmf") grounds without
   the "paragon" keyword. Remaining tail (plan §4): the eval-harness pin;
   any wider carryover window once real usage exists. Diagnose any new
   instance with `scripts/btd6_probe.py "<text>"`.

### Current state & next actions (READ FIRST)

> **Provenance precedence (owner decision Q-0037, 2026-06-08): trust the dump wherever
> it is complete and accurate** — it's a direct export of the game's internal files and
> the most recent. Dump > bloonswiki when the dump's value is present and unambiguous.
> **Caveat earned twice this session:** "accurate" requires reading the *right* model.
> The dump has template/variant models that look internally consistent but aren't
> canonical — base `Ddt` is non-camo (children `CeramicRegrow`) vs the real `DdtCamo`
> (children `CeramicRegrowCamo`); a `DiamondbackDiamondBloon` variant reads health 60 vs
> the canonical `DiamondBloon` 80. Select by the bloon's own properties
> (`_select_bloon_model`) and sanity-check a surprising value before asserting it. (Both
> traps were caught by the maintainer's domain knowledge, not the structural self-check.)
> Verified: all 23 dump-modelled bloons match the dump on health **and** speed already —
> our curated bloon stats are correct; only BAD's DDT children needed the camo correction.

**Where the data stands (verified post-cutover, full CI green):**
- **Towers 25, Heroes 17, Paragons 13 — ALL game-native v55.1 (PR #649,
  2026-06-10).** Stats files are regenerated from the dump via the cutover
  merge (curated display names, the two `:` upgrade cards' cost/xp, and the
  `_CUTOVER_CARRYFORWARD` entries are the only wiki-era content left inside
  them). **Rounds** 140 wiki-shaped but dump-parity-proven (140/140, #638)
  with derived per-round + cumulative cash.
- **Bloons** 26 — **children + immunity + health + speed + fortified-health cut
  over to game data** (`--bloons`): `immune_to` derived from each bloon's
  `bloonProperties` bitflag (via `utils.btd6.damage_types.immunities_for_bloon_properties`,
  23/23), `children` from the dump's `SpawnChildrenModel` (variant modifiers
  preserved), and `health`/`speed`/`health_fortified` are direct dump scalars
  (`maxHealth`/`speed`, + the Fortified variant's `maxHealth`) — **verified
  byte-identical 23/23 at cutover** (0 corrections), so the curated combat numbers
  were already right and are now game-sourced + reproducible. `rbe`/`rbe_fortified`
  stay **derived** from `health`+`children` (not dump scalars; pinned by
  `test_btd6_rbe.py`, which turns red if a future dump health moves without an rbe
  reconcile). The rest (layers/category/aliases/description) stays wiki-curated.
- **Maps** 86 — **fully cut over to game data** (`--maps`), with `has_water`,
  curated **removables** (18 maps), and aggregate count/list grounding. (89 dump
  files minus the 3 non-player `IsStandard=False` maps: Blons, Base Editor Map,
  Protect the Yacht.)
- **Modes** 18 — **curated taxonomy, game-sourced rules** (`--modes`): 3
  difficulties (Easy/Medium/Hard) + 13 modes (Standard is the base mode in every
  difficulty) + 2 modifiers (Double Cash, Fast Track; relative-effect, no fixed
  numbers). The `kind` / `difficulties` / prose `description`+`restrictions` stay
  curated (not in the dump), but each of the **15 mapped modes now carries a
  structured `rules` block sourced from `Mods/<mode>.json`** — starting cash/lives,
  start/end rounds, cost/speed/income multipliers, MOAB-health mult, locked tower
  classes/towers, and no-continue/no-sell/no-MK/no-income flags — parsed from
  `mutatorMods[]` (standard economy-curve mutators dropped). This **corrected the
  earlier "the dump has no game-mode rules" finding** (the rules live in `Mods/`,
  the same place MK effects do), and the cutover **caught one real curated typo**:
  Sandbox `starting_lives` 9999999 → the game model's 999999. `mode_rules_source`
  records provenance; `ModeEntry.rules` surfaces it at runtime (display unchanged
  — wiring the block into the mode embed is the teed-up follow-up).
- **Consumable / meta catalogs — game-data-native lookups:** **Powers** 25,
  **Monkey Knowledge** 134, **Geraldo items** 16 (`--powers` / `--knowledge` /
  `--geraldo`). All player-facing name/description/cost catalogs, each behind an
  AI lookup tool. Powers additionally carry decoded effect factors + the
  `btd6_power_effect` apply-tool (attack-speed-on-a-boost). **Monkey Knowledge now
  carries dump-native structured `effect` factors** (119/134) decoded from
  `mod.mutatorMods[]` — More Cash `+200` starting cash, Bonus Monkey free Dart
  Monkey, etc. (corrected the earlier "not in the dump" finding; see the MK
  session log). Geraldo items carry cash cost, Geraldo unlock level, and
  stock/replenish cadence.
- **Mapper** (`scripts/parse_gamedata.py`): faithful — `--audit` is
  **nothing-SUSPECT**, anchors pass. Decodes attacks/projectiles/sub-projectiles,
  **subtowers** (**all 7 spawn mechanisms as of 2026-06-09** — the "named-ref
  morph" premise was wrong: Alchemist's morph is an embedded
  `secondaryTowerModel`; Beast Handler leash carries up to two beasts;
  Mini-Comanche / TranceTotem / PermaPhoenix-class spawns wired; subtower
  lifespans fall back to the embedded `TowerExpireModel` — Marine 30 s, Lava
  Phoenix 20 s, both committed-confirmed), **zones** (top-level + nested in
  subtowers, now incl. the meaning-disambiguating `inclusive` flag — Obyn's
  totem pair), **buffs** (**14 of 38** confirmed types in `_BUFF_FIELD_MAP` —
  2026-06-09 added `RangeSupportModel` (fraction semantics pinned by 4
  independent committed confirmations), `ProjectileRadiusSupportModel`
  (Striker identity) and `BananaCashIncreaseSupportModel` (Benjamin prose;
  buffs now committed via hero re-export) — each carrying its activation
  `trigger` where one applies. Air-unit attacks (`AttackAirUnitModel`) emit
  for **subtowers only** (Mini-Comanche missile verified); widening them to
  base towers is cutover-scope.

**Do next (ordered; correctness over speed — the maintainer's standing rule):**

> **⛔ SUPERSEDED 2026-06-10 — this list's end-goal (step 5, the towers cutover)
> shipped in PR #649; steps 1–4's "blocked on cutover" items are unblocked or
> done.** It is kept for the per-step evidence trails. The live worklist is the
> **"Post-cutover decode backlog"** in the ⭐ header above.

1. **Buff decode tail (11 → 38).** The 2026-06-08 pass added **two** types the
   earlier "exhausted" read had missed — both confirmed exact against committed
   wiki values (see the session log below): `SupportShinobiTacticsModel`
   (Ninja Shinobi Tactics, `multiplier 0.92` → `rateMultiplier`) and
   `DamageModifierSupportModel` (Mortar Pop-and-Awe, nested `damageAddative 1.0`
   vs tag `Bad` → `damageAdditiveForBad`). **Now genuinely exhausted for committed
   *combat* towers:** every other top-level support/buff model lands on (a) a
   **hero** (Brickell/Benjamin/Etienne/Ezili/Gwen/Obyn/Striker/Corvus/Silas/
   Sheriff — heroes flow through `map_hero`→`_map_tier`→`_buffs`, but **none of
   the unmapped types appears on a tower in `stats/*.json` with a committed
   `buffs[]` to confirm against**), (b) an **economy/support tower with no
   committed tiers** (Banana Farm `BananaCentralBuffModel`/`CentralMarketBuffModel`,
   Monkey Village `MonkeyCityIncomeSupportModel` etc. — blocked, maintainer call,
   step 2), or (c) a **paragon** `base` node (`ObynBuffModel`) / a degenerate
   empty buff (`GroundZeroBombBuffModel` `damageIncrease 0`). So the remaining
   numbers can only be validated *at/after the cutover*. Do **not** write a number
   you can't confirm. **Methodology note for next time:** discovery must scan
   **all** top-level `behaviors[]` whose short type is a buff, **not** only types
   ending in `SupportModel`/`BuffModel` — that suffix filter is what hid Shinobi
   (`SupportShinobiTacticsModel`) and the nested-effect case (`DamageModifierSupportModel`).
2. **`SCHEMA_FIRST` buff/zone types** — projectile speed/radius, freeze duration,
   banana-cash, etc. carry a real number but `_BUFF_FIELDS` /
   `btd6_upgrade_detail_service` has no field to render it. Extend the renderer
   first, then decode.
   - **DONE — render coverage for already-decoded-but-dropped fields** (the safe
     `extracted ≠ answerable` fix; no new value asserted, just un-dropped):
     - buff cash/economy: `cashPerRoundPerMechantship` /
       `cashPerRoundPerFavouredTrades` / `cashbackZoneMultiplier` → **Trade
       Empire income + Favored Trades sellback** now answer.
     - buff `heroXpMultiplier` → **Sub Energizer's +50% hero XP**.
     - zone `multiplier` / `multiplierForMoabs` → **Ice Monkey's Arctic Wind slow**
       (×0.6/0.4 speed; MOABs ×0.7) — Ice's signature effect was unstated.
       Verified `multiplier` only ever appears on Ice slow zones, so the generic
       render can't mislabel another zone type.
     - zone `damageModifierForCeramicOrMoabs` → **Druid Thorn zone** +14/8/4 vs
       Ceramic/MOAB.
   - **BLOCKED — income multiplier (`incomeMultiplier`).** The dump has Banana
     Farm `CentralMarketBuffModel` ×1.1 (wiki-confirmed "+10%"),
     `BananaCentralBuffModel` ×1.25, and Monkey Village `MonkeyCityIncomeSupportModel`
     ×1.2 ("+20%") — but **`banana_farm.json` and `monkey_village.json` have no
     committed `tiers`** (economy/support towers were curated without per-tier
     stats), so there is nowhere to attach a `buffs[]` entry for the renderer to
     surface. Also entangled with prerequisite #4 (Banana Farm's nominal
     `AttackModel`). Needs the cutover, or a deliberate model extension that gives
     economy/support towers a minimal tier structure — a maintainer call, not a
     clean pass.
   - **DONE — buff duration + trigger (PR #501).** The seconds-vs-rounds overload
     is resolved by a `trigger` discriminator: `VigilanteTowerBehaviorModel`
     (Desperado lives-lost line) was de-orphaned with frame→seconds windows
     (`lifespan` 15 s / `cooldown` 60 s), `cashOnLeakMultiplier` 2.0, and
     `trigger=on_life_lost`; the start-of-round buff's `duration` is a ROUND count
     (now `duration_rounds`, `durationFrames`=0, `trigger=start_of_round`).
     Rendered by `_buff_trigger_clause`.
3. **Zone effect tail** (28 types) + zones **nested in sub-towers**.
   - **DONE (2026-06-08) — Heli Pilot `MoabShoveZoneModel` rendered + decoded.**
     The maintainer confirmed the sign semantics: **negative cap = the blimp is
     shoved *backward*** (moves in reverse up to that fraction of normal speed);
     **positive = slowed forward** (too heavy to reverse); **0 = halt**. The
     committed per-blimp caps were verified **exact** against the dump's
     `moab/bfb/zomgPushSpeedScaleCap` on every tier (Comanche Defense 0-0-4 base:
     MOAB −0.4 / BFB 0 / ZOMG 0.2; top-crosspath 0-1-4 strengthens it to MOAB
     −0.51 / BFB −0.11 / ZOMG 0.09). Findings worth recording: **MOAB is always
     negative; BFB also goes negative (−0.11) at the tier-4/5 top/middle
     crosspaths**, not just MOAB; ZOMG is always positive. `_zone_text` now renders
     all present classes (e.g. "MOAB-class shoved backward at x-0.51 speed, BFB
     shoved backward at x-0.11 speed, ZOMG slowed to x0.09 speed"), and `_zones()`
     emits the renamed caps for a future cutover. **Crosspath effects now answerable** —
     all 15 crosspath tier-states carry their own shove values via
     `stats.tier(<code>)`, and naming a crosspath ("0-1-4 heli") already grounded
     its *headline* stats but **dropped buff/zone effects**; `_render_tower_crosspath`
     now also emits a `[btd6_tower_stats effect]` line per crosspath buff/zone
     (via the new `btd6_upgrade_detail_service.tier_effect_lines`), so the
     crosspath-specific shove (0-1-4 → MOAB −0.51 vs 0-0-4 base −0.4) reaches the
     user. (`get_upgrade_detail` still keys on single upgrade *cards*, so it shows
     the base-tier effect — expected; the crosspath path is how a named crosspath
     answers.) **DDT — settled (2026-06-08).** An
     exhaustive whole-dump search confirmed `moab/bfb/zomgPushSpeedScaleCap` are the
     **only three** push caps in all 9,916 files — there is **no**
     `ddtPushSpeedScaleCap` anywhere (so the recurring "it's in the dump under
     another name" was checked and is genuinely *not* here for this zone; DDT-speed
     fields **do** exist for towers that define them — Silas `ddtSpeedModifier`,
     Gyrfalcon `moabSpeedScale` — just not on Heli's shove). The game-authored text
     ("Can collide with and shove **MOAB-class** Bloons, reversing or slowing their
     movement") + the maintainer's in-game check (DDT **slowed, not stopped**)
     confirm DDT is affected via the heaviest-handled (**ZOMG**) cap, which the
     committed data already mirrors and the renderer surfaces. The parser still does
     **not** fabricate `multiplierForDdt` (no dump field); the ZOMG-mirror is the
     faithful representation. Only the cutover-storage choice (keep the curated
     mirror vs. drop it) remains, and it's low-stakes.
4. **Economy-tower attack suppression** (Banana Farm's nominal `AttackModel`) +
   preserve `paragon_cost`/`paragon_name` — cutover prerequisites.
5. **The tower cutover** (overlay numbers, or full game-native) — gated on 1–4
   plus the `NameDowngradeError` name guard.
6. **Map removable / blocker / destructible-object data — NOT in the dump;
   now PARTIALLY sourced from the wiki (18 maps).** Confirmed the v55 dump has
   none: `Maps/<difficulty>/*.json` carry only catalog metadata (`difficulty`,
   `hasWater`, `theme`, `mapMusic`, `mapSprite`, `odysseyStatue`,
   `coopMapDivisionType`, `unlockDifficulty`) — **0 of the 89 dump map files** name a
   removable, and a whole-dump grep finds only UI strings (`"Removable Cost"`,
   `ft_trackremovable*`) and Unity asset refs (`Removables/*.prefab`). Per-map
   removable placement/cost lives in the AssetBundle map scenes, absent from
   this JSON export — so it can't be derived like per-round cash was. Instead,
   **maintainer-supplied bloonswiki prose** was curated into
   `parse_gamedata._MAP_REMOVABLES` (18 maps: what each removable is, whether it
   blocks line of sight, what removal opens, conditions like Cargo's R39 gate;
   **costs omitted — not in the source**). `map_maps` injects it (regen-safe),
   `MapEntry.removables` carries it, and `btd6_response_builder.for_map` grounds
   it. The `_TASK_CONTRACT` clause was flipped from blanket-unsupported to:
   answer from the `[btd6_map]` fact when present, say "no data" for ungrounded
   maps, and **never claim a complete cross-map list** (coverage is partial —
   ~18 of the ~30+ maps that have removables). Extend `_MAP_REMOVABLES` (not the
   parser logic) to cover more maps; costs still need a verified source.

**Exploration tooling — use this before reading dump files manually:**

`scripts/explore_gamedata.py` (added 2026-06-08, PR #587) — a read-only search tool
for the game-data dump. Clone the dump first, then run it:

```bash
git clone --depth 1 https://github.com/Btd6ModHelper/btd6-game-data /tmp/btd6gd

# What model types exist under a tower? (use before mapping a new area)
python3.10 scripts/explore_gamedata.py --dump /tmp/btd6gd --list-types --in Towers/Village

# Find every instance of a model type + its fields (use when a buff/zone type is unknown)
python3.10 scripts/explore_gamedata.py --dump /tmp/btd6gd --search RangeSupportModel --struct

# Find every node that carries a specific field (use when the field name is known, model is not)
python3.10 scripts/explore_gamedata.py --dump /tmp/btd6gd --field damageAddative --in Towers

# Show the field values (not just names) for a specific model instance
python3.10 scripts/explore_gamedata.py --dump /tmp/btd6gd --search MoabShoveZoneModel --in Towers/HeliPilot

# Show the JSON path to each match (use when you need to understand the nesting)
python3.10 scripts/explore_gamedata.py --dump /tmp/btd6gd --search RangeSupportModel --show-path --limit 5
```

The tool walks the full nested JSON tree (depth 30 by default). `--struct` shows field
names only — useful for deciding if a model type is worth decoding before reading values.
`--in` accepts any case-insensitive substring of the file path. Provenance note: outputs
are unverified — cross-check a few against the raw JSON before trusting them in a mapping
decision.

**Binding discipline for every decode step:**
- Re-validate anchors first (`--validate-anchors`); if they fail the dump moved → stop.
- Confirm each mapping against the **committed wiki value on a matching tier** —
  the committed value is the arbiter, **not** semantic priors (the
  `distanceMultiplier`→`lifespanMultiplier` case proved both directions).
- Buff/zone `name`s are the dump's **internal** ids → audit aligns by name and
  ignores them (keeps `--audit` nothing-SUSPECT); never downgrade a curated name.
- `python3.10 scripts/check_quality.py --full` before pushing.

### Session log — 2026-06-10 (the Navarch routing diagnosis + items 6a–c, PR #662)

The maintainer's ask: continue the decode lane AND diagnose the screenshot's
wrong answer ("does the navarch of seas paragon make coins" → "no") as
*missing data or missing routing*. The ⭐ entry carries the what; durable
how/why:

- **Diagnose by replaying the exact text, not the cleaned-up version.** The
  probe `build("does the navarch of seas paragon make coins")` returned **0
  facts** — the single highest-information measurement of the session. With
  the article restored it returned 7 facts (still no income). One probe
  separated "resolution failed" from "rendering failed"; every fix followed
  from those two numbers. Grep-reading the grounding code alone would have
  found layer 3 but missed layer 1 (the one that actually fired live).
- **A confident wrong answer needs grounding-shaped absence, not just absence.**
  The model's two answers *sounded* sourced ("Based on the verified data…")
  while holding zero facts; the instruction stack's faithfulness framing
  styles ungrounded prose too. Worth remembering when triaging the next
  "the bot said X wrongly" report: check what grounding the message
  actually produced before blaming data.
- **"Decoded" has three ends, and each surface misses independently.** The
  same `cashPerRound` was: grounded for towers (specials), grounded for
  heroes (specials), invisible for paragons (headline-only renderer); shown
  on the normal menu view, dark on every `_stat_node_embed` view. When
  adding a field, grep every renderer family — the #655 "dark-data check"
  now has a fourth member (paragon grounding) in its checklist.
- **The cap eats the last sentence first.** Curated descriptions put the
  punchline ("It also generates cash like a Trade Empire.") at the end —
  exactly what `_cap` truncates. Structured facts beat prose tails; if a
  fact matters, give it its own line.
- **Survey before stoplist.** The 6a guards were designed off a 5-minute
  walk of every real subtower name (41 names) — which showed beast names
  are upgrade names (collision guard does the work, no alias table needed)
  and surfaced the Pouākai tokenizer split nobody had reported. The scout's
  sketch was right but the data made the design decisions.
- **Verification:** 12 + 10 new tests (incl. the screenshot text verbatim);
  full CI mirror green (8,672 passed); arch strict 0 errors; clean live
  boot; the deterministic Ask path returns the income fact.

### Session log — 2026-06-10 (the carry-forward decode pass, PR #655 continuation)

Backlog item 1 executed end-to-end in the same session as the verification
pass (maintainer: "you can continue"). The ⭐ entry carries the what; durable
how/why:

- **Evidence-first per mechanism, then one implementation pass.** Each of the
  six mechanisms got its dump model inspected and value-compared against the
  committed entries *before* any code: that's what surfaced the two premise
  corrections (the backlog's "raw v55.1 has ibp 0 on 150/250, committed
  carries 17" claim was inverted — committed already had the split; "the
  paragon's triple SentryParagonChild" was actually towers[] holding three
  *distinct* colour sentries with the child nested inside each) and the one
  semantic transform (`MonkeySubParagonSupportModel`'s `*Bonus*` fields are
  additive: +1 == committed totals, six field confirmations).
- **The transplant mechanism quietly finished the job.** Committed-only
  annotations (`filterInBaseTowerId`, the paragon global buff's neutral
  `heroXpMultiplier: 1`) rode `_transplant_absent_fields` onto the decoded
  entries by name-match — no carry-forward needed for a curated string on a
  decoded entry.
- **Scope dedupe, never blanket.** The first dedupe (name-excluded key over
  *every* spawn) collapsed the four typed sentries and the two beasts in
  minimal test fixtures — real entities differ in combat, but the hermetic
  tests exposed the latent class. Final shape: dedupe only
  `TowerCreateParagonTowerModel` lists (per-degree skins) and the sequenced
  spawner's nested children.
- **Decode wins over carried data, visibly:** striker gains the attack-speed
  aura on L7–17 and Bomb-Shooter on L18+ (committed holes the dump fills);
  sentries gain real per-type combat (Shatter/Explosion/Cold/Plasma) +
  expiry lifespans (25s typed / 19s Modified); Root of All Nature gains its
  thorn rings (10/15/30 dmg) — none of this existed in the wiki rows.
- **The audit is now a true mirror**: 91 CLEAN · 0 DELTA · 0 SUSPECT — with
  the carry-forward layer empty, any future nonzero DELTA is a real dump
  change (or a mapper regression), not expected noise. The inventory report
  regenerated to match.

### Session log — 2026-06-10 (post-cutover verification, PR #655)

The maintainer's ask: verify everything is correctly fetched from the dump and
answerable via the AI **and** the menu. Method + durable findings:

- **Fidelity method that worked:** re-clone the dump (same SHA `4e22e586` as
  the cutover) → anchors → audit → **re-run every generator/overlay flag and
  demand `git status` come back clean**. The byte-identity check is the
  strongest cheap test we have — it caught the one real data drift
  (maps.json's missed 55.1 stamp) that the audit can't see (the audit compares
  values, not metadata).
- **Surface method that worked:** drive the real builders, not samples —
  all 1,600 tower-tier + 340 hero-level + 52 paragon + 25 crosspath + 5 list
  embeds through `utils/btd6/stats_embed.py` with a Discord-limits validator,
  and every BTD6 AI tool handler with pinned-value probes. One real send-bug
  fell out (`!btd6 diagnostics` 86-map field 1,059 > 1,024 — Discord 400s
  oversized fields, it does not truncate). Embed-limit validation belongs in
  any future render-surface test.
- **The "0 corrections" trap:** an overlay that only writes on value changes
  silently lets `game_version` rot one version behind on every
  values-didn't-change re-pull (bloons/modes sat at 55.0 after the 55.1
  verification; the answerability tool told users "game 55.0"). Verified-at-a-
  version IS information — overlays now re-stamp every verified run.
- **Probe your probes:** 8 of my first battery's 9 "failures" were my own
  wrong argument shapes / comma-formatted expectations, not product bugs.
  Diff a failing probe against the tool spec before believing it.
- **Dark-data check is cheap and high-yield:** "is the ingested field
  serialized by the tool AND rendered by the embed?" — the modes `rules` block
  failed both halves (now fixed + pinned both places). When ingesting new
  structured data, land the surface wiring (or a backlog entry) in the same PR.

### Session log — 2026-06-10 (THE TOWERS CUTOVER — Q-0066/Q-0067/Q-0068, PR #649)

Executed the owner-decided `--all` cutover end-to-end. Everything below is the
durable how/why; the ⭐ header carries the what.

- **The write path is now a merge, not a raw emit.** `--all`/`--tower`/`--hero`
  write through `cutover_payload(mapped, committed, entity_id)`:
  top-level curated keys (`paragon_cost`/`paragon_name`) → upgrade cost/xp fill
  for the `:` ids → committed upgrade-name restore → beast per-tier naming →
  carry-forwards → absent-scalar transplants → `_assert_cutover_names` (hard
  stop on any curated-name loss). Paragon files scope their tables under
  `"<tower_id>:paragon"`. **Re-running `--all` is idempotent** — the merge
  re-derives the same file, so the data-refresh workflow (#633) keeps working.
- **Name policy (the binding "no internal strings reach users" rule):**
  zones/buffs keep a name **only** if curated (`_CURATED_EFFECT_NAMES`, keys
  optionally `Kind:InternalName` — Mermonkey's totem stamps two effects with
  one `NaturesClarityBuff` id); unmapped internal names are **stripped** (the
  renderer shows the effect body label-free, and a zone with no name and no
  decoded effect renders nothing). Subtowers keep their display-grade
  `towerModel` names unless renamed. Retirements are explicit
  (`_CUTOVER_NAME_RETIREMENTS`): Q-0068's "Beast", two literal "Buff" labels,
  benjamin's committed `BuffIconBenjamin` icon id.
- **Wiki↔game upgrade names diverge for whole towers** — the dump's
  `Upgrades/*.json` `name` is an internal id for Buccaneer ("Buccaneer-Faster
  Shooting", all 15), plus diacritic/case variants (game "Pouakai" vs curated
  "Pouākai"). Committed names are restored at the merge: they are the resolver
  vocabulary (towers.json `upgrade_paths` + aliases) — renaming them would
  desync catalog from stats. Adopting game spellings catalog-wide would be a
  separate, deliberate decision.
- **The two `:` upgrade ids have NO `Upgrades/` file** ("Operation: Dart
  Storm", "Necromancer: Unpopped Army") — `:` is Windows-illegal, the exporter
  skips them; this was the root cause of the historical 373/375 description
  gap. `_upgrades_for` now derives path/tier from the state-file reference's
  target code and the description from textTable; cost/xp are genuinely not in
  the dump and stay committed-preserved.
- **The audit cannot see an empty mapped list** (`_walk_audit` walks keys
  present in both; `zip` over `[] vs [...]` compares nothing) — which is how
  "Monkey Ace maps with zero attacks" stayed invisible until a value-pinned
  test caught it. Ace's entire attack set is `AttackAirUnitModel`; widening it
  to base towers (it was subtower-only) also restored the Goliath Doomship.
  *Lesson: after any structural mapper change, diff entity counts
  (attacks/projectiles per tier) committed-vs-mapped — don't trust the audit
  alone for presence.*
- **More "wrong-place" recoveries** (the recurring trap, again): PoD's
  reanimated BFB at `weapon.emission.alternateProjectile`; knockback as
  `PushBackModel` (not `KnockbackModel.distance`); Bomb Blitz as an
  `AbilityDamageAllModel` inclusive/exclusive pair (== committed
  `damageToBad`/`damageToNonBad`); Supply Drop's crate under
  `ActivateAttackModel.attacks[] → … → CashModel`; a stun stored as
  `SlowModel{multiplier 0}` with the semantics on `overlayType`/`mutationId`
  (names now read those, and visual-only `CreateEffectOn…` nodes are dropped
  so class names can't leak into the Pro view).
- **Q-0067 decode lifts** (each pinned by committed upgrade prose quoted in
  `_BUFF_FIELD_MAP` comments): Central Market ×1.1 / Banana Central ×1.25 /
  Monkey City ×1.2 as **true multipliers** (`incomeMultiplier` — unlike the
  fraction-encoded `*Percentage` family), Primary Training `pierce`,
  Monkey Town `cashPerPopMultiplier` ×1.5, `abilityCooldownSpeedScale`
  (direction prose-pinned: bigger = recharges faster), `freeUpgradeTiers`,
  camo-grant + MIB **presence flags** (`_BUFF_FLAG_TYPES` — no number to
  mis-map), DiscountZone 0.1/0.05 + `tierCap` 3. Echosense
  (`SupportStackingRangeModel`) and Flagship
  (`FlagshipAttackSpeedIncreaseModel`) decoded by committed identity;
  `isGlobalRange` normalises to `isGlobal`.
- **Q-0068 beasts:** the leash model keeps the base internal name at every
  tier — per-tier names (Barracuda…Megalodon, Pouākai) exist only as the
  path's **upgrade names**, so `_beast_subtower_names` labels each beast from
  its path digit + the (post-restore, curated-spelling) upgrade card.
- **Suppression is damage-based, not blanket:** Village's 5-x-x Mega Ballista
  (damage 10) is a real attack and stays; the banana spawner / empty
  `SharedAttack` / Monkeyopolis banana attack go. Farm keeps abilities
  (IMF Loan 85s, Monkey-Nomics 60s) and income (`cashPerRound` 4000 at x-x-5).
- **Pins that held through the cutover** (the wiki numbers were v55-right):
  PoD reanimate 2 dmg/1 pierce @0.275s · Goliath 200+300 @0.66s (degree-65
  cooldown 0.4215 sqrt-curve unchanged) · Herald beam 600→1210 @d100 ·
  Tack→Inferno cumulative $50,310 · ice ×0.6/×0.4+×0.7 · heli shove tiers.
  What changed in tests was **names** (game ids) and **premises** (Farm has
  tiers; no paragon is prose-sourced; beast has real crosspaths).
- **Verification:** anchors PASS · cutover guard green 55/55 · `--audit`
  76 CLEAN · 9 DELTA · 0 SUSPECT (DELTAs = the carry-forward sentry entries
  diffing vs raw mapper output, by design) · full CI mirror **8543 passed /
  22 skipped** · arch strict 0 errors · decode-inventory report regenerated.

### Session log — 2026-06-08 (buff tail 9 → 11: Shinobi Tactics + Pop-and-Awe de-orphaned)

Picked up the buff decode tail with the new `scripts/explore_gamedata.py` tool. The
prior "exhausted" verdict held for every type that earlier discovery had *seen* — but
the discovery itself was incomplete: it ranked only `*SupportModel`/`*BuffModel`-suffixed
types, so two confirmable buffs were never examined. Both are now in `_BUFF_FIELD_MAP`
(parser) and render with no renderer change (the schema fields already existed):

- **`SupportShinobiTacticsModel` → `rateMultiplier`** (Ninja "Shinobi Tactics", 0-3-0+).
  Dump `multiplier 0.92` == committed wiki buff `Shinobi Tactics → rateMultiplier 0.92`,
  and dump `maxStackSize 20` == committed `20` (stacks to 20 ninjas). The dump model has
  **no pierce field**, so only the confirmed rate is written — the committed buff's extra
  `+8% pierce` lives on a different mechanism and stays unasserted (faithful-over-complete).
- **`DamageModifierSupportModel` → `damageAdditiveForBad`** (Mortar "Pop and Awe", 0-4-0+).
  The earlier (2026-06-04) note wrote this off as matching "only on the trivial
  `customRadius/maxStackSize=0`… real effect lives in a different model" — but the effect
  is in the **nested `damageModifierModel`** of the *same* model: the misspelled additive
  `damageAddative 1.0` vs tag `Bad` (the same `damageAddative`-not-`damageMultiplier` trap
  the projectile tag-bonus decode hit). Raw `1.0` == committed `damageAdditiveForBad 1`,
  consistent across all 5 instances. A small nested-tag decoder reads it; an unmapped tag
  emits **no** entry (never a bare value-less buff). Tag→field map covers Bad/Ceramic/Moabs;
  only `Bad` appears in v55.

**Verification:** `--validate-anchors` PASS (Dart 200, Super 2500); `--audit` stays
**nothing-SUSPECT** (internal buff names don't align with curated, so they're ignored);
real-dump output checked (`Ninja-030`/`Ninja-052` → `rateMultiplier 0.92`; `Mortar-050` →
`damageAdditiveForBad 1, isGlobal True`); `_buff_text` renders "x0.92 attack cooldown" /
"+1 damage vs BAD". Pinned by `test_buffs_shinobi_tactics_maps_multiplier_to_rate` +
`test_buffs_damage_modifier_support_reads_nested_tag_bonus` (+ the unmapped-tag drop test).
Full `check_quality.py --full` green (8070 passed).

**Honest frontier:** 11 is the confirmed ceiling for committed **combat** towers pre-cutover
(see "Do next" step 1 for why every remaining type is hero / no-committed-tier / paragon).
~~Known small gap: `_buffs()` does not emit `maxStackSize`…~~ **FIXED (2026-06-08, see session
log below).** `_buffs()` now passes through both stack-cap field names (`maxStacks` /
`maxStackSize`) verbatim, so the parser-native (cutover) path reproduces the renderer's
`_stack_cap` "(stacks up to N)" clause instead of dropping it. *Forward-looking* fidelity fix:
the **committed** buffs already carry the cap (overlay never rewrites `buffs[]`, only
`{range, footprintRadius}`), so live answers were unaffected — the gap was that the eventual
game-native cutover would have silently regressed the clause.

### Session log — 2026-06-08 (buff stack-cap now parser-reproducible — cutover fidelity fix)

Closed the standing "known small gap" the buff-tail session flagged: the game-native parser
path (`map_tower` → `_map_tier` → `_buffs`) dropped the buff **stack cap**, so a future tower
cutover would have silently lost the renderer's "(stacks up to N)" clause (Ninja Shinobi
Tactics "stacks up to 20", Trade Empire "up to 20 Merchantmen", sellback "3").

- **Root cause, precisely:** `_buffs()` emitted `isGlobal` but not the stack-cap field, even
  though `btd6_upgrade_detail_service._stack_cap` reads it (`maxStacks` on most towers,
  `maxStackSize` on Sniper/Ninja/Mermonkey). The **committed** `buffs[]` still carry the cap
  (the numeric `--overlay` only refreshes `{range, footprintRadius}`, never `buffs[]`), so live
  answers were correct — this was a *forward-looking* fidelity gap, not a live bug.
- **Fix:** `_buffs()` now passes both stack-cap names through **verbatim** (a faithful
  structural copy, like `isGlobal` — no transform, so it respects "never write a number you
  can't confirm"; the value *is* the dump's own field). `0` is preserved ("applies once, does
  not stack"); the renderer remains the single place that suppresses the clause for a
  non-positive cap. Emitted *after* the nested-tag drop check, so a stack cap alone never keeps
  a bare value-less buff alive.
- **Tests:** updated `test_buffs_shinobi_tactics_maps_multiplier_to_rate` (was asserting the cap
  *dropped* — it encoded the bug) + two new (`test_buffs_emit_stack_cap_both_field_names`,
  `test_buffs_stack_cap_zero_preserved`). `check_quality.py --full` **green (8157 passed)**.
- **Honest scope:** parser-side only; no new decoded effect, no committed-data change. It makes
  the cutover path reproduce what the committed data + renderer already surface.

### 🔍 Dump re-audit — what's actually missing vs. mis-claimed "not in the dump" (2026-06-08)

After the MK correction, the maintainer asked: *which other data did a session call "not in
the dump" — re-verify it.* Did a full top-level sweep of the v55.1 dump (18 domains) and
re-checked every "not in the dump / hardcoded" claim against the raw files. **The recurring
bug is the same one every time: a session read the obvious top-level model and never opened the
nested `mutatorMods[]` / `behaviors[]` array where the value actually lives.**

**Re-verified "not in the dump" claims:**

| Claim | Prior verdict | Re-verified truth |
|---|---|---|
| MK effect magnitudes | "NOT in dump / hardcoded" | ❌ **FALSE** — `mod.mutatorMods[]` (fixed, PR #598) |
| **Game-mode rules** (start cash/lives/restrictions/end round) | "gameplay code, not exported assets" | ❌ **FALSE** — `Mods/` (22) holds the full set as typed mutators (see Modes correction below) |
| **Per-pop cash** ($1/pop) | "hardcoded, bloon `cash` null" | ⚠️ **PARTLY FALSE** — `DistributeCashModel{cash:1.0}` per bloon (top-level `cash` is null, but the behavior carries it) |
| Map removables / costs | "in AssetBundle scenes, not JSON" | ✅ **TRUE** — whole-dump search finds no removable model, only editor UI strings |
| `theme` / `coopMapDivisionType` / `unlockDifficulty` | "opaque int enums, not decodable" | ✅ **TRUE** — ints (theme 0–6, coop 0–4), no label source in `textTable` |
| DDT push-speed cap | "no dump field" | ✅ **TRUE** — exhaustively confirmed earlier |

**Genuinely missing data (present in the dump, NOT yet fetched) — the real backlog:**

| What | Where in dump | Value | Notes |
|---|---|---|---|
| **Boss bloons** | `Bloons/{Bloonarius,Blastapopoulos,Lych,Vortex,Dreadbloon,Phayze}/…` (101 boss models incl. Elite + Diamondback segments) | ~~HIGH~~ **FETCHED** | `bosses.json` carries all 7 bosses' roster + per-tier `maxHealth`/`speed` for **Standard AND Elite** tiers (Elite backfilled 2026-06-11, BUG-0002 — `map_bosses` reads `<Family>Elite{1..5}.json`). Remaining tail: co-op health scaling, Dreadbloon rock-segment models, deeper per-tier behaviors (skull counts etc.) — demand-driven. |
| **Game-mode rules cutover** | `Mods/` (22) | MED–HIGH | `modes.json` is curated; the dump is the authoritative source (and confirms our values). Cutover or verify. |
| **Alternate round sets** (ABR, etc.) | `Rounds/` (5,181 files = many round sets) | MED | We expose only the default 140. |
| Achievements | `Achievements/` (156) | LOW | `name`/`goal`/`loot` lookup catalog (e.g. "All for one…" → `KnowledgePoints:1`). |
| Rogue Legends / Frontier | `Artifacts/` (568), `rogueData.json`, `frontierData.json` | LOW (niche modes) | Roguelike artifacts + the Wild-West Frontier mode config. |
| Skins / TrophyStore / BloonOverlays | resp. dirs | SKIP | cosmetic — not gameplay. |
| Per-pop cash (provenance) | `Bloons/*/DistributeCashModel` | LOW | already derived correctly; now confirmable as dump-native. |

**Binding takeaway (already added to the MK correction, restated):** before writing "not in the
dump", **descend into `mutatorMods[]` / `behaviors[]` and check the per-instance model**, and run
a whole-dump model-type search (`explore_gamedata.py --search <Model> --struct`). Three of the six
re-checked "absent" claims were wrong because the array was never opened.

### Session log — 2026-06-08 (Monkey Knowledge magnitudes — they WERE in the dump)

The maintainer pushed back on the prior "MK magnitudes aren't in the dump" verdict — *"it has
to be there, it's a very important part of the game."* He was right. Re-cloned the v55 dump and
opened an actual `Knowledge/*.json`: the magnitude is in **`mod.mutatorMods[]`**, a layer the
earlier check never descended into (it read `mod.name`, saw `ModModel`, and stopped).

- **Evidence (full-roster survey of all 134):** **120** carry flat scalar magnitudes, **13** are
  nested-only behavioural (Cold Front, Tiny Tornadoes, Wingmonkey, Vine Rupture, …), **1** empty
  (Grand Prix Spree). Headline confirmations, each matching its committed description exactly:
  More Cash `StartingCash{addition 200}`, Bonus Monkey/Glue Gunner `FreeTower{baseTowerID, charges 1}`,
  Charged Chinooks `Lives{percentBonus 0.25}`+`Cash{percentBonus 0.25}`, Mo' Monkey Money
  `MonkeyMoney{multiplier 1.1}`, Big Bloon Sabotage `BloonHealth{percentageHealthReduced 0.1}`,
  Mana Shield `StartingShield{25/25/+5}`, Hero Favors/Scholarships 10% off, Supa-Thrive `Thrive{+0.05}`.
- **Extraction (`parse_gamedata._mk_effect`):** a **faithful structural passthrough** of each
  mutator's own fields → `effect = {"factors": [{"kind": <snake type>, <numbers>}, ...]}`. No
  semantic transform that could be wrong (same discipline as the buff decode); internal/display
  ids dropped, identity no-ops (`0`) and the unlimited-`charges` sentinel dropped. Behavioural /
  empty → `effect == {}` (description-only), never fabricated. `monkey_knowledge.json` regenerated
  (verified **0 non-effect churn** — only `effect` added to 119 rows).
- **Runtime:** `MonkeyKnowledgeEntry.effect` + surfaced on `btd6_monkey_knowledge_lookup`. So
  "how much cash does More Cash add / what does Bonus Monkey give / how big is the Hero Favors
  discount" now answer with the exact dump number.
- **Tests:** parser (`_mk_effect` scalar/multi-factor/noise-drop/behavioural-empty + the existing
  category test extended), data_service (More Cash effect loads, ≥110 carry a magnitude), ai_tools
  (lookup surfaces the effect). `check_quality.py --full` green.
- **Binding lesson (recorded in the correction above):** **descend into nested `*Mods[]` /
  `behaviors[]` arrays before declaring data absent.** The dump nests effects one level below the
  obvious model; "bare reference" was an artefact of not opening the array. Trust the domain
  knowledge that says a core mechanic "has to be there."

### ⚠ Answerability audit — Powers/Knowledge are *lookup catalogs*, not *applied modifiers* (2026-06-08)

Asked the sharp question: can the bot answer **"what is the attack speed of Crossbow Master
on a Monkey Boost / Hype Monkey"** or **"starting cash / first-tower cost / upgrade cost / free
monkeys / extra lives with knowledge X"**? Verified end-to-end. **The answer is no** — and here
is exactly where the line falls, so the next session doesn't rediscover it:

| Question | Answerable now? | Why |
|---|---|---|
| "What does Monkey Boost / Supa-Thrive do?" | ✅ | lookup returns the game-authored description |
| "How much (Monkey Money) is the Camo Trap power?" | ✅ | `monkey_money_cost` is structured |
| "What's Crossbow Master's attack speed / cost?" (base) | ✅ | base tier stat (cooldown 0.2375s) via the tower path |
| "List the magic monkey knowledge / 50-MM powers" | ✅ | category/roster filters |
| "What's Monkey Boost's exact effect factor?" | ✅ | now structured: `rate_scale 0.5` for `15s` (2026-06-08) |
| **"…attack speed of Crossbow Master *on a Monkey Boost*"** (as a number) | ✅ | `btd6_power_effect` applies the factor to the resolved tier stat (2026-06-08, step 2 DONE) |
| **"…what's the *magnitude* of knowledge X (starting cash / free monkeys / lives / discount)"** | ✅ | **dump-native structured `effect` on `btd6_monkey_knowledge_lookup` (2026-06-08, see correction below)** |
| **"…starting cash / upgrade cost *with knowledge X*, computed against the economy"** | ❌ | the *magnitude* is now structured, but no layer yet **applies** it (no `btd6_*_effect` apply-tool for MK) |

> **⛔ CORRECTION (2026-06-08) — root-cause point 2 below was WRONG.** "MK magnitudes are NOT in
> the dump / hardcoded game logic / every `mod` is a bare `ModModel{name}` (134/134)" is **false**.
> The earlier check stopped at `mod.name` and never opened **`mod.mutatorMods[]`**, where every
> magnitude lives as a *typed* mutator model: More Cash → `StartingCashModModel{addition 200}`,
> Bonus Monkey → `FreeTowerModModel{baseTowerID DartMonkey, charges 1}`, Mo' Monkey Money →
> `MonkeyMoneyModModel{multiplier 1.1}`, Charged Chinooks → `LivesModModel{percentBonus 0.25}` +
> `CashModModel{percentBonus 0.25}`. **120 of 134 carry flat scalar magnitudes; 13 are nested-only
> behavioural (Cold Front, Tiny Tornadoes, …); 1 empty (Grand Prix Spree).** Every spot-checked
> value matches its committed description exactly. Now extracted as a structured `effect`
> (`{"factors": [...]}`) on each MK row + `btd6_monkey_knowledge_lookup`. **Lesson (binding):
> descend into nested `*Mods[]`/`behaviors[]` arrays before declaring data absent — the
> maintainer's "it has to be there" was right.** See the session log "Monkey Knowledge magnitudes".

**Root cause — two missing things, not one:**

1. **Powers carry their real effect in the dump, but we didn't extract it and nothing applies
   it.** `MonkeyBoostModel` has `rateScale 0.5` + `duration 15` (= 2× attack speed for 15 s);
   we stored only the prose *"twice as fast for {0} seconds"* (the `{0}` is literally the hole
   where the structured value belongs). Even with the factor extracted, computing
   `0.2375 × 0.5 = 0.119 s` needs a **deterministic apply-tool** (the structured factor × the
   resolved base stat, grounded by construction — the exact `btd6_cumulative_cost` pattern), or
   the faithfulness verifier rejects the derived number as ungrounded.
2. ~~**Monkey Knowledge effect magnitudes are NOT in the dump.**~~ **FALSE — corrected above.**
   The magnitudes *are* dump-native, in `mod.mutatorMods[]`, now extracted as structured
   `effect` factors. (The *prose* is still the only form for the ~13 purely behavioural ones —
   those legitimately have no scalar magnitude, e.g. "Acid lasts longer".) The remaining gap is
   only the **apply** step — turning "free Glue Gunner / +$200 cash / -10% hero cost" into a
   computed economy number — which, like Powers, needs a deterministic apply-tool, not new data.

**Suggested next steps (ordered, for the following session):**

1. **Extract the Power *effect* structure — ✅ DONE (2026-06-08).** `powers.json` now carries a
   structured `effect` for the cleanly-decodable powers — Monkey Boost `{rate_scale: 0.5,
   duration_seconds: 15}`, Thrive `{cash_scale: 1.25}`, Camo/Glue Trap `{affects_bloons: 500/300}`
   — read from the dump effect model (`parse_gamedata._POWER_EFFECTS`), and **the `{0}`
   placeholders are filled** from those same values (e.g. "twice as fast for **15 seconds**",
   "by **25%**", "the first **500** Bloons"). Surfaced on `btd6_power_lookup` as `effect`. So the
   model can now state the *factor* precisely ("Monkey Boost = ×0.5 cooldown for 15s") — but
   *applying* it to a named tower's stat is still step 2.
2. **Build `btd6_power_effect` (a deterministic apply-tool) — ✅ DONE (2026-06-08).**
   `btd6_upgrade_detail_service.power_effect(power, tower)` resolves the tower/upgrade via the
   deterministic upgrade resolver (`"Crossbow Master"`, `"Dart Monkey"`, `"dart 0-4-0"` → the
   base tier `000`), reads the tier's `attacks[0].rate` (the same cooldown the stats path
   surfaces), and applies the Power's decoded `rate_scale` → base vs boosted cooldown +
   attacks/sec + duration. Surfaced as the `btd6_power_effect` AI tool (registered + in
   `BTD6_GROUNDING_TOOL_NAMES`). **Grounded by construction** (factor × resolved stat, never a
   model multiplication). Scoped tightly to **attack-speed** for now: only Monkey Boost's
   `rate_scale` modifies a tower stat; Thrive (cash) / Camo & Glue Trap (bloons) fail closed with
   a pointer to `btd6_power_lookup` rather than inventing a number, and economy towers
   (Banana Farm) report "no attack-speed stat". `_POWER_STAT_EFFECTS` is the extension point for
   future stat-modifying factors (e.g. a cash-multiplier apply against the economy). Power name
   resolution was de-duplicated into `btd6_data_service.find_power` (shared by the lookup +
   effect tools). "Crossbow Master on Monkey Boost" now answers **8.42 attacks/sec for 15 s
   (vs 4.21 base)**.
3. **Monkey Knowledge magnitudes — ✅ DONE (2026-06-08), dump-native (NOT curated/maintainer call).**
   The earlier "not dump-sourced, maintainer call" verdict was wrong (see the correction above):
   the magnitudes live in `mod.mutatorMods[]`. `parse_gamedata._mk_effect` now decodes them into a
   structured `effect` (`{"factors": [{"kind": ..., <numbers>}]}`) — a faithful structural
   passthrough of the dump's own mutator fields (snake-cased, identity no-ops dropped; no semantic
   transform), the same discipline as the buff decode. Surfaced on `MonkeyKnowledgeEntry.effect` +
   `btd6_monkey_knowledge_lookup`. 119/134 carry a magnitude; the rest are behavioural (description
   -only). So "what does Bonus Monkey give / how much cash does More Cash add / how big is the Hero
   Favors discount" now answer with the exact number.
   - **Possible follow-ups (not blocking):** (a) a clean *curated relabel* of the long-tail field
     names (the passthrough keeps the dump's own keys, incl. misspellings like `addative`); (b) an
     **MK apply-tool** (`btd6_*_effect`) that computes the economy (e.g. "+$200 starting cash" →
     resulting first-tower affordability), the MK analogue of `btd6_power_effect` — that's the only
     remaining ❌ in the table above.
4. **The lookup now answers MK *magnitudes* directly**; the only still-partial case is a *computed*
   economy ("what's my starting cash *after* More Cash + difficulty"), which needs the apply-tool
   in 3(b). "What does X do / how much does X give" is fully answerable.

### Session log — 2026-06-08 (Bloons children + immunity cut over to game data)

Maintainer-approved cutover of the two `bloons.json` fields that are exactly
reproducible from the dump, sourcing them from game data instead of bloonswiki.

- **Immunity** — derived from each bloon model's `bloonProperties` bitflag via a new
  public inverter `utils.btd6.damage_types.immunities_for_bloon_properties` (the inverse of
  the existing projectile-side `_DAMAGE_TYPES` map — *one* source of truth for the bitmask).
  A bloon with property bit `p` is immune to every damage type whose `immuneBloonProperties`
  mask shares `p` (Lead bit 1 → Shatter/Cold/Energy/Sharp; Zebra 6 = Black|White). **Verified
  23/23 exact** against the curated `immune_to` lists, so the overlay leaves them byte-identical
  (provenance-only) — zero churn.
- **Children** — from the dump's `SpawnChildrenModel`, each child resolved to its **base**
  bloon via the child model's `baseId` and tagged with the variant's `isCamo`/`isGrow`/
  `isFortified` modifiers. **Model selection matters:** a bloon that is *itself* a variant
  (a DDT is inherently Camo) must read from its matching model (`DdtCamo`, children
  `CeramicRegrowCamo`), **not** the non-camo base `Ddt` template (children `CeramicRegrow`) —
  `_select_bloon_model` picks the model whose flags match the bloon's own `properties`. With
  that, the derivation matches the curated modifier children (Glass Bloon's plain/regrow/camo
  Zebras; DDT's 4 Camo Regrow Ceramics) and surfaces **one genuine wiki correction**:
  - **BAD** → `3 DDTs` became `3 **Camo** DDTs` (BAD's DDTs are camo in-game; the wiki dropped it).
  - *(A first pass mis-matched DDT to the base template and wrongly dropped its Camo; caught by
    the maintainer and fixed — DDT's children stay Camo Regrow. Regression-pinned by
    `test_inherently_modified_bloon_selects_its_variant_model`.)*
- **Tooling:** `parse_gamedata.py --bloons` (overlay; `--dry-run` to preview). It updates only
  `children`/`children_list`/`immune_to`, preserves every other curated field, and writes a
  `children_immunity_source` provenance marker. Re-runnable per dump pull.
- **Coverage map:** `Bloons/` note updated (children+immunity game-sourced; the rest still wiki).
- **Tests:** damage-types inverter (Lead/Black/White/Purple/Zebra-union, dedup, no Normal/Unknown);
  parser child base-resolution + modifier preservation + prose; data_service cutover assertions
  (one pre-existing DDT test corrected from the old wiki value). Full suite green.

### Session log — 2026-06-08 (Geraldo shop items ingested → answerable)

Next ⬜ domain off the coverage map, mirroring the proven Powers/Knowledge
extracted→committed→tool→answerable pattern. All **16** Geraldo shop items are now a
game-data-native lookup catalog.

- **Decodability verified first:** every item's `GeraldoItemModel` carries a `locsId`, and the
  textTable keys it as `"<locsId> name"` / `"<locsId> description"` — **0 of 16 missing**. The
  model also carries structured `cost` (in-game cash), `levelUnlockedAt` (Geraldo hero level),
  `startingQuantity`/`maxQuantity`, and `roundsToReplenish`/`amountToReplenish`.
- **Parser** (`parse_gamedata.py --geraldo`): `map_geraldo_items` → `geraldo_items.json` (16),
  sorted by unlock level then id. Names/descriptions HTML-stripped via `_clean_desc`; an item
  missing its name string is skipped + warned (none are today).
- **Runtime** (`btd6_data_service`): `GeraldoItemEntry` (optional fixture, validated,
  id/canonical-unique) + `get_geraldo_item` / `find_geraldo_item`; `geraldo_items.json` added to
  `_OPTIONAL_FIXTURES`.
- **AI tool** `btd6_geraldo_lookup` (single + roster) registered + in
  `BTD6_GROUNDING_TOOL_NAMES`. "What does Geraldo's Blade Trap do / how much is the Genie Bottle /
  what level unlocks the Paragon Power Totem" now answer.
- **Structured effects (follow-on).** Five items whose named behaviour model carries clean,
  description-confirmable numbers gained a structured `effect` (mirroring `PowerEntry.effect`):
  Sharpening Stone `{pierce_increase:1, rounds:10}`, Jar of Pickles `{damage_increase:1,
  attack_speed_scale:0.75, rounds:5}`, Fertilizer `{cash_scale:1.2, rounds:4}`, Rejuv Potion
  `{lives_gained:50}`, See Invisibility Potion `{rounds:5}`. Items whose effect is a spawned
  projectile (Blade Trap, Stack of Old Nails, Tube of Amaz-o-Glue), a tower summon (Creepy Idol,
  Genie Bottle, Shooty Turret), or non-numeric stay description-only — `effect == {}`, never
  fabricated. Surfaced on `btd6_geraldo_lookup`.
- **Coverage map:** `GeraldoItems/` fetch-status ⬜ → ✅ (regenerated via `--full-map`).
- **Tests:** parser (decode + skip-missing-name), data_service (load/resolve/fail-closed), tool
  (single/partial/roster/miss); both registry rosters updated. Full suite green.
- **Honest scope:** this is a *lookup catalog* (what each item is/costs/unlocks), not an
  *applied-modifier* tool — same boundary as Powers/Knowledge. The items' mechanical effects
  (e.g. Sharpening Stone's +damage magnitude) live in their `behaviorModels` and are **not**
  extracted; "Blade Trap on a Dart Monkey as a number" is not claimed.

### Session log — 2026-06-08 (`btd6_power_effect` apply-tool — answerability next-step #2 closed)

Built the deterministic Power→tower-stat apply-tool that the prior session left as the
last owed piece. The maintainer's standing question — *"what's Crossbow Master's attack
speed **on** a Monkey Boost"* — now answers as a grounded number.

- **Compute** (`btd6_upgrade_detail_service.power_effect`): resolves the tower/upgrade via the
  existing deterministic resolver (upgrade name / alias / path-notation, falling back to a bare
  tower's base tier `000`), reads `attacks[0].rate`, and applies the Power's decoded `rate_scale`
  → `{base,boosted}_cooldown_seconds` + `{base,boosted}_attacks_per_second` + `duration_seconds`.
  Grounded by construction (factor × resolved stat), so the faithfulness verifier accepts it.
- **Honest boundaries (fail closed, never fabricate):** only `rate_scale` modifies a tower stat
  today, so Thrive (cash) / Camo & Glue Trap (bloons) return `found=false` with a `btd6_power_lookup`
  pointer; economy towers with no committed attack (Banana Farm) return "no attack-speed stat";
  unknown power / unresolved-or-ambiguous tower / missing args all fail closed.
  `_POWER_STAT_EFFECTS` is the named extension point for the next stat-modifying factor.
- **Tool:** `btd6_power_effect(power, tower)` registered in `ai_tools` + added to
  `BTD6_GROUNDING_TOOL_NAMES` (auto-propagates to the grounding allowlist). Power-name resolution
  de-duplicated into `btd6_data_service.find_power` (+ a sibling `find_tower`), shared by the
  lookup and effect tools — one home.
- **Tests:** 5 service-level (`test_btd6_upgrade_detail_service`) + 2 tool-level
  (`test_ai_tools`) pinning the boost math (2× rate), the bare-tower base tier, and all four
  fail-closed paths; both registry-roster tests updated for the new tool. `check_quality --full`
  **green (8127 passed)**, `check_architecture --mode strict` 0 errors.
- **Still owed:** MK magnitudes (maintainer call — not dump-sourced) and the Steam-API
  patch-detect refresh trigger (gated on executable-CI sign-off) carry forward.

### Session log — 2026-06-08 (Power effect factors extracted + `{0}` placeholders filled)

Closed answerability next-step #1. `map_powers` now decodes a structured `effect` from each
power's dump effect model (`_POWER_EFFECTS` table, values from the dump — never hardcoded) and
**fills the description's `{0}`** from that same value:

| Power | `effect` | filled prose |
|---|---|---|
| Monkey Boost | `{rate_scale: 0.5, duration_seconds: 15}` | "…twice as fast for **15** seconds." |
| Thrive | `{cash_scale: 1.25}` | "…cash production …by **25**% …" |
| Camo Trap | `{affects_bloons: 500}` | "…remove Camo …from the first **500** Bloons…" |
| Glue Trap | `{affects_bloons: 300}` | "…slow the first **300** Bloons…" |

`PowerEntry.effect` carries it; `btd6_power_lookup` surfaces it. So the model can now state a
power's exact factor, though *applying* it to a named tower's stat is still the pending apply-tool
(answerability next-step #2). No `{0}` remains in any committed power description. Pinned by
`test_map_powers_fills_placeholder_and_extracts_effect` / `_pct_fill_renders_scale_as_percent`
+ the data-service effect assertion.

### Session log — 2026-06-08 (Powers + Monkey Knowledge ingested → answerable)

Two whole domains the coverage map flagged `⬜` are now `✅` end-to-end, following the
maps/modes/relics pattern (extracted → committed → tool → answerable):

- **Powers (25).** `parse_gamedata.py --powers` → `powers.json` (name, game-authored
  description, Monkey-Money cost, quantity, between-rounds). Names/descriptions resolve via
  `PowerId` → `textTable`; 2 hidden/event powers (no name string) are skipped, never surfaced
  as internal ids. HTML-ish markup (`<sup>TM</sup>`) stripped; `{0}` placeholders kept verbatim
  (filling them needs per-power effect decode — never invent).
- **Monkey Knowledge (134).** `--knowledge` → `monkey_knowledge.json` (name, **category from the
  `Knowledge/<Category>/` folder** — authoritative, like Maps' difficulty folders, not the
  opaque int — description, MM cost, investment required, prerequisites). Categories: Primary 32
  / Military 30 / Magic 22 / Support 22 / Heroes 13 / Powers 15.
- **Runtime:** `btd6_data_service` gained `PowerEntry` / `MonkeyKnowledgeEntry` (optional
  fixtures, validated, unique-checked) + `get_power` / `get_monkey_knowledge`; `ai_tools`
  gained `btd6_power_lookup` + `btd6_monkey_knowledge_lookup` (single + roster + category),
  both registered in `BTD6_GROUNDING_TOOL_NAMES`. So "what does Monkey Boost do", "how much is
  the Camo Trap power", "list the magic monkey knowledge", "what does Supa-Thrive do" now answer.
- **Verified:** anchors PASS; `--audit` unaffected (new fixtures, not stats overlay); the
  coverage map's fetch-status flips Powers/Knowledge → `✅`. Pinned by parser + data-service +
  ai_tools tests (incl. the two registry drift-guards updated for the new tools).

### Session log — temporary-buff triggers (units fixed) + Vigilante de-orphan + cash-on-leak

Decoded the two **time/round-windowed** buffs whose duration field was unit-ambiguous:
- **Desperado lives-lost buff** (`VigilanteTowerBehaviorModel`, the Nomad/Enforcer/…
  bottom line) was **orphaned** — not in `_BUFF_FIELD_MAP`, so a re-parse dropped
  it (committed values were right but unreproducible). Now decoded: raw
  `loseLifeAttackSpeedBuff`/`loseLifeRangeBuff` → `rateMultiplier`/`rangeAdditive`;
  `loseLifeBuff{Duration,Cooldown}Frames` ÷60 → `lifespan`/`cooldown` **in seconds**
  (900f=15s, 3600f=60s); `bloonLeakValueModifier` 2.0 → `cashOnLeakMultiplier`
  (a leaked bloon grants **2× its value as cash** — maintainer-confirmed, same
  mechanic as Bloon Trap / Obyn trees). Trigger `on_life_lost`.
- **Engineer/Spike start-of-round buff** (`StartOfRoundRateBuffModel`): the raw
  `duration` is a **round count** (`durationFrames` is 0), so it now maps to
  `duration_rounds` — keeping `lifespan` exclusively for seconds. Trigger
  `start_of_round`; re-applies every round (effectively permanent), so the renderer
  states the condition, not a misleading "lasts 3s".
- **Why it matters:** the committed `lifespan` field was carrying *two units*
  (15 = seconds on Desperado, 3/10 = rounds on Spike). The new `trigger` field is
  the discriminator that fixes the unit downstream. `_BUFF_TRIGGER` /
  `_BUFF_FRAME_FIELDS` in the parser; `_buff_trigger_clause` in
  `btd6_upgrade_detail_service`. Committed data re-merged (parser-reproducible,
  coverage unchanged: 26 Desperado + 15 Engineer + 26 Spike tiers). Pinned by
  `test_buffs_vigilante_lives_lost` / `test_buffs_start_of_round_rate` (parser) and
  the trigger/cash-on-leak render tests.

### Session log — per-round cash (all 140, derived) + where the cash economy lives

Traced "cash per pop / per round" end to end:
- **Per-pop:** flat **$1 per bloon layer** (maintainer-confirmed + BloonsWiki "Cash
  per pop"), ×0.5 on Half Cash, reduced in late rounds by the income-decay curve.
  ~~**Not in the asset dump** — hardcoded game logic.~~ **CORRECTED 2026-06-08 (dump
  re-audit):** it *is* in the dump. The top-level `cash` field is null, but each bloon
  carries a **`DistributeCashModel{cash: 1.0}`** behavior — that is the per-pop value
  (`Bloons/Red/Red.json` → `behaviors[1]`). The derived $1 was right; the "hardcoded,
  not in dump" reasoning was wrong (didn't read the bloon's `behaviors[]`).
- **Per-round *tower* income** IS in the dump as `PerRoundCashBonusTowerModel.
  cashPerRound` (Benjamin 90→5000 by level, farms, SOTF) — already surfaced for
  the towers that have committed tiers.
- **Per-round *game* cash** (pop cash + end-of-round bonus, standard/Medium, no
  income towers) is NOT stored anywhere (cash is computed) — but it is fully
  **DERIVABLE**: `cash(n) = pop_count(n) × cash-per-pop-decay(n) + ($100 + n)`,
  where `pop_count` = the round's spawn composition × each bloon's total pops (a
  MOAB = 1 pop but 200 RBE — which is why cash ≠ RBE once blimps appear). The
  decay bands are the v55 `DefaultIncomeSet`. **Validated 80/80** against the
  cyberquincy data set and topper64's calculator (both use this exact formula).
  Now derived for **all 140 rounds** straight from `rounds.json`'s own
  composition + `bloons.json` child-trees, pinned by
  `test_btd6_round_cash.py` (the cash analogue of the RBE test). `RoundEntry`
  gained `cash` (float) + `cumulative_cash`.
- **81-140 resolved (our composition is v55-current; cyberquincy was stale).**
  The 81+ divergence was NOT a composition gap — our committed `groups` match the
  dump's v55 `DefaultRoundSet` pop-counts exactly. It was **cyberquincy** being
  out of date: freeplay cash-per-pop was buffed (×0.02 → ×0.04 past round 120) a
  few updates ago. So 81-140 cash is computed from our v55 composition with the
  current decay. (The Steam Web API doesn't expose round economy; the game files
  store emissions, not cash — derivation from composition is the route.)

### Session log — 2026-06-04 (dump re-validation: confirmable data mapping is caught up)

Cloned the v55 dump (`Btd6ModHelper/btd6-game-data` @ `a3348a89` — the pinned
commit; `main` is still there, no drift) and re-ran the pipeline end to end.
**The confirmable data mapping is caught up; the remaining frontier is genuinely
cutover-gated.** Evidence:

- **Anchors pass; `--audit` is nothing-SUSPECT** against the fresh dump.
- **`--overlay --dry-run`, `--descriptions --dry-run`, and `--maps` are all
  no-ops / byte-identical** → committed tower/hero/map data is fully in sync with
  v55. There is no pending value to refresh.
- **Buff decode tail (step 1) — re-confirmed exhausted via a roster-wide
  discovery.** Of ~24 undecoded `*SupportModel`/`*BuffModel` types, **none is
  value-confirmable now**: most (`RangeSupportModel` ×134, `PierceSupportModel`
  ×60, `MonkeyCityIncome`/`ProjectileSpeed`/`ProjectileRadius`/`FreezeDuration`/
  `Pyrotechnics`/`BananaCashIncrease`…) have **no committed `buffs[]` counterpart**
  on a matching tier to verify against; the only two with a committed match
  (`DamageModifierSupportModel`, `TargetSupplierSupportModel`) match **only** on
  the trivial `customRadius/maxStackSize=0` — their real effect
  (`damageAdditiveForBad`, `rateMultiplier`) lives in a *different* model, so
  there is no raw number to confirm. The `SCHEMA_FIRST` set carries a direct
  multiplier but with **no committed value and direction/transform ambiguity**
  (is `0.25` ×0.25 or +25%?), so it can't be confirmed pre-cutover either. Holds
  the standing rule: **do not write a number you can't confirm.**
- **`theme`/`coopMapDivisionType`/`unlockDifficulty` are opaque integer enums**
  (`theme` is 0–6) with no in-dump label source → not decodable without a
  confirmed mapping (would be guessing).
- **Removables: not in this dump** (see step 6 below) — closed.

**Net:** for *new* numbers the next motion is the **tower cutover machinery** or
**external value sources** — both need the maintainer's call. But one safe,
wiki-grounded win was available without writing any new number and was taken:
the **`SCHEMA_FIRST` cash renderer** (step 2). `_BUFF_FIELDS` had no cash field,
so Trade Empire's income (already decoded + committed via `TradeEmpireBuffModel`)
was silently *dropped* — "what does Trade Empire do" answered with only the +1
damage. Added `cashPerRoundPerMechantship` / `cashPerRoundPerFavouredTrades` /
`cashbackZoneMultiplier` render entries (labels wiki-confirmed), so the income now
reaches the answer. This is the canonical *extracted ≠ answerable* fix — no new
value asserted, just un-dropped. See step 2 for the income-multiplier decode that
this renderer work teed up.

### Session log — 2026-06-04 (behaviour layer: PMFC/Mermonkey thin-grounding + guards)

Picked up the phrasing-sensitivity cluster (PR #491 / absence-claim-guard design
Update 3). The sandbox still can't reach Discord, so this is the retrieval-side
work verifiable here; the prompt-layer items still owe a live check.

- **Mechanism 2 fixed (thin upgrade grounding) — `btd6_context_service`.** An
  upgrade-only query ("what's the damage type when plasma monkey fan club ability
  is activated") resolved the *upgrade* (PMFC → 4 facts) but not its *tower*, so a
  conceptual question had almost nothing to stand on and the model refused despite
  holding the Sharp fact. New **Pass 3d** grounds the upgrade's **parent tower**
  (PMFC → Dart Monkey's ~60 facts; POD → Wizard Monkey) when the tower wasn't
  already resolved, deduped so a tower the user *named* isn't grounded twice.
  Verified: PMFC ability query **4 → 63 facts**; "super monkey prices" still 17
  cost lines (no double). Retrieval only — the design doc's §4.1 Layer A
  enrichment, **not** the Layer B guard (still design-only; do not build blind).
- **Map removables faithfulness fix** — the "Unsupported BTD6 areas" clause in
  `_TASK_CONTRACT` now covers per-map removables, so "list maps with removables"
  states the limitation instead of improvising example maps from memory.
- **Guard tests** — 89-map embed pinned under Discord's field/total limits; a
  single tower's grounding pinned ≤ 80 lines / ≤ 240 chars per line (current worst
  60) so the rich auto-grounding can't silently balloon the prompt.

**Still owed (need live Discord verification — could not run here):** mechanism 1
(conversational context not carried — a follow-up with no entity routes to general
with 0 facts) and mechanism 3 (answer-what's-grounded vs. wholesale refuse) are
prompt/stage-layer; build those from a live repro. The Bomb Shooter / Mermonkey
"path" phrasings already ground 60 / 52 facts via tower fallback, so any remaining
failure there is mechanism 3, not retrieval.

### Session log — Maps hub button + correct difficulty/mode/modifier taxonomy

- **Maps button added** to the BTD6 hub (`views/btd6/panel.py`, row 2) →
  `build_maps_embed()` lists all 86 maps grouped by difficulty with a 💧 water
  marker (surfacing the `has_water` fact from the maps cutover).
- **Modes corrected to the real BTD6 taxonomy** (from the in-game select
  screens, screenshots verified). `ModeEntry` gained `kind`
  (`difficulty`/`mode`/`modifier`) + `difficulties`:
  - **Difficulties** (set lives/speed/prices): Easy 200 / Medium 150 / Hard 100
    (Hard starts round 3); medal per round cap.
  - **Modes**: Standard is the **base mode in every difficulty** (was wrongly
    collapsed into "standard"); the specials are difficulty-scoped (Primary
    Only/Deflation→Easy, Military/Apopalypse/Reverse→Medium, Magic/Double HP/
    Half Cash/ABR/Impoppable/CHIMPS→Hard); Sandbox spans all.
  - **Modifiers** (NEW finding — *are* extractable, as descriptions): Double
    Cash and Fast Track. The dump's `textTable` carries their game-authored text
    (`btd6_doublecashmode`/`btd6_fasttrackpack`), but their effect is **relative**
    (Double Cash = ×2 cash forever; Fast Track = start ~¼ into the round count
    with the cash you'd have there) — there is **no fixed starting-cash/round
    constant** to extract, so `starting_cash`/`starting_lives` are now optional
    (`None` for modifiers). Encoded honestly with the relative rule in
    `restrictions`.

### Session log — buff decode started (2 confirmed types)

- **Buffs — decode progressing, correctness-first (8 of 38).** Confirmed eight
  types across two passes (each value hand-vetted exact against committed wiki
  data on a matching tier): `RateSupportModel`, `PoplustSupportModel`,
  `SubCommanderSupportModel` (Sub 0-0-5 = 4/0/2), `PiercePercentageSupportModel`
  (Mermonkey 1.1/1.2/1.4), `TradeEmpireBuffModel` (Buccaneer 0-0-5),
  `PlacementAreaTypeRangeBuffModel` (Mermonkey in-water 1.35),
  `StartOfRoundRateBuffModel` (Engineer/Spike: `modifier`→`rateMultiplier` 0.25,
  `duration`→`lifespan` — two-tower), and `PrinceOfDarknessZombieBuffModel`
  (Wizard Undead: `damageIncrease`→`damageAdditive` 3, `distanceMultiplier`→
  `lifespanMultiplier` 1.5).
  - **Verification discipline note:** the roster-wide discovery harness is a
    *lead generator*, not truth — it ranks candidates by value coincidence. The
    **committed wiki data is the arbiter**: e.g. `distanceMultiplier`→
    `lifespanMultiplier` *looked* like a semantic false positive, but the
    committed Undead buff carries `lifespanMultiplier 1.5` and the only raw 1.5
    is `distanceMultiplier`, so it is in fact the correct correspondence. Vet
    each candidate against the committed value, not against priors.
  - Also this pass: confirmed **Deflation = start round 31 with $20,000, no
    income** (in-game screenshots), and that **Double Cash doubles the starting
    cash** ($40,400 = 2×$20,200 with the ×2 modifier active).
- **Buffs — decode started, correctness-first (2 of 38).** `_buffs()` now emits a
  `buffs[]` entry per top-level `*SupportModel`/`*BuffModel`, but **only writes a
  number for types confirmed against the committed wiki value on a matching tier**:
  - `RateSupportModel.multiplier` → `rateMultiplier` (Sniper Elite Defender: raw
    `0.75` == wiki `0.75`).
  - `PoplustSupportModel.ratePercentIncrease`/`piercePercentIncrease` →
    `ratePercentage`/`piercePercentage` (Druid Poplust: `0.15`/`0.15`).
  - Validated roster-wide: no tower has a raw value contradicting the committed
    one. (Notably, `monkey_village` carries a raw `RateSupportModel 0.85` the wiki
    omitted — game-data is richer, not wrong.)
  - **Deferred (not yet confirmed):** `PierceSupportModel.pierce`→`pierceAdditive`
    — the wiki's pierce buffs are `pierceMultiplier` from a *different* model, so
    this needs same-tier confirmation before it's written. The other ~35 types
    likewise await confirmation (or a renderer field, for the `SCHEMA_FIRST` set).
  - Names: buff `name` is the dump's **internal** id (`buffLocsName`/`mutatorId`),
    never a curated label — those aren't in the dump, so the audit aligns by name
    and ignores ours (stays nothing-SUSPECT). Wired into `_map_tier`.
- **Next buff step:** confirm one more type per pass (cross-check raw vs committed
  on a matching tier), add to `_BUFF_FIELD_MAP`. The `SCHEMA_FIRST` types
  (projectile speed/radius, freeze duration, banana-cash multiplier) need a new
  field on `_BUFF_FIELDS` in `btd6_upgrade_detail_service` + its renderer first.

### Session log — maps + modes cutover + zone decode started

- **Maps — full game-data cutover (3 → 89).** `parse_gamedata.py --maps` rebuilds
  `maps.json` from the dump's `Maps/<Difficulty>/` folders. Difficulty is taken
  from the folder (authoritative — it corrected stale curated rows, e.g.
  Cornfield was mis-tagged "Beginner", is actually **Advanced**); display names
  from `textTable`; new `has_water` fact wired through `MapEntry` →
  `btd6_map_lookup` (the bot can now answer "which maps have water"). Curated
  prose (`description`/`lines_of_sight_notes`) is preserved where it existed.
- **Modes — full set (2 → 13).** ~~The dump has **no** game-mode rules (starting
  cash/lives/restrictions are gameplay code, not exported assets).~~ **CORRECTED
  2026-06-08 (dump re-audit) — FALSE, same `mutatorMods` trap as MK/cash.** `Mods/`
  (22 files) carries the **entire** rule set as typed mutators at the file's top-level
  `mutatorMods[]`: Easy/Med/Hard `StartingCashModModel 650` + `StartingHealthModModel
  200/150/100` + `GlobalCost`/`GlobalSpeed`/`SellMultiplier`/`BonusCashPerRound`/
  `EndRoundModModel 40/60/80` + `MonkeyMoneyModModel`; **HalfCash** `ModifyAllCash ×0.5`;
  **Deflation** `StartingCash 20000`+`StartingRound 31`+no-income; **Impoppable** 1 life/
  `GlobalCost ×1.2`/end 100; **CHIMPS is internally `Clicks.json`** (`ChimpsModModel`+lock
  farm+1 life+no sell/continue/MK); Primary/Military/MagicOnly = `LockTowerSetModModel`
  by `towerSet` id. The curated `modes.json` values happen to match the dump (they were
  right) — but it could be **sourced/verified from `Mods/`** rather than hand-curated.
  So `modes.json` is **currently curated** from established facts: Standard,
  Primary/Military/Magic Only, Deflation, Apopalypse, Reverse, Double HP MOABs, Half
  Cash, ABR, Impoppable, CHIMPS, Sandbox.
- **Zones — decode started.** `_zones()` emits every top-level `*ZoneModel` as a
  structured `{kind, name, + decodable numbers}` (Ice Arctic Wind →
  `speedScale 0.6`, `zoneRadius 25`), wired into `_map_tier` and audit-safe.
  Remaining: the per-type effect tail, zones nested in sub-towers, and curated
  display names (not in the dump). See the 🟡 table.

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
- **Live bug-report round 2 (maintainer + friends) — verified, two hypotheses
  corrected.** Three reported issues:
  - **Paragon false "no paragon" (Buccaneer).** Maintainer hypothesised a broken
    tower→paragon linkage. **All-tower audit disproves it:** every paragon-bearing
    tower is consistent (`monkey_buccaneer`→`paragon_cost=550000`→`navarch_of_the_
    seas`), and `build("…buccaneer")` **emits** the correct `[btd6_paragon]`
    Navarch line. So **no data fix** — the false "no paragon" is the model
    confabulating an absence when that grounding wasn't surfaced → it's the **pure
    absence-claim repro** (absence-claim design Update 2), not a linkage bug.
  - **Upgrade-cost routing.** Maintainer hypothesised the *task router* branches
    cost intent to general vs the cost tool. **Tested `classify()` — disproven:**
    route ≠ outcome (`monkey ace upgrades`/`pricing of monkey buccaneer` route to
    `btd6.answer` yet failed; `what are all the upgrade costs of the heli` routes
    to `general.nl_answer` yet worked). Real mechanism: inconsistent model
    invocation of the deterministic cost tools for *derived* numbers — the
    derived-value family (finding §5.2). Fix is **auto-attached cost grounding**,
    not a router change.
  - **Absence-claim guard RE-ELEVATED** — the paragon case is the pure repro, and
    a new hard requirement landed: **absence claims leave no audit row** (recent_
    audit is denial-only), so the guard must emit an auditable signal. See the
    absence-claim design Update 2.
  - **Not broken (confirmed):** `btd6_cumulative_cost` arithmetic across Wizard/
    Heli/Buccaneer; `btd6_relic_lookup`/`btd6_bloon_filter` registered (see the
    capability-surface bullet above).
- **Live bug-report round 3 (super monkey) — route≠outcome confirmed LIVE +
  upgrade-descriptions FIXED.** `recent_audit` showed the super-monkey upgrade
  refusals as `grounding_failed` on **`task=btd6.answer`** — so the question
  *did* route to BTD6 and auto-ground, yet failed: **live proof that routing is
  not the cause** (matches the `classify()` test). Two grounding gaps isolated:
  - **Gap A — descriptions not surfaced (FIXED).** `build()` listed upgrade
    NAMES + costs but **not** their game-authored descriptions (all 15 exist via
    `get_upgrade_detail`), so "list all the upgrades and descriptions of X" had
    no grounding → the model free-recalled → `grounding_failed`. Added
    `_render_upgrade_descriptions` (mirrors `_render_hero_descriptions`): every
    described card now grounds as a `[btd6_upgrade]` line. Verified in-sandbox
    (super monkey: 15/15 attached). *Live-owed: the re-ask must now answer.*
  - **Gap B — derived prices (FIXED).** "list upgrade prices" failed even
    though MEDIUM prices are grounded, because the model elaborated into
    *difficulty-scaled/cumulative* prices it didn't route through the cost tools
    → `grounding_failed`. Maintainer chose the broad scope (**every tower
    question**). Added `_render_tower_costs`: every resolved tower now grounds a
    `[btd6_cost]` block — base + each upgrade's **per-buy** (Easy/Med/Hard/Impop)
    **and cumulative** (base+priors) cost, reusing the tested
    `cumulative_upgrade_costs` engine. So the all-difficulty / total-cost tables
    are grounded by construction, with no dependence on the model calling a tool.
    Verified in-sandbox (super monkey: 17 lines; True Sun God Impoppable per-buy
    $600,000; numbers reconcile). *Live-owed: the re-ask must now answer.*
- **Live bug-report round 4 (phrasing-sensitivity cluster) — diagnosed, NOT a
  data gap.** With tonight's reachability fixes in, the remaining failures are a
  behaviour layer: the answer depends on phrasing/resolution, not data presence.
  Clean A/B repros (verified in-sandbox — data present in all): "PMFC (0-5-DART)"
  answered ideally (Sharp + flagged the ability-conversion gap) while "...when
  plasma monkey fan club ability is activated" refused with the Sharp fact in
  hand; "what does mermonkey bottom path do" refused despite **52** grounded
  facts; "explain what the bottom path does" (no tower named) routed general with
  0 facts. Three mechanisms: (1) conversational context not carried into
  resolution; (2) upgrade-resolution gives thin grounding (4 facts) vs tower
  (63); (3) **partial-answer-vs-refuse** — the model refuses wholesale instead of
  answering the grounded part + flagging the gap. Captured in the absence-claim
  design **Update 3**; behaviour/resolution-layer, design-first, not built blind.
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
>   has-curated-name?). Emits `docs/btd6/btd6-decode-inventory-v55.md`; validates
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
| **Maps — full game-data cutover (86)** | `parse_gamedata.py --maps` → `maps.json` | difficulty from the dump's folder (corrects stale curated rows, e.g. Cornfield → Advanced), names via `textTable`, `has_water` + curated `removables` (18) wired into `MapEntry`. 3 non-player `IsStandard=False` maps filtered (Blons, Base Editor Map, Protect the Yacht) → **86** player maps load + tests green |
| **Modes — full set (13)** | curated `modes.json` | this session; the dump has **no** game-mode rules (cash/lives/restrictions live in game code, not assets), so authored from established facts: Standard, Primary/Military/Magic Only, Deflation, Apopalypse, Reverse, Double HP MOABs, Half Cash, ABR, Impoppable, CHIMPS, Sandbox |

### 🟡 Partial — NOT complete

| Item | Done | Missing |
|---|---|---|
| **Subtowers** (`subtowers[]`) | **All 7 spawn mechanisms (2026-06-09)**: `AbilityCreateTower`/`CreateTower`/`MorphTower` (embedded **and** Alchemist's `secondaryTowerModel` — no named-ref morph exists in v55.1; `TransformedMonkey*.json` are orphans) + `BeastHandlerLeash` (`towerModel`+`towerModelSecond`, dual beasts) + `ComancheDefence` + `TowerCreateTower` (PermaPhoenix, Corvus Spirit) + `TranceTotemSpawner`. Lifespan falls back to the embedded `TowerExpireModel` (Marine 30 s / Lava Phoenix 20 s, committed-confirmed). Subtower-scoped `AttackAirUnitModel` emission (Mini-Comanche missile rate 3 / Explosion 4, committed-confirmed). All confirmable values verified vs committed: Alchemist 72/0.03/10/2, Beast tiers, Trance totem, PermaPhoenix 5/8 | Beast Handler bird-path `GyrfalconPatternModel` (grab/pattern combat needs a bespoke reader — committed "Grab" attack stays curated); `FindDeploymentLocationModel` deliberately unwired (duplicate Marine); per-tier beast display names vs committed "Beast" = maintainer call at cutover; base-tower `AttackAirUnitModel` widening = cutover-scope |
| **Zones** (`zones[]`) — **started** | `_zones()` emits every top-level `*ZoneModel` as `{kind, name, + decodable numbers}` (e.g. Ice Arctic Wind → `speedScale 0.6`, `zoneRadius 25`); now also the Heli **MOAB-Shove** per-blimp caps via `_ZONE_RENAME` (`*PushSpeedScaleCap` → `multiplierFor{Moab,Bfb,Zomg}`, verified exact vs committed). `_zone_text` renders Ice slow, Druid thorn-bonus **and** MOAB-Shove (negative = shoved backward, maintainer-confirmed). Wired into `_map_tier`, audit-safe (internal names) | the rest of the 28 types' specific effect fields (per the SHA-pinned report §3a only `BuffBlowbackZone` (DEFER, hero not committed), `BonusCashZone` (Temple sacrifice-conditional) and `ActivateRangeSupportZone` (in-ability, value unconfirmed) carry numbers at all); curated display names (not in the dump — stay wiki-owned); MOAB-Shove **DDT** cap (no dump field — curated mirror of ZOMG, maintainer to confirm at cutover). *(2026-06-09: zones nested in sub-towers verified emitting — Obyn's totem is the only catalog case — and the meaning-disambiguating `inclusive` flag is now captured: Obyn's two same-tag SlowBloonsZones are False = non-MOABs ×0.6 / True = MOABs ×0.8; without the flag the exclusive zone reads inverted.)* |
| **Projectile flattening completeness** | spawn-model coverage (under-emission 177→111) | 111 attacks still differ in projectile count vs wiki; flattening *style* (naming/grouping) differs |
| **Buffs** (`buffs[]`) — **started (14 of 38)** | `_buffs()` decodes eleven types **confirmed exact against committed wiki values on a matching tier**: `RateSupportModel`, `PoplustSupportModel`, `SubCommanderSupportModel`, `PiercePercentageSupportModel`, `TradeEmpireBuffModel`, `PlacementAreaTypeRangeBuffModel`, `StartOfRoundRateBuffModel`, `PrinceOfDarknessZombieBuffModel`, `VigilanteTowerBehaviorModel` (Desperado lives-lost: frame→seconds windows + `cashOnLeakMultiplier` + `trigger`), `SupportShinobiTacticsModel` (Ninja, `multiplier 0.92`→`rateMultiplier`) and `DamageModifierSupportModel` (Mortar Pop-and-Awe, nested `damageAddative`+tag→`damageAdditiveForBad`); **2026-06-09:** `RangeSupportModel` (additive→`rangeAdditive`, multiplier→`rangePercentage` — the old ambiguity pinned by 4 independent committed confirmations: Mermonkey conch identity, Ninja-paragon identity, Etienne 10%/20% prose, Obyn +5 prose), `ProjectileRadiusSupportModel` (multiplier→`radiusMultiplier`, Striker L7 identity ×1.1) and `BananaCashIncreaseSupportModel` (multiplier→`incomePercentage`, Benjamin L5 +5% / L9 12% prose — **committed** via the benjamin.json re-export, rendered by the new `_BUFF_FIELDS` rows). See `_BUFF_FIELD_MAP` / `_BUFF_DAMAGE_MODIFIER_TYPES` / `_BUFF_TRIGGER`. Wired into `_map_tier`, audit-safe (internal names) | the other 27 buff types — each needs same-tier confirmation before its number is written, and (2026-06-08 finding) **none of the remaining types lands on a committed combat tower with a `buffs[]` to confirm against**: they are hero-only (separate `map_hero` path), on economy/support towers with **no committed tiers** (Village/Farm — blocked, maintainer call), or paragon `base` nodes. `SCHEMA_FIRST` types (projectile-speed/radius, freeze-duration, banana-cash) also need a new renderer field. The discovery harness is a lead generator; vet each candidate against the committed value (it is the arbiter, not semantic priors) |
| **Numeric overlay applied** | 3 files (Desperado range, mermonkey xp, ace cost), uniquely-keyed only | per-projectile/ability values cannot be safely overlaid (wiki↔dump name mismatch) |

### 🔴 Not started

*(2026-06-10: this list is cleared — every row either shipped or moved. Economy
attack suppression + the towers cutover + the paragon cutover = **PR #649**;
bloons children/immunity/health/speed cut over earlier (`--bloons`), bosses via
`--bosses`; Powers/Knowledge ingested 2026-06-08; ABR rounds + IncomeSets in
**#638**. The live worklist is the ⭐ post-cutover backlog.)*

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
   `scripts/btd6_decode_inventory_report.py` → `docs/btd6/btd6-decode-inventory-v55.md`,
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
   > **Slice 1 shipped (#477):** the ×100 render fix only — at that time no
   > buff/zone numbers were written. **Update (later sessions):** zone decode is
   > now started and **8 of 38 buff types are written** (`_BUFF_FIELD_MAP`); see
   > the ✅/🟡 completion tables above for the live counts (the old "0 of 28 /
   > 0 of 38" no longer holds).

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
- **Domains never opened (cosmetic-skip; verdicts stand):** `Achievements/`,
  `BloonOverlays/`, `Skins/`, `TrophyStoreItems/`. *(The rest of the old
  "never opened" list has since been ingested: `GeraldoItems/`, `Knowledge/`,
  `Maps/`, `Mods/` — see the ⭐ top section.)* `Artifacts/` was spot-checked
  2026-06-09: it carries **real gameplay modifiers** (rate/damage behavior
  models), but exclusively for the Rogue Legends / Frontier spin-off modes —
  skip stands on scope, not on "cosmetic".
- **Only counted (structure not mapped):** `Rounds/` (5,181 files across 46
  round-set folders incl. `AlternateRoundSet`), `IncomeSets/` (7).
- **Loose files — triaged 2026-06-09:** `frontierData.json` = Frontier event
  meta-mode balance (121 keys; no main-game boss scaling — the old dictionary
  label was wrong); `rogueData.json` = Rogue Legends spin-off balance;
  `resources.json` = a 19,260-entry GUID→asset-path lookup, zero stat content.
  All three: skip on scope. **`paragonDegreeData.json` is now CROSS-CHECKED
  (2026-06-09):** `paragon_degrees.power_for_degree` matches the dump's
  `powerDegreeRequirements` **100/100 exactly** (incl. 0 @ d1, 200,000 @ d100),
  and all 12 scalar caps/divisors + the scaling-formula constants match
  `paragon_math` / `paragon_degrees`. Known, accepted edge: the offline
  fallback `paragon_math.threshold` replicates the live Paragon-API *floor*
  where the game *rounds* — 48 boundaries sit exactly 1 power low (e.g. d6:
  API 3407 vs game 3408). Display path is game-exact; only the API-replica
  fallback carries the 1-power edge (kept API-faithful on purpose).
  `POWER_PER_TOTEM = 2000` has no dump counterpart — still unverified.
- **Within `Towers/` (examined domain) still undecoded:** the **28 zone + 38
  buff** model types' remaining effect fields (the SHA-pinned inventory report
  §3 is the live worklist; 11 buff types are decoded); status-effect /
  targeting / income behavior models beyond what `_map_tier` reads.

## Freshness
- Re-pull the dump per patch; re-validate anchors (Dart 200, Super 2500) and
  re-run `--audit`. Use the Steam patch-notes feed (#459) as the "time to
  re-pull" signal.
