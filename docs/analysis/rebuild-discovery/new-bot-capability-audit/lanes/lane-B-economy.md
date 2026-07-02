# Lane B — Economy & Character-sim (Axis 1)

> **Status:** `reference` — **Lane B audit COMPLETE** (the highest-risk grammar-fit lane: deep persistent
> state). Produced by an Opus 4.8 ULTRACODE session (2026-07-02): an 11-agent
> source-verification fan-out (one agent per subsystem, ~1.24M tokens, every unit cited to `file:line`),
> then a 7-agent **adversarial refute pass** on every proposed new amendment + every surprising fit, then
> synthesis. Method + contract: [`../BRIEF.md`](../BRIEF.md) · [`../PARTITION.md`](../PARTITION.md) ·
> `tools/grammar_spike/` · [`../ground-truth/command-surface.json`](../ground-truth/command-surface.json).
> Verification rule (Q-0120): source & merged PRs beat docs; uncertain rows are marked `⚠ unverified`.

**Subsystems (disjoint from Lanes A/C/D):** economy · inventory · treasury · mining · fishing · creature ·
farm · xp · casino · four_twenty · counters.

---

## 1. Headline verdict

**Lane B fits the §2 manifest grammar at 67% as-written → 88% with amendments** (449 surface units).
That clears the "generated, not hand-written" bet for **9 of 11** subsystems — but only after a specific,
**bounded** set of amendments, and with **two hard-tier-3 residues the grammar must never absorb.**

- **The grammar holds for the money/config/collection surface.** treasury, farm, inventory, counters,
  four_twenty reach **92–100%** with amendments; economy/mining/fishing/creature reach **91–93%**. The
  ~2/3 of every subsystem that is commands→panels, settings, bindings, stores, help, and read-models
  generates cleanly — exactly the logging/karma result, at scale.
- **The deep-state core needs SIX real primitive families, all economy/character-sim-shaped**, none of
  which exist in §2 today: **G-7 EconomyTransactionSpec** (the load-bearing one), **G-8 ItemCatalogSpec**,
  **G-9 ProgressionSpec**, **G-11 ShopSpec**, **G-12 CraftingRecipeSpec**, **G-13 IdleAccrualSpec** (plus a
  scoped **G-10** persistent-world store convention). These are *additive tier-2 declaration families* — a
  docs-pass into the spec, not a redesign.
- **The adversarial pass refuted seven over-eager amendments.** The first-pass fan-out proposed new
  families for RNG loot, multi-seat tables, read-model projections, participation prefs, managed
  projections, setting-preset bundles, and auto-responders. **All seven fold into existing grammar or stay
  tier-3** (§4) — the amendment list is deliberately *short*. This is the poison-guard the BRIEF names
  (Q-0120): a "needs a new family" verdict that is really "I didn't see the existing form" corrupts the
  spec. The refute pass cut the amendment count roughly in half and corrected casino's fit **68% → 24%.**
- **Two residues are legitimate tier-3 forever** (§2.9/§10.1 — "the grammar must never be a worse
  programming language"): **(a) game engines and per-player weighted-RNG reward/encounter/drop rolls**
  (blackjack rules, poker eval, mining ore draws, fishing catch weighting, creature encounter) and **(b)
  stateful live-game loops** (casino's multi-seat poker table). **Casino is the floor of the whole
  audit at 16% → 24%** — below blackjack's 44%, because it has *zero* config/settings/store/event
  surface to generate and its game is more complex. That is honest and expected, not a grammar failure:
  casino is ~85% game logic by unit, and game logic is the one thing the grammar is designed *not* to own.

**GO-with-amendments for Lane B.** No subsystem is NO-GO. The amendment list (§4) is bounded, all six
core families are economy/character-sim primitives a future bot needs anyway, and every tier-3 residue is
dispositioned as either a named amendment or a documented deliberate escape hatch.

---

## 2. Fit numbers (measured, per subsystem)

Sorted by as-written fit. "Units" counts every surface unit (a `×N` row counts as N). Casino/counters/
four_twenty amended figures are **post-adversarial** (the first-pass fan-out over-credited them; §4).

| Subsystem | Units | Fit — as-written | Fit — with amendments | Verdict | Danger tier |
|---|--:|--:|--:|---|---|
| **casino** | 25 | **16%** | **24%** | keep | 🔴 stateful live game (the floor) |
| **economy** | 54 | **63%** | **93%** | keep | 🟠 currency kernel + earn RNG |
| **inventory** | 21 | **67%** | **100%** | redesign | 🟡 item taxonomy, unaudited grants |
| **mining** | 108 | **67%** | **93%** | redesign | 🔴 grid world + 27 txns (the deepest) |
| **farm** | 19 | **68%** | **100%** | keep | 🟡 idle accrual |
| **fishing** | 89 | **71%** | **91%** | keep | 🟠 minigame + accrual + crafting |
| **creature** | 28 | **75%** | **93%** | keep | 🟠 PvP battle + encounter RNG |
| **xp** | 57 | **75%** | **82%** | keep | 🟡 progression + import parser |
| **counters** | 21 | **81%** | **95%** | keep | 🟢 scheduled loop (mis-binned — operator band) |
| **four_twenty** | 12 | **83%** | **92%** | keep | 🟢 observe-only easter egg |
| **treasury** | 15 | **80%** | **100%** | keep | 🟢 escrow (well-guarded) |
| **Lane B total** | **449** | **67%** | **88%** | GO-w/-amend | — |

Comparison to the spike's 3 measured subsystems (karma 80→87%, logging 79→97%, blackjack 44→44%,
overall 73→85%): Lane B's config-heavy subsystems match logging; its games match blackjack; **the new
finding is the middle band** — economy-sim (mining/fishing/farm/economy) sits at ~63–71% as-written and
lifts to ~88–100% via the six new families. The spike's "85% is a floor" assumption **holds at the lane
level (88%)** but is **not uniform**: the floor is casino (24%), and the games/economy-sim band only
reaches it *with* the six amendments — without them Lane B is a 67% lane, which would re-inherit the
fragmentation the rebuild is trying to kill.

---

## 3. Confirmed amendment families (survive adversarial re-check)

**Rubric (applied uniformly):** a new family is justified only if it is **(a) not expressible via an
existing Spec or a thin composition of them, AND (b) recurs across ≥2 *shipped* subsystems.** Six families
(+ one scoped) clear it. Line numbers are representative; the per-subsystem ledgers (§7) carry the full
cites.

| Id | Family | What it declares | Recurs across | Tier lift |
|---|---|---|---|---|
| **G-7** | `EconomyTransactionSpec` | An **atomic multi-write money mutation** as data: debit/credit legs + immutable `economy_audit_log` row(s) + `economy.balance_changed` emitted **after commit**, as one `db.transaction()`, with `settle_once` / conditional-debit and `refund_policy`. | economy (`transfer`/`bet_and_settle`), treasury (`contribute`/`disburse`), mining (~10 legs), farm (3), fishing (2), inventory grants — **6 subsystems** | 3→2 on every money-moving seam |
| **G-8** | `ItemCatalogSpec` + `InventoryItemSpec` store | **Item taxonomy as data** (kind, stackable, unique, rarity, emoji, category) **+ kernel-owned atomic, unique-fenced, AUDITED grant/consume/has** ops. Directly fixes the inventory cert's "unaudited item grants" weak spot. | inventory, mining, fishing, creature — **4 subsystems** | 3→2 on grant/consume paths |
| **G-9** | `ProgressionSpec` | The **cooldown-gated earn + streak + level/curve GATE** as declared data (daily 24 h + streak, work 1 h, xp quadratic curve + per-message cooldown, mining depth/skill gates). **Declares the gate, not the payout** (the payout stays tier-3, §5). | economy, xp, mining, fishing, creature, farm — **6 subsystems** | 3→2 on the *gate*; payout stays 3 |
| **G-11** | `ShopSpec` | A **priced catalog** (data) with declared **buy (currency-out) / sell (currency-in)** workflows, each a G-7 transaction leg. A recurring *composition* of G-7+G-8 worth declaring (cf. G-3). | economy shop, mining market, fishing rod/bait shops, farm shop — **4 subsystems** | 3→2 on buy/sell |
| **G-12** | `CraftingRecipeSpec` | A **recipe (inputs→outputs, gated by a required structure/tier)** as data; the consume-inputs/grant-outputs transform is a G-8 atomic multi-item op. | mining (build/forge/quickcraft/cook), fishing (craft bait/rod/charm/pearl/curio) — **2 subsystems, 15+ recipes** | 3→2 on craft |
| **G-13** | `IdleAccrualSpec` | **Time-based accrual computed on read** with a cap + spend gate (farm egg lay, fishing energy regen). Genuinely un-expressible today — §2 has no time-accrual primitive; the settle-on-read formula is pure data. | farm, fishing (+ mining passive) — **2–3 subsystems** | 3→1/2 on accrual reads |

**Scoped / lower-confidence:**

| Id | Family | Honest scope |
|---|---|---|
| **G-10** | `PersistentWorldSpec` (world-position store convention) | **Mostly folds into `StoreSpec` + tier-3 handlers.** Mining's grid = persisted `(pos_x, pos_y, depth)` + fog-of-war + a per-guild seed (`mining_grid.py`). The *stores* are tier-1 `StoreSpec`; the seed-deterministic world **content generator** and the **dig/descend/ascend move resolvers** are tier-3 game engines (legit escape hatch). The genuinely-new, narrow part is a **declared "shared-seed per-player world-position + fog store" convention** so the kernel owns save/load/fog windows. Recurs only in mining (fishing venue is a scalar, not a grid). **Recommend as a design-decision, not a firm new dataclass** — the persistent stores need no amendment; only the "world" grouping does. |

`G-7` is the **load-bearing** amendment: it is the single most-recurring tier-3 choreography in Lane B and
the one with a **safety** dimension. Today every money-moving service re-hand-writes the same
"conditional-debit + domain-leg in one `db.transaction()`, emit after commit" pattern (verified in
`economy_service.transfer`, `treasury_service.contribute/disburse`, `mining_workflow` ×27,
`farm_workflow`, `fishing_workflow`). It is currently *correct everywhere* — but correct because each
author re-derived it. Making it a kernel-owned declared transaction means a **new** subsystem can't get
double-spend / partial-settle wrong. That is the strongest single argument for the whole grammar bet in
this lane.

---

## 4. Refuted / folded amendments (the adversarial pass — do NOT add)

The first-pass fan-out proposed these; the 7-agent refute pass (each prompted to *refute*, defaulting
skeptical) knocked every one down. **Recorded so the capstone does not re-propose them.**

| Proposed | Verdict | Folds into (existing grammar) |
|---|---|---|
| **G-14 LootTableSpec** (weighted-RNG reward/drop/encounter table) | **WEAKER — downgrade** | The weighted pick is a **stdlib one-liner** (`random.choices`); each subsystem's balance function (daily streak `take_c/take_u` redistribution vs. mining depth `max(0.5,w−d)` curve vs. fishing inverse-size-pull exponent vs. creature two-stage catch) is a **distinct tier-3 domain engine** kept tier-3 by §10.1, exactly like the blackjack rules engine. Only the daily-reward case matches the proposed "rarity-tiers + value-ranges" shape. **Keep the four roll engines as registered tier-3 escape hatches; no new Spec.** |
| **G-15 MultiSeatTableSessionSpec** (live multi-seat game session) | **FOLD** | `ChallengeSessionSpec` already models a multi-player session — `blackjack.tournament` is declared with it and scored tier-2. Poker's session folds in identically. The lobby (join/leave/start/close), per-seat ephemeral broadcast, game moves (fold/check/call/raise) and seat/board renderers are the **tier-3 `renderer_override` + handlers** the spike already keeps for blackjack. The first pass's 68% casino lift was **unsupported** (no casino manifest exists in the spike to measure). At most add optional `max_seats` / `lobby_policy` fields to `ChallengeSessionSpec`. |
| **G-16 ReadModelProjectionSpec** (sort/filter/group on read-models) | **FOLD** | "Provider re-invoked with projection state" **is the existing `ProviderRef` contract** — the shipped BTD6 tower/hero browsers already do facet-filter + pagination as a tier-2 provider taking `(page, category)` args. Inventory's `_sort_items`/`_apply`/`_group_page_by_rarity` map onto a provider taking `(sort_mode, type_filter, page)`. Fold: (a) a minor **projection-args field on `ProviderRef`** (not a sibling family), (b) enum-rank ordering rides **G-8** catalog data, (c) facets ride `SelectorSpec(kind=enum)` + `BlockSpec.kind`. |
| **G-17 ParticipationPrefSpec** (per-user earn opt-out / visibility / prefs) | **WEAKER** | Three of four concerns are **user-scoped `SettingSpec`** (`scope_default='user'`): earn opt-out (bool gate + G-9), visibility toggles (bool + a `LeaderboardSpec` filter hook), preference (`allowed_values`). Only the narrow **notification-delivery intent** (digestable / default-suppressed) is genuinely unrepresentable — scope any amendment to *that*, not a broad participation family. **Does not change xp's fit** (already scored tier-1 as user settings). |
| **G-18 ManagedProjectionSpec** (mirror a metric onto a resource attribute) | **FOLD** | Counters' rename loop is structurally `ManagedTaskSpec(trigger="interval:600", handler="counters.sync", error_policy=…)` — **already in the spec**. The bound channel is `BindingSpec(kind=channel)`, the template is a `SettingSpec`; the compute/render/change-detect/rename **sync handler stays tier-3** (correctly). No new family. (A `per_target_backoff` value on the existing `ManagedTaskSpec.error_policy` string absorbs `GuildSyncBackoff` — a vocabulary extension, not a dataclass.) |
| **G-19 SettingsPresetSpec** (multi-setting preset bundle) | **FOLD** | A named cross-setting bundle is `SettingSpec.presets` (per-setting candidate values already exist) + a thin kernel `WorkflowRef("apply_preset_group")` over the settings-mutation workflow. The shipped apply is a **non-atomic** loop of `set_value` calls, so the "applied atomically" claim is false; the welcome/logging recurrence claim is unsupported. |
| **G-20 AutoResponderSpec / ContentPoolBlock** (keyword→reaction/response) | **FOLD** | Decomposes into `G-1` (the observe-only message-stage listener) + a `ProviderRef` (random content pool) + a **tier-3 `HandlerRef`** for the keyword-match/pick-response rule (one-off domain logic, legitimately tier-3). Recurrence fails: four_twenty is a single 12-unit hardcoded easter egg; there is no user-configurable autoresponder anywhere in the bot. |

**Net minor spec extensions** the folds imply (all additive to *existing* dataclasses, no new families):
`ProviderRef` optional projection-args (sort/filter/page) · `ChallengeSessionSpec` optional
`max_seats`/`lobby_policy` · `ManagedTaskSpec.error_policy += "per_target_backoff"`.

---

## 5. Structural danger-zone matrix

Which Lane B danger patterns are present, and whether the grammar (with the §3 amendments) expresses them
or they stay a deliberate tier-3 escape hatch. `✅ declared` = tier-1/2 with an amendment; `⛔ tier-3` =
legitimate escape hatch the grammar must not absorb; `— absent` = not present.

| Danger pattern | Present in | Grammar answer |
|---|---|---|
| **Transactional multi-write money mutation** | economy, treasury, mining, farm, fishing, inventory | ✅ **G-7 `EconomyTransactionSpec`** — the recurring `db.transaction()` + audit + emit-after-commit choreography becomes declared data. |
| **Escrow / settlement + double-settle / double-spend risk** | treasury (pool), economy (`transfer`), casino (side-pots, in-game) | ✅ **G-7** (`settle_once` + conditional-debit) for real coins. **Verified already well-guarded**: `try_debit_treasury` / `try_debit_coins` are single-statement conditional `UPDATE`s (no read-then-write race); underfunded rolls the whole txn back. Casino side-pots are in-memory play-chips → ⛔ stays inside the tier-3 engine. |
| **Deep persistent per-player world state** (mining grid, fog, depth, seed) | mining (grid); fishing (scalar venue only) | 🟡 **stores → `StoreSpec` (tier-1); world grouping → scoped G-10.** The move resolvers + seed-deterministic content generator are ⛔ tier-3 game engines. |
| **Inventory / item taxonomy** | inventory, mining, fishing, creature | ✅ **G-8 `ItemCatalogSpec`** — taxonomy as data + audited atomic unique-fenced grant/consume. |
| **XP / progression + leaderboard derivation** | xp, mining, fishing, creature, farm, economy | ✅ **G-9 `ProgressionSpec`** (curve/streak/cooldown gate) + `LeaderboardSpec` (already in spec) for the boards. The payouts stay ⛔ tier-3. |
| **Idle accrual (compute-on-read)** | farm (eggs), fishing (energy), mining (passive) | ✅ **G-13 `IdleAccrualSpec`** — the settle-on-read formula + cap as data (no `@tasks.loop` ticker; ADR-001/002-compatible). |
| **Weighted-RNG reward / encounter / drop roll** | economy (daily), mining (ore), fishing (catch), creature (encounter) | ⛔ **tier-3 by design** (§10.1). The pick is stdlib; the balance function is a domain engine. **NOT an amendment** (G-14 refuted). |
| **Stateful live game loop** | casino (multi-seat poker) | ⛔ **tier-3** — session lifecycle folds into `ChallengeSessionSpec`; lobby/broadcast/moves/renderers/engine stay tier-3. This is the 24%-fit floor. |
| **Creature PvP battle (turn state + level-normalized engine)** | creature | 🟡 session via `ChallengeSessionSpec` (coin-free); the battle turn-resolver + engine ⛔ tier-3. |
| **Scheduled loop + per-target backoff** | counters (channel rename) | ✅ **`ManagedTaskSpec`** (already in spec) declares the schedule; `error_policy += per_target_backoff` absorbs `GuildSyncBackoff`. The rename/compute handler stays ⛔ tier-3. |
| **Gateway / message-pipeline listener** | xp (`on_message` earn), four_twenty (stage), economy (`on_ready`/`on_guild_join`) | ✅ **G-1 `GatewayListenerSpec`** declares the listener + gate. xp's earn goes through `message_pipeline` (`XpStage`), not a raw gateway event — cite the pipeline-stage wiring, not G-1, for xp. The domain handler behind the gate stays thin-tier-2 or tier-3 per case. |
| **Command cooldown (anti-abuse rate limit)** | economy, four_twenty | ✅ **G-4 `CommandSpec.cooldown`** (already in the spike spec). Distinct from the *gameplay* cooldowns (daily 24 h / work 1 h), which are G-9. |
| **`wait_for` wizard** | — (verified absent) | Fishing's cast/reel is a **button-driven `View`**, not a `wait_for` loop; treasury/economy modals are single-field kernel modal-collects. No multi-step `wait_for` wizard in Lane B. |

---

## 6. Build order & cross-lane dependencies (capstone carry-forward)

The recommendations converge on a clean **dependency-layered build order** — Lane B is *not* a flat set;
it is a currency kernel with a fan-out of consumers. Build the kernel first; the games fall out.

- **L0 — operator/presentation (no economy dep):** `four_twenty` (pure easter egg), `counters`
  (**mis-binned into Lane B — its true kin is the Lane A operator band: logging/welcome**; no currency at
  all). Build with the config lanes, not the economy lanes.
- **L1 — currency & progression kernel:** `economy` (the coin store + `economy_audit_log` +
  **G-7** + `economy.balance_changed`) and `xp` (the **G-9** progression store). Everything money- or
  level-shaped depends on L1. **Build economy first.**
- **L2 — item store & shared pool:** `inventory` (**G-8** item catalog + store, grants pair atomically
  with L1 debits via G-7), `treasury` (one aggregate pool + two G-7 transactions — "falls out for free").
- **L3 — economy-sim games:** `farm` (**G-13** accrual + **G-11** shop on L1/L2), `fishing` (**G-11**/
  **G-12**/**G-13** + minigame engine), `creature` (coin-free — collection store + **G-9** + PvP
  `ChallengeSessionSpec`), `casino` (self-contained play-chip game; `ChallengeSessionSpec` + tier-3
  engine; **latent L1 dep only if real-coin buy-ins are ever added**).
- **L4/L5 — the deepest consumer:** `mining` exercises **every** proposed family (G-7/G-8/G-9/G-11/G-12/
  G-13 + scoped G-10) — it should be **ported last and used as the acceptance test for the whole Lane B
  primitive stack.** If the grammar can regenerate mining, it can regenerate the lane.

**Cross-lane dependencies (for the capstone):**
- **Lane C (games)** shares the `game_xp` service + `LeaderboardSpec` vocabulary (mining/fishing/creature
  boards ↔ leaderboard hub) and the `ChallengeSessionSpec` escrow seam (blackjack/rps ↔ economy INV-F).
  **G-7 must be an economy/currency-kernel primitive Lane C composes, not a Lane-B-local one.**
- **Lane A (governance/operator)** owns the real home of **counters** (operator band) and the
  role-automation lane XP level-up feeds (xp threshold-role grants). xp *triggers*, role owns.
- **Lane D (platform)** owns `settings`/`logging` (counters' preset apply routes through the audited
  `SettingsMutationPipeline`; economy/xp emit into the server-logging fanout) and the `message_pipeline`
  substrate (xp `XpStage`, four_twenty `FourTwentyStage`).
- **Lane F (ecosystem benchmark)** is `pending` for every subsystem's outperform bar — the per-subsystem
  recommendations (§7) name candidate incumbents (UnbelievaBoat/Dank Memer for economy/inventory,
  MEE6/Arcane/Amari for xp, Virtual Fisher for fishing, Poketwo/MewBot for creature, IdleRPG/OwO for
  farm/mining) and the concrete edge (audited atomic money, shared seed-deterministic world, cross-minigame
  inventory), but the head-to-head is Lane F's to confirm.

**Owner-gated / status:** every subsystem's runtime is production-clean *as shipped* (this audit found no
runtime blocker). The `owner-gated` status on economy/inventory/mining/fishing/farm/xp is **the amendment
approval itself** (the six new families are additive tier-2 declarations the owner must accept into the
§2 spec) plus a few **product** decisions the certs already surface: inventory item-grant audit
granularity + item actions (must not flood on every ore/fish), mining deep-sim scope, and fishing's Q-0175
"do fish pay coins?" open question (gates the fishing sell/market leg). None block the *audit*; all feed
the build plan.

---

## 7. Per-subsystem detail (verified ledgers, manifest sketches, dispositions)

Each section below is the source-verified surface-unit ledger (both tier columns), a §2 manifest sketch,
the tier-3 → amendment/escape-hatch dispositions, fit numbers, structural flags, the MAP→RECONSIDER→
SIMULATE→OPTIMIZE recommendation with capstone fields, cross-lane deps, and `⚠ unverified` judgment calls.
Casino/counters/four_twenty ledgers carry `[ADVERSARIAL: …]` notes where the refute pass revised a tier.

> **Numbering caveat.** The per-subsystem ledgers were authored by independent agents that used **local
> numbering** for *proposed* new families (any `G-14`+ id in a ledger is one agent's local proposal — the
> same "G-14" means LootTable in economy's section but MultiSeatSession in casino's). **§3 and §4 are the
> canonical, adversarially-reconciled catalog** — G-7…G-13 are the confirmed/scoped families; every
> `G-14`+ proposal was **refuted or folded** (§4). Read any in-ledger `G-14`+ reference as "a proposed
> family — see §4 for its canonical id and verdict." The confirmed **G-7…G-13** ids are consistent
> everywhere (they were pre-seeded to the fan-out). Tier *numbers* in every ledger are canonical and
> adversarially-corrected; only the *proposed-family labels* above G-13 carry the local-numbering caveat.

---
### economy
_cogs/source: disbot/cogs/economy_cog.py · services/economy_service.py · utils/db/economy.py · views/economy/*_

| Unit | Kind | File:line | Tier (as-written) | Tier (with amendments) | Rationale / gap |
|---|---|---|---|---|---|
| !economymenu | command | disbot/cogs/economy_cog.py:65-70 | 1 | 1 | Command -> panel_manager.get_or_render_panel(EconomyPanelView): pure kernel open-panel workflow, PanelRef route. |
| /economy (slash) | command | disbot/cogs/economy_cog.py:81-96 | 1 | 1 | Slash front door reuses build_help_menu_view -> same hub panel, ephemeral defer+followup. Kernel open-panel workflow. |
| !daily | command | disbot/cogs/economy_cog.py:216-278 | 3 | 3 | Domain handler: 24h cooldown gate + streak increment/reset + weighted-RNG loot pick (_pick_daily) + audited credit + set_daily_claim + log embed. Cooldown/streak declarable (G-9); loot RNG payout stays code. |
| !work | command | disbot/cogs/economy_cog.py:282-321 | 3 | 2 | Opens _WorkView job selector but gated by 1h cooldown + _available_jobs eligibility. As-written the gate is code; G-9 declares cooldown gate + eligibility provider -> selector-open. |
| !shop | command | disbot/cogs/economy_cog.py:325-330 | 1 | 1 | Opens _ShopView with static _shop_embed catalog: kernel open-panel workflow. |
| !balance (bal, wallet) | command | disbot/cogs/economy_cog.py:334-347 | 2 | 2 | Read-model command: get_coins + get_xp -> wallet embed. Routed to a read provider (FieldsBlock). |
| !setlogchannel (admin) | command | disbot/cogs/economy_cog.py:351-360 | 1 | 1 | admin_or_owner-gated binding-set through BindingMutationPipeline.set_binding(economy.log_channel): kernel binding-set workflow. |
| !joblist (jobs) | command | disbot/cogs/economy_cog.py:364-406 | 2 | 2 | Read-model over JOBS catalog + per-job mastery/lock state: TableBlock over a provider. |
| @commands.cooldown economymenu 3/10/user | cooldown | disbot/cogs/economy_cog.py:64 | 3 | 2 | Anti-abuse rate limit; no CommandSpec field as-written -> G-4 CommandSpec.cooldown makes it a declared tuple. |
| @commands.cooldown daily 2/5/user | cooldown | disbot/cogs/economy_cog.py:216 | 3 | 2 | Same G-4 class (distinct from the 24h gameplay daily cooldown). |
| @commands.cooldown work 2/5/user | cooldown | disbot/cogs/economy_cog.py:282 | 3 | 2 | Same G-4 class (distinct from the 1h gameplay work cooldown). |
| EconomyPanelView (persistent hub) | panel | disbot/views/economy/main_panel.py:42-43 | 1 | 1 | @register PersistentView, stateless, SUBSYSTEM='economy'; a declared PanelSpec container. Buttons counted separately. |
| hub daily_btn (economy:daily) | panel-action | disbot/views/economy/main_panel.py:52-117 | 3 | 3 | Duplicate of !daily: credit + streak + loot RNG mutation. G-9 for gate; loot RNG payout stays code. |
| hub work_btn (economy:work) | panel-action | disbot/views/economy/main_panel.py:119-171 | 3 | 2 | Cooldown+eligibility-gated navigation to _WorkSubView. G-9 declares the gate -> panel-open navigation. |
| hub shop_btn (economy:shop) | panel-action | disbot/views/economy/main_panel.py:173-188 | 1 | 1 | Navigation to _ShopSubView (edit_message): kernel nav workflow. |
| hub balance_btn (economy:balance) | panel-action | disbot/views/economy/main_panel.py:190-210 | 2 | 2 | Read-model re-render (coins+level): provider-backed panel action. |
| hub inventory_btn (economy:inventory) | panel-action | disbot/views/economy/main_panel.py:212-240 | 1 | 1 | Cross-subsystem navigation to UnifiedInventoryView with back-chain: kernel nav workflow. |
| hub jobs_btn (economy:jobs) | panel-action | disbot/views/economy/main_panel.py:242-290 | 2 | 2 | Read-model over JOBS+mastery: provider-backed panel action (duplicate of !joblist). |
| hub treasury_btn (economy:treasury) | panel-action | disbot/views/economy/main_panel.py:292-318 | 1 | 1 | Cross-subsystem navigation to treasury panel with back-chain: kernel nav workflow. |
| hub overview_btn (economy:overview) | panel-action | disbot/views/economy/main_panel.py:320-332 | 1 | 1 | Re-render of hub overview embed: kernel re-render workflow. |
| _WorkView/_WorkSubView (Job Center selector) | panel | disbot/views/economy/work_panel.py:38,174 | 2 | 2 | BaseView hosting a job-select over the eligibility provider + Back nav: read-model selector panel. |
| _JobSelect callback (work earn transaction) | panel-action | disbot/views/economy/work_panel.py:82-171 | 3 | 3 | THE work economics: cooldown re-check + increment_job mastery + _job_pay curve + audited credit + xp_service.award (cross-subsystem) + set_last_worked + log. Multi-domain earn -> legitimate escape hatch (partial G-7/G-9). |
| _WorkResultView | panel | disbot/views/economy/work_panel.py:207-239 | 1 | 1 | Result screen: renders handler result + single back button. Kernel-generated result render. |
| _ShopView (standalone shop panel) | panel | disbot/views/economy/shop_panel.py:28-43 | 2 | 2 | BaseView catalog + item select over SHOP_ITEMS: read-model selector panel. |
| _ShopSubView (in-panel shop + Back) | panel | disbot/views/economy/shop_panel.py:125-165 | 2 | 2 | Same catalog select embedded in hub flow with back-chain: read-model selector panel. |
| _ShopSelect callback (buy) | panel-action | disbot/views/economy/shop_panel.py:46-122 | 3 | 2 | Atomic buy via shop_purchase_workflow.purchase_unique_item (grant+debit+audit+event in one txn). G-11 ShopSpec declares priced-catalog buy workflow -> data. |
| _ShopPanelSelect callback (buy, panel variant) | panel-action | disbot/views/economy/shop_panel.py:168-243 | 3 | 2 | Duplicate buy seam (in-panel edit variant). Same G-11 ShopSpec. |
| economy.log_channel binding | binding | disbot/cogs/economy/schemas.py:30-41 | 1 | 1 | BindingSpec(kind=CHANNEL, capability economy.settings.configure): pure declaration. |
| log_channel ResourceRequirement | resource | disbot/cogs/economy/schemas.py:54-69 | 1 | 1 | ResourceRequirement(CHANNEL, suggested economy-log, binding_name=log_channel): pure declaration. |
| capabilities x5 (currency.view/earn, shop.browse/buy, settings.configure) | capability×5 | disbot/utils/subsystem_registry.py:166-172 | 1 | 1 | Capability-string declarations on the registry entry: pure manifest metadata. |
| on_ready (ensure economy-log channel) | listener | disbot/cogs/economy_cog.py:100-104 | 3 | 2 | Gateway listener auto-provisioning the log channel per guild. No primitive as-written; G-1 GatewayListenerSpec + the declared offer_on_enable ResourceRequirement lifecycle owns provisioning -> thin. |
| on_guild_join (ensure economy-log channel) | listener | disbot/cogs/economy_cog.py:106-109 | 3 | 2 | Same auto-provision path on guild join. G-1 + kernel resource-provisioning lane. |
| EVT_BALANCE_CHANGED EventSpec (economy.balance_changed) | event | disbot/services/economy_service.py:57 (emit x5: 81,118,270,278,319) | 1 | 1 | One EventSpec declaration; emits live inside the audited seams. The domain's canonical currency event (reused by treasury/mining/farm/fishing). |
| credit/debit audited single-write seam | mutation | disbot/services/economy_service.py:64-126 | 3 | 2 | add_coins + _audit + emit as a hand-written seam with InsufficientFundsError. G-7 EconomyTransactionSpec declares debit/credit/audit/event as one atomic mutation. |
| transfer atomic two-party seam (#1541 give/pay) | mutation | disbot/services/economy_service.py:196-286 | 3 | 2 | debit+credit+2 audit rows in one asyncpg txn, 2 events after commit. THE transactional multi-write danger unit. G-7 EconomyTransactionSpec (multi-leg, settle-once, refund). Currently no !give/!pay command wires to it (ready seam). |
| bet_and_settle settlement seam | mutation | disbot/services/economy_service.py:289-327 | 3 | 2 | Affordability check + apply outcome_delta + audit + event; consumed by blackjack/rps. G-7 settle leg (outcome_delta computed by the calling game engine). |
| refund seam | mutation | disbot/services/economy_service.py:330-354 | 3 | 2 | Distinct credit alias for recoverable filtering; consumed by blackjack/rps/game GC. G-7 refund_policy on the transaction spec. |
| debit_in_txn / credit_in_txn workflow legs | mutation | disbot/services/economy_service.py:129-193 | 3 | 2 | Caller-owned-txn variants (emit-none) that let a domain workflow commit a coin leg atomically with its own leg (shop/mining/farm). G-7 composable-leg semantics. |
| economy table store (last_daily/daily_streak/daily_count/last_worked) | store | disbot/utils/db/economy.py:224-300 | 1 | 1 | StoreSpec (aggregate) -> generated sole-writer fence; ensure_and_get + atomic claim/work update helpers. |
| xp.coins balance store (coin ledger column) | store | disbot/utils/db/economy.py:25-216 | 1 | 1 | StoreSpec: coin balance lives in xp.coins, economy_service is sole audited writer. Shared table with xp subsystem (cross-lane). |
| job_progress store (times_worked per job) | store | disbot/utils/db/economy.py:308-331 | 1 | 1 | StoreSpec (aggregate); atomic increment_job upsert. Backs the mastery pay curve. |
| economy_audit_log store (immutable ledger) | store | disbot/utils/db/economy.py:88-105 | 1 | 1 | StoreSpec (ledger-class) -> generated append-only fence; insert_economy_audit is the sole writer. |
| economy_flow_by_reason read provider (faucet/sink) | provider | disbot/utils/db/economy.py:108-147 | 2 | 2 | Pure aggregation over economy_audit_log by reason; consumed by economy_flow_service. Read-model provider (ProviderRef). |
| economy_flow_daily read provider (mint/drain time series) | provider | disbot/utils/db/economy.py:150-197 | 2 | 2 | Pure per-UTC-day aggregation; consumed by economy_flow_service. Read-model provider. |
| JOBS catalog (12 jobs: tier/pay/xp/level/items/mastery) | data | disbot/services/economy_helpers.py:34-147,189-204 | 3 | 2 | Hardcoded progression catalog: level+item-gated tiers with +1%/work mastery pay curve. As data it is G-9 ProgressionSpec (level-gated earn + mastery) + a declared job catalog; item-requirements cross-link inventory (G-8). |
| SHOP_ITEMS catalog (car/toolkit/suit, priced unique) | data | disbot/services/economy_helpers.py:150-162 | 3 | 2 | Hardcoded priced catalog of unique inventory items (own-at-most-one, job-unlock links). G-11 ShopSpec (priced catalog) + G-8 InventoryItemSpec (unique item taxonomy). |
| daily reward loot table (_DAILY_TIERS + _daily_weights streak shift) | data | disbot/services/economy_helpers.py:24-31,165-186 | 3 | 3 | 6-rarity weighted-random reward table with a streak-luck weight-shift formula (capped 60d). No G-1..G-13 primitive fits a weighted-RNG reward -> proposes G-14 LootTableSpec; residual RNG payout is a legitimate escape hatch. |
| _available_jobs eligibility provider | provider | disbot/services/economy_helpers.py:195-204 | 2 | 2 | Read-model: level+inventory -> eligible job list. Feeds the work selector options_source (ProviderRef). |
| _build_economy_embed hub overview provider | provider | disbot/services/economy_helpers.py:223-260 | 2 | 2 | Read-model: coins+level+streak+daily/work cooldown status -> the hub panel body (FieldsBlock over a provider). |
| help entry (economy hub via build_help_menu_view) | help | disbot/cogs/economy_cog.py:72-79 | 1 | 1 | HelpEntrySpec / help-menu direct-navigation hook returning the hub panel: help-as-projection. |

**Fit:** 54 units · tier-1/2 as-written **63%** (34/54) · with amendments **93%** (50/54).

**§2 manifest sketch**

```python
ECONOMY = SubsystemManifest(
    key="economy", display_name="Economy", emoji="💰", category="economy",
    visibility_tier="user",
    capabilities=("economy.currency.view","economy.currency.earn",
                  "economy.shop.browse","economy.shop.buy","economy.settings.configure"),
    commands=(
        CommandSpec("economymenu", BOTH, "Open the Economy hub",
                    route=PanelRef("economy.hub"), cooldown=(3,10,"user")),   # G-4, G-6
        CommandSpec("daily", PREFIX, "Claim daily reward",
                    route=HandlerRef("economy.daily_claim","streak-loot earn"),
                    cooldown=(2,5,"user")),                                    # tier3 residual
        CommandSpec("work", PREFIX, "Open Job Center",
                    route=PanelRef("economy.job_center"), cooldown=(2,5,"user")),  # G-9 gate
        CommandSpec("shop", PREFIX, "Browse the shop", route=PanelRef("economy.shop")),
        CommandSpec("balance", PREFIX, "Show wallet",
                    route=ProviderRef("economy.wallet"), aliases=("bal","wallet")),
        CommandSpec("joblist", PREFIX, "List jobs",
                    route=ProviderRef("economy.job_list"), aliases=("jobs",)),
        CommandSpec("setlogchannel", PREFIX, "Set economy log channel",
                    route=WorkflowRef("binding_set",(("binding","log_channel"),)),
                    capability_required="economy.settings.configure"),
    ),
    panels=(
        PanelSpec("economy.hub","economy","Economy Panel", audience="persistent", timeout_s=None,
            body=(BlockSpec("fields", ProviderRef("economy.overview")),),
            actions=(
              PanelActionSpec("economy:daily","🎁 Daily",
                  HandlerRef("economy.daily_claim"), audit="economy:daily"),      # tier3
              PanelActionSpec("economy:work","💼 Work", PanelRef("economy.job_center")),  # G-9
              PanelActionSpec("economy:shop","🛒 Shop", PanelRef("economy.shop")),
              PanelActionSpec("economy:balance","💰 Balance", ProviderRef("economy.wallet")),
              PanelActionSpec("economy:inventory","🎒 Inventory", PanelRef("inventory.hub")),
              PanelActionSpec("economy:jobs","📋 Jobs", ProviderRef("economy.job_list")),
              PanelActionSpec("economy:treasury","🏛️ Treasury", PanelRef("treasury.hub")),
              PanelActionSpec("economy:overview","↩ Overview", WorkflowRef("rerender")),
            )),
        PanelSpec("economy.job_center","economy","Job Center",
            selectors=(SelectorSpec("job_pick","enum",
                HandlerRef("economy.work_earn","credit+xp+mastery"),
                options_source=ProviderRef("economy.available_jobs")),)),          # tier3 select
        PanelSpec("economy.shop","economy","Item Shop",
            selectors=(SelectorSpec("shop_pick","entity",
                HandlerRef("economy.shop_buy"),                                      # G-11
                options_source=ProviderRef("economy.shop_catalog")),)),
    ),
    settings=(),                        # FINDING: ECONOMY_SETTINGS is empty; all tunables
                                        # (cooldowns, reward tiers, job pay) are hardcoded constants.
    bindings=(BindingSpec("log_channel","channel", capability_required="economy.settings.configure"),),
    resources=(ResourceRequirement("channel","log_channel","recommended",
        binding_name="log_channel", offer_on_enable=True),),
    events=(EventSpec("economy.balance_changed",
        (FieldSpec("guild_id","int"),FieldSpec("user_id","int"),
         FieldSpec("delta","int"),FieldSpec("new_balance","int"),FieldSpec("reason","str")),
        owner_subsystem="economy", observability_only=True),),
    gateway_listeners=(                                                              # G-1
        GatewayListenerSpec("on_ready", HandlerRef("economy.ensure_log_channel"),
            gate="resource:log_channel:offer_on_enable"),
        GatewayListenerSpec("on_guild_join", HandlerRef("economy.ensure_log_channel")),
    ),
    stores=(
        StoreSpec("economy","economy.daily_work_writer","aggregate"),
        StoreSpec("xp","economy.coin_writer","ledger", invariant_tag="coins>=0",
                  reader_domains=("xp","leaderboard","treasury","mining","farm")),
        StoreSpec("job_progress","economy.job_writer","aggregate"),
        StoreSpec("economy_audit_log","economy.audit_writer","ledger"),
    ),
    # PROPOSED families the real manifest would need:
    #   transactions=(EconomyTransactionSpec("transfer", legs=("debit","credit"),   # G-7
    #                   settle_once=True, refund_policy=HandlerRef("economy.refund")),
    #                 EconomyTransactionSpec("credit"/"debit"/"bet_and_settle")),
    #   shop=ShopSpec(catalog=ProviderRef("economy.shop_catalog"),                   # G-11
    #                 buy=EconomyTransactionSpec("shop_buy", legs=("grant","debit"))),
    #   progression=ProgressionSpec(daily=CooldownStreak(86400), work=Cooldown(3600), # G-9
    #                 jobs=JobCatalog(level_gated, item_gated, mastery_curve="+1%/work,max+100%")),
    #   loot=LootTableSpec("daily", tiers=_DAILY_TIERS, luck_by="daily_streak"),      # G-14 (new)
    help=HelpEntrySpec("Daily coins, work, shop, balance."),
)
```

**Tier-3 dispositions**

| Tier-3 unit | Verdict | Reason |
|---|---|---|
| !daily / hub daily_btn (streak-loot earn) | grammar-gap:G-9 + escape-hatch(loot) | Cooldown+streak cadence and the audited credit are declarable via G-9 ProgressionSpec + G-7; the weighted-RNG rarity/amount pick (_pick_daily over _daily_weights) is genuine reward math that should stay a thin handler or route to a new G-14 LootTableSpec. |
| _JobSelect work earn transaction | escape-hatch (legitimate) + grammar-gap:G-9 | Kernel should not own the cross-subsystem earn orchestration (increment_job mastery -> _job_pay curve -> audited credit -> xp_service.award -> set_last_worked). G-9 declares the cooldown/level gate + mastery curve, but the multi-domain payout wiring is legitimately code. |
| _ShopSelect / _ShopPanelSelect buy | grammar-gap:G-11 (+G-7) | Atomic grant+debit+audit+event is exactly the priced-catalog buy pattern; G-11 ShopSpec over G-7 EconomyTransactionSpec makes it declared data. Two near-identical select callbacks collapse to one declared workflow. |
| credit / debit audited seam | grammar-gap:G-7 | Single balance write + immutable audit row + EVT_BALANCE_CHANGED is the atomic-mutation primitive G-7 EconomyTransactionSpec is designed to declare. |
| transfer atomic two-party seam (#1541) | grammar-gap:G-7 | debit+credit+2 audit rows in one transaction + post-commit events is the multi-leg transactional-mutation shape; G-7 (multi-leg, settle-once, refund_policy) expresses it as data, not bespoke SQL. |
| bet_and_settle settlement seam | grammar-gap:G-7 | Affordability gate + apply-delta + audit + event is a G-7 settle leg; the outcome_delta is supplied by the calling game engine (correctly external). |
| refund seam | grammar-gap:G-7 | Thin credit alias kept distinct only for audit-reason filtering; folds into G-7 refund_policy on the transaction spec. |
| debit_in_txn / credit_in_txn workflow legs | grammar-gap:G-7 | Caller-owned-transaction, emit-none variants that let a domain workflow commit a coin leg atomically with its own leg; this composability IS the G-7 leg abstraction. |
| on_ready / on_guild_join ensure-log-channel | grammar-gap:G-1 | Auto-provision-a-channel on gateway events has no primitive as-written; G-1 GatewayListenerSpec + the already-declared offer_on_enable ResourceRequirement lets the kernel provisioning lane own it, leaving a thin handler. |
| JOBS catalog (progression) | grammar-gap:G-9 (+G-8) | Level+item-gated job tiers with a +1%/work mastery curve are progression data; G-9 ProgressionSpec + a declared job catalog, with item-requirements cross-linking G-8 inventory taxonomy. |
| SHOP_ITEMS catalog | grammar-gap:G-11 (+G-8) | Priced unique-item catalog with job-unlock links; G-11 ShopSpec (pricing/buy) over G-8 InventoryItemSpec (unique/own-at-most-one taxonomy). |
| daily reward loot table (_DAILY_TIERS + streak weighting) | needs-new-primitive:G-14 LootTableSpec / escape-hatch | A weighted-random reward table with a streak-luck weight-shift formula fits none of G-1..G-13; propose G-14 LootTableSpec (tiers + luck source). Residual streak-shift math is a legitimate thin escape hatch. |
| @commands.cooldown x3 (anti-abuse) | grammar-gap:G-4 | Command-layer rate limits with no §2.2 field; G-4 CommandSpec.cooldown declares them as a (rate,per,bucket) tuple. |

**Structural-gap flags**

- **transactional multi-write mutation (transfer: debit+credit+2 audit rows in one txn)** — `with-amendment:G-7` — economy_service.py:196-286. The subsystem's defining danger unit; G-7 EconomyTransactionSpec declares multi-leg atomic money moves as data.
- **atomic cross-domain mutation (shop buy: grant item + debit coins in one txn)** — `with-amendment:G-7+G-11` — shop_purchase_workflow.py + economy_service.debit_in_txn. Grant-first-then-debit-rolls-back is a G-11 ShopSpec buy over a G-7 leg; the cosmetic view pre-checks are already race-safe (workflow re-decides in-txn).
- **settlement + double-settle risk (bet_and_settle / refund)** — `with-amendment:G-7` — economy_service.py:289-354. economy provides the settle+refund primitives; escrow/settle-once lives in the game (blackjack ChallengeSessionSpec). G-7 settle_once + refund_policy.
- **irreversible economy op (transfer / purchase mint+burn)** — `with-amendment:G-7` — Every seam writes economy_audit_log (immutable ledger StoreSpec) with actor+reason; G-7 makes audit+event mandatory-by-declaration rather than by convention.
- **XP + leaderboard derivation from currency** — `yes` — work awards xp (xp_service.award, cross-subsystem) and coins feed leaderboard.economy.view. Read side is LeaderboardSpec/provider (tier-2); the earn wiring is the tier-3 work handler.
- **cooldown + streak progression (daily 24h+streak, work 1h, job level/mastery gating)** — `with-amendment:G-9` — All gameplay cadence is hardcoded constants in economy_helpers.py (not settings). G-9 ProgressionSpec declares cooldown-gated earn + streak + mastery curve as data.
- **weighted-random loot table (daily rarity tiers + streak luck shift)** — `needs-new-primitive` — helpers.py:24-31,165-186. No G-1..G-13 fits; propose G-14 LootTableSpec. Residual RNG payout math is a legitimate escape hatch.
- **inventory / item taxonomy (unique shop items + job item-requirements)** — `with-amendment:G-8` — car/toolkit/suit are own-at-most-one items gating jobs; cross-lane dep on the inventory subsystem's item store (G-8 InventoryItemSpec).
- **gateway-listener auto-provisioning (on_ready/on_guild_join -> create #economy-log)** — `with-amendment:G-1` — economy_cog.py:100-212. G-1 + the declared offer_on_enable ResourceRequirement moves provisioning to the kernel lane.
- **deep persistent per-player world state** — `yes` — NOT present — economy state is shallow (coins, streak, last_daily/last_worked, job times); plain aggregate/ledger StoreSpecs. No grid/battle/farm world (contrast mining/creature/farm lanes).
- **stateful game loop / wait_for wizard** — `yes` — NOT present — persistent hub + selects + panel_manager, no wait_for and no in-memory game loop.

**MAP → RECONSIDER → SIMULATE → OPTIMIZE**

- **Verdict:** keep · **status:** owner-gated
- **Optimal new-bot form:** A generated currency-kernel SubsystemManifest: G-7 EconomyTransactionSpec declares every audited money move (credit/debit/transfer/settle/refund) as atomic data with mandatory audit+event; G-9 ProgressionSpec owns daily/work cooldown+streak and the job level/mastery progression; G-11 ShopSpec declares the priced catalog + atomic buy; G-14 LootTableSpec declares the daily reward table. The hub panel, wallet/joblist read providers, bindings, resource and event are pure declarations. Only the streak-loot RNG payout and the cross-subsystem work-earn orchestration remain thin handlers.
- **Dependency layer:** L1 currency kernel — the foundational money layer everything else builds on (inventory L2 links item taxonomy; blackjack/rps/mining/farm/fishing/treasury are L3 consumers of the L1 seams). Build economy first.
- **Production-grade done:** Parity golden: (1) credit/debit/transfer/bet_and_settle/refund each write balance + economy_audit_log + emit EVT_BALANCE_CHANGED atomically (transfer never leaves a one-sided move); (2) daily 24h cooldown + streak reset/increment and work 1h cooldown reproduce current payouts and mastery curve; (3) shop buy is atomic with zero double-charge under raced clicks (existing AST invariant test_no_view_level_purchase_writes stays green); (4) wallet/joblist/flow read models match; (5) the currently-unwired transfer() gains its !give/!pay command (#1541) on the same G-7 seam.
- **Outperform target:** Beat UnbelievaBoat / Dank Memer on auditability + atomicity (every move ledgered, no double-charge) and on declarative extensibility (new jobs/shop items/loot tables are data edits) — full competitive framing pending Lane F.

**Cross-lane dependencies**

- inventory (Lane B): shop items car/toolkit/suit and job item-requirements are unique inventory-store items — G-8 InventoryItemSpec; shop buy grants via db.try_grant_unique_item
- xp (Lane B): coin balance physically lives in the xp.coins column (shared store); work awards xp via xp_service.award — economy is coin sole-writer, xp owns level
- treasury (Lane B): reuses economy's EVT_BALANCE_CHANGED event name and moves coins via the same seams (contribute=sink, disburse=faucet)
- leaderboard: leaderboard.economy.view derives from xp.coins (LeaderboardSpec over economy's balance store)
- blackjack / rps_tournament (Lane C games): consume economy_service.bet_and_settle + refund for wager escrow/settlement
- mining / farm / fishing (Lane B): consume economy_service credit/debit and the *_in_txn legs for market/repair/collect/purchase coin flows
- economy_flow_service / insights: consumes economy_flow_by_reason + economy_flow_daily read providers (analytics surface, likely a separate insights lane)

**⚠ Unverified / judgment calls**

- !give/!pay command (#1541): economy_service.transfer() is a fully-audited two-party seam but grep found NO command or other caller wiring to it (only refund/bet_and_settle are consumed). The transfer seam is ready-but-unwired; the give/pay user command is not yet shipped. Counted transfer as a contract-bearing unit regardless.
- capabilities counted as ×5 (one per capability string) rather than 1 registry-entry unit — a judgment call; if counted as 1 the units_total drops to 50 and fit% shifts by ~1pt.
- economy_flow_by_reason/daily providers are confirmed consumed by economy_flow_service.py but the user/admin-facing panel that renders them was not traced — classified tier-2 read providers by shape.
- JOBS mastery pay curve and daily loot weighting classified from source math; whether a rebuild would declare jobs via ProgressionSpec vs a dedicated JobCatalog primitive is a design call (folded into G-9 here).
- _WorkResultView classified tier-1 (result render) though it is a discord.ui BaseView subclass; if counted as a stateful view container it could read tier-2, low impact.

---

### inventory
_cogs/source: disbot/cogs/inventory_cog.py · utils/db/inventory.py · services/shop_purchase_workflow.py_

| Unit | Kind | File:line | Tier (as-written) | Tier (with amendments) | Rationale / gap |
|---|---|---|---|---|---|
| !inventory / !inv command (opens hub) | command | disbot/cogs/inventory_cog.py:562 | 2 | 2 | Command → read-model panel (the hub body IS item data, matching karma-card tier-2, not logging config-panel tier-1). Route=PanelRef; optional target member is a param. No cooldown decorator (read). |
| UnifiedInventoryView hub panel (per-category summary + nav buttons) | panel | disbot/cogs/inventory_cog.py:465 | 2 | 2 | Read-model panel: list/preview over _build_combined_inventory provider; category buttons are generated from non-empty groups. Fields-over-provider = tier 2. |
| _CategoryView detail panel (item list, read-model core + pagination) | panel | disbot/cogs/inventory_cog.py:271 | 2 | 2 | Read-model TableBlock/list over provider; core render + 8/page pagination are kernel affordances. The sort/filter/group facets on top are split out as separate units below. |
| Category nav buttons (hub → category detail) | panel-action | disbot/cogs/inventory_cog.py:496 | 1 | 1 | Pure open-panel navigation workflow (one dynamic button per non-empty category). |
| Pagination prev/next on category view | panel-action | disbot/cogs/inventory_cog.py:341 | 1 | 1 | Kernel table-pagination workflow; boundary-disabled nav is generated. |
| Sort cycle action (rarity/quantity/name; rarity uses domain _RARITY_ORDER rank) | panel-action | disbot/cogs/inventory_cog.py:426 | 3 | 2 | As-written: registered handler re-sorts+re-renders (_sort_items pure fn + rarity-rank map); §2 read-model has NO declarative sort facet → tier 3. With G-14 sortable-read-model (declared sort keys incl. enum rank as data) → tier 2. |
| Type filter select (filter by item type, shown when >1 type) | selector | disbot/cogs/inventory_cog.py:435 | 3 | 2 | As-written: bespoke filter handler (_apply recomputes slice+pages); §2 has no declarative filter facet on a read model → tier 3. With G-14 filter-facet declaration → tier 2. |
| Per-rarity-tier grouped rendering (dedicated embed field per rarity tier) | renderer | disbot/cogs/inventory_cog.py:182 | 3 | 2 | As-written: §2.3 BlockSpec kinds are text/fields/table/list — no group-by-key block → needs renderer_override (tier 3). _group_page_by_rarity is thin display, NOT game rules, so it should be kernel-owned. With G-14 group-by key on a read-model block → tier 2 data. |
| build_help_menu_view help-menu hook (returns hub) | help | disbot/cogs/inventory_cog.py:574 | 1 | 1 | Help-as-projection + panel-open navigation hook; pure declaration. |
| Economy-hub 🎒 Inventory button (economy:inventory entry) | panel-action | disbot/views/economy/main_panel.py:256 | 2 | 2 | Cross-subsystem entry: reads get_inventory and navigates into the inventory read model. Read-model navigation = tier 2. |
| capability inventory.item.view | setting | disbot/utils/subsystem_registry.py:193 | 1 | 1 | Capability declaration string in the manifest header; pure data. |
| capability inventory.item.use (aspirational/unenforced) | setting | disbot/utils/subsystem_registry.py:194 | 1 | 1 | Declared capability, tier-1 as a manifest string — but no feature enforces it (cert punch #3). Declaration is tier 1; the gap is a missing behavior, not a grammar gap. |
| capability inventory.craft.recipe (aspirational/unenforced) | setting | disbot/utils/subsystem_registry.py:195 | 1 | 1 | Same: declared-but-unenforced capability string; tier-1 declaration. |
| subsystem registry header (display_name/emoji/category/parent_hub=economy/entry_points/dependencies=[economy]) | setting | disbot/utils/subsystem_registry.py:174 | 1 | 1 | The SubsystemManifest root record itself — pure declaration. No settings_keys / SubsystemSchema exists (cert punch #6: no per-guild config). |
| inventory table (migration 234; (user,guild,item)→qty, guild-scoped economy items) | store | disbot/utils/db/migrations.py:234 | 1 | 1 | Shallow item ledger → StoreSpec generated sole-writer fence. NOTE: live sole writer is try_grant_unique_item only (add_item has no runtime caller). |
| get_inventory read provider | store | disbot/utils/db/inventory.py:13 | 1 | 1 | Plain SELECT → generated reader backing the panels; folds into StoreSpec/read-model provider. |
| add_item grant primitive (ON CONFLICT increment, UNAUDITED; no live caller) | mutation | disbot/utils/db/inventory.py:21 | 3 | 2 | Direct upsert write with NO emit_audit_action (cert weak spot). §2 has no inventory-item grant primitive → bespoke mutation seam (tier 3). With G-8 InventoryItemSpec declared grant op (kernel-owned atomic upsert + audit) → tier 2. Also currently defined-but-unused in runtime. |
| try_grant_unique_item (conditional own-at-most-one upsert; closes double-click double-charge race) | mutation | disbot/utils/db/inventory.py:39 | 3 | 2 | Bespoke race-safe conditional upsert (ownership decided atomically) — the LIVE grant path, still UNAUDITED for the item leg. §2 has no primitive → tier 3. With G-8 unique-item kind → kernel-owned once-grant fence owns the race → tier 2. |
| has_item ownership read | store | disbot/utils/db/inventory.py:69 | 1 | 1 | Generated has-op (quantity>0 check); G-8 declares a `has` op. Tier 1 read. |
| ITEM_CATALOGUE taxonomy (~20 items × category/type/rarity/emoji, hardcoded) | store | disbot/cogs/inventory_cog.py:17 | 3 | 2 | Hardcoded Python dict = the item taxonomy, consumed by the renderer; §2 has NO item-catalog primitive → lives as code-side data feeding bespoke render (tier 3). With G-8 ItemCatalogSpec → declared data (tier 2). Counted as 1 unit (one taxonomy structure), not ×20. |
| purchase_unique_item atomic grant+debit txn (inventory grant leg of the shop purchase) | mutation | disbot/services/shop_purchase_workflow.py:46 | 3 | 2 | One db.transaction() wrapping try_grant_unique_item + economy debit + post-commit EVT_BALANCE_CHANGED — transactional multi-write. §2 has no atomic money+item primitive → tier 3. With G-7 EconomyTransactionSpec (declared debit+grant+event) → tier 2. Cross-lane (economy/shop owns it; inventory owns the grant leg). |

**Fit:** 21 units · tier-1/2 as-written **67%** (14/21) · with amendments **100%** (21/21).

**§2 manifest sketch**

```python
from tools.grammar_spike.spec import *

INVENTORY = SubsystemManifest(
    key="inventory", display_name="Inventory", emoji="🎒",
    description="Unified cross-minigame item browser + grant/consume store",
    category="economy", parent_hub="economy",
    visibility_tier="user", dependencies=("economy",),
    capabilities=("inventory.item.view", "inventory.item.use", "inventory.craft.recipe"),

    commands=(
        # command → read-model panel (like karma card) = tier 2
        CommandSpec("inventory", CommandKind.PREFIX, "View your unified inventory",
                    route=PanelRef("inventory.hub"), aliases=("inv",),
                    audience_tier="user"),
    ),

    panels=(
        # tier-2 read-model hub: list/preview over a provider, nav to category
        PanelSpec("inventory.hub", "inventory", "🎒 Inventory",
                  body=(BlockSpec("list", provider=ProviderRef("inventory.grouped_summary")),),
                  # dynamic per-category nav = kernel navigation actions (tier 1)
                  navigation=NavigationSpec(show_home=True)),
        # tier-2 read-model detail — BUT sort/filter/group need G-14 (see below);
        # as-written today this panel carries a renderer_override (tier 3) for the
        # per-rarity-tier grouped fields + sort/filter handlers.
        PanelSpec("inventory.category", "inventory", "Category detail",
                  body=(BlockSpec("table", provider=ProviderRef("inventory.category_page")),),
                  # G-14 target — declarative projection instead of _CategoryView:
                  #   sort_keys=("rarity"(enum-rank), "quantity", "name"),
                  #   filters=("type",), group_by="rarity"
                  renderer_override=HandlerRef("inventory.category_render",
                      justification="G-14 gap: §2 read-model has no sort/filter/group facet")),
    ),

    # No settings_keys / SubsystemSchema exists today (cert punch #6). Capabilities
    # inventory.item.use / craft.recipe are declared but UNENFORCED (punch #3).

    stores=(
        StoreSpec(table="inventory", sole_writer="inventory.item_store",
                  checkpoint_class="aggregate", invariant_tag="qty>=0",
                  reader_domains=("economy", "mining", "inventory")),
    ),

    # ---- what the grammar CANNOT express today (the Lane-B deep-state gaps) ----
    # G-8 ItemCatalogSpec: the ~20-item ITEM_CATALOGUE taxonomy as declared data
    #     ItemCatalogSpec(items=(InventoryItemSpec("diamond", rarity="Epic",
    #         type="Gem", stackable=True), ..., InventoryItemSpec("car",
    #         unique=True, ...)))
    # G-8 grant/consume/has ops with kernel-owned atomic upsert + AUDIT (closes the
    #     unaudited-grant weak spot AND the unique-grant race in try_grant_unique_item)
    # G-7 EconomyTransactionSpec: purchase_unique_item = declared debit+grant+event txn
    # G-14 ReadModelProjectionSpec: sortable(enum-rank)/filterable/groupable read block
    events=(
        # MISSING today — no inventory.item.granted event, no audit.action_recorded.
        # Should exist under G-8 so the item trail matches the coin trail's intent.
    ),
    help=HelpEntrySpec(summary="View items earned via mining/shop/crafting"),
)
```

**Tier-3 dispositions**

| Tier-3 unit | Verdict | Reason |
|---|---|---|
| Sort cycle action (rarity/quantity/name) | grammar-gap:G-14 | Thin display re-sort (pure _sort_items + rarity-rank map), not game rules — kernel should own it via a declarative sortable read-model (sort keys incl. enum rank as data). |
| Type filter select (filter by item type) | grammar-gap:G-14 | Bespoke filter handler; a declared filter-facet on the read model makes it data. Kernel-ownable. |
| Per-rarity-tier grouped rendering | grammar-gap:G-14 | §2.3 BlockSpec has no group-by-key kind; grouping a list by a domain enum tier is a projection concern the kernel should own, not an escape hatch. |
| add_item grant primitive (unaudited upsert) | grammar-gap:G-8 | Item grant is a declared store op, not bespoke SQL; kernel should provide the atomic upsert AND the audit/event the current code omits. Also currently dead (no runtime caller). |
| try_grant_unique_item (unique-grant race-safe upsert) | grammar-gap:G-8 | A `unique` item kind + kernel-owned once-grant fence owns the double-click race and the audit — the exact escrow/settle-once analog for item ownership. Not a legit escape hatch. |
| ITEM_CATALOGUE taxonomy (~20 items) | grammar-gap:G-8 | Item taxonomy (kind/rarity/type/stackable/unique) is declarative data; no ItemCatalogSpec exists so it lives as a hardcoded dict feeding the renderer. |
| purchase_unique_item atomic grant+debit txn | grammar-gap:G-7 | Atomic debit+grant+post-commit event is the canonical EconomyTransactionSpec shape; today it is bespoke workflow code. Cross-lane (economy/shop owns it). |

**Structural-gap flags**

- **inventory / item taxonomy** — `with-amendment:G-8` — ITEM_CATALOGUE (~20 items × category/type/rarity/emoji, inventory_cog.py:17) is a hardcoded dict — the item taxonomy has NO §2 primitive. G-8 ItemCatalogSpec/InventoryItemSpec makes it declared data. This is the single biggest as-written gap and the convergence point across all Lane-B item subsystems.
- **transactional multi-write mutation** — `with-amendment:G-7` — purchase_unique_item (shop_purchase_workflow.py:46) wraps try_grant_unique_item + economy debit + post-commit EVT_BALANCE_CHANGED in one txn. Needs G-7 EconomyTransactionSpec to be data not bespoke code.
- **unique-grant / double-settle risk** — `with-amendment:G-8` — try_grant_unique_item (inventory.py:39) closes a double-click double-charge race via a conditional own-at-most-one upsert — the item-ownership analog of escrow/settle-once. A declared `unique` item kind + kernel-owned once-grant fence owns this.
- **irreversible / unaudited economy op** — `with-amendment:G-8` — CERT WEAK SPOT: both item-grant primitives emit NO audit.action_recorded and no item event — only the COIN leg is audited (EVT_BALANCE_CHANGED). The item trail is incomplete. G-8 should declare an audited grant op / item.granted event. NOTE punch #2: owner-gated granularity decision needed first (a dedicated item-event, not audit-channel flood).
- **read-model sort/filter/group projection** — `needs-new-primitive` — NEW pattern (G-14): _CategoryView has a sort cycle, type filter, and per-rarity-tier grouped fields. §2's read-model (fields/table/list over ProviderRef) has no declarative sort-key / filter-facet / group-by-key. Recurs across every browser panel (dex, fishlog, market, titles, leaderboards).
- **deep persistent state** — `yes` — ABSENT for inventory-owned data — the inventory table is a shallow (user,guild,item)→qty ledger (StoreSpec, tier 1). The DEEP state (mining grid / creature dex / farm accrual) lives in OTHER Lane-B subsystems that this browser only READS via get_mining_inventory. G-10 not needed here.
- **stateful game loop / wait_for wizard / scheduled loop+cooldown / XP+leaderboard / creature-battle / farm-growth** — `yes` — ALL ABSENT — inventory is a read-only browser with no game loop, no wizard, no @tasks.loop, no @bot.event/Cog.listener/bus.on, no cooldown decorator, no leaderboard. Notably it has ZERO legitimate escape hatches (no game rules): everything tier-3 is a grammar gap, so 100% is kernel-expressible with G-7/G-8/G-14.

**MAP → RECONSIDER → SIMULATE → OPTIMIZE**

- **Verdict:** redesign · **status:** owner-gated — punch #2 (audit granularity: dedicated item-event vs audit channel, must NOT flood on every ore/fish), punch #1 (whether to add use/sell/trade/gift item actions), and punch #3 (capability enforce-or-remove) each need an owner decision before the redesign lands (cert docs/planning/feature-completion/units/inventory.md).
- **Optimal new-bot form:** A first-class declared Item kernel: ItemCatalogSpec (taxonomy as data) + InventoryItemSpec store family exposing audited, atomic, unique-fenced grant/consume/has ops, feeding a GENERATED sortable/filterable/grouped read-model browser — replacing the hand-written UnifiedInventoryView/_CategoryView and MERGING the two divergent item tables (economy `inventory` + mining `mining_inventory`) behind one manifest so mining/fishing/farm/shop all grant through the same audited seam.
- **Dependency layer:** L2 item store — sits on L1 currency kernel (grants pair with debits atomically via G-7 EconomyTransactionSpec) and is consumed by L3 games (mining/fishing/farm/shop). Build order: L1 currency → G-8 item store → G-7 transactions → G-14 browser projection.
- **Production-grade done:** Golden parity: the browser renders byte-identical grouped/sorted output for a seeded mixed inventory (economy+mining merge, summed overlapping keys, rarest-first, unknown→Other); EVERY grant/consume routes through the audited seam emitting a declared item event; a unique-grant double-click yields exactly one item + one debit (race golden, extends test_shop_purchase_workflow); and inventory.item.use / craft.recipe capabilities are either enforced or removed.
- **Outperform target:** pending Lane F (compare to item/economy bots such as UnbelievaBoat and Dank Memer) — beat on unified cross-minigame inventory + fully audited item trail + fully declarative catalogue with no bespoke per-cog SQL.

**Cross-lane dependencies**

- mining_inventory table (owned by MINING lane; disbot/utils/db/games/mining.py) — inventory READS it via get_mining_inventory and merges it into the unified browser (inventory_cog.py:245). The two item tables are separately owned but co-displayed.
- economy/shop lane owns shop_purchase_workflow.purchase_unique_item, which is the LIVE writer of the inventory table (grant leg) — the atomic debit+grant txn. Any G-7/G-8 redesign must be co-designed with the economy lane.
- economy lane: economy_service.debit_in_txn + EVT_BALANCE_CHANGED (shop_purchase_workflow.py:75,91) — the coin leg paired with every item grant; the item trail's audit gap is defined relative to this coin trail.
- G-8 ItemCatalogSpec is a SHARED convergence primitive across the whole Lane-B family: mining ores/structures/tools, fishing pearls/coral/curios, and economy job-unlocks (car/suit) all appear in ITEM_CATALOGUE — one item kernel should serve them all.

**⚠ Unverified / judgment calls**

- add_item (utils/db/inventory.py:21) has NO live runtime caller in disbot/ (grep confirmed: only try_grant_unique_item writes the inventory table, via shop_purchase_workflow). Classified tier-3 as a defined grant primitive but it is effectively dead code today — flagged for the store's sole-writer characterization.
- Whether the inventory.item.use / inventory.craft.recipe capabilities are enforced anywhere: cert docs assert they are declared-but-unenforced (punch #3); I verified the read view has only BaseView ownership check and found no capability gate in inventory_cog.py, consistent with the cert, but did not exhaustively grep every consumer.
- Exact granularity the owner wants for item-grant auditing (punch #2 is explicitly deferred pending an owner decision) — my G-8 'audited grant op' assumes a dedicated low-frequency item-event, not audit.action_recorded on every grant; this is an owner call, not a verified requirement.
- Sort/filter tier-3-as-written calls (units 6,7) are a defensible judgment, not a hard grammar fact: a provider that accepted sort/filter params could arguably render them tier-2 today. I classified them tier-3 because §2's ProviderRef exposes no declared projection surface; a reviewer could rate them tier-2 as-written, which would lift as-written fit from 67% toward ~76%.

---

### treasury
_cogs/source: disbot/cogs/treasury_cog.py · services/treasury_service.py · utils/db/treasury.py · views/treasury/*_

| Unit | Kind | File:line | Tier (as-written) | Tier (with amendments) | Rationale / gap |
|---|---|---|---|---|---|
| !treasury (aliases bank, pool) — open panel | command | disbot/cogs/treasury_cog.py:42-50 | 1 | 1 | invoke_without_command opens open_treasury_panel → PanelRef, kernel open-panel workflow. Zero domain code. |
| !treasury contribute (donate, deposit) | command | disbot/cogs/treasury_cog.py:52-59 + services/treasury_service.py:70-118 | 3 | 2 | Routes to treasury_service.contribute: atomic debit-user + credit-pool + audit (economy_audit_log) + emit inside one db.transaction, with positive-amount guard and typed insufficient-funds copy. §2 as-written has no atomic-money-move family → HandlerRef tier 3. With G-7 EconomyTransactionSpec (debit+credit+audit+event declared) → tier 2; typed error rides §2.7 Result grammar. |
| !treasury grant (disburse, payout) — manage_guild gated | command | disbot/cogs/treasury_cog.py:61-80 + services/treasury_service.py:121-181 | 3 | 2 | Capability-gated (perms_or_owner manage_guild) disburse: try_debit_treasury conditional UPDATE (double-spend guard, no read-then-write race) → credit user → audit → emit; underfunded rolls back with typed copy. capability_required is a tier-1 field; the atomic multi-write body is tier 3 as-written, tier 2 with G-7 (settle-once/conditional-debit is a declared G-7 property). |
| build_help_menu_view — Help-menu navigation hook | command/help-nav | disbot/cogs/treasury_cog.py:84-89 | 1 | 1 | Returns open_treasury_panel — navigation entry point → PanelRef open-panel workflow. Pure declaration. |
| TreasuryView panel — read-model embed (pool balance + viewer wallet) | panel | disbot/views/treasury/menu.py:28-73,76-120 | 2 | 2 | build_treasury_embed over _panel_data (treasury_service.get_balance + db.get_coins) — FieldsBlock over a read-model ProviderRef, no bespoke view survives. HubView author-restriction is kernel-owned. |
| Contribute button — open modal | panel-action | disbot/views/treasury/menu.py:102-112 | 1 | 1 | send_modal(_ContributeModal) — kernel modal-open workflow, no domain logic in the button itself. |
| _ContributeModal on_submit — parse + contribute mutation | panel-action/modal | disbot/views/treasury/menu.py:123-158 | 3 | 2 | Single-field modal: int parse + positive guard, then same treasury_service.contribute seam, then redraw with flash. As-written the mutation makes it tier 3; with G-7 the modal is a kernel modal-collect feeding a declared EconomyTransactionSpec → tier 2. Not a wait_for wizard (single modal). |
| Refresh button — re-render panel | panel-action | disbot/views/treasury/menu.py:114-120,87-100 | 1 | 1 | _redraw re-reads _panel_data onto a fresh view (timeout reset) — kernel re-render workflow, pure declaration. |
| guild_treasury table — shared-pool balance store | store | disbot/migrations/092_guild_treasury.sql:15-19 + utils/db/treasury.py:24-88 | 1 | 1 | One-row-per-guild aggregate balance. StoreSpec: sole_writer=treasury_service, checkpoint_class=aggregate, generated sole-writer fence. CRUD (get/credit/try_debit) are the store's conditional-write primitives owned by the fence + G-7, not separate surfaces. |
| EVT_BALANCE_CHANGED emission (reused economy event; contribute + disburse reasons) | event | disbot/services/treasury_service.py:104-111,167-174 | 1 | 1 | Treasury does not own an event — it emits economy.balance_changed after commit with treasury:contribute / treasury:disburse reasons. Declared event reference; the emit becomes a declared leg of the G-7 transaction. Verbatim event name = compat item 3. |
| capabilities: treasury.pool.view / contribute / disburse | capability×3 | disbot/utils/subsystem_registry.py:224-228 | 1 | 1 | Three governance capability strings mapped to command capability_required — tier-1 manifest declarations (permission model), like bindings. |
| Help entry (summary/examples projection) | help | disbot/cogs/treasury_cog.py:84-89 (surface); registry description :208 | 1 | 1 | HelpEntrySpec — help-as-projection, tier 1. |
| Economy hub '🏛️ Treasury' nav button (economy:treasury) | panel-action/nav | disbot/views/economy/main_panel.py:292-308 | 1 | 1 | Cross-subsystem navigation to open_treasury_panel with back-target forwarding — kernel navigation panel-action (lives in economy's manifest, treasury entry point). Pure declaration. |

**Fit:** 15 units · tier-1/2 as-written **80%** (12/15) · with amendments **100%** (15/15).

**§2 manifest sketch**

```python
TREASURY_MANIFEST = SubsystemManifest(
    key="treasury", display_name="Treasury", emoji="🏛️",
    category="economy", parent_hub="economy", visibility_tier="user",
    capabilities=("treasury.pool.view","treasury.pool.contribute","treasury.pool.disburse"),
    dependencies=(),                       # soft-depends economy; no HARD dep (read-only when economy off)
    commands=(
        CommandSpec(name="treasury", aliases=("bank","pool"), kind=PREFIX,
            summary="Open the server treasury.", route=PanelRef("treasury.hub")),          # tier 1
        CommandSpec(name="treasury contribute", aliases=("donate","deposit"), kind=PREFIX,
            summary="Donate your coins into the pool.",
            route=HandlerRef("treasury.contribute",                                        # tier 3 -> G-7 tier 2
                justification="atomic debit-user+credit-pool+audit+event (G-7 EconomyTransactionSpec)")),
        CommandSpec(name="treasury grant", aliases=("disburse","payout"), kind=PREFIX,
            capability_required="treasury.pool.disburse",
            summary="Disburse from the pool to a member.",
            route=HandlerRef("treasury.disburse",                                          # tier 3 -> G-7 tier 2
                justification="conditional-debit pool (settle-once) + credit user + audit + event")),
    ),
    panels=(
        PanelSpec(panel_id="treasury.hub", subsystem="treasury", title="🏛️ Server Treasury",
            audience="invoker",
            body=(BlockSpec(kind="fields", provider=ProviderRef("treasury.pool_and_wallet")),),  # tier 2
            actions=(
                PanelActionSpec(action_id="contribute", label="Contribute", emoji="➕", style="success",
                    handler=WorkflowRef("modal_collect",                                    # tier 1 open
                        (("field","amount:int"),("then","treasury.contribute")))),          # submit -> G-7 tier 2
                PanelActionSpec(action_id="refresh", label="Refresh", emoji="🔄",
                    handler=WorkflowRef("panel_rerender", (("panel","treasury.hub"),))),     # tier 1
            )),
    ),
    settings=(),                            # verified: NO settings_keys / db.get_setting — capability-only
    events=(),                              # emits economy.balance_changed (foreign, owned by economy)
    subscriptions=(),                       # emits only; subscribes to nothing
    gateway_listeners=(),                   # none
    tasks=(),                               # none (no @tasks.loop, no @commands.cooldown)
    stores=(
        StoreSpec(table="guild_treasury", sole_writer="treasury.service",
            checkpoint_class="aggregate", invariant_tag="INV-T",
            reader_domains=("economy","treasury")),                                          # tier 1
    ),
    # PROPOSED G-7: the two seams become declared atomic transactions (data, not code):
    # transactions=(
    #   EconomyTransactionSpec("treasury.contribute", legs=(Debit("user","arg:amount"),
    #       Credit("treasury","arg:amount")), audit="economy_audit_log", event="economy.balance_changed",
    #       on_insufficient="user"),
    #   EconomyTransactionSpec("treasury.disburse", legs=(ConditionalDebit("treasury","arg:amount"),
    #       Credit("user","arg:amount")), settle_once=True, audit="economy_audit_log",
    #       event="economy.balance_changed", on_insufficient="pool"),
    # ),
    help=HelpEntrySpec(summary="Contribute coins to the shared pool; managers disburse.",
        examples=("!treasury","!treasury contribute 100","!treasury grant @user 50")),
)
```

**Tier-3 dispositions**

| Tier-3 unit | Verdict | Reason |
|---|---|---|
| !treasury contribute | grammar-gap:G-7 | Atomic debit-user + credit-pool + audit + post-commit event is exactly the recurring money-move shape G-7 EconomyTransactionSpec declares; kernel SHOULD own atomic money movement (safety-critical), so not a legitimate escape hatch. Typed insufficient-funds copy rides §2.7 Result grammar. |
| !treasury grant (disburse) | grammar-gap:G-7 | Conditional-debit pool (double-spend guard) + credit user + audit + event, underfunded rollback = G-7 with settle-once/conditional-debit property. The manage_guild gate is already a tier-1 capability_required field, not the reason it is tier 3. |
| _ContributeModal on_submit | grammar-gap:G-7 | Same contribute transaction reached via a single-field modal; kernel modal-collect (tier 1) feeding a declared G-7 transaction (tier 2) removes all domain code. Int-parse/positive guard is generic input validation the kernel owns. |

**Structural-gap flags**

- **transactional multi-write mutation (debit+credit+audit+event in one db.transaction)** — `with-amendment:G-7` — Both contribute (debit user/credit pool) and disburse (debit pool/credit user) compose two coin legs + audit + post-commit emit on one conn via Q-0071. As-written = HandlerRef tier 3; G-7 EconomyTransactionSpec makes it declared data.
- **escrow/settlement + double-settle / double-spend risk** — `with-amendment:G-7` — try_debit_treasury is a single-statement conditional UPDATE (balance >= amount) — decides sufficiency and writes atomically, no read-then-write race; underfunded matches nothing and rolls the whole txn back. This settle-once/conditional-debit semantic is a declared G-7 property, not bespoke code.
- **irreversible economy op (shared-pool contribute/disburse; grant is a manager faucet)** — `with-amendment:G-7` — Audited to economy_audit_log with actor_id attribution + balance-changed event = declared G-7 legs; the manage_guild gate is a tier-1 capability_required.
- **shared collective-balance store (server-owned pool)** — `yes` — One aggregate row per guild — StoreSpec sole-writer fence (tier 1). No per-player deep state.
- **foreign event reuse (emits economy.balance_changed, owned by economy)** — `yes` — Verbatim event-name reference; no new primitive needed. Cross-lane: economy owns the EventSpec + economy_audit_log store.
- **deep persistent state / inventory taxonomy / mining grid / creature battle / farm growth / XP-leaderboard / scheduled loop / cooldown / stateful game loop / wait_for wizard** — `yes` — NONE present in treasury (verified). The single modal is a one-field kernel modal-collect, not a wizard; no @tasks.loop, no @commands.cooldown, no gateway listener, no subscription.

**MAP → RECONSIDER → SIMULATE → OPTIMIZE**

- **Verdict:** keep · **status:** ok
- **Optimal new-bot form:** A thin SubsystemManifest: one read-model panel (pool + viewer wallet) with open/refresh/help/nav as tier-1 kernel declarations, plus TWO declared EconomyTransactionSpec (G-7) atomic multi-writes for contribute and disburse (debit+credit+audit+event, settle-once conditional-debit) replacing all bespoke service code. The shared pool is a single aggregate StoreSpec; the balance-changed event is a foreign reference to economy's EventSpec.
- **Dependency layer:** L1 currency kernel (economy coins store + economy_audit_log + G-7 EconomyTransactionSpec + economy.balance_changed event) → treasury is L2: one shared-pool aggregate store + two G-7 transaction declarations composed on top of L1. Build economy L1 first; treasury falls out almost for free.
- **Production-grade done:** Parity golden: (1) contribute atomically debits the user and credits the pool, rolling both back on insufficient funds; (2) grant is manage_guild-gated and can NEVER overdraw the pool (conditional single-statement debit); (3) both write economy_audit_log with actor attribution and emit economy.balance_changed only after commit; (4) a concurrency test proves two simultaneous disburses cannot double-spend the pool. Acceptance = existing treasury tests green + the added no-double-spend concurrency test + audit-trail assertion.
- **Outperform target:** pending Lane F (shared guild-bank / collective-pool feature vs UnbelievaBoat-class economy bots; edge = audited, transaction-safe, governance-gated pool with attributable disbursements).

**Cross-lane dependencies**

- economy owns EVT_BALANCE_CHANGED (economy.balance_changed) — treasury emits it as a FOREIGN event reference, does not declare its own EventSpec (services/treasury_service.py:104,167; economy_service.py:57).
- economy owns the money trail: contribute/disburse audit via economy_service.debit_in_txn/credit_in_txn → economy_audit_log (economy_service.py:129-193). G-7 EconomyTransactionSpec must be an economy/currency-kernel primitive that treasury COMPOSES, not a treasury-local one.
- utils/db.transaction() cross-leg composition (Q-0071 precedent) — shared infra the treasury pool leg and the user coin leg ride on one connection.
- economy read: TreasuryView panel provider calls db.get_coins for the viewer wallet (views/treasury/menu.py:56) — read-model dependency on economy store.
- Economy hub entry-point button (economy:treasury) lives in views/economy/main_panel.py:292-308 — the treasury nav surface is authored in economy's manifest, so Lane B must place cross-subsystem nav consistently.
- G-7 is the convergence point for the whole money-moving Lane B (economy transfer, casino escrow, shop/market, payouts) — align the amendment id and the EconomyTransactionSpec shape across those lane reports.

**⚠ Unverified / judgment calls**

- capability×3 counted as 3 surface units (judgment call — capabilities are governance declarations mapped to command capability_required, weighted like bindings). If capabilities are excluded, units_total=12, tier12_aswritten=9 → fit still 75% as-written / 100% amended.
- Economy hub '🏛️ Treasury' button attributed to treasury's entry surface but source-owned by views/economy/main_panel.py — included as a treasury-reachability unit, tier 1 either way (does not change fit).

---

### mining
_cogs/source: disbot/cogs/mining_cog.py · services/mining_workflow.py · utils/db/games/mining*.py · utils/mining/* · views/mining/*_

| Unit | Kind | File:line | Tier (as-written) | Tier (with amendments) | Rationale / gap |
|---|---|---|---|---|---|
| !minemenu | command | disbot/cogs/mining_cog.py:57 | 1 | 1 | opens MiningHubView via panel_manager.get_or_render_panel — pure kernel open-panel workflow |
| !mine | command | disbot/cogs/mining_cog.py:91 | 1 | 1 | opens the MineGridView grid navigator; command route is a panel-open (the stateful board is a separate tier-3 unit) |
| !fastmine | command | disbot/cogs/mining_cog.py:102 | 3 | 3 | mining_workflow.mine: loot-roll engine + grant + wear + xp; thin game-loop handler — stays escape-hatch (loot table extractable via G-14) |
| !chop | command | disbot/cogs/mining_cog.py:118 | 3 | 3 | mining_workflow.harvest: roll + grant; thin game-loop action, escape-hatch |
| !mineinv | command | disbot/cogs/mining_cog.py:137 | 1 | 1 | delegates to !inventory via ctx.invoke — a declared alias/route, no logic |
| !minestats | command | disbot/cogs/mining_cog.py:150 | 2 | 2 | read-model: reads inventory/depth/level → FieldsBlock over a provider |
| !build (alias craft) | command | disbot/cogs/mining_cog.py:193 | 3 | 2 | mining_workflow.craft (materials→product atomic); recipe transform → G-12 CraftingRecipeSpec makes it data |
| !buildlist | command | disbot/cogs/mining_cog.py:209 | 2 | 2 | read-model over recipes.json → TableBlock provider |
| !buildable | command | disbot/cogs/mining_cog.py:240 | 2 | 2 | read-model: recipes filtered by inventory → provider |
| !explore | command | disbot/cogs/mining_cog.py:265 | 3 | 3 | mining_workflow.explore: exploration-event engine + loot + wear; thin loop handler, escape-hatch |
| !use | command | disbot/cogs/mining_cog.py:281 | 3 | 2 | use_item: consume item + optional energy restore atomic → G-8 item-consume op + G-13 energy |
| !cook | command | disbot/cogs/mining_cog.py:292 | 3 | 2 | cook: campfire-gated consume fish → grant cooked-fish atomic → G-8 consume/grant + G-12 (fish→food recipe) |
| !equip | command | disbot/cogs/mining_cog.py:315 | 3 | 2 | equip: slot-set with ownership check, no coins → G-8 InventoryItemSpec equip op |
| !unequip | command | disbot/cogs/mining_cog.py:326 | 3 | 2 | unequip: clear slot → G-8 equip op |
| !gear | command | disbot/cogs/mining_cog.py:338 | 2 | 2 | read-model gear embed + paper-doll (render is a projection); provider-shaped |
| !loadout (save/apply/list/delete) | command | disbot/cogs/mining_cog.py:361 | 3 | 2 | verb-router into loadout preset mgmt (snapshot/restore gear-set) → G-8 declared item-set ops |
| !character (profile/char) | command | disbot/cogs/mining_cog.py:411 | 2 | 2 | read-model character card + doll image; provider (doll renderer counted separately) |
| !descend | command | disbot/cogs/mining_cog.py:441 | 3 | 2 | descend: light-gated depth-band move + depth-record xp → G-10 persistent-world state move |
| !ascend | command | disbot/cogs/mining_cog.py:458 | 3 | 2 | ascend: set_depth-1 thin state move → G-10 |
| !mineworld [seed] | command | disbot/cogs/mining_cog.py:474 | 3 | 2 | show seed (read) + admin reseed_world (perms-gated set_world_seed) → G-10 world-seed state |
| !sell | command | disbot/cogs/mining_cog.py:501 | 3 | 2 | sell: inventory-debit + coin-credit atomic, audited → G-7 EconomyTransactionSpec / G-11 MarketSpec |
| !sellall | command | disbot/cogs/mining_cog.py:516 | 3 | 2 | sell_all: all resource removals + one credit atomic → G-7/G-11 |
| !buy | command | disbot/cogs/mining_cog.py:522 | 3 | 2 | buy: coin-debit + gear-grant atomic → G-7/G-11 priced catalog |
| !market | command | disbot/cogs/mining_cog.py:535 | 2 | 2 | read-model: sellables + shop listing → provider |
| !vault | command | disbot/cogs/mining_cog.py:571 | 1 | 1 | opens MiningVaultView — panel-open workflow |
| !stash | command | disbot/cogs/mining_cog.py:585 | 3 | 2 | vault_deposit: move item inventory→vault atomic (no coins) → G-8 item-move op |
| !unstash | command | disbot/cogs/mining_cog.py:605 | 3 | 2 | vault_withdraw: vault→inventory atomic → G-8 |
| !vaultupgrade | command | disbot/cogs/mining_cog.py:625 | 3 | 2 | vault_upgrade: rising coin-debit + capacity-tier bump atomic → G-7 (coin sink) + G-9 tier curve |
| !skills | command | disbot/cogs/mining_cog.py:637 | 1 | 1 | opens MiningSkillsView — panel-open |
| !skill <branch> | command | disbot/cogs/mining_cog.py:651 | 3 | 2 | skill_service.allocate: spend points into branch (cap/budget checks) → G-9 ProgressionSpec skill tree |
| !titles | command | disbot/cogs/mining_cog.py:674 | 1 | 1 | opens MiningTitlesView — panel-open |
| !forge | command | disbot/cogs/mining_cog.py:690 | 1 | 1 | opens MiningForgeView — panel-open |
| !home | command | disbot/cogs/mining_cog.py:706 | 1 | 1 | opens MiningHomeView — panel-open |
| !workshop | command | disbot/cogs/mining_cog.py:722 | 1 | 1 | opens MiningWorkshopView — panel-open |
| !repair | command | disbot/cogs/mining_cog.py:736 | 3 | 2 | repair: coin-debit + wear-clear atomic, audited → G-7 EconomyTransactionSpec |
| !quickcraft | command | disbot/cogs/mining_cog.py:750 | 3 | 2 | quick_craft: re-craft last-broken + auto-equip + marker-clear atomic → G-12 recipe + G-8 equip |
| !reset_inventory (admin) | command | disbot/cogs/mining_cog.py:758 | 3 | 3 | admin_reset: capability-gated wipe of a user's inventory — legit thin admin escape-hatch |
| MiningHubView (persistent hub) | panel | disbot/views/mining/main_panel.py:147 | 1 | 1 | stateless 6-action nav hub, PersistentView — panel + navigation panel-actions |
| MineGridView (grid board) | panel | disbot/views/mining/grid_mine_view.py:84 | 3 | 3 | stateful seed-deterministic (x,y,z) roam board w/ fog-of-war, re-renders in place — renderer_override game board, §2.9 escape-hatch by design |
| MiningCharacterHubView (sub-hub) | panel | disbot/views/mining/character_hub.py:91 | 1 | 1 | sub-hub, 6 nav buttons + back — kernel nav choreography |
| MiningWorkshopHubView (sub-hub) | panel | disbot/views/mining/workshop_hub.py:41 | 1 | 1 | sub-hub, 4 nav buttons + back — nav choreography |
| MiningGearView | panel | disbot/views/mining/gear_panel.py:358 | 2 | 2 | read-model gear+doll with slot→item cascading selects (equip actions tier-3, counted separately) |
| MiningLoadoutView | panel | disbot/views/mining/gear_panel.py:621 | 2 | 2 | read-model loadout list + apply/delete selects + save-modal (mgmt actions share the loadout seam) |
| MiningMarketView | panel | disbot/views/mining/market_panel.py:271 | 2 | 2 | read-model sell+buy; Category→Type→Variant cascading selects route to audited buy (tier-3 seam) |
| MiningRecipeBrowserView | panel | disbot/views/mining/recipe_browser.py:240 | 2 | 2 | read-model Category→Type→Variant recipe browser; variant select routes to craft seam |
| MiningSkillsView | panel | disbot/views/mining/skills_panel.py:65 | 2 | 2 | read-model skill tree; 4 branch buttons route to allocate (tier-3 seam) |
| MiningRespecView | panel | disbot/views/mining/skills_panel.py:206 | 1 | 1 | confirm/cancel choreography — kernel confirm workflow (the refund is the tier-3 seam) |
| MiningTitlesView | panel | disbot/views/mining/titles_panel.py:108 | 2 | 2 | read-model earned-title picker; select sets equipped_title (thin item-state seam → G-8) |
| MiningVaultView | panel | disbot/views/mining/vault_panel.py:153 | 2 | 2 | read-model vault; deposit/withdraw modals + stash-all + upgrade route to seams |
| MiningForgeView | panel | disbot/views/mining/forge_panel.py:76 | 2 | 2 | read-model forge status; Build button routes to build_structure seam |
| MiningHomeView | panel | disbot/views/mining/home_panel.py:72 | 2 | 2 | read-model home status; Build button routes to build_structure seam |
| MiningWorkshopView | panel | disbot/views/mining/workshop_panel.py:159 | 2 | 2 | read-model workshop; repair select routes to repair seam |
| MiningHowToView | panel | disbot/views/mining/how_to_panel.py:50 | 1 | 1 | static one-screen guide + back button — pure projection/nav |
| character paper-doll renderer | renderer | disbot/cogs/mining_cog.py:428 | 3 | 3 | build_character_doll/render_gear_doll Pillow image composition — renderer_override escape-hatch, legit |
| grid dig move-resolver (6 dig buttons) | panel-action | disbot/views/mining/grid_mine_view.py:118 | 3 | 3 | dig(direction): move-into-cell + mine + fog-mark + wear + energy-spend atomic — game-move handler; G-10 declares state but the move-and-mine loop stays tier-3 |
| Equip Best (all slots) | panel-action | disbot/views/mining/gear_panel.py:402 | 3 | 2 | panel-only bulk best-in-slot equip → G-8 item ops |
| Stash All Ore | panel-action | disbot/views/mining/vault_panel.py:179 | 3 | 2 | vault_deposit_all_resources: sweep all resources to vault atomic → G-8 |
| Respec-branch (per-branch refund) | panel-action | disbot/services/skill_service.py:168 | 3 | 2 | surgical single-branch refund for coins → G-7 (coin) + G-9 (skill) |
| hub + sub-hub navigation actions | panel-action×15 | disbot/views/mining/main_panel.py:161 | 1 | 1 | Mine/Explore/Character/Gear/Workshop/How-to + character-hub(6) + workshop-hub(4) open-panel/nav workflows — kernel-generated |
| panel back/return buttons | panel-action×12 | disbot/views/mining/character_hub.py:287 | 1 | 1 | one ↩ back button per child panel — kernel navigation workflow |
| mining stores (inventory/equipment/gear_wear/player_state/discovered/world/loadout_presets/structures/vault/player_skills) | store×10 | disbot/utils/db/games/mining_player_state.py:48 | 1 | 1 | StoreSpec generated sole-writer fences; player_skills shared/mining-consumed; all writes funnel through mining_workflow (RS02) |
| world grid procedural generator | engine | disbot/utils/mining/grid.py | 3 | 3 | cell_at(seed,x,y,z) richness+featured-ore deterministic generation — procedural engine, legit escape-hatch (grammar must not own generation rules) |
| loot roll tables | engine | disbot/services/mining_workflow.py:809 | 3 | 2 | rewards.roll_mine_loot / explore_from_state weighted depth/biome drop tables → NEW G-14 LootTableSpec makes drop tables data |
| gear wear / durability system | engine | disbot/services/mining_workflow.py:173 | 3 | 2 | WEAR_PLAN tick + break-cascade (consume+unequip+clear+remember) — durability as data via G-8 extension; the break-cascade seam stays thin |
| energy idle-accrual system | engine | disbot/utils/mining/energy.py | 3 | 2 | settle/regen-on-read + DIG_COST gate (frequency brake, not a cooldown) → G-13 IdleAccrualSpec |
| game XP curve + level | engine | disbot/services/game_xp_service.py:148 | 3 | 2 | GAME_MINING/GAME_CRAFTING award + level curve + depth-record → G-9 ProgressionSpec (shared with other Lane-B games) |
| skill tree (branches/caps/budget) | engine | disbot/services/skill_service.py:75 | 3 | 2 | 4 branches, per-branch cap, points-from-level budget → G-9 ProgressionSpec |
| structures system (forge/home/campfire tiers) | engine | disbot/services/mining_workflow.py:705 | 3 | 2 | build_structure: level curve + coin+material cost + unlocks (forge gear-tier, home cosmetic, campfire cooking) → G-9/G-12 declared tier data + G-7 sink |
| vault capacity tiers | engine | disbot/utils/mining/capacity.py | 3 | 2 | vault_upgrade_cost/capacity curve + pack soft-cap → G-9 declared tier curve |
| EVT_BALANCE_CHANGED emit (economy-owned) | event | disbot/services/mining_workflow.py:533 | 1 | 1 | reuses economy's EventSpec; emit lives after-commit inside the audited seam — declaration-only from mining's side |
| capabilities mining.resource.mine / .view | capability×2 | disbot/utils/subsystem_registry.py:278 | 1 | 1 | declared capability strings — manifest header fields |
| subsystem registry header | header | disbot/utils/subsystem_registry.py:259 | 1 | 1 | display_name/emoji/category/entry_points/dependencies(economy)/parent_hub/hub_group — SubsystemManifest root fields |
| help entry (build_help_menu_view) | help | disbot/cogs/mining_cog.py:67 | 1 | 1 | help-menu direct-nav hook returning the hub panel — help-as-projection |

**Fit:** 108 units · tier-1/2 as-written **67%** (72/108) · with amendments **93%** (100/108).

**§2 manifest sketch**

```python
MINING_MANIFEST = SubsystemManifest(
    key="mining", display_name="Mining", emoji="⛏️",
    category="economy", parent_hub="games", hub_group="activities",
    dependencies=("economy",),                      # hard dep: coins via economy INV-F seam
    capabilities=("mining.resource.mine","mining.resource.view"),
    commands=(
        # --- tier-1 panel-opens (kernel open-panel workflow) ---
        CommandSpec("minemenu", PREFIX, route=PanelRef("mining.hub")),
        CommandSpec("mine",     PREFIX, route=PanelRef("mining.grid")),      # opens the stateful board
        CommandSpec("vault",    PREFIX, route=PanelRef("mining.vault")),
        CommandSpec("skills",   PREFIX, route=PanelRef("mining.skills")),
        CommandSpec("titles",   PREFIX, route=PanelRef("mining.titles")),
        CommandSpec("forge",    PREFIX, route=PanelRef("mining.forge")),
        CommandSpec("home",     PREFIX, route=PanelRef("mining.home")),
        CommandSpec("workshop", PREFIX, route=PanelRef("mining.workshop")),
        CommandSpec("mineinv",  PREFIX, route=PanelRef("inventory.hub")),    # alias/route
        # --- tier-2 read providers ---
        CommandSpec("minestats", PREFIX, route=ProviderRef("mining.stats_provider")),
        CommandSpec("buildlist", PREFIX, route=ProviderRef("mining.recipes_provider")),
        CommandSpec("buildable", PREFIX, route=ProviderRef("mining.buildable_provider")),
        CommandSpec("gear",      PREFIX, route=ProviderRef("mining.gear_provider")),
        CommandSpec("character", PREFIX, route=ProviderRef("mining.character_provider")),
        CommandSpec("market",    PREFIX, route=ProviderRef("mining.market_provider")),
        # --- tier-3 seams (thin route → amendment family) ---
        CommandSpec("fastmine", PREFIX, route=HandlerRef("mining.mine",   just="loot engine")),    # stays 3
        CommandSpec("chop",     PREFIX, route=HandlerRef("mining.harvest",just="loot engine")),    # stays 3
        CommandSpec("explore",  PREFIX, route=HandlerRef("mining.explore",just="event engine")),   # stays 3
        CommandSpec("sell",     PREFIX, route=EconomyTransactionSpec.ref("mining.sell")),          # G-7/G-11
        CommandSpec("sellall",  PREFIX, route=EconomyTransactionSpec.ref("mining.sell_all")),      # G-7/G-11
        CommandSpec("buy",      PREFIX, route=ShopSpec.ref("mining.gear_shop")),                   # G-11
        CommandSpec("repair",   PREFIX, route=EconomyTransactionSpec.ref("mining.repair")),        # G-7
        CommandSpec("vaultupgrade", PREFIX, route=EconomyTransactionSpec.ref("mining.vault_up")),  # G-7
        CommandSpec("build",    PREFIX, aliases=("craft",), route=CraftingRecipeSpec.ref("mining.craft")),   # G-12
        CommandSpec("quickcraft", PREFIX, route=CraftingRecipeSpec.ref("mining.quick_craft")),     # G-12
        CommandSpec("equip",    PREFIX, route=InventoryItemSpec.op("equip")),                      # G-8
        CommandSpec("unequip",  PREFIX, route=InventoryItemSpec.op("unequip")),                    # G-8
        CommandSpec("use",      PREFIX, route=InventoryItemSpec.op("consume")),                    # G-8+G-13
        CommandSpec("cook",     PREFIX, route=CraftingRecipeSpec.ref("mining.cook")),              # G-12+G-8
        CommandSpec("stash",    PREFIX, route=InventoryItemSpec.op("move_to_vault")),              # G-8
        CommandSpec("unstash",  PREFIX, route=InventoryItemSpec.op("move_from_vault")),            # G-8
        CommandSpec("loadout",  PREFIX, aliases=("loadouts",), route=InventoryItemSpec.op("loadout")), # G-8
        CommandSpec("skill",    PREFIX, route=ProgressionSpec.ref("skills.allocate")),             # G-9
        CommandSpec("descend",  PREFIX, route=GameStateSpec.move("descend")),                      # G-10
        CommandSpec("ascend",   PREFIX, route=GameStateSpec.move("ascend")),                       # G-10
        CommandSpec("mineworld",PREFIX, route=GameStateSpec.reseed("mining.world"), cap="mining.world.reseed"), # G-10
        CommandSpec("reset_inventory", PREFIX, route=HandlerRef("mining.admin_reset"), cap="mining.admin"),     # stays 3 (admin)
    ),
    panels=(
        PanelSpec("mining.hub", audience="persistent", timeout_s=None,   # 6 nav actions
                  actions=(nav("mine"),nav("harvest→seam"),nav("explore"),nav("character"),nav("gear"),nav("workshop"),nav("how_to"))),
        PanelSpec("mining.grid", renderer_override=HandlerRef("mining.render_grid",
                  just="stateful seed-deterministic (x,y,z) fog-of-war board"),   # tier-3 board
                  actions=(dig("N"),dig("S"),dig("E"),dig("W"),dig("Down"),dig("Up"),nav("menu"),nav("help"))),
        PanelSpec("mining.character_hub", actions=(nav()*6, back())),   # sub-hub
        PanelSpec("mining.workshop_hub",  actions=(nav()*4, back())),   # sub-hub
        PanelSpec("mining.gear",   body=FieldsBlock(ProviderRef("mining.gear_provider")),
                  selectors=(slot_select, item_select), actions=(equip_best, loadouts_nav, back)),
        PanelSpec("mining.market", body=FieldsBlock(ProviderRef("mining.market_provider")),
                  selectors=(cat_select, type_select, buy_select→ShopSpec)),   # cascading
        PanelSpec("mining.recipes", selectors=(cat, type, variant→CraftingRecipeSpec)),
        PanelSpec("mining.skills", actions=(allocate*4→ProgressionSpec, respec_nav, titles_nav, back)),
        PanelSpec("mining.vault",  actions=(deposit, withdraw, stash_all, upgrade→G-7, back)),
        # + forge, home, workshop, titles, respec, loadout, how_to panels …
    ),
    stores=(
        StoreSpec("mining_inventory", sole_writer="mining_workflow", checkpoint_class="aggregate"),
        StoreSpec("mining_equipment", sole_writer="mining_workflow", checkpoint_class="aggregate"),
        StoreSpec("mining_gear_wear", sole_writer="mining_workflow", checkpoint_class="aggregate"),
        StoreSpec("mining_player_state", sole_writer="mining_workflow", checkpoint_class="aggregate"),  # pos/depth/title/energy/last_broken
        StoreSpec("mining_discovered", sole_writer="mining_workflow", checkpoint_class="aggregate"),    # fog-of-war  → G-10
        StoreSpec("mining_world", sole_writer="mining_workflow", checkpoint_class="aggregate"),         # guild seed → G-10
        StoreSpec("mining_loadout_presets", sole_writer="mining_workflow", checkpoint_class="aggregate"),
        StoreSpec("mining_structures", sole_writer="mining_workflow", checkpoint_class="aggregate"),
        StoreSpec("mining_vault", sole_writer="mining_workflow", checkpoint_class="aggregate"),
        StoreSpec("player_skills", sole_writer="skill_service", checkpoint_class="aggregate", reader_domains=("mining","xp")),
    ),
    events=(),                       # emits economy.EVT_BALANCE_CHANGED (economy-owned) after commit
    # NEW families this subsystem forces:  G-7 EconomyTransactionSpec · G-8 InventoryItemSpec ·
    #   G-9 ProgressionSpec · G-10 GameStateSpec/PersistentWorldSpec · G-11 ShopSpec ·
    #   G-12 CraftingRecipeSpec · G-13 IdleAccrualSpec · G-14 LootTableSpec (new)
    help=HelpEntrySpec(summary="Mine a shared seed-deterministic world; craft, trade, and level up."),
)
# NO settings, NO bindings, NO gateway_listeners, NO cooldowns, NO tasks — verified absent in source.
```

**Tier-3 dispositions**

| Tier-3 unit | Verdict | Reason |
|---|---|---|
| !fastmine / !chop / !explore (mine/harvest/explore actions) | escape-hatch (loot table → G-14) | thin game-loop orchestration (roll+grant+wear+xp); the loot/event roll is engine-like. Loot tables extract to G-14 LootTableSpec data, but the per-swing orchestration is a legitimate thin domain handler, like a game move. |
| grid dig move-resolver (6 dig buttons) | grammar-gap:G-10 + escape-hatch | G-10 GameStateSpec declares the persistent (x,y,z)+fog state; the 'dig = move-into-and-mine' choreography (light-gated Down, lateral tunnels, atomic 5-write) is a game-move handler that should stay code. |
| MineGridView stateful board (renderer_override) | escape-hatch | seed-deterministic roam board with in-place re-render and fog-of-war — the §2.9 game-board renderer class, tier-3 by design (kernel must not own board rendering); direct analog of blackjack.board. |
| character/gear paper-doll renderer | escape-hatch | Pillow image composition (attachment://character.png) — a renderer_override, legitimately code; kernel should not own image compositing. |
| world grid procedural generator (cell_at/richness/featured-ore) | escape-hatch | deterministic procedural generation from seed — a generation engine analogous to game rules; grammar must never express generation, the 'worse programming language' failure mode. |
| !reset_inventory (admin_reset) | escape-hatch | capability-gated one-off admin wipe; thin, deliberate operator action — kernel need not own it. |
| loot roll tables (roll_mine_loot/explore_from_state) | grammar-gap:G-14 | weighted, depth/biome-conditioned drop tables recur across mining/fishing/creature/farm; a declarative LootTableSpec (weighted drops as data) turns them tier-2. NEW primitive proposed. |
| sell / sellall / buy / repair / vault_upgrade (audited coin ops) | grammar-gap:G-7/G-11 | atomic coin-leg + inventory/state-leg + economy-audit; EconomyTransactionSpec (G-7) / ShopSpec (G-11) express the transaction as declared data. |
| build / craft / quickcraft / cook (recipe transforms) | grammar-gap:G-12 | inputs→outputs recipe transform (materials+product atomic, forge-gated); CraftingRecipeSpec expresses recipe as data, the thin transform executor is a registered ref. |
| equip / unequip / use / stash / unstash / loadout / titles (item ops) | grammar-gap:G-8 | equip-slot/consume/move/grant + gear-set snapshot/restore + title-set — declared InventoryItemSpec/ItemCatalogSpec ops over the mining stores, not per-cog SQL. |
| skill allocate / respec / respec-branch + XP curve | grammar-gap:G-9 | skill tree (branches/caps, points-from-level budget) + XP earn/level/depth-record → ProgressionSpec declared curve+budget; respec's coin leg also uses G-7. |
| descend / ascend / mineworld-reseed (world-state moves) | grammar-gap:G-10 | depth-band move (light-gated) and guild world-seed reseed are persistent-world state mutations expressed by GameStateSpec/PersistentWorldSpec. |
| gear wear/durability + energy idle-accrual + vault-capacity + structures tiers | grammar-gap:G-8/G-13/G-9 | durability (G-8 extension), regen-on-read energy gate (G-13 IdleAccrualSpec — the cooldown-analog), capacity/structure level curves (G-9) — all recurring Lane-B tier curves declarable as data. |

**Structural-gap flags**

- **deep persistent per-player world state** — `with-amendment:G-10` — mining_player_state (pos/depth/title/energy), mining_discovered fog-of-war grid, mining_world seed, mining_structures — StoreSpec covers rows but G-10 GameStateSpec/PersistentWorldSpec is needed for the world/grid semantics (position, band, discovered-window queries).
- **transactional multi-write mutation** — `with-amendment:G-7` — every workflow op runs in ONE db.transaction (coin+inventory, materials+product, wear break-cascade of 4 writes, move-and-mine of 5 writes); RS02/Q-0071. G-7 EconomyTransactionSpec declares the money-bearing ones; pure item moves via G-8. The atomicity contract is real and must survive the port.
- **escrow/settlement + double-settle risk** — `yes` — NOT PRESENT — mining has no PvP session, escrow, or settle-once path; its atomicity is a single-actor db.transaction, not an escrow. ChallengeSessionSpec is not needed here.
- **inventory / item taxonomy** — `with-amendment:G-8` — resources/gear/tools/lights/charms/fish/food/treasure with equip slots, durability, stackability, unique gear; resolve_item_name fuzzy matching. Needs G-8 ItemCatalogSpec + a durability facet.
- **mining grid / procedural world** — `needs-new-primitive` — seed-deterministic (x,y,z) grid where every dig MOVES you and mines the cell you enter, with fog-of-war reveal-radius gated by equipped light. G-10 declares the state; the generator (cell_at) and the move-resolver stay tier-3 engines by design.
- **XP + progression + leaderboard derivation** — `with-amendment:G-9` — GAME_MINING/GAME_CRAFTING XP curve + level, depth-record, skill tree (4 branches, caps, points-from-level). G-9 ProgressionSpec. No explicit mining leaderboard command exists (LeaderboardSpec unused here), though max-depth is a record.
- **scheduled loop + cooldown** — `with-amendment:G-13` — NO @tasks.loop and NO @commands.cooldown (verified absent). The frequency brake is ENERGY: idle-accrual regen-on-read + DIG_COST gate — the cooldown-analog. G-13 IdleAccrualSpec expresses it; G-4 cooldown is NOT needed for mining.
- **irreversible economy op** — `with-amendment:G-7` — sell/buy/repair/vault-upgrade/build spend or credit coins through economy_service.debit/credit_in_txn (audited, EVT_BALANCE_CHANGED after commit). Reversibility = audit trail, not escrow. G-7 EconomyTransactionSpec.
- **stateful game loop** — `yes` — MineGridView is an in-place re-rendering roam loop (BaseView, 120s timeout). Expressible as PanelSpec + renderer_override (tier-3 board) with G-10-declared state — same shape as blackjack.board.
- **wait_for wizard** — `yes` — NO raw discord wait_for. Multi-step flows use cascading dependent Selects (Category→Type→Variant in market+recipes) and Modals (build, vault move, loadout save). SelectorSpec+modal cover them, though dependent-select chaining (Type options depend on Category pick) is a mild SelectorSpec ergonomics gap worth noting.
- **crafting recipe transform** — `with-amendment:G-12` — recipes.json inputs→outputs, forge-tier-gated, shared by !build, _BuildModal, recipe browser, cook (fish→food), quickcraft. G-12 CraftingRecipeSpec as data.

**MAP → RECONSIDER → SIMULATE → OPTIMIZE**

- **Verdict:** redesign · **status:** owner-gated
- **Optimal new-bot form:** One declarative mining SubsystemManifest whose CONFIG/READ/NAV/STORE/HELP surface (~2/3 of units) generates for free, and whose deep-sim core sits on a small stack of new Lane-B primitive families (G-7 EconomyTransaction, G-8 InventoryItem, G-9 Progression, G-10 GameState/World, G-11 Shop, G-12 Recipe, G-13 IdleAccrual, G-14 LootTable). What legitimately stays tier-3 code, exactly as blackjack does: the procedural world generator, the loot roll orchestration, the dig move-resolver (game loop), and the paper-doll/board renderers.
- **Dependency layer:** L1 currency kernel (economy G-7) → L2 item store + shop + recipe (G-8/G-11/G-12) → L3 progression + idle-accrual (G-9/G-13) → L4 persistent world + loot (G-10/G-14) → L5 mining game loop (grid board renderer + dig/mine/explore engines) built on L1-L4. Mining is the DEEPEST Lane-B consumer — it exercises every proposed family, so it should be the last subsystem ported and the acceptance test for the whole Lane-B primitive stack.
- **Production-grade done:** Production-grade = a golden-parity port where: (1) all 37 command surfaces + 17 panels behave byte-identically to the characterization tests (test_mining_workflow_characterization); (2) every multi-write op stays in one transaction with the same rollback semantics (test_mining_write_boundary AST ratchet still passes); (3) the shared seed-deterministic world produces identical grids per seed across servers (Q-0173); (4) economy legs remain audited and emit EVT_BALANCE_CHANGED after-commit; (5) energy idle-accrual and gear-wear break-cascade reproduce exactly.
- **Outperform target:** IdleRPG/OwO-class economy-sim bots and Minecraft-style mining bots — beat them on the shared seed-deterministic roam-and-dig world (dig-moves-you locomotion + fog-of-war is distinctive) and on transactional integrity (no lost-item/double-spend windows). Confirm the specific best-in-class comparator pending Lane F.

**Cross-lane dependencies**

- economy (Lane B) — HARD dependency: all coin movement via economy_service.debit_in_txn/credit_in_txn, EVT_BALANCE_CHANGED, economy audit log; mining owns NO coin table (registry dependencies=['economy'])
- inventory (Lane B) — !mineinv delegates to !inventory; unified inventory hub shares item display
- xp/progression (Lane B) — game_xp_service (GAME_MINING/GAME_CRAFTING) and skill_service are shared; player_skills table is shared/mining-consumed
- fishing (Lane B) — utils.mining.structures is SHARED (tide_pool/dock/boathouse/fishery build bonuses live in mining_workflow._build_success_suffix); cook consumes fish (items.is_fish); shared item catalog
- explore / world hub (navigation) — the hub 🗺️ Explore button forwards to views.explore.world_hub (federated 'town square', re-parented out of mining); cross-subsystem nav via attach_back_button
- governance/audit (cross-lane) — economy audit seam (RS01/RS02) is the write-boundary contract mining must preserve

**⚠ Unverified / judgment calls**

- workshop_panel.py repair/craft select internals read via grep only (class _RepairSelect at :97) — assumed they route to mining_workflow.repair/craft like the market/recipe selects do
- recipe_browser _VariantSelect craft routing confirmed by grep/docstring ('workshop-panel craft idiom'), not read line-by-line
- game_xp_service.award curve internals read at signature level only (:148) — XP formula/thresholds not inspected; ProgressionSpec (G-9) mapping assumes a standard level curve
- render_gear_doll / build_character_doll Pillow internals not read — classified tier-3 renderer by role (image compositing), not by reading the composition code
- utils.mining.grid.cell_at / rewards.roll_mine_loot / energy.settle module bodies not opened — engine tiers inferred from call-sites in mining_workflow.py and docstrings
- store table definitions inferred from utils/db/games/*.py function bodies (get_energy/mark_discovered/etc.), not from the migration SQL files; mining_discovered and energy columns confirmed via mining_grid.py:113 and mining_player_state.py:187
- no mining leaderboard command found (no !minetop) — assumed absent; max_depth record exists but is not surfaced as a LeaderboardSpec board
- navigation-button unit count (×15 hub/sub-hub + ×12 back buttons) estimated from the grep of @discord.ui.button across views/mining — exact per-panel back-button total approximated at 12

---

### fishing
_cogs/source: disbot/cogs/fishing_cog.py · services/fishing_workflow.py · utils/fishing/* · views/fishing/* · migrations 075/087/088/091/094_

| Unit | Kind | File:line | Tier (as-written) | Tier (with amendments) | Rationale / gap |
|---|---|---|---|---|---|
| !fish (cast minigame launch) | command | disbot/cogs/fishing_cog.py:76 | 3 | 3 | launches the timed cast view via prepare_cast→begin_cast: energy gate + level-gated catch roll + spawn background bite task. Session-launch handler like blackjack.start (3/3). |
| !fishing (fishmenu) | command | disbot/cogs/fishing_cog.py:86 | 1 | 1 | opens the FishingMenuView nav/hub panel — kernel open-panel workflow. |
| !forecast | command | disbot/cogs/fishing_cog.py:97 | 2 | 2 | read-model over the date-seeded weather provider (get_forecast). |
| !sail (setsail) | command | disbot/cogs/fishing_cog.py:116 | 3 | 2 | toggle_venue (workflow:580) — per-player enum state flip + domain copy. G-10 persistent player-state with declared toggle (scope_default already exists on SettingSpec). |
| !fishlog (fishdex) | command | disbot/cogs/fishing_cog.py:131 | 2 | 2 | read provider: catch log + trophy records + level, rendered to embed. |
| !fishtop (topfishers) | command | disbot/cogs/fishing_cog.py:145 | 2 | 2 | routes to db.top_fishers leaderboard read (LeaderboardSpec). |
| !trophies (bigfish) | command | disbot/cogs/fishing_cog.py:172 | 2 | 2 | routes to db.top_trophies (heaviest-catch) leaderboard read. |
| !rod (rodshop) | command | disbot/cogs/fishing_cog.py:196 | 1 | 1 | opens RodShopView panel — panel-open workflow. |
| !bait (baitshop) | command | disbot/cogs/fishing_cog.py:207 | 1 | 1 | opens BaitShopView panel — panel-open workflow. |
| !craftbait | command | disbot/cogs/fishing_cog.py:221 | 3 | 2 | craft_bait (workflow:826): fish→bait inventory transform in a txn. G-12 CraftingRecipeSpec makes the recipe+consume/grant declared data. |
| !craftcharm | command | disbot/cogs/fishing_cog.py:245 | 3 | 2 | craft_charm (workflow:1037): fish→charm transform. G-12. |
| !craftrod | command | disbot/cogs/fishing_cog.py:271 | 3 | 2 | craft_rod (workflow:1101): fish→next-rod-tier transform. G-12. |
| !rodrecipes | command | disbot/cogs/fishing_cog.py:282 | 2 | 2 | opens the recipe-progress read-model panel (RodRecipeBrowserView). |
| !craftpearl | command | disbot/cogs/fishing_cog.py:288 | 3 | 2 | craft_pearl_bait (workflow:885): pearl→premium-bait transform. G-12. |
| !curios | command | disbot/cogs/fishing_cog.py:318 | 2 | 2 | read-model: coral count + curio collection progress over the curio catalog. |
| !tidepool (reef) | command | disbot/cogs/fishing_cog.py:349 | 1 | 1 | opens TidePoolView build panel — panel-open workflow. |
| !dock (pier) | command | disbot/cogs/fishing_cog.py:361 | 1 | 1 | opens DockView build panel — panel-open workflow. |
| !boathouse (boat) | command | disbot/cogs/fishing_cog.py:373 | 1 | 1 | opens BoathouseView build panel — panel-open workflow. |
| !fishery (hatchery) | command | disbot/cogs/fishing_cog.py:385 | 1 | 1 | opens FisheryView build panel — panel-open workflow. |
| !craftcurio (carve) | command | disbot/cogs/fishing_cog.py:398 | 3 | 2 | craft_curio (workflow:960): coral→cosmetic-curio transform. G-12. |
| help entry / build_help_menu_view | help | disbot/cogs/fishing_cog.py:423 | 1 | 1 | help-as-projection; the hook returns the live FishingMenuView (nav). |
| FishingMenuView (nav hub panel) | panel | disbot/views/fishing/menu.py:203 | 1 | 1 | author-restricted HubView; kernel-generated nav shell (Cast/Sail/Rod/Bait/Structures/Fishdex/How-to). |
| menu: Cast action | panel-action | disbot/views/fishing/menu.py:219 | 3 | 3 | launches the cast minigame in place (same begin_cast+roll+spawn as !fish). Game launch (escape hatch). |
| menu: Set sail action | panel-action | disbot/views/fishing/menu.py:242 | 3 | 2 | toggle_venue + re-render. Same venue-state flip as !sail. G-10. |
| menu: Rod action | panel-action | disbot/views/fishing/menu.py:254 | 1 | 1 | nav to rod shop panel. |
| menu: Bait action | panel-action | disbot/views/fishing/menu.py:270 | 1 | 1 | nav to bait shop panel. |
| menu: Structures action | panel-action | disbot/views/fishing/menu.py:287 | 1 | 1 | nav to structures sub-hub. |
| menu: Fishdex action | panel-action | disbot/views/fishing/menu.py:310 | 2 | 2 | re-render with fishdex read-model (_fishdex_embed). |
| menu: How to fish action | panel-action | disbot/views/fishing/menu.py:324 | 1 | 1 | ephemeral static how-to card — help projection. |
| cast board renderer (bite/fight state) | renderer | disbot/views/fishing/cast_view.py:142 | 3 | 3 | renderer_override — stateful timed game board (in-memory active_casts, background tasks, tension bar). Escape hatch by design (§2.9). |
| cast: Reel action (bite/fight/grace/escape) | panel-action | disbot/views/fishing/cast_view.py:273 | 3 | 3 | game-move handler: premature-grace, in-time check, trophy fight taps, snap-free escape. Escape hatch. |
| minigame timing engine | engine | disbot/views/fishing/cast_view.py:202 (utils/fishing/minigame.py) | 3 | 3 | roll_bite_delay/roll_fakeout/roll_escape/is_trophy/reel_fight_taps — pure game rules. Escape hatch (grammar must never express game rules). |
| commit_catch (audited multi-write) | mutation | disbot/services/fishing_workflow.py:176 | 3 | 3 | one txn: record_catch(log+best_weight)+3× update_mining_item(pearl/coral/fish)+game_xp award, post-commit event. Reward RNG (bonus/pearl/coral) is domain. Escape hatch; G-7/G-10 could own the atomicity but rolls stay code. |
| catch roll engine (level-gated + rewards) | engine | disbot/services/fishing_workflow.py:129 (utils/fishing roll_catch/rewards) | 3 | 3 | roll_catch (band gate + rarity pull) + roll_bonus/pearl/coral. Pure game rules. Escape hatch. |
| _FishingDoneView (terminal nav panel) | panel | disbot/views/fishing/cast_view.py:545 | 1 | 1 | HubView continuation — auto Help/Games nav; kernel shell. |
| done: Cast again action | panel-action | disbot/views/fishing/cast_view.py:562 | 3 | 3 | re-runs prepare_cast — a game launch. Escape hatch. |
| RodShopView (shop read-model panel) | panel | disbot/views/fishing/rod_shop.py:89 | 2 | 2 | read-model of rod ladder + balance; G-11 ShopSpec would make body declarative. |
| rod shop: Upgrade action | panel-action | disbot/views/fishing/rod_shop.py:119 | 3 | 2 | buy_rod (workflow:607): audited coin debit + tier raise + EVT_BALANCE. G-7 EconomyTransactionSpec / G-11 ShopSpec declared buy. |
| rod shop: Craft-from-fish action | panel-action | disbot/views/fishing/rod_shop.py:130 | 3 | 2 | craft_rod. G-12. |
| rod shop: Recipes action | panel-action | disbot/views/fishing/rod_shop.py:141 | 1 | 1 | nav to recipe browser. |
| rod shop: Back action | panel-action | disbot/views/fishing/rod_shop.py:157 | 1 | 1 | nav back to fishing menu. |
| BaitShopView (shop read-model panel) | panel | disbot/views/fishing/bait_shop.py:209 | 2 | 2 | read-model of bait shelf/craftables/pearl-craftables + balance; G-11 ShopSpec. |
| bait shop: Buy-bait select | selector | disbot/views/fishing/bait_shop.py:123 | 3 | 2 | buy_bait (workflow:677): audited coin debit + load/stack charges + event. G-7/G-11. |
| bait shop: Craft-from-fish select | selector | disbot/views/fishing/bait_shop.py:160 | 3 | 2 | craft_bait. G-12. |
| bait shop: Craft-from-pearls select | selector | disbot/views/fishing/bait_shop.py:197 | 3 | 2 | craft_pearl_bait. G-12 (rare-material recipe). |
| bait shop: Back action | panel-action | disbot/views/fishing/bait_shop.py:240 | 1 | 1 | nav back to fishing menu. |
| RodRecipeBrowserView (read-model panel) | panel | disbot/views/fishing/rod_recipe_browser.py:104 | 2 | 2 | read-model: per-tier live eligible-fish progress over recipes. |
| recipe browser: Craft-next action | panel-action | disbot/views/fishing/rod_recipe_browser.py:131 | 3 | 2 | craft_rod (same seam as rod shop craft). G-12. |
| recipe browser: Back action | panel-action | disbot/views/fishing/rod_recipe_browser.py:142 | 1 | 1 | nav to rod shop. |
| StructuresView (sub-hub read-model + nav) | panel | disbot/views/fishing/structures_hub.py:93 | 2 | 2 | read-model of the 4 structures' levels/bonuses; nav to each. |
| structures: Tide Pool nav | panel-action | disbot/views/fishing/structures_hub.py:102 | 1 | 1 | nav to structure panel. |
| structures: Dock nav | panel-action | disbot/views/fishing/structures_hub.py:121 | 1 | 1 | nav. |
| structures: Boathouse nav | panel-action | disbot/views/fishing/structures_hub.py:140 | 1 | 1 | nav. |
| structures: Fishery nav | panel-action | disbot/views/fishing/structures_hub.py:159 | 1 | 1 | nav. |
| structures: Back nav | panel-action | disbot/views/fishing/structures_hub.py:178 | 1 | 1 | nav back to menu. |
| TidePoolView (build read-model panel) | panel | disbot/views/fishing/tide_pool.py:84 | 2 | 2 | read-model: built level, bonus, next cost. |
| tide pool: Build action | panel-action | disbot/views/fishing/tide_pool.py:93 | 3 | 2 | mining_workflow.build_structure: audited coin+coral debit + level raise. G-7/G-11 (priced coral+coin sink). |
| tide pool: Back action | panel-action | disbot/views/fishing/tide_pool.py:114 | 1 | 1 | nav to structures hub. |
| DockView (build read-model panel) | panel | disbot/views/fishing/dock.py:80 | 2 | 2 | read-model build panel (identical shape to tide pool). |
| dock: Build action | panel-action | disbot/views/fishing/dock.py:97 | 3 | 2 | build_structure(DOCK): audited coin+coral sink. G-7/G-11. |
| dock: Back action | panel-action | disbot/views/fishing/dock.py:114 | 1 | 1 | nav. |
| BoathouseView (build read-model panel) | panel | disbot/views/fishing/boathouse.py:81 | 2 | 2 | read-model build panel. |
| boathouse: Build action | panel-action | disbot/views/fishing/boathouse.py:98 | 3 | 2 | build_structure(BOATHOUSE): audited coin+coral sink (raises energy regen). G-7/G-11. |
| boathouse: Back action | panel-action | disbot/views/fishing/boathouse.py:114 | 1 | 1 | nav. |
| FisheryView (build read-model panel) | panel | disbot/views/fishing/fishery.py:82 | 2 | 2 | read-model build panel. |
| fishery: Build action | panel-action | disbot/views/fishing/fishery.py:99 | 3 | 2 | build_structure(FISHERY): audited coin+coral sink (raises double-catch). G-7/G-11. |
| fishery: Back action | panel-action | disbot/views/fishing/fishery.py:114 | 1 | 1 | nav. |
| capability fishing.catch.fish | setting | disbot/utils/subsystem_registry.py:313 | 1 | 1 | capability declaration. |
| capability fishing.collection.view | setting | disbot/utils/subsystem_registry.py:314 | 1 | 1 | capability declaration. NOTE: fishing has NO db.get_setting keys, NO bindings, NO resources (hub-less v1). |
| EVT_BALANCE_CHANGED emit (rod purchase) | event | disbot/services/fishing_workflow.py:644 | 1 | 1 | reuses economy-owned event; emit lives inside the audited buy_rod seam — declaration. |
| EVT_BALANCE_CHANGED emit (bait purchase) | event | disbot/services/fishing_workflow.py:723 | 1 | 1 | emit inside buy_bait seam — declaration. |
| game_xp award events emit | event | disbot/services/fishing_workflow.py:265 | 1 | 1 | emit_award_events after commit — EventSpec/emit declaration. |
| fishing_catch_log store (dex + trophy records) | store | disbot/migrations/075_fishing_catch_log.sql:12 | 1 | 1 | StoreSpec ledger/aggregate; sole writer = commit_catch/record_catch; best_weight column IS the trophy record (one table, not two). |
| fishing_rod store | store | disbot/migrations/087_fishing_rod.sql:12 | 1 | 1 | StoreSpec aggregate (owned rod tier). |
| fishing_energy store (+idle regen) | store | disbot/migrations/088_fishing_energy.sql:14 | 1 | 1 | StoreSpec: energy value + last-settled ts; regen computed on read. |
| fishing_bait store | store | disbot/migrations/091_fishing_bait.sql:16 | 1 | 1 | StoreSpec: active bait key + charges. |
| fishing_venue store | store | disbot/migrations/094_fishing_venue.sql:12 | 1 | 1 | StoreSpec: current venue string. |
| mining_inventory (shared, fishing co-writes fish/pearl/coral/curio/charm) | store | disbot/services/fishing_workflow.py:228,250 | 1 | 1 | cross-subsystem StoreSpec: fishing is a co-writer of mining-owned inventory (legacy TEXT user_id). Sole-writer fence needs fishing as an authorized writer domain — ownership smell. |
| mining_structures (shared, fishing builds coral structures) | store | disbot/views/fishing/tide_pool.py:101 | 1 | 1 | cross-subsystem StoreSpec: coral structures live on the generic mining_structures table via mining_workflow.build_structure. |
| top_fishers leaderboard (total catches) | game | disbot/utils/db/games/fishing.py:101 | 2 | 2 | LeaderboardSpec: SUM(count) per user over current catalog. |
| top_trophies leaderboard (heaviest catch) | game | disbot/utils/db/games/fishing.py:124 | 2 | 2 | LeaderboardSpec: per-species best_weight hall of fame. |
| fishing level derivation (reuses game_xp) | progression | disbot/services/fishing_workflow.py:60 | 2 | 2 | fishing_level_from_xp = min(MAX_LEVEL, 1+level_index) over shared db.level_progress. G-9 ProgressionSpec (declared curve over game_xp). |
| energy idle-regen accrual (on-read settle) | accrual | disbot/services/fishing_workflow.py:351 | 3 | 2 | fish_energy.settle: time-based regen (Boathouse-adjusted interval) computed on read. G-13 IdleAccrualSpec makes the accrual declared data. |
| fish species catalog (21 species, size/venue/weight) | catalog | disbot/utils/fishing/fish.py (SPECIES) | 2 | 1 | item taxonomy dataset behind the roll engine. G-8 ItemCatalogSpec makes it declared item data (tier1). |
| rod ladder + recipes catalog | catalog | disbot/utils/fishing/rods.py (ROD_LADDER/ROD_RECIPES) | 2 | 1 | priced tier ladder + fish→rod recipes. G-11 ShopSpec + G-12 CraftingRecipeSpec as data. |
| bait catalog + recipes | catalog | disbot/utils/fishing/bait.py (BAIT_CATALOG/CRAFTABLE_KEYS/pearl_recipe) | 2 | 1 | priced/consumable item catalog + fish and pearl recipes. G-8/G-11/G-12. |
| curio + charm catalog | catalog | disbot/utils/fishing/curios.py + gear.py | 2 | 1 | cosmetic curio item catalog + charm recipes. G-8 (TREASURE items) + G-12. |
| weather conditions catalog (date-seeded) | catalog | disbot/utils/fishing/weather.py (CONDITIONS) | 2 | 2 | deterministic shared-per-day provider (rarity/bite multipliers). Read provider (data + pure derivation). |
| venue profiles catalog (shore/deepwater) | catalog | disbot/utils/fishing/venue.py (SHORE/DEEPWATER profiles) | 2 | 1 | per-venue bite band/window/escape data + species pool split. Declared data (G-10-adjacent). |

**Fit:** 89 units · tier-1/2 as-written **71%** (63/89) · with amendments **91%** (81/89).

**§2 manifest sketch**

```python
FISHING_MANIFEST = SubsystemManifest(
    key="fishing", display_name="Fishing", emoji="🎣", category="games",
    parent_hub="games", hub_group="activities", dependencies=(),   # soft: economy/xp/mining
    capabilities=("fishing.catch.fish", "fishing.collection.view"),

    commands=(
      # panel-open (tier1)
      CommandSpec("fishing", CommandKind.PREFIX, "Open the fishing menu",
                  PanelRef("fishing.menu"), aliases=("fishmenu",)),
      CommandSpec("rod", CommandKind.PREFIX, "Rod shop", PanelRef("fishing.rodshop"),
                  aliases=("rodshop","buyrod")),
      CommandSpec("bait", CommandKind.PREFIX, "Bait shop", PanelRef("fishing.baitshop"),
                  aliases=("baitshop","buybait")),
      CommandSpec("tidepool", CommandKind.PREFIX, "Tide Pool", PanelRef("fishing.tidepool")),
      CommandSpec("dock", CommandKind.PREFIX, "Dock", PanelRef("fishing.dock")),
      CommandSpec("boathouse", CommandKind.PREFIX, "Boathouse", PanelRef("fishing.boathouse")),
      CommandSpec("fishery", CommandKind.PREFIX, "Fishery", PanelRef("fishing.fishery")),
      # read-model (tier2)
      CommandSpec("forecast", CommandKind.PREFIX, "Today's forecast",
                  ProviderRef("fishing.weather"), aliases=("fishforecast","fishingweather")),
      CommandSpec("fishlog", CommandKind.PREFIX, "Your dex",
                  ProviderRef("fishing.dex"), aliases=("fishdex",)),
      CommandSpec("curios", CommandKind.PREFIX, "Curio collection",
                  ProviderRef("fishing.curios"), aliases=("curio","carvings")),
      CommandSpec("rodrecipes", CommandKind.PREFIX, "Rod recipes",
                  PanelRef("fishing.rodrecipes"), aliases=("rodrecipe","rrecipes")),
      CommandSpec("fishtop", CommandKind.PREFIX, "Top anglers",
                  ProviderRef("fishing.board.catches"), aliases=("topfishers",)),
      CommandSpec("trophies", CommandKind.PREFIX, "Biggest catches",
                  ProviderRef("fishing.board.trophies"), aliases=("bigfish","fishtrophy")),
      # tier3 escape-hatch launches / mutations
      CommandSpec("fish", CommandKind.PREFIX, "Cast a line",
                  HandlerRef("fishing.cast_start", justification="energy gate + level-gated roll + spawn timed view")),
      CommandSpec("sail", CommandKind.PREFIX, "Set sail / dock",
                  HandlerRef("fishing.venue_toggle"), aliases=("setsail",)),    # G-10 target
      CommandSpec("craftbait", CommandKind.PREFIX, "Craft bait",
                  HandlerRef("fishing.craft_bait")),   # G-12
      CommandSpec("craftcharm", CommandKind.PREFIX, "Craft charm", HandlerRef("fishing.craft_charm")),  # G-12
      CommandSpec("craftrod", CommandKind.PREFIX, "Craft rod", HandlerRef("fishing.craft_rod")),        # G-12
      CommandSpec("craftpearl", CommandKind.PREFIX, "Craft pearl bait", HandlerRef("fishing.craft_pearl")),  # G-12
      CommandSpec("craftcurio", CommandKind.PREFIX, "Carve curio", HandlerRef("fishing.craft_curio")),  # G-12
    ),

    panels=(
      # nav hub — actions are workflows(nav)/handlers(cast,sail)
      PanelSpec("fishing.menu", "fishing", "🎣 Fishing", actions=(
        PanelActionSpec("cast", "Cast", HandlerRef("fishing.cast_start")),        # tier3
        PanelActionSpec("sail", "Set sail", HandlerRef("fishing.venue_toggle")),  # G-10
        PanelActionSpec("rod", "Rod", PanelRef("fishing.rodshop")),
        PanelActionSpec("bait", "Bait", PanelRef("fishing.baitshop")),
        PanelActionSpec("structures", "Structures", PanelRef("fishing.structures")),
        PanelActionSpec("fishdex", "Fishdex", ProviderRef("fishing.dex")),
        PanelActionSpec("howto", "How to fish", WorkflowRef("show_help")),
      )),
      # THE GAME BOARD — renderer_override + game move (tier3 by design)
      PanelSpec("fishing.cast", "fishing", "🎣 Cast",
        renderer_override=HandlerRef("fishing.render_cast", justification="timed bite/reel/fight board"),
        actions=(PanelActionSpec("reel", "Reel", HandlerRef("fishing.reel",
                 justification="bite/grace/fight-tap/escape resolution")),)),
      # shops (read-model bodies; G-11 ShopSpec would generate the buy legs)
      PanelSpec("fishing.rodshop", "fishing", "Rod shop", body=(BlockSpec("fields", ProviderRef("fishing.rod")),),
        actions=(PanelActionSpec("upgrade","Upgrade",HandlerRef("fishing.buy_rod"), audit="fishing:rod_purchase"),  # G-7/G-11
                 PanelActionSpec("craft","Craft",HandlerRef("fishing.craft_rod")),   # G-12
                 PanelActionSpec("recipes","Recipes",PanelRef("fishing.rodrecipes")))),
      PanelSpec("fishing.baitshop", "fishing", "Bait shop", body=(BlockSpec("fields", ProviderRef("fishing.bait")),),
        selectors=(SelectorSpec("buy","enum",HandlerRef("fishing.buy_bait")),      # G-7/G-11
                   SelectorSpec("craftfish","enum",HandlerRef("fishing.craft_bait")),   # G-12
                   SelectorSpec("craftpearl","enum",HandlerRef("fishing.craft_pearl")))),  # G-12
      PanelSpec("fishing.rodrecipes","fishing","📋 Rod Recipes", body=(BlockSpec("table",ProviderRef("fishing.rod_progress")),),
        actions=(PanelActionSpec("craftnext","Craft next",HandlerRef("fishing.craft_rod")),)),   # G-12
      # structures sub-hub + 4 build panels (each build = G-7/G-11 coin+coral sink)
      PanelSpec("fishing.structures","fishing","🏗 Structures", body=(BlockSpec("fields",ProviderRef("fishing.structures")),),
        actions=(PanelActionSpec("tidepool","Tide Pool",PanelRef("fishing.tidepool")),
                 PanelActionSpec("dock","Dock",PanelRef("fishing.dock")),
                 PanelActionSpec("boathouse","Boathouse",PanelRef("fishing.boathouse")),
                 PanelActionSpec("fishery","Fishery",PanelRef("fishing.fishery")))),
      *[PanelSpec(f"fishing.{s}","fishing",s.title(), body=(BlockSpec("fields",ProviderRef(f"fishing.{s}")),),
          actions=(PanelActionSpec("build","Build",HandlerRef("fishing.build_structure"),  # G-7/G-11
                   audit=f"fishing:build_{s}"),)) for s in ("tidepool","dock","boathouse","fishery")],
    ),

    stores=(
      StoreSpec("fishing_catch_log", sole_writer="fishing.commit_catch", checkpoint_class="aggregate"),  # dex+best_weight
      StoreSpec("fishing_rod", "fishing.rod_writer", "aggregate"),
      StoreSpec("fishing_energy", "fishing.energy_writer", "aggregate"),   # + G-13 IdleAccrualSpec(regen)
      StoreSpec("fishing_bait", "fishing.bait_writer", "aggregate"),
      StoreSpec("fishing_venue", "fishing.venue_writer", "aggregate"),
      # shared (mining-owned) — fishing declared as an authorized writer domain:
      StoreSpec("mining_inventory", "mining.inventory", "aggregate", reader_domains=("fishing",)),   # G-8 items live here
      StoreSpec("mining_structures", "mining.structures", "aggregate", reader_domains=("fishing",)),
    ),

    events=(EventSpec("economy.balance_changed", (...), owner_subsystem="economy"),),  # reused; emitted in buy_rod/buy_bait
    game=GameFacet(leaderboards=(
      LeaderboardSpec("fishing.catches","fishing.catches","sum"),
      LeaderboardSpec("fishing.trophies","fishing.best_weight","max"))),
    # PROPOSED NEW FAMILIES referenced above: G-7 EconomyTransactionSpec, G-8 ItemCatalogSpec,
    # G-9 ProgressionSpec, G-10 player-state/GameStateSpec, G-11 ShopSpec, G-12 CraftingRecipeSpec,
    # G-13 IdleAccrualSpec. Irreducible tier-3 stays in a fishing engine module (roll/minigame/reel/commit).
    help=HelpEntrySpec("Cast a line, reel it in, level up, and build your collection.",
                       examples=("!fish","!sail","!rod","!fishlog")),
)
```

**Tier-3 dispositions**

| Tier-3 unit | Verdict | Reason |
|---|---|---|
| !fish (cast launch) | escape-hatch | session/game-launch handler (energy gate + catch roll + spawn timed view); thin domain, kernel should not own the roll — like blackjack.start. |
| menu: Cast action | escape-hatch | same game launch as !fish, in-panel. |
| done: Cast again action | escape-hatch | re-enters the cast launch flow. |
| cast board renderer | escape-hatch | renderer_override — stateful timed board; §2.9 named escape-hatch class. |
| cast: Reel action | escape-hatch | game-move handler (bite/grace/fight/escape); grammar must not express game moves. |
| minigame timing engine | escape-hatch | pure game rules (bite delay/fakeout/trophy/escape) — must stay code (§10.1 risk 5). |
| catch roll engine | escape-hatch | level-gated catch RNG + reward rolls — game rules. |
| commit_catch (audited multi-write) | escape-hatch | reward RNG (bonus/pearl/coral) + xp award are domain; the atomic write is G-7/G-10-shaped but the rolls keep it tier-3. Legit thin seam. |
| !sail + menu: Set sail | grammar-gap:G-10 | per-player venue enum flip; a scope=user enum SettingSpec + declared toggle workflow (scope_default already exists) closes it. |
| !craftbait / bait shop craft-fish select | grammar-gap:G-12 | fish→bait recipe transform; CraftingRecipeSpec makes inputs→outputs declared data (smallest-first spend = shared kernel policy). |
| !craftcharm | grammar-gap:G-12 | fish→charm recipe. |
| !craftrod / rod shop craft / recipe browser craft-next | grammar-gap:G-12 | fish→next-rod-tier recipe (crafts tier above owned). |
| !craftpearl / bait shop craft-pearl select | grammar-gap:G-12 | pearl→premium-bait recipe (rare-material input). |
| !craftcurio | grammar-gap:G-12 | coral→cosmetic-curio recipe. |
| rod shop: Upgrade (buy_rod) | grammar-gap:G-7/G-11 | audited coin debit + tier raise + EVT_BALANCE — declarable as ShopSpec buy over EconomyTransactionSpec. |
| bait shop: Buy-bait select (buy_bait) | grammar-gap:G-7/G-11 | audited coin debit + charge load/stack + event. |
| tide pool / dock / boathouse / fishery Build (build_structure ×4) | grammar-gap:G-7/G-11 | audited coin+coral debit + level raise; priced dual-currency sink = ShopSpec/EconomyTransactionSpec. |
| energy idle-regen accrual | grammar-gap:G-13 | time-based on-read regen (Boathouse-adjusted interval) = IdleAccrualSpec declared data. |

**Structural-gap flags**

- **stateful game loop / wait_for-ish minigame** — `needs-new-primitive` — cast→bite→reel→fight is an in-memory, background-task-armed timed button loop (active_casts set, _round_id staleness token, ADR-002 non-restart-safe). Stays tier-3 renderer_override + engine BY DESIGN; the grammar correctly must not express game rules. Kernel owns only the launch surface + auth/audit shell.
- **transactional multi-write mutation** — `with-amendment:G-7` — commit_catch = catch-log + best_weight + 3× inventory grants + game_xp in ONE txn; buy_rod/buy_bait/build_structure = debit+state+event. EconomyTransactionSpec declares the atomicity; reward RNG in commit_catch still keeps that one unit tier-3.
- **deep persistent per-player state** — `with-amendment:G-10` — 5 owned tables (rod/energy/bait/venue/catch_log) + shared structures + inventory. StoreSpec covers the fences; venue toggle + energy are player-state ops needing a declared state family.
- **inventory / item taxonomy** — `with-amendment:G-8` — 21 fish species + pearls + coral + curios + charms + rods + baits. Currently ALL piggyback the mining-owned mining_inventory (legacy TEXT user_id) — cross-subsystem ownership smell; ItemCatalogSpec + a proper item store would fix it.
- **idle accrual (energy regen)** — `with-amendment:G-13` — fish_energy.settle computes regen on read (no ticker, ADR-001/002), Boathouse-adjusted interval. IdleAccrualSpec makes the accrual declared data.
- **XP + leaderboard derivation** — `with-amendment:G-9` — fishing_level_from_xp derives level from shared game_xp; top_fishers/top_trophies are LeaderboardSpec-shaped (already in grammar). ProgressionSpec would declare the level curve.
- **priced shop / market (buy + craft dual sourcing)** — `with-amendment:G-11+G-12` — rod & bait shops each expose coin-buy AND fish/pearl-craft paths to the same item; ShopSpec (currency in/out) + CraftingRecipeSpec (inputs→outputs) together make the whole shelf declarative.
- **irreversible economy op** — `with-amendment:G-7` — rod/bait/structure purchases spend coins irreversibly; the audited debit_in_txn + settle-once is the EconomyTransactionSpec target.
- **escrow / double-settle risk** — `yes` — LOW risk — no held bet; energy+bait spent per attempt, catch committed once on a landed reel. The per-attempt-spend/commit-on-success is a mild settle pattern, not double-settle-prone; StoreSpec sole-writer fence suffices.
- **scheduled loop + cooldown** — `yes` — NONE present — no @tasks.loop, no @commands.cooldown (energy bar is the throttle). Cast timing uses per-cast ephemeral tasks.spawn inside the engine, not a ManagedTaskSpec. No G-4 needed for fishing.
- **gateway listener** — `yes` — NONE — no @bot.event/@commands.Cog.listener/bus.on in fishing. Only bus.emit (economy event) + a structural guild-only cog_check. No G-1 needed.

**MAP → RECONSIDER → SIMULATE → OPTIMIZE**

- **Verdict:** keep · **status:** owner-gated — fish COIN VALUE is an explicit OPEN owner question (Q-0175): v1 pays no coins, so the sell/market leg and any G-11 sell workflow await that decision. G-7/G-8/G-11 are new primitive families (owner-gated per the friction→guard split); the fishing surface itself is complete and sound as shipped.
- **Optimal new-bot form:** Rebuild fishing as ONE SubsystemManifest = a fully-declared shell (7 panel-open commands, 6 read-model/leaderboard reads, 5 owned StoreSpecs + 2 shared, capabilities, reused economy/xp events, nav) PLUS a small irreducible tier-3 fishing engine module (level-gated catch roll, the reel/bite/fight minigame, and the commit_catch reward-roll seam). Everything between the shell and the engine — venue toggle, all 6 craft paths, 3 shops, 4 structure builds, energy regen — collapses into declared data once the Lane-B economy primitives (G-7/G-8/G-9/G-10/G-11/G-12/G-13) land.
- **Dependency layer:** L3 game — sits on L1 currency kernel (G-7 EconomyTransaction over economy_service debit), L2 item/shop/craft store (G-8 items + G-11 shops + G-12 recipes), shared game_xp (G-9) and mining_structures/mining_workflow (mining L2). Build order: currency+item store → shop/craft primitives → fishing manifest + engine last.
- **Production-grade done:** Parity golden: (1) a landed cast writes byte-identical fishing_catch_log (count/best_weight), mining_inventory (fish+bonus+pearl+coral grants), and game_xp rows in one txn, with post-commit events matching; (2) buy_rod/buy_bait/build_structure produce identical debit+audit+EVT_BALANCE_CHANGED and insufficient-funds rollback; (3) top_fishers/top_trophies and fishdex read identical; (4) energy regen settles identically on read; (5) minigame outcome distribution matches the sim under a seeded rng.
- **Outperform target:** pending Lane F — the reference is a dedicated fishing bot (e.g. Virtual Fisher class). Beat it on depth-per-declaration: shared date-seeded weather (a reason to fish today), a skill reel-fight minigame, and a coral-structure economy that ties fishing into the wider mining/character sim — all generated from one manifest rather than a bespoke cog.

**Cross-lane dependencies**

- economy (Lane B): coin debits via economy_service.debit_in_txn + EVT_BALANCE_CHANGED for buy_rod/buy_bait/build — fishing is a coin sink; G-7 EconomyTransactionSpec is the shared primitive.
- inventory/mining (Lane B): fish species, bonus catches, pearls, coral, curios, and charms ALL stored in the mining-owned mining_inventory (legacy TEXT user_id, cast via str(user_id)); G-8 ItemCatalogSpec + a shared item store is a Lane-B convergence point.
- mining (Lane B): coral structures (Tide Pool/Dock/Boathouse/Fishery) live on mining_structures and build through mining_workflow.build_structure — fishing reuses mining's build seam and structure catalog.
- mining/character (Lane B): equipped fishing charms fold into the cast via character.character_stats over mining equipment+skills (fishing_gear.fishing_pull_mult / bite_speed_mult).
- xp (Lane B): fishing level derives from shared game_xp (game_xp_service.GAME_FISHING, db.level_progress); award happens inside commit_catch — G-9 ProgressionSpec + the shared game_xp store.
- cross-lane store-ownership note: fishing WRITES two mining-owned tables — the StoreSpec sole-writer fence must name fishing as an authorized writer domain, or the ownership model breaks.

**⚠ Unverified / judgment calls**

- dock.py / boathouse.py / fishery.py back-button + panel bodies read only via grep (build_structure + build_*_embed pattern confirmed identical to tide_pool.py); back_btn line numbers (dock:114/boathouse:114/fishery:114) inferred from the shared HubView shape, not line-read.
- utils/fishing internals (fish.py roll_catch, minigame.py, rewards.py, rods.py, bait.py, curios.py, gear.py, weather.py, venue.py, energy.py) classified as tier-3 engines / tier-2 catalogs from their confirmed call sites in the workflow + views, not from full module reads; catalog sizes (21 fish, rod ladder length, bait shelf size) taken from cog docstring/usage, not from fish.json or the catalog constants directly.
- fishing_level_from_xp tier (2/2 vs a possible 3-as-written) is a judgment call — it is a thin cap over shared db.level_progress; treated as a read-model progression derivation.
- catalog units (fish/rod/bait/curio/weather/venue = 6 rows) are counted as contract-bearing surface; a stricter methodology that folds pure datasets into their engine would lower units_total by ~6 and nudge both fit percentages up slightly (fit is robust either way: ~71% as-written / ~91% amended).

---

### creature
_cogs/source: disbot/cogs/creature_cog.py + creature_battle_cog.py · services/creature_service.py + creature_battle_service.py · migrations 077/082 · views/creature*/*_

| Unit | Kind | File:line | Tier (as-written) | Tier (with amendments) | Rationale / gap |
|---|---|---|---|---|---|
| !catch (alias hunt) | command | disbot/cogs/creature_cog.py:58 → services/creature_workflow.py:60 | 3 | 2 | The catch seam: rarity-weighted encounter roll (encounters.roll_encounter) + probability catch roll (attempt_catch) + ONE atomic txn recording the collection-log row and awarding GAME_CREATURE xp (workflow.py:82-92). As-written a bespoke handler. Amended: the roll is declarable weighted-table DATA (RARITY_ENCOUNTER_WEIGHT/RARITY_CATCH_BASE/CATCH_BONUS_PER_LEVEL) → G-14 EncounterTableSpec, and the collection grant → G-8 collection store; the xp leg is the shared game_xp dep. |
| !creatures (creaturemenu, pets) | command | disbot/cogs/creature_cog.py:69 | 1 | 1 | Command → open CreatureMenuView hub panel. Pure kernel open-panel workflow (PanelRef route). |
| !dex (collection) | command | disbot/cogs/creature_cog.py:78 | 2 | 2 | Command → read-model: load_progress + build_dex_embed over the collection log. Read provider behind a fields projection. |
| !dextop (topcatchers) | command | disbot/cogs/creature_cog.py:85 → utils/db/games/creatures.py:59 | 2 | 2 | Command → top_collectors leaderboard read (SUM/COUNT, catalog-filtered). LeaderboardSpec over collection log. |
| !cbattle <opponent> (creaturebattle) | command | disbot/cogs/creature_battle_cog.py:72 | 3 | 2 | Opens the PvP challenge session (constructs CreatureBattleChallengeView after trivial no-bot/no-self guards). As-written a bespoke wait_for-style challenge open. Amended: command→session-open route onto the declared ChallengeSessionSpec (already in §2.8). |
| !cbrecord (battlerecord) | command | disbot/cogs/creature_battle_cog.py:89 → utils/db/games/creature_battles.py:53 | 2 | 2 | Command → read-model: get_battle_record → build_record_embed. Read provider (self or target member). |
| !cbattletop (pvptop, battletop) | command | disbot/cogs/creature_battle_cog.py:96 → utils/db/games/creature_battles.py:71 | 2 | 2 | Command → top_battlers leaderboard read (wins DESC, losses ASC). LeaderboardSpec over battle record. |
| CreatureMenuView (hub panel container) | panel | disbot/views/creature/menu.py:60 | 1 | 1 | Author-restricted HubView; declares SUBSYSTEM='creature' for auto Help/↩Games nav. Container is a declared hub panel; its actions classified separately. |
| Catch button (panel-action) | panel-action | disbot/views/creature/menu.py:69 | 3 | 2 | Runs creature_workflow.catch in place (same seam as !catch) then edit_message keeping the menu. Same G-14 + G-8 disposition as !catch. |
| Dex button (panel-action) | panel-action | disbot/views/creature/menu.py:80 | 1 | 1 | Navigation: opens CreatureDexView read-model browser. Kernel open/re-render workflow. |
| Challenge button (panel-action) | panel-action | disbot/views/creature/menu.py:92 | 1 | 1 | Navigation: opens CreatureChallengeSelectView opponent picker. Kernel nav workflow. |
| Ladder button (panel-action) | panel-action | disbot/views/creature/menu.py:115 | 2 | 2 | Reads top_battlers → build_battletop_embed in place. Read provider / LeaderboardSpec surface. |
| How-to-play button (panel-action) | panel-action | disbot/views/creature/menu.py:132 | 1 | 1 | Sends static build_rules_embed ephemerally. Help/rules projection (HelpEntrySpec rules_text). |
| CreatureDexView (read-model browser panel) | panel | disbot/views/creature/menu.py:184 | 2 | 2 | Filterable collection browser over the log. Read-model panel (FieldsBlock per-element over a ProviderRef). |
| _ElementFilterSelect (selector) | selector | disbot/views/creature/menu.py:148 | 2 | 2 | Element-filter select that re-renders the dex embed. SelectorSpec (enum kind) → read provider; options from catalog ELEMENTS. |
| CreatureDexView Back button | panel-action | disbot/views/creature/menu.py:199 | 1 | 1 | Navigation back to the menu (open_creature_menu). Kernel nav workflow. |
| CreatureChallengeSelectView (opponent-picker panel) | panel | disbot/views/creature/menu.py:213 | 1 | 1 | Container panel hosting a UserSelect + Back. Declared nav panel. |
| _OpponentSelect (UserSelect selector) | selector | disbot/views/creature/menu.py:237 | 3 | 2 | On select: validates opponent (member/bot/self) then constructs CreatureBattleChallengeView (opens the PvP session). As-written bespoke; amended a member SelectorSpec whose on_select opens the declared ChallengeSessionSpec. |
| CreatureChallengeSelectView Back button | panel-action | disbot/views/creature/menu.py:223 | 1 | 1 | Navigation back to the menu. Kernel nav workflow. |
| CreatureBattleChallengeView PvP session lifecycle | session | disbot/views/creature_battle/challenge.py:30 (accept:55 decline:101 on_timeout:118) | 2 | 2 | Accept/Decline + settle-once (SettleOnceMixin.claim_settlement) + 60s accept timeout + _resolved race guard + on_timeout expiry copy + W/L stat_writes on settle. Exactly ChallengeSessionSpec (accept_timeout_s, settle_once=True, stat_writes, no escrow — coin-free PvP). Session choreography leaves the domain. |
| CreatureRematchView (two-participant rematch) | session | disbot/views/creature_battle/rematch.py:28 | 2 | 2 | Rematch button re-issues a fresh challenge; specialized interaction_check widens auth to BOTH fighters. No new battle logic (reuses the challenge flow). ChallengeSessionSpec rematch-reissue choreography with a dual-participant auth predicate. |
| Battle engine (type chart, stat derivation, moves, policies, resolve_battle) | engine | disbot/utils/creatures/battle.py:73,134,190,296-340,402 | 3 | 3 | Pure combat rules: element cycle effectiveness (1.5/0.67), rarity-budget×archetype stat derivation, 4-move set, 4 move-selection policies, 6v6 lead-until-faint turn resolution with SPD ordering + stall guard, NORMALIZED_LEVEL anti-P2W. Game rules — tier-3 BY DESIGN; the grammar must never express them (§10.1 risk 5). |
| build_result_embed (battle outcome renderer_override) | renderer | disbot/views/creature_battle/render.py:63 | 3 | 3 | Bespoke turn-by-turn presentation: per-side roster with 💀 fainted markers, KO-highlight log capped at 12, updated W/L records field, winner + xp_note. renderer_override — §2.9's NAMED escape-hatch class, by design. |
| creature_collection_log table (per user/guild/creature tally) | store | disbot/migrations/077_creature_collection_log.sql:1 → utils/db/games/creatures.py:32 | 1 | 1 | StoreSpec: sole_writer=creature_workflow (conn-aware upsert), aggregate class, additive-safe (empty = pre-creature bot). Generated sole-writer fence. |
| creature_battle_record table (per user/guild W/L tally) | store | disbot/migrations/082_creature_battle_record.sql:1 → utils/db/games/creature_battles.py:37 | 1 | 1 | StoreSpec: sole_writer=creature_battle_service (conn-aware dual upsert), aggregate class, additive-safe. Generated sole-writer fence. |
| Creature help entry (Help-menu hook → live panel) | help | disbot/cogs/creature_cog.py:98 + creature_battle_cog.py:50 | 1 | 1 | Both cogs' build_help_menu_view return the same live CreatureMenuView so Games-hub → Creatures lands on a playable panel (completion cert Q-0209). HelpEntrySpec + panel route — help-as-projection. |
| Creature capabilities (creature.catch.creature, creature.collection.view) | capability | disbot/utils/subsystem_registry.py:352 | 1 | 1 | Two declared capability strings + registry entry (parent_hub=games, hub_group=activities, ui_priority=22, no hard deps). Pure declarations in the manifest capabilities tuple. No discrete settings_keys / get_setting / cooldowns exist for this subsystem (verified). |
| game_xp earn integration (catch +4, battle_win +6, level nudges catch odds) | progression | services/creature_workflow.py:84 + creature_battle_service.py:173 + game_xp_service.py:28-29,74 | 3 | 2 | Two registered award() calls into the shared GAME_CREATURE xp track inside the catch/battle txns; creature_level_from_xp derives level and encounters.catch_chance grants a bounded per-level catch bonus. As-written bespoke earn code; amended G-9 ProgressionSpec declares the earn actions. Cross-lane dep on the xp subsystem (game_xp.awarded/level_up events are xp-owned, not creature-owned). |

**Fit:** 28 units · tier-1/2 as-written **75%** (21/28) · with amendments **93%** (26/28).

**§2 manifest sketch**

```python
CREATURE = SubsystemManifest(
    key="creature", display_name="Creatures", emoji="🐾",
    category="games", parent_hub="games", hub_group="activities", ui_priority=22,
    capabilities=("creature.catch.creature", "creature.collection.view"),
    dependencies=(),  # coin-free by design: no economy dep (registry:343)
    commands=(
        CommandSpec("catch", PREFIX, "Catch a wild creature",
            route=HandlerRef("creature.catch", "encounter+catch roll (G-14) + collection grant (G-8) + xp (G-9)"),
            aliases=("hunt",)),                                   # tier3→2
        CommandSpec("creatures", PREFIX, "Open the Creatures panel",
            route=PanelRef("creature.menu"), aliases=("creaturemenu","pets")),  # tier1
        CommandSpec("dex", PREFIX, "Your collection", route=ProviderRef("creature.dex"),
            aliases=("collection",)),                            # tier2
        CommandSpec("dextop", PREFIX, "Top collectors", route=ProviderRef("creature.board.collectors"),
            aliases=("topcatchers",)),                           # tier2 LeaderboardSpec
        CommandSpec("cbattle", PREFIX, "Challenge a trainer to PvP",
            route=WorkflowRef("challenge_open", (("session","creature.pvp"),)),
            aliases=("creaturebattle",)),                        # tier3→2 session-open
        CommandSpec("cbrecord", PREFIX, "Your battle record", route=ProviderRef("creature.record"),
            aliases=("battlerecord",)),                          # tier2
        CommandSpec("cbattletop", PREFIX, "Top trainers", route=ProviderRef("creature.board.battlers"),
            aliases=("pvptop","battletop")),                     # tier2 LeaderboardSpec
    ),
    panels=(
        PanelSpec("creature.menu", "creature", "Creatures", actions=(
            PanelActionSpec("catch", "Catch", HandlerRef("creature.catch")),        # tier3→2
            PanelActionSpec("dex", "Dex", PanelRef("creature.dex")),                 # tier1 nav
            PanelActionSpec("challenge", "Challenge", PanelRef("creature.opponent")),# tier1 nav
            PanelActionSpec("ladder", "Ladder", ProviderRef("creature.board.battlers")), # tier2
            PanelActionSpec("rules", "How to play", WorkflowRef("show_rules")),      # tier1
        )),
        PanelSpec("creature.dex", "creature", "Creature Dex",                        # tier2 read-model
            body=(BlockSpec("fields", ProviderRef("creature.dex")),),
            selectors=(SelectorSpec("element", "enum", ProviderRef("creature.dex"),
                options_source=("Ember","Tide","Bramble","Spark","Stone","Gust")),)),# tier2
        PanelSpec("creature.opponent", "creature", "Challenge a trainer",
            selectors=(SelectorSpec("opponent", "member",
                on_select=WorkflowRef("challenge_open", (("session","creature.pvp"),))),)), # tier3→2
        # PvP challenge accept/decline + settle-once + KO-log render:
        PanelSpec("creature.pvp.result", "creature", "Creature Battle",
            renderer_override=HandlerRef("creature.render_result", "bespoke KO-log — tier3 escape hatch")),
    ),
    game=GameFacet(
        sessions=(ChallengeSessionSpec(game_key="creature.pvp",
            accept_timeout_s=60, turn_timeout_s=0, stale_after_s=60,
            settle_once=True, persistence="ephemeral",  # auto-resolves in-memory; no mid-battle state persisted
            escrow=None,                                 # coin-free PvP
            stat_writes=("creature_battle_record.wins","creature_battle_record.losses"),
            refund_policy=None),),
        leaderboards=(
            LeaderboardSpec("creature.board.collectors", "collection_log.count", "sum"),
            LeaderboardSpec("creature.board.battlers", "battle_record.wins", "count"),
        ),
    ),
    stores=(
        StoreSpec("creature_collection_log", "creature.catch", "aggregate"),
        StoreSpec("creature_battle_record", "creature.pvp.settle", "aggregate"),
    ),
    # PROPOSED families this manifest leans on:
    #   G-14 EncounterTableSpec(weights=RARITY_ENCOUNTER_WEIGHT, catch_base=RARITY_CATCH_BASE,
    #                           level_bonus=(0.02, cap=0.20), success_cap=0.95)  # the catch roll as DATA
    #   G-8  collection-store grant op (creature name → collection_log)
    #   G-9  ProgressionSpec(track=GAME_CREATURE, earn={"catch":4,"battle_win":6}, curve=shared)
    # STAYS tier-3 (registered handlers, by design):
    #   creature.render_result (renderer_override)  ·  utils.creatures.battle (pure engine, game rules)
    help=HelpEntrySpec("Catch original creatures, fill your dex, battle in level-normalized PvP",
        examples=("!catch","!dex","!cbattle @trainer"),
        rules_text="Teams normalize to level 50 — type matchups + collection decide it (anti-P2W)."),
)
```

**Tier-3 dispositions**

| Tier-3 unit | Verdict | Reason |
|---|---|---|
| !catch (alias hunt) / Catch button | grammar-gap:G-14 + G-8 | Rarity-weighted encounter + probability catch is declarable weighted-table DATA (G-14 EncounterTableSpec); the collection-log grant is G-8. Not a true game engine — a generic loot/gacha roll (contrast the battle engine). The xp leg is the shared game_xp dep. |
| !cbattle command | grammar-gap:ChallengeSessionSpec | Only opens the PvP session after trivial no-bot/no-self guards; needs a generated command→session-open route onto the already-specced ChallengeSessionSpec (§2.8). Not domain logic. |
| _OpponentSelect (UserSelect) | grammar-gap:ChallengeSessionSpec | A member SelectorSpec whose on_select opens the declared PvP session; the bot/self validation is a kernel guard, not domain logic. |
| game_xp earn integration | grammar-gap:G-9 | Two registered award() earn actions (catch=+4, battle_win=+6) + level derivation reusing the shared curve. G-9 ProgressionSpec declares the earn map; cross-lane dep on the xp subsystem. |
| Battle engine (utils/creatures/battle.py) | escape-hatch | Type chart, stat derivation, move policies and 6v6 turn resolution are game rules. Checked the kernel should NOT own this — §10.1 risk 5 says the grammar must never express game rules; a registered pure engine (blackjack-engine lineage) is the correct tier-3 form. |
| build_result_embed (KO-log renderer) | escape-hatch | Bespoke turn-by-turn battle-log presentation (roster + faint markers + capped KO highlights + records) is not a FieldsBlock/TableBlock projection. renderer_override is §2.9's sanctioned named escape hatch for exactly this. |

**Structural-gap flags**

- **deep persistent battle state** — `yes` — NOT present — PvP resolves synchronously in-memory (resolve_battle); nothing mid-battle is persisted. Only the collection log + W/L aggregate are stored. No GameStateSpec/G-10 needed (unlike mining grid).
- **transactional multi-write mutation** — `with-amendment:G-8` — catch = collection upsert + xp award in one db.transaction (workflow.py:82); battle settle = both fighters' W/L + winner xp in one txn (creature_battle_service.py:171). Expressible via ChallengeSessionSpec.stat_writes (battle, in spec) + G-8 grant + shared xp (catch).
- **escrow / settlement + double-settle risk** — `yes` — SettleOnceMixin.claim_settlement on Accept AND Decline (challenge.py:63,107) + _resolved on_timeout race guard. Fully covered by ChallengeSessionSpec.settle_once=True (already in §2.8). No coin escrow — PvP is stakeless.
- **inventory / collection taxonomy** — `with-amendment:G-8` — The dex is a per-(user,guild,creature) collection store; catalog is data (creatures.json, 36 creatures, 6 elements × 4 rarities). G-8 collection/ItemCatalogSpec expresses ownership + grant; taxonomy (element/rarity/archetype) is catalog data.
- **creature-battle engine (game rules)** — `no` — needs-new-primitive is the WRONG call — this is a deliberate tier-3 escape hatch (pure engine, blackjack-engine lineage). Grammar must never own game rules (§10.1 risk 5).
- **XP + leaderboard derivation** — `with-amendment:G-9` — catch/battle_win feed shared GAME_CREATURE xp; two boards (top_collectors, top_battlers) are LeaderboardSpec (in spec). Earn actions are G-9 ProgressionSpec. Catch odds get a bounded per-level nudge (data).
- **scheduled loop + cooldown** — `yes` — NEITHER present — no @tasks.loop and no @commands.cooldown anywhere in the subsystem (verified). Notably !catch is uncapped (no rate-limit) — a possible balance gap, not a grammar gap.
- **irreversible economy op** — `yes` — NOT present — creature is deliberately coin-free (registry:343). No currency debit/credit; catch grants only collection+xp, PvP has no stakes. No G-7/G-11 needed.
- **stateful interactive game loop** — `yes` — NOT present — there is no player-driven turn loop (no hit/stand analog); the battle auto-resolves on Accept. Only the challenge accept/decline is interactive.
- **wait_for-style challenge wizard** — `yes` — CreatureBattleChallengeView is the challenge/accept/decline wizard (60s timeout, expiry copy). ChallengeSessionSpec accept phase covers it — no wait_for primitive gap.
- **weighted encounter / loot roll** — `with-amendment:G-14` — NEW recurring primitive: rarity-weighted spawn + probability-gated acquisition + bounded level bonus (encounters.py). All the numbers are data tables; only a generic kernel roll is missing. Recurs in fishing/mining — Lane B convergence candidate.

**MAP → RECONSIDER → SIMULATE → OPTIMIZE**

- **Verdict:** keep · **status:** ok
- **Optimal new-bot form:** A declarative creature SubsystemManifest: catalog stays JSON data, collection + battle-record as StoreSpecs, two LeaderboardSpecs, a coin-free ChallengeSessionSpec for PvP (settle_once, 60s accept, stat_writes, no escrow), an EncounterTableSpec (G-14) for the catch roll and a ProgressionSpec (G-9) for xp earn — with ONLY the pure battle engine (utils/creatures/battle.py) and the KO-log renderer_override staying as registered tier-3 handlers. This subsystem is already unusually well-factored (pure domain / thin service seam / shared embed builders / settle-once), so it ports cleanly.
- **Dependency layer:** L3 game on L2 collection store + shared game_xp (L1 progression). No currency layer — creature is deliberately coin-free, so it does NOT sit on the economy/currency kernel (build order: encounter+collection first, PvP session + engine second).
- **Production-grade done:** Parity golden: (1) catch outcome distribution matches RARITY_ENCOUNTER_WEIGHT × RARITY_CATCH_BASE × level-bonus over N seeded rolls; (2) dex renders all catalog creatures grouped by element with correct caught/uncaught state and legacy-row filtering; (3) resolve_battle is deterministic given a seed and re-passes the sim's fairness gates (no side-edge, level-normalized ~50/50 on mirror pools); (4) settle-once: Accept double-click and Accept-vs-Decline race record the battle exactly once; (5) collection+xp and W/L+xp each commit atomically or not at all; (6) leaderboards rank by the documented tiebreaks.
- **Outperform target:** pending Lane F — likely Poketwo/MewBot (Pokemon-style collection bots). Differentiate on original IP (no Pokemon), instant level-normalized skill-PvP (anti-P2W, Q-0039) vs their grind/whale ladders, and a single one-panel Catch/Dex/Challenge/Ladder UX.

**Cross-lane dependencies**

- game_xp (xp subsystem): game_xp_service.award/emit_award_events + GAME_CREATURE track + shared level curve (db.level_progress) + game_xp.awarded/level_up events are xp-OWNED, not creature-owned
- economy: NONE by design — creature is coin-free (registry line 343 notes no hard dep so it isn't locked out when economy is disabled)
- LeaderboardSpec + ChallengeSessionSpec: shared game-facet primitives (already in the frozen §2.8 spec)
- SettleOnceMixin (utils/terminal_guard): shared settle-once claim used by the PvP challenge — the deathmatch/blackjack settle-once lineage
- core.runtime.guild_resources.resolve_member: shared member resolution for leaderboard name rendering

**⚠ Unverified / judgment calls**

- game_xp_service.award internal transaction/return semantics — read its signature, event names, and the catch/battle call sites, but not the full function body (assumed award() honors the passed conn per the docstring contract)
- creatures.json catalog contents — the '36 creatures, 6 per element × 4 rarities' count is taken from module docstrings and build_menu_embed's len(CREATURES); did not open/count the JSON file itself
- catch has no @commands.cooldown — verified by grep returning zero cooldown/get_setting/settings_key hits across both cogs and both services; flagged as a possible balance gap (uncapped catch), not a grammar gap

---

### farm
_cogs/source: disbot/cogs/farm_cog.py · services/farm_workflow.py · utils/farm.py · utils/db/games/farm.py · migration 090 · views/farm/*_

| Unit | Kind | File:line | Tier (as-written) | Tier (with amendments) | Rationale / gap |
|---|---|---|---|---|---|
| !farm command (aliases chickenfarm, coop) | command | disbot/cogs/farm_cog.py:43-47 | 1 | 1 | Command → panel open: opens FarmMenuView, no domain logic. PanelRef route → kernel open-panel workflow. |
| FarmMenuView main panel (flock/coop-fill/lay-rate/balance/away-blurb) | panel | disbot/views/farm/menu.py:164, build_farm_embed:33-82 | 2 | 2 | Read-model panel: pure fields built from settled state via a provider (get_status). NOT a live game board renderer_override (contrast blackjack) — FieldsBlock over ProviderRef. |
| FarmShopView shop sub-panel (next-hen/coop prices + balance) | panel | disbot/views/farm/menu.py:230, build_shop_embed:85-121 | 2 | 2 | Read-model panel over provider; static landing (no DB read) then re-renders with prices from state. FieldsBlock over ProviderRef. |
| collect_btn → farm_workflow.collect (settle→credit→zero eggs→award XP→emit, one txn) | panel-action | disbot/views/farm/menu.py:197-207, disbot/services/farm_workflow.py:114-179 | 3 | 2 | Audited multi-write mutation seam (credit_in_txn + set_chicken_farm + game_xp.award inside one db.transaction, EVT after commit). tier3 as-written; G-7 EconomyTransactionSpec + G-13 accrual-reset + G-9 XP compose it into a declared atomic transaction. |
| shop_btn → open shop sub-panel | panel-action | disbot/views/farm/menu.py:209-219 | 1 | 1 | Navigation to FarmShopView — kernel open-panel workflow, zero domain code. |
| refresh_btn → re-settle & redraw in place | panel-action | disbot/views/farm/menu.py:221-227 | 1 | 1 | Panel re-render workflow (re-reads provider, redraws onto fresh view). Kernel re-render. |
| buy_btn → farm_workflow.buy_chicken (settle-old-flock→debit price→chickens+1, one txn) | panel-action | disbot/views/farm/menu.py:253-260, disbot/services/farm_workflow.py:191-248 | 3 | 2 | Audited coin sink: debit_in_txn + set_chicken_farm in one txn, InsufficientFundsError rollback. tier3 as-written; G-11 ShopSpec (priced item, geometric price curve, effect=chickens+1) + G-7 debit leg makes it declared data. |
| upgrade_btn → farm_workflow.upgrade_coop (settle→debit price→coop+1, one txn) | panel-action | disbot/views/farm/menu.py:267-273, disbot/services/farm_workflow.py:251-310 | 3 | 2 | Audited coin sink near-identical to buy. tier3 as-written; G-11 ShopSpec (price=coop_upgrade_price curve, effect=coop_level+1) + G-7 debit leg. |
| back_btn → nav to main panel | panel-action | disbot/views/farm/menu.py:275-296 | 1 | 1 | Navigation to FarmMenuView — kernel open-panel workflow. |
| farm status read provider (get_status / _panel_data) | provider | disbot/services/farm_workflow.py:82-98, disbot/views/farm/menu.py:124-140 | 2 | 2 | Read-model provider: settled state + balance + seconds-to-full + 'while away' delta. Thin read behind a ProviderRef — read-only, persists nothing. |
| settle() idle egg accrual (computed on read, no ticker) | engine | disbot/utils/farm/farm.py:68-92 | 3 | 2 | Core idle mechanic: eggs accrue in batches of `chickens` per LAY_INTERVAL_SECONDS, capped at coop_capacity, remainder-preserving (idempotent). Pure domain math, tier3 as-written; G-13 IdleAccrualSpec (rate=chickens/interval, cap=coop_capacity(level), interval=300s) makes it declared data. |
| economy tuning curves (chicken_price/coop_upgrade_price/coop_capacity/collect_value + caps) | engine | disbot/utils/farm/farm.py:108-141 | 3 | 2 | Faucet+sink economics: geometric price growth (base*growth^n), linear capacity (base+per_level), egg value, MAX_CHICKENS/MAX_COOP_LEVEL. Parametric curves, not a rules engine — tier3 as-written; G-11 ShopSpec price-formula-as-data + G-13 accrual params make it declarative. Distinct surface from the txn seams (the designer-tuned numbers). |
| game_xp earn hook on collect (award collect_eggs=3 + level-up emit) | progression | disbot/services/farm_workflow.py:150-169, disbot/services/game_xp_service.py:107 | 3 | 2 | Progression earn coupled into the collect txn. Action→XP is already data in _AWARDS; tier3 as-written (bespoke award() call in handler), G-9 ProgressionSpec declares the earn hook (action=collect_eggs, xp=3, game=farm). |
| EVT_BALANCE_CHANGED emission (collect/buy/upgrade, post-commit) | event | disbot/services/farm_workflow.py:158-165,235-242,296-303 | 1 | 1 | EventSpec declaration; economy-owned event, emitted post-commit from the mutation seams. Declaration is tier-1; the emit rides inside the (tier-3→G-7) transaction. |
| chicken_farm store (per user+guild flock/coop/egg-accrual) + conn-aware get/set CRUD | store | disbot/migrations/090_chicken_farm.sql:13-21, disbot/utils/db/games/farm.py:42-113 | 1 | 1 | StoreSpec → generated sole-writer fence (aggregate class). CRUD is generated; set is conn-aware so it composes into the workflow transaction (Q-0071 pattern). |
| FarmProvider leaderboard (flock size, coop-level tie-break; aliases farmlb/farming/chickenlb) | leaderboard | disbot/services/rank_providers.py:321-368,657-659 | 2 | 2 | LeaderboardSpec: reads top_farmers (ORDER BY chickens DESC, coop_level DESC). Flock size is the durable rankable stat (not the momentary unsettled eggs). In-spec family already. |
| Explore-world entry (_register_farm_world / WorldEntry, order=30) | navigation | disbot/cogs/farm_cog.py:59-99 | 1 | 1 | Navigation registration into the federated world hub; opener is a thin panel-open closure (kept in cog to avoid services→views edge). Declared hub docking (parent_hub/hub_group + world entry). |
| Help hub hook / help projection (build_help_menu_view) | help | disbot/cogs/farm_cog.py:51-56 | 1 | 1 | Help-menu direct-navigation hook opens the interactive panel — help-as-projection + navigation, zero domain code. |
| subsystem registry declaration (identity/emoji/category/parent_hub/hub_group/ui_priority/tags/soft-deps/capabilities farm.egg.collect+farm.coop.manage) | manifest-header | disbot/utils/subsystem_registry.py:364-387 | 1 | 1 | The SubsystemManifest root metadata + capability strings. Pure declaration. NOTE: the two capabilities are declared but not enforced in the handlers (the HubView author-check is the real gate). |

**Fit:** 19 units · tier-1/2 as-written **68%** (13/19) · with amendments **100%** (19/19).

**§2 manifest sketch**

```python
SubsystemManifest(
  key="farm", display_name="Chicken Farm", emoji="🐔",
  category="games", parent_hub="games", hub_group="activities", ui_priority=23,
  capabilities=("farm.egg.collect", "farm.coop.manage"),
  dependencies=(), # soft-depends economy only (needs a SubsystemManifest.soft_dependencies field)
  commands=(
    CommandSpec("farm", CommandKind.PREFIX, "Open your idle chicken farm",
      route=PanelRef("farm_main"), aliases=("chickenfarm","coop")),            # tier 1
  ),
  panels=(
    PanelSpec("farm_main","farm","🐔 Chicken Farm",
      body=(BlockSpec("fields", provider=ProviderRef("farm.status")),),        # tier 2 read-model
      actions=(
        PanelActionSpec("collect","Collect", emoji="🥚", style="success",
           handler=HandlerRef("farm.collect"), audit="farm:collect"),          # tier 3 → G-7(+G-13,+G-9)
        PanelActionSpec("shop","Shop", emoji="🛒", handler=PanelRef("farm_shop")),   # tier 1 nav
        PanelActionSpec("refresh","Refresh", emoji="🔄",
           handler=WorkflowRef("panel_rerender")),                             # tier 1
      )),
    PanelSpec("farm_shop","farm","🛒 Farm Shop",
      body=(BlockSpec("fields", provider=ProviderRef("farm.shop_prices")),),   # tier 2 read-model
      actions=(
        PanelActionSpec("buy","Buy hen", emoji="🐔",
           handler=HandlerRef("farm.buy_chicken"), audit="farm:buy_chicken"),  # tier 3 → G-11(+G-7)
        PanelActionSpec("upgrade","Upgrade coop", emoji="🏠",
           handler=HandlerRef("farm.upgrade_coop"), audit="farm:upgrade_coop"),# tier 3 → G-11(+G-7)
        PanelActionSpec("back","Back", emoji="◀", handler=PanelRef("farm_main")),    # tier 1 nav
      )),
  ),

  # ---- PROPOSED Lane-B families (NOT in frozen §2) --------------------------
  accruals=(  # G-13 IdleAccrualSpec — idle egg laying, computed on read, no ticker
    IdleAccrualSpec(resource="eggs", rate_source="chickens", interval_s=300,
        cap_expr="coop_capacity(coop_level)", settle_before_mutate=True,
        store="chicken_farm", idempotent=True),),                             # tier 2
  shops=(  # G-11 ShopSpec — priced coin sinks with declared geometric curves
    ShopSpec("farm_shop", currency="coins", items=(
       ShopItem("hen",  price_expr="round(40*1.55**(n-1))", effect="chickens+1", cap=100),
       ShopItem("coop", price_expr="round(100*1.8**level)", effect="coop_level+1", cap=10),
    )),),                                                                       # tier 2
  transactions=(  # G-7 EconomyTransactionSpec — the collect payout as one atomic declared txn
    EconomyTransactionSpec("farm.collect",
       legs=("credit: collect_value(eggs)=eggs*2", "store: eggs=0 @ now",
             "progress: xp collect_eggs"),
       audit="farm:collect", event="economy.balance_changed"),),              # tier 2
  progression=(  # G-9 ProgressionSpec — earn hook (already data in game_xp _AWARDS)
    ProgressionSpec(game="farm", earn=(("collect_eggs", 3),)),),               # tier 2

  stores=(StoreSpec("chicken_farm", sole_writer="farm.workflow",
            checkpoint_class="aggregate"),),                                    # tier 1
  events=(EventSpec("economy.balance_changed", (...), owner_subsystem="economy",
            observability_only=False, expected_subscribers=(...)),),            # tier 1 (economy-owned)
  game=GameFacet(leaderboards=(
     LeaderboardSpec("farm","chickens","max", scope="guild",
        empty_state="No farms yet. Use !farm to start your coop."),)),         # tier 2
  help=HelpEntrySpec("Idle egg farm — collect eggs for coins, buy hens, upgrade the coop.",
        examples=("!farm",)),                                                   # tier 1
)
# Providers: farm.status (get_status/settle), farm.shop_prices (price curves) — thin read refs.
# World-hub docking (Explore) + Help hook = generated from parent_hub/hub_group + PanelRef.
```

**Tier-3 dispositions**

| Tier-3 unit | Verdict | Reason |
|---|---|---|
| collect_btn → farm_workflow.collect | grammar-gap:G-7 | Audited atomic payout (credit+store-reset+XP+event in one txn). G-7 EconomyTransactionSpec expresses the money+audit+event legs; the accrual reset needs G-13 and the XP leg needs G-9 to co-compose. Load-bearing: the three declared specs must compose into ONE db.transaction — verified the handler IS one txn (farm_workflow.py:132-156), but kernel tri-spec atomic composition is the open bet. |
| buy_btn → farm_workflow.buy_chicken | grammar-gap:G-11 | Priced coin sink (debit + increment store field, settle-first, InsufficientFunds rollback). G-11 ShopSpec (price curve + effect) + G-7 debit leg. Clean, strong fit — near-identical to upgrade. |
| upgrade_btn → farm_workflow.upgrade_coop | grammar-gap:G-11 | Priced coin sink raising the egg cap (debit + coop_level+1). G-11 ShopSpec (coop_upgrade_price curve, effect=coop_level+1) + G-7 debit leg. |
| settle() idle egg accrual | grammar-gap:G-13 | Batch accrual (chickens/interval) capped at coop_capacity, remainder-preserving/idempotent, no ticker. Simple parametric math, NOT a rules engine → not a legit escape hatch; G-13 IdleAccrualSpec declares rate/interval/cap. |
| economy tuning curves (prices/capacity/egg value/caps) | grammar-gap:G-11 | Geometric price growth + linear capacity + fixed egg value + soft caps. Parametric curves expressible as ShopSpec/IdleAccrualSpec data (price_expr, cap). No bespoke rules → grammar gap, not escape hatch. |
| game_xp earn hook on collect | grammar-gap:G-9 | action→XP mapping is already data (game_xp _AWARDS collect_eggs=3); only the call-site is code. G-9 ProgressionSpec declares the earn hook. Shared game_xp_service stays the provider. |

**Structural-gap flags**

- **deep persistent per-player state** — `with-amendment:G-13` — chicken_farm row (flock/coop/egg-accrual, 4 scalars) — shallow, not a grid/battle. StoreSpec + G-13 IdleAccrualSpec suffice; no G-10 GameStateSpec needed.
- **transactional multi-write mutation** — `with-amendment:G-7` — collect/buy/upgrade each run a coin leg + farm-row write (collect also +XP) inside ONE db.transaction (farm_workflow.py:132,210,270). THE core danger; G-7 EconomyTransactionSpec targets exactly this.
- **escrow/settlement + double-settle risk** — `with-amendment:G-13` — No PvP escrow, but a genuine settlement subtlety: settle() is idempotent (remainder-preserving) AND buy/upgrade settle at the OLD flock size BEFORE mutating (farm_workflow.py:206) so faster rate never applies retroactively; fresh-farm normalized to now (no 1970 free-fill, farm_workflow.py:39-55). G-13 must encode settle_before_mutate + idempotency as invariants — load-bearing.
- **farm growth state (idle activity)** — `with-amendment:G-13` — Scalar accrual (eggs over time), not a mining grid or creature dex. Fully covered by G-13 IdleAccrualSpec; the deeper G-10 world/grid family is NOT needed here.
- **XP + leaderboard derivation** — `with-amendment:G-9` — collect earns game XP (G-9 ProgressionSpec) and FarmProvider ranks by flock size (LeaderboardSpec, in-spec). Both derive from the store; no new primitive.
- **irreversible economy op** — `with-amendment:G-7` — collect (faucet) + buy/upgrade (sinks) move real audited coins. G-7 declares the audit+event legs so the irreversible move is a declared, audited transaction.
- **scheduled loop + cooldown** — `yes` — DELIBERATELY ABSENT — no @tasks.loop ticker (ADR-001/002: accrual computed on read) and no @commands.cooldown (the coop cap is the rate limiter). A positive: no ManagedTaskSpec, no G-4 needed.
- **stateful game loop / wait_for wizard / inventory taxonomy** — `yes` — NONE present. Menu re-renders on demand (no live loop), no modal wizard, eggs are a scalar counter not an item catalog (no G-8 needed). Farm is the clean end of Lane B.

**MAP → RECONSIDER → SIMULATE → OPTIMIZE**

- **Verdict:** keep · **status:** owner-gated — the subsystem is production-clean and needs no redesign, but full declarative expression is gated on approving the Lane-B amendment family G-7/G-9/G-11/G-13 (as-written §2 lacks any economy/shop/accrual/progression primitive, so as-written fit is only 68%). No runtime blocker; amendments are additive tier-2 families.
- **Optimal new-bot form:** A single SubsystemManifest that re-expresses today's clean decomposition as data: an IdleAccrualSpec (G-13) for egg laying, a ShopSpec (G-11) with declared geometric price curves for the hen/coop sinks, EconomyTransactionSpec (G-7) collect/buy/upgrade seams, a ProgressionSpec (G-9) collect_eggs earn hook, a StoreSpec for chicken_farm, a LeaderboardSpec for flock size, and two GENERATED read-model panels (main + shop) with kernel nav/re-render actions — zero bespoke view or engine code.
- **Dependency layer:** L3 idle game built on L1 currency kernel (economy_service + G-7) and L2 accrual/shop/progression primitives (G-13/G-11/G-9); also depends on the shared game_xp_service, the leaderboard/rank_providers hub, and the Explore world_registry.
- **Production-grade done:** Parity golden: a player collects → buys hens → upgrades coop and every number matches the current settle()/pricing math exactly (egg value=2, geometric prices 40*1.55^n / 100*1.8^level, cap=20+15*level, MAX 100 hens / 10 coop); idle accrual over arbitrary elapsed time is bit-identical and idempotent; the two anti-exploit invariants hold (fresh farm accrues from now not 1970; buy settles at OLD flock first); every coin move is audited + emits balance_changed; leaderboard ranks by flock size with coop-level tie-break.
- **Outperform target:** pending Lane F (best-in-class idle/farming Discord bots, e.g. IdleRPG-style); beat on transactional integrity (audited atomic coin moves, no double-settle) and restart-safe no-ticker accrual (state is a stored value+timestamp, survives restarts with zero scheduler).

**Cross-lane dependencies**

- economy_service — credit_in_txn/debit_in_txn/InsufficientFundsError/EVT_BALANCE_CHANGED (the L1 currency kernel; farm is a pure consumer, farm_workflow.py:27,133,211,271)
- game_xp_service — award/GAME_FARM/collect_eggs earn + emit_award_events (shared progression, farm_workflow.py:150-168)
- leaderboard hub / rank_providers — FarmProvider registration + aliases (shared leaderboard subsystem, rank_providers.py:321,635,657)
- world_registry — Explore world-hub docking via WorldEntry (farm_cog.py:60-98)
- idle_summary util — shared 'while you were away' blurb (also used by fishing/mining, menu.py:132)
- utils.db.pool + db.transaction — shared DB seam (conn-aware set_chicken_farm composes the coin leg, Q-0071 pattern)

**⚠ Unverified / judgment calls**

- collect tier_amended=2 assumes G-7 + G-13 + G-9 compose into ONE atomic declared transaction (settle→credit→reset-eggs→award-XP→emit). I verified the shipped handler IS a single db.transaction (farm_workflow.py:132-156), but whether the rebuilt kernel can atomically compose three separate declared specs is unproven — if it cannot, collect stays tier 3.
- The 'settle eggs at OLD flock size before applying a purchase' ordering invariant (farm_workflow.py:206) and the fresh-farm 1970-normalization (farm_workflow.py:39-55) are confirmed in source; their declarability as an IdleAccrualSpec flag (settle_before_mutate / uninitialized-ts handling) is assumed, not demonstrated by any existing spec.
- capabilities farm.egg.collect / farm.coop.manage are declared in subsystem_registry.py:383-386 but I did NOT find them enforced in the panel-action handlers (the HubView author-restriction is the actual gate) — counted as tier-1 declarations regardless of enforcement.
- Unit 12 (economy tuning curves) is scored as a distinct surface from the buy/upgrade/collect handlers that CALL it; a reviewer who folds it into those handlers would drop units_total to 18 and nudge as-written fit to ~65% (tier12 12/18) — the amended 100% is unaffected.

---

### xp
_cogs/source: disbot/cogs/xp_cog.py + cogs/xp/* · services/xp_service.py · utils/db/xp.py · utils/xp_migration.py · views/xp/*_

| Unit | Kind | File:line | Tier (as-written) | Tier (with amendments) | Rationale / gap |
|---|---|---|---|---|---|
| !xpmenu | command | disbot/cogs/xp_cog.py:91 | 1 | 1 | Command -> PanelRef open of the XP hub (_XpHubView). Kernel open-panel workflow, zero domain code. |
| !rank [stat\|category\|@user] | command | disbot/cogs/xp_cog.py:119 | 2 | 2 | Routes to a read-model provider (rank_providers). Arg dispatch (stat/category/member) is thin routing over a ProviderRef read; card is a projection. |
| !givexp @user amount | command | disbot/cogs/xp_cog.py:177 | 3 | 3 | Admin XP-grant seam (xp_service.award) with positive-amount typed copy. Thin domain mutation, same class as karma.grant. |
| !resetxp @user | command | disbot/cogs/xp_cog.py:195 | 3 | 3 | Audited destructive mutation: delete_xp + EVT_XP_RESET + emit_audit_action (xp_service.reset). Escape-hatch by design. |
| !xpconfig | command | disbot/cogs/xp_cog.py:208 | 1 | 1 | Command -> PanelRef open of XpConfigView. Kernel open-panel workflow. |
| !xpimport [source][#ch][limit] | command | disbot/cogs/xp_cog.py:216 | 3 | 3 | Bot-to-bot migration: arg parse + channel scan + preview orchestration (xp_migration.scan_channel). External-format tool. |
| XP hub panel (rank read-model + chrome) | panel | disbot/views/xp/main_panel.py:17 | 2 | 2 | Read-model panel: build_rank_response over the rank provider (embed + generic Pillow card). No bespoke domain in the panel body. |
| hub stat-toggle Both/XP/Coins | panel-action x3 | disbot/views/xp/main_panel.py:81-91 | 1 | 1 | Three buttons that re-render the read-model with a stat param (kernel re-render). Counted x3. |
| hub Configure nav | panel-action | disbot/views/xp/main_panel.py:93 | 1 | 1 | Auth re-check + open-panel navigation to config panel. |
| hub Give XP action (modal) | panel-action | disbot/views/xp/main_panel.py:115 | 3 | 3 | Opens _GiveXpModal -> xp_service.award admin grant. Same domain seam as !givexp. |
| hub Reset XP action (modal) | panel-action | disbot/views/xp/main_panel.py:127 | 3 | 3 | Opens _ResetXpModal -> xp_service.reset audited mutation with CONFIRM guard. |
| XP config panel (settings read-model) | panel | disbot/views/xp/config_panel.py:22 | 1 | 1 | Config-choreography panel: reads xp_min/max/cooldown + announce binding and renders; set/re-render/nav only. |
| config XP Range edit (button+_XpRangeModal) | panel-action | disbot/views/xp/config_panel.py:69 | 1 | 1 | setting_edit workflow via SettingsMutationPipeline for xp_min+xp_max; modal is the kernel-generated edit UI. |
| config Cooldown edit (button+_XpCooldownModal) | panel-action | disbot/views/xp/config_panel.py:79 | 1 | 1 | setting_edit workflow for xp_cooldown; kernel-generated modal (numeric_presets input_hint declarable). |
| config Level-up Channel edit (button+_XpChannelModal) | panel-action | disbot/views/xp/config_panel.py:89 | 1 | 1 | binding_set/clear workflow via BindingMutationPipeline for xp.announce_channel. Kernel binding-set. |
| config Import nav | panel-action | disbot/views/xp/config_panel.py:99 | 1 | 1 | Open-panel navigation to XpImportSetupView. |
| config Back nav | panel-action | disbot/views/xp/config_panel.py:41 | 1 | 1 | attach_back_button navigation to parent hub. Kernel nav workflow. |
| import-setup channel select | selector | disbot/views/xp/import_panel.py:252 | 1 | 1 | ChannelSelect that stores channel_id and re-renders. Kernel selector + re-render. |
| import-setup source select | selector | disbot/views/xp/import_panel.py:266 | 1 | 1 | Enum select over the announcer-format registry; stores key + re-render. Options-source provider. |
| import-setup Scan action | panel-action | disbot/views/xp/import_panel.py:276 | 3 | 3 | Admin re-check + channel history scan/parse (scan_channel) building a ScanPlan. External-format domain. |
| import-setup Cancel | panel-action | disbot/views/xp/import_panel.py:349 | 1 | 1 | Disable + stop view. Kernel dismiss workflow. |
| import-preview panel (ScanPlan read-model) | panel | disbot/views/xp/import_panel.py:30 | 2 | 2 | Read-model of a resolved ScanPlan (scanned/matched/sample/unresolved). Provider-shaped projection. |
| import-preview Apply action | panel-action | disbot/views/xp/import_panel.py:100 | 3 | 3 | Admin re-check + bulk raise-only import (xp_migration.import_levels) + optional role sync + summary audit. Irreversible-ish batch mutation. |
| import-preview toggle-roles | panel-action | disbot/views/xp/import_panel.py:162 | 1 | 1 | Boolean flip + re-render. Kernel re-render. |
| import-preview Cancel | panel-action | disbot/views/xp/import_panel.py:174 | 1 | 1 | Disable + stop. Kernel dismiss. |
| rank stat dropdown (_RankView) | selector | disbot/views/xp/rank_view.py:19 | 2 | 2 | Ephemeral read-model re-render selector over build_rank_response (Both/XP/Coins). |
| xp_min setting | setting | disbot/cogs/xp/schemas.py:71 | 2 | 1 | int with _validate_positive_int registered validator ref (tier2 as-written); G-5 makes the bound declarative data (tier1). |
| xp_max setting | setting | disbot/cogs/xp/schemas.py:80 | 2 | 1 | Same G-5 bounded-int class. |
| xp_cooldown setting (+presets) | setting | disbot/cogs/xp/schemas.py:89 | 2 | 1 | int with _validate_cooldown validator + numeric presets (0/15/30/60/120/300). G-5 declares the non-negative bound + presets as data. |
| announce_channel binding | binding | disbot/cogs/xp/schemas.py:57 | 1 | 1 | BindingSpec (CHANNEL, optional) with legacy xp_announce_channel KV alias. Pure declaration. |
| announce_channel resource | resource | disbot/cogs/xp/schemas.py:118 | 1 | 1 | ResourceRequirement (CHANNEL, OPTIONAL provisioning, suggested level-ups). Pure declaration. |
| participation subscription (earn opt-out) | setting | disbot/cogs/xp/schemas.py:148 | 1 | 1 | User-scoped bool; gates the on_message earn. Expressible as user-scoped SettingSpec (cleaner via G-14). |
| xp.leaderboard.public visibility intent | setting | disbot/cogs/xp/schemas.py:160 | 1 | 1 | User-scoped bool visibility declaration (hide from leaderboard). |
| xp.rank.public visibility intent | setting | disbot/cogs/xp/schemas.py:170 | 1 | 1 | User-scoped bool visibility declaration (hide rank on lookup). |
| xp.levelup notification intent | setting | disbot/cogs/xp/schemas.py:180 | 1 | 1 | User-scoped DM-on-levelup opt-in (digestable). Declarative notification intent. |
| rank_embed_style preference (enum) | setting | disbot/cogs/xp/schemas.py:192 | 1 | 1 | User-scoped enum (standard/compact/rich). Plain allowed_values setting. |
| xp capabilities (rank.view, leaderboard.view, settings.configure) | capability x3 | disbot/utils/subsystem_registry.py:407-409 | 1 | 1 | Three declared capability strings on the subsystem. Pure declaration. Counted x3. |
| XpStage pipeline registration (order=30) | listener | disbot/cogs/xp/stage.py:25 | 2 | 2 | Thin MessageStage wrapper (name+order, delegates to handle_message). A declared message-stage spec (G-1-adjacent); wrapper is thin. |
| on_message earn hot path (handle_message) | listener | disbot/cogs/xp/listener.py:93 | 3 | 2 | Cooldown check + participation gate + random(xp_min..xp_max) award + level recompute. G-9 declares cooldown-gated earn as data + G-1 the on_message wiring. |
| announce_level_up (level-up embed to announce channel) | handler | disbot/cogs/xp/listener.py:144 | 3 | 2 | Resolves announce binding + posts a templated level-up embed. G-3 AnnouncementRouteSpec (event xp.level_up -> template -> bound destination). |
| level-up server-log embed (post_log_embed) | handler | disbot/cogs/xp/listener.py:179 | 3 | 2 | Bespoke log-embed to server logging. G-3 template route / or a declared EventSubscription to logging. |
| _apply_xp_threshold_roles (grant level roles) | handler | disbot/cogs/xp/listener.py:184 | 3 | 3 | Plans + applies XP threshold roles through audited role_automation. Real cross-subsystem domain; belongs to the role-automation lane (escape hatch here). |
| EVT_XP_AWARDED (xp.awarded) | event | disbot/services/xp_service.py:126 | 1 | 1 | EventSpec declaration; emit lives inside the award seam. |
| EVT_LEVEL_UP (xp.level_up) | event | disbot/services/xp_service.py:136 | 1 | 1 | EventSpec declaration on level-boundary crossing. |
| EVT_XP_RESET (xp.reset) | event | disbot/services/xp_service.py:239 | 1 | 1 | EventSpec declaration emitted by the reset seam. |
| audit.action_recorded (reset + import) | event | disbot/services/xp_service.py:247 | 1 | 1 | emit_audit_action on reset (xp_service.py:247) and import (xp_migration.py:173). Declared via audited=True on the mutation seam. |
| xp table (xp/level/messages/last_xp) | store | disbot/utils/db/xp.py:45 | 1 | 1 | StoreSpec -> generated sole-writer fence (xp_service). NOTE: table is shared with economy (coins column) -> split ownership. |
| level curve engine (xp_for_level/level_progress/total_xp_for_level) | engine | disbot/utils/db/xp.py:15-42 | 3 | 2 | Progression math (5L^2+50L+100, cumulative inverse). Simple curve -> G-9 ProgressionSpec declares coefficients as data (unlike an irreducible game-rules engine). |
| import_level raise-only seam | seam | disbot/services/xp_service.py:153 | 3 | 3 | Absolute raise-only XP set (db.set_imported_xp GREATEST merge), idempotent, event-silent. Bespoke migration primitive. |
| announcer format registry / parsers (arcane/mee6/superbot/generic) | parser | disbot/utils/xp_migration.py | 3 | 3 | Per-bot level-up message parsers (parse_level_message + regex formats). External-format parsing the kernel cannot own. |
| XP leaderboard (XpProvider top/member_rank) | game | disbot/services/rank_providers.py:107 | 2 | 2 | LeaderboardSpec over xp.xp (ORDER BY xp) + member_rank derivation. Read-only ranking. |
| rank card read-model provider (build_rank_card_data) | provider | disbot/services/xp_helpers.py:89 | 2 | 2 | Fetch-once read model (rank + level_progress + coins) feeding embed + generic render_rank_card (parameterized card engine, not domain code). |
| help entry (XP hub via build_help_menu_view) | help | disbot/cogs/xp_cog.py:98 | 1 | 1 | Help-as-projection; direct-nav hook renders the same hub panel. |

**Fit:** 57 units · tier-1/2 as-written **75%** (43/57) · with amendments **82%** (47/57).

**§2 manifest sketch**

```python
XP_MANIFEST = SubsystemManifest(
    key="xp", display_name="XP & Levels", description="Chat-XP progression, ranks and leaderboards.",
    emoji="🏆", category="community", visibility_tier="user",
    capabilities=("xp.rank.view","xp.leaderboard.view","xp.settings.configure"),
    commands=(
        CommandSpec("xpmenu", PREFIX, "Open the XP panel.", route=PanelRef("xp.hub")),
        CommandSpec("rank", PREFIX, "Show a member's rank.", route=ProviderRef("rank.card")),   # tier2 read
        CommandSpec("xpconfig", PREFIX, "Configure XP (admin).", route=PanelRef("xp.config"),
                    capability_required="xp.settings.configure"),
        CommandSpec("givexp", PREFIX, "Grant XP (admin).",
                    route=HandlerRef("xp.give", justification="admin grant seam + typed copy")),   # tier3
        CommandSpec("resetxp", PREFIX, "Wipe a member's XP (admin).",
                    route=HandlerRef("xp.reset", justification="audited destructive mutation")),   # tier3
        CommandSpec("xpimport", PREFIX, "Import levels from another bot.",
                    route=HandlerRef("xp.import.open", justification="external-format migration tool")),
    ),
    panels=(
        PanelSpec("xp.hub", "xp", "🏆 XP Panel — {member}",
            body=(BlockSpec("fields", provider=ProviderRef("rank.card")),),
            selectors=(SelectorSpec("xp.hub.stat","enum", WorkflowRef("panel_rerender"),
                       options_source=("both","xp","coins")),),
            actions=(PanelActionSpec("cfg","⚙️ Configure", PanelRef("xp.config")),
                     PanelActionSpec("give","🎁 Give XP", HandlerRef("xp.give"), capability_required="xp.settings.configure"),
                     PanelActionSpec("reset","🔄 Reset XP", HandlerRef("xp.reset"), destructive=True, style="danger",
                                     audit="xp.reset"))),
        PanelSpec("xp.config", "xp", "⚙️ XP Configuration",
            actions=(PanelActionSpec("range","XP Range", WorkflowRef("setting_edit",(("keys","xp_min,xp_max"),))),
                     PanelActionSpec("cd","Cooldown", WorkflowRef("setting_edit",(("key","xp_cooldown"),))),
                     PanelActionSpec("ch","Level-up Channel", WorkflowRef("binding_set",(("binding","announce_channel"),))),
                     PanelActionSpec("imp","📥 Import", PanelRef("xp.import.setup")))),
        PanelSpec("xp.import.setup","xp","📥 Import XP from another bot",
            selectors=(SelectorSpec("pick_ch","channel", WorkflowRef("panel_rerender")),
                       SelectorSpec("pick_src","enum", WorkflowRef("panel_rerender"),
                                    options_source=ProviderRef("xp.announcer_formats"))),
            actions=(PanelActionSpec("scan","🔍 Scan", HandlerRef("xp.import.scan")),)),   # tier3
        PanelSpec("xp.import.preview","xp","📥 Import preview",
            body=(BlockSpec("fields", provider=ProviderRef("xp.import.plan")),),
            actions=(PanelActionSpec("apply","✅ Apply import", HandlerRef("xp.import.apply"), audit="xp.import"),
                     PanelActionSpec("roles","Assign level roles", WorkflowRef("panel_rerender")))),
    ),
    settings=(
        SettingSpec("xp_min","int",15,"xp_min", validator=BoundedInt(min=1)),      # G-5
        SettingSpec("xp_max","int",25,"xp_max", validator=BoundedInt(min=1)),      # G-5
        SettingSpec("xp_cooldown","int",60,"xp_cooldown", validator=BoundedInt(min=0),
                    presets=(0,15,30,60,120,300)),                                 # G-5
        # user-scoped participation/visibility/notification/preference (G-14)
        SettingSpec("participation","bool",True,"xp.participation", scope_default="user",
                    activation=ON_BY_DEFAULT),
        SettingSpec("leaderboard_public","bool",True,"xp.leaderboard.public", scope_default="user", activation=ON_BY_DEFAULT),
        SettingSpec("rank_public","bool",True,"xp.rank.public", scope_default="user", activation=ON_BY_DEFAULT),
        SettingSpec("levelup_dm","bool",False,"xp.levelup", scope_default="user", activation=OFF_UNTIL_OPT_IN),
        SettingSpec("rank_embed_style","enum","standard","xp.rank_embed_style", scope_default="user",
                    allowed_values=("standard","compact","rich")),
    ),
    bindings=(BindingSpec("announce_channel","channel", required=False,
              legacy_settings_key_aliases=("xp_announce_channel",)),),
    resources=(ResourceRequirement("channel","announce_channel","optional", binding_name="announce_channel"),),
    events=(EventSpec("xp.awarded", (...), owner_subsystem="xp", observability_only=True),
            EventSpec("xp.level_up", (...), owner_subsystem="xp",
                      expected_subscribers=(HandlerRef("server_logging.on_levelup"),)),
            EventSpec("xp.reset", (...), owner_subsystem="xp", audited=True,
                      expected_subscribers=(HandlerRef("server_logging.on_audit_fanout"),))),
    # G-1: on_message earn declared as a gated message-stage; handler is real domain (tier3->tier2 w/ G-9)
    gateway_listeners=(GatewayListenerSpec("on_message", HandlerRef("xp.earn_on_message"),
                       gate="setting:xp.participation AND cooldown:xp_cooldown"),),
    # G-3: level-up announcement route (event -> template -> bound destination)
    announcement_routes=(AnnouncementRouteSpec("xp.level_up",
                         template="🎉 {member} reached Level {new_level}!", destination="announce_channel"),),
    stores=(StoreSpec("xp","xp.service","aggregate", invariant_tag="INV-XP",
            reader_domains=("leaderboard","economy","role")),),  # shared coins col owned by economy
    game=GameFacet(
        leaderboards=(LeaderboardSpec("xp.top","xp.xp","max"),),
        progression=(ProgressionSpec(curve="5*L^2+50*L+100", earn=RandRange("xp_min","xp_max"),
                     cooldown="xp_cooldown"),),   # G-9
    ),
    help=HelpEntrySpec(summary="Earn XP by chatting; !rank shows your standing.",
                       examples=("!rank","!xpmenu","!xpimport arcane #level-ups")),
)
# ESCAPE HATCHES (stay code): xp.give (admin grant), xp.reset (audited wipe),
# xp.import.scan/apply + announcer parsers (external-bot migration), threshold-role grant (role lane).
```

**Tier-3 dispositions**

| Tier-3 unit | Verdict | Reason |
|---|---|---|
| !givexp / hub Give XP action | escape-hatch | Thin admin XP-grant seam with typed positive-amount copy (same class as karma.grant); could partially route through a G-9 grant workflow but the admin-auth + typed copy stay code. |
| !resetxp / hub Reset XP action | escape-hatch | Audited destructive mutation (delete_xp + emit_audit_action + CONFIRM guard). Deliberate escape hatch; kernel should not silently own an XP wipe. |
| !xpimport / import-setup Scan action | escape-hatch | Reads another bot's channel history and parses free-text level-up announcements; external-format scanning the grammar cannot own. |
| import-preview Apply action / import_level seam | escape-hatch | Bulk raise-only absolute-set migration (GREATEST merge) + optional role sync + one summary audit. Bespoke idempotent migration primitive. |
| announcer format registry / parsers | escape-hatch | Per-bot regex parsers (arcane/mee6/superbot/generic). Legitimate code -- arbitrary third-party message formats. |
| on_message earn hot path (handle_message) | grammar-gap:G-9 | Cooldown-gated random earn + level recompute is exactly ProgressionSpec's domain (G-9) atop the on_message wiring (G-1). Reduces to tier-2 declared data + kernel earn workflow. |
| announce_level_up (level-up embed) | grammar-gap:G-3 | event xp.level_up -> templated embed -> bound announce_channel is an AnnouncementRouteSpec (G-3); the recurring welcome/counter/spotlight shape. |
| level-up server-log embed (post_log_embed) | grammar-gap:G-3 | Bespoke log-embed to server logging; expressible as a G-3 template route or a declared EventSubscription (xp.level_up -> logging). |
| _apply_xp_threshold_roles | escape-hatch | Real role-automation domain (planner + audited role_automation.apply). Belongs to the role-automation lane; XP is only the trigger (cross-lane dep). |
| level curve engine | grammar-gap:G-9 | 5L^2+50L+100 is a simple declarable curve (coefficients as data), unlike an irreducible game-rules engine. G-9 ProgressionSpec expresses it -> tier-2. |

**Structural-gap flags**

- **gateway listener (on_message earn hook via MessagePipelineStage)** — `with-amendment:G-1` — Runs through the kernel message_pipeline (stage order=30), not raw @bot.event, but is functionally an on_message listener whose handler carries real earn logic; G-1 declares the wiring, G-9 the earn.
- **XP + leaderboard/rank derivation** — `yes` — LeaderboardSpec over xp.xp + read-model rank provider (build_rank_card_data). Already registry-driven (rank_providers); the card renderer is a generic parameterized engine, not domain code.
- **level-curve progression + cooldown-gated earn** — `with-amendment:G-9` — Quadratic curve + random(xp_min..xp_max) + xp_cooldown gate + participation gate. G-9 ProgressionSpec declares curve/earn/cooldown as data (curve is coefficients, not rules).
- **event -> template -> bound destination announcement** — `with-amendment:G-3` — Level-up embed to announce_channel + level-up log embed. Recurring AnnouncementRouteSpec shape (G-3).
- **audited destructive mutation (reset) + bulk migration (import)** — `yes` — Reset is a single-row delete + emit_audit_action; import is raise-only per-row. Both stay tier-3 escape hatches but are audited/idempotent, not multi-write money transactions.
- **per-user participation / visibility / notification / preference schema** — `with-amendment:G-14` — Phase-1b participation gate + 2 visibility intents + 1 notification intent + 1 enum preference. Expressible today as user-scoped SettingSpecs (tier-1), but a dedicated ParticipationPrefSpec family (G-14) is the recurring cross-subsystem primitive.
- **external-bot format parsing (xp import)** — `needs-new-primitive` — Per-bot regex message parsers have no grammar home and should not -- a legitimate registered escape-hatch tool.
- **cross-subsystem role automation on level-up** — `yes` — XP threshold-role grant is owned by the role-automation lane; XP declares the trigger only (EventSubscription). Not an XP-owned primitive.
- **shared store (xp table split with economy coins)** — `with-amendment:G-1` — StoreSpec sole_writer fence is per-writer, but the xp table has TWO owners (xp.service writes xp/level/messages; economy writes coins). Grammar assumes one sole_writer per table -> a column-scoped ownership note is needed.
- **transactional multi-write / escrow / deep persistent world state** — `yes` — ABSENT in XP (unlike economy/mining/creature). XP is a single flat aggregate row; no escrow, no grid/battle/farm state, no multi-write money transaction. Lowers XP's structural risk.

**MAP → RECONSIDER → SIMULATE → OPTIMIZE**

- **Verdict:** keep · **status:** owner-gated
- **Optimal new-bot form:** A declarative XP SubsystemManifest where the level curve + cooldown-gated per-message earn is a ProgressionSpec (G-9) atop a generated store-writer fence, the level-up announce/log is an AnnouncementRouteSpec (G-3), rank/leaderboard is a LeaderboardSpec + read-model provider, and the on_message hook is a declared message-stage/gateway listener (G-1); admin give/reset stay thin audited seams and the bot-to-bot import stays a registered escape-hatch tool.
- **Dependency layer:** L1 progression kernel (curve + earn + xp store) built on the currency/store kernel; needs L2 leaderboard read-model + L2 announcement routing; level-role grant is an L3 dependency on the role-automation lane.
- **Production-grade done:** Parity golden: identical XP-per-message (random xp_min..xp_max, xp_cooldown-gated, participation-gated), identical curve (5L^2+50L+100), identical level-up announce + server-log + threshold-role grant, identical rank/leaderboard ordering, raise-only import producing byte-identical results, and audit rows for reset + import.
- **Outperform target:** MEE6 / Arcane / Amari (leveling incumbents) -- beat on per-guild declarative curve config, transparent rank cards, and one-click cross-bot import; or pending Lane F.

**Cross-lane dependencies**

- role-automation lane: xp_role_sync + role_automation + role_exemption_service grant XP threshold roles on level-up and import (listener.py:184, xp_migration.py:211); XP only triggers, does not own
- economy lane: xp table shares a coins column owned by economy; rank card + CoinsProvider read coins (split store ownership)
- server-logging lane: post_log_embed level-up log + audit.action_recorded fanout on reset/import (listener.py:179, xp_service.py:247)
- leaderboard lane: rank_providers/leaderboard_cog consume XpProvider; !rank routes across all providers (mining/creature/fishing/etc.)
- core.runtime substrate: message_pipeline (stage registry), participation_schema + feature_flags (participation gate), config_arbitration + binding/settings mutation pipelines
- xp threshold-role config/store (migrations/003_role_xp_thresholds.sql) is read via get_xp_threshold_roles but is owned by the role subsystem, not XP

**⚠ Unverified / judgment calls**

- utils/rank_render.py internals not fully read -- confirmed render_rank_card is a generic parameterized engine (declarative stats/progress/theme inputs), so the rank card is classified tier-2 read-model, not a tier-3 renderer_override; deep Pillow layout unread
- utils/xp_migration.py parser/format-registry line numbers not pinned (formats: arcane/mee6/superbot/generic; parse_level_message); classified tier-3 from the cog/service call sites
- migrations/003_role_xp_thresholds.sql not opened -- XP-threshold-role store assumed owned by the role subsystem (XP consumes via get_xp_threshold_roles); not counted as an XP-owned store
- subsystem_registry.py xp entry read only via grep (lines 388-409): 3 capabilities + tags confirmed; full entry_points list not enumerated
- !leaderboard xp path lives in leaderboard_cog (separate subsystem) -- XP's leaderboard contribution counted once as XpProvider/LeaderboardSpec, not the leaderboard hub command surface
- G-14 ParticipationPrefSpec is a proposed new id; the 5 participation/visibility/notification/preference units are scored tier-1 as user-scoped SettingSpecs, so fit is unaffected whether or not G-14 is adopted

---

### casino
_cogs/source: disbot/cogs/casino_cog.py · views/casino/* · utils/poker/* · utils/cards/* (no DB/settings/events)_

| Unit | Kind | File:line | Tier (as-written) | Tier (with amendments) | Rationale / gap |
|---|---|---|---|---|---|
| !casino command → hub open | command | disbot/cogs/casino_cog.py:40 | 1 | 1 | Command → build_casino_hub_panel; pure open-panel route, no domain code → kernel PanelRef workflow. |
| !poker (+holdem) command → launch table | command | disbot/cogs/casino_cog.py:46 | 3 | 3 | Handler calls poker_table.launch_table (in-memory session create + lobby post + dedupe-per-channel). Lobby-creation orchestration, no primitive as-written; G-14 MultiSeatTableSessionSpec makes it a declared session-open route (no money/deal here). [ADVERSARIAL: G-15 refuted→FOLD; ChallengeSessionSpec covers only the session lifecycle+ephemeral store — this lobby/broadcast/move/renderer stays tier-3 per §2.9/§10.1 (blackjack precedent)]. |
| build_help_menu_view help hook / help entry | help | disbot/cogs/casino_cog.py:67 | 1 | 1 | Returns the hub panel — help-as-projection / Games-hub navigation hook. Pure declaration. |
| Casino hub panel (CasinoHubView + build_casino_hub_embed) | panel | disbot/views/casino/hub.py:23 | 1 | 1 | Router panel, static descriptive fields + nav buttons. No read-model, no state → tier-1 config/navigation panel (PanelSpec, HubView child). |
| Hub action: New Poker Table | panel-action | disbot/views/casino/hub.py:58 | 3 | 3 | Second seam onto launch_table (dedupe + create + ephemeral confirm). Same lobby-create orchestration as !poker → G-14 declared session-open action. [ADVERSARIAL: G-15 refuted→FOLD; ChallengeSessionSpec covers only the session lifecycle+ephemeral store — this lobby/broadcast/move/renderer stays tier-3 per §2.9/§10.1 (blackjack precedent)]. |
| Hub action: Roulette (disabled placeholder) | panel-action | disbot/views/casino/hub.py:101 | 1 | 1 | Disabled button, sends 'coming soon'. Pure declaration / nav placeholder. |
| Public lobby+board panel renderer (_public_embed/_lobby_public_embed) | renderer | disbot/views/casino/poker_table.py:458 | 3 | 3 | Live spectator board over PokerGame state (board, pot, per-seat status, results). Stateful game-board renderer → renderer_override, §2.9 named escape hatch by design. |
| Per-player private ephemeral hand panel renderer (_seat_embed) | renderer | disbot/views/casino/poker_table.py:421 | 3 | 3 | Renders each seat's private hole cards / to-call / turn from game state. Per-player game-board renderer → renderer_override escape hatch by design. |
| Lobby: Join button → add_player | panel-action | disbot/views/casino/poker_table.py:573 | 3 | 3 | Seat-join choreography: full-table/started/dup guards, seat append, sends ephemeral seat panel + captures webhook handle for broadcast. No primitive as-written; G-14 lobby-join kernel workflow. [ADVERSARIAL: G-15 refuted→FOLD; ChallengeSessionSpec covers only the session lifecycle+ephemeral store — this lobby/broadcast/move/renderer stays tier-3 per §2.9/§10.1 (blackjack precedent)]. |
| Lobby: Leave button → remove_player | panel-action | disbot/views/casino/poker_table.py:581 | 3 | 3 | Seat-leave choreography (drop seat/handle, edit ephemeral, refresh public). G-14 lobby-leave kernel workflow. [ADVERSARIAL: G-15 refuted→FOLD; ChallengeSessionSpec covers only the session lifecycle+ephemeral store — this lobby/broadcast/move/renderer stays tier-3 per §2.9/§10.1 (blackjack precedent)]. |
| Lobby: Start button → table.start (build engine + deal) | panel-action | disbot/views/casino/poker_table.py:589 | 3 | 3 | Host-auth + min-players guard, builds Player list, constructs PokerGame, begin_hand (engine deal — counted as engine unit), schedule turn, broadcast. Seam is thin (no bet-parse/escrow, unlike blackjack.start); G-14 session-start transition, engine is the separate escape hatch. [ADVERSARIAL: G-15 refuted→FOLD; ChallengeSessionSpec covers only the session lifecycle+ephemeral store — this lobby/broadcast/move/renderer stays tier-3 per §2.9/§10.1 (blackjack precedent)]. |
| Lobby: Close button → cancel/_teardown (host) | panel-action | disbot/views/casino/poker_table.py:597 | 3 | 3 | Host-only session close: teardown edits messages + drops registry. Generic session-close → kernel workflow (auth is declarative capability). G-14 close. [ADVERSARIAL: G-15 refuted→FOLD; ChallengeSessionSpec covers only the session lifecycle+ephemeral store — this lobby/broadcast/move/renderer stays tier-3 per §2.9/§10.1 (blackjack precedent)]. |
| SeatLobby: Leave seat button (ephemeral) | panel-action | disbot/views/casino/poker_table.py:613 | 3 | 3 | Ephemeral-surface variant of Leave → remove_player. Same G-14 lobby-leave workflow (distinct surface). [ADVERSARIAL: G-15 refuted→FOLD; ChallengeSessionSpec covers only the session lifecycle+ephemeral store — this lobby/broadcast/move/renderer stays tier-3 per §2.9/§10.1 (blackjack precedent)]. |
| End: Deal next hand button → deal_next_hand | panel-action | disbot/views/casino/poker_table.py:633 | 3 | 3 | Host-auth, funded-player check (<2 funded → teardown, declaring table winner), engine begin_hand (deal), reschedule, broadcast. Multi-hand continuation choreography → G-14; funded-gate is declarable session rule; engine deal counted separately. [ADVERSARIAL: G-15 refuted→FOLD; ChallengeSessionSpec covers only the session lifecycle+ephemeral store — this lobby/broadcast/move/renderer stays tier-3 per §2.9/§10.1 (blackjack precedent)]. |
| End: End table button → _teardown (host) | panel-action | disbot/views/casino/poker_table.py:645 | 3 | 3 | Host-only teardown. Generic session close → kernel workflow. G-14/kernel. [ADVERSARIAL: G-15 refuted→FOLD; ChallengeSessionSpec covers only the session lifecycle+ephemeral store — this lobby/broadcast/move/renderer stays tier-3 per §2.9/§10.1 (blackjack precedent)]. |
| Seat move: Fold | panel-action | disbot/views/casino/poker_table.py:712 | 3 | 3 | handle_action(FOLD): turn-owner check, refresh webhook handle, engine.act, advance/broadcast. Game-move handler over engine rules → escape hatch (mirrors blackjack hit/stand). |
| Seat move: Check | panel-action | disbot/views/casino/poker_table.py:721 | 3 | 3 | Game-move handler (engine.act CHECK), gated by legal_actions. Escape hatch by design. |
| Seat move: Call | panel-action | disbot/views/casino/poker_table.py:731 | 3 | 3 | Game-move handler (engine.act CALL, amount from legal_actions). Escape hatch by design. |
| Seat move: Raise/Bet (min/pot/all-in presets, one action) | panel-action | disbot/views/casino/poker_table.py:742 | 3 | 3 | engine.act(RAISE, raise_to=…); the min/pot/all-in preset computation + legal-actions gating is game logic. Escape hatch by design. |
| Per-turn idle timeout auto-check/fold timer (_turn_timeout/_schedule_turn) | task | disbot/views/casino/poker_table.py:329 | 3 | 3 | asyncio per-turn clock: on TURN_SECONDS, auto-check if free else fold so AFK can't stall. Declaration maps to session turn_timeout_s (ManagedTask/ChallengeSession field) → G-14; handler is thin extract-and-route (never lose chips to AFK). [ADVERSARIAL: G-15 refuted→FOLD; ChallengeSessionSpec covers only the session lifecycle+ephemeral store — this lobby/broadcast/move/renderer stays tier-3 per §2.9/§10.1 (blackjack precedent)]. |
| Per-player ephemeral broadcast fan-out (_broadcast/_refresh_public) | renderer-infra | disbot/views/casino/poker_table.py:352 | 3 | 3 | The marquee mechanic: re-render + edit every seat's stored InteractionMessage webhook handle + the public board on any state change. Bespoke as-written; G-14 declares 'per-seat private ephemeral broadcast' as a kernel session capability (renderers stay tier-3, the fan-out plumbing does not). [ADVERSARIAL: G-15 refuted→FOLD; ChallengeSessionSpec covers only the session lifecycle+ephemeral store — this lobby/broadcast/move/renderer stays tier-3 per §2.9/§10.1 (blackjack precedent)]. |
| In-memory session store (_tables dict, ephemeral) | store | disbot/views/casino/poker_table.py:59 | 3 | 2 | One PokerTable per channel_id in a module dict; NO DB table, NO persistence, not restart-safe (ADR-002). StoreSpec is DB-only, so no primitive as-written; G-14 persistence='ephemeral' declares the in-memory registry (upgradeable to checkpointed). [ADVERSARIAL: lifts via EXISTING ChallengeSessionSpec (as blackjack.tournament), NOT a new G-15 family]. |
| Poker betting engine (blinds/rounds/side pots/showdown payout) | engine | disbot/utils/poker/engine.py:97 | 3 | 3 | Pure PokerGame state machine: blinds, betting rounds, all-ins, side pots, uncontested/showdown settlement, odd-chip rule. Game rules → escape hatch by design (§10.1 risk 5: grammar must never express game rules). |
| Poker hand evaluator (5-of-7 ranking, split-pot ties) | engine | disbot/utils/poker/evaluate.py:1 | 3 | 3 | Pure best_hand/score_five: brute-force C(n,5) ranking into totally-ordered tuples for compare + tie detection. Game rules → escape hatch by design. |
| Poker table session lifecycle (lobby→multi-hand→teardown, rotating button/blinds, settle-once side-pot payout) | session | disbot/views/casino/poker_table.py:109 | 3 | 2 | The declarable choreography. ChallengeSessionSpec is 1v1/single-message/ephemeral and does NOT cover multi-seat (2–8), multi-hand continuous play, or per-player ephemeral fan-out → tier-3 as-written. G-14 MultiSeatTableSessionSpec declares it (turn clock, settle-once, ephemeral persistence, seats). [ADVERSARIAL: lifts via EXISTING ChallengeSessionSpec (as blackjack.tournament), NOT a new G-15 family]. |

**Fit:** 25 units · tier-1/2 as-written **16%** (4/25) · with amendments **24%** (6/25).

**§2 manifest sketch**

```python
from tools.grammar_spike.spec import (
    SubsystemManifest, CommandSpec, CommandKind, PanelSpec, PanelActionSpec,
    HandlerRef, PanelRef, HelpEntrySpec,
)
# G-14 (proposed): MultiSeatTableSessionSpec / GameFacet.tables — NOT in spec.py yet.
# from tools.grammar_spike.spec import MultiSeatTableSessionSpec  # G-14

CASINO_MANIFEST = SubsystemManifest(
    key="casino",
    display_name="Casino",
    description="Group casino card games — everyone gets a private live-updating hand.",
    emoji="🎰",
    category="games",
    parent_hub="games",
    # NO settings / bindings / resources / events / subscriptions / gateway_listeners:
    # play-chips only, no economy, no DB, no bus (verified: casino_cog has none).
    commands=(
        CommandSpec(name="casino", kind=CommandKind.PREFIX,
            summary="Open the Casino hub.",
            route=PanelRef("casino.hub")),                         # tier 1
        CommandSpec(name="poker", aliases=("holdem",), kind=CommandKind.PREFIX,
            summary="Open a multiplayer Texas Hold'em table here.",
            route=HandlerRef("casino.poker_launch",
                justification="lobby create; G-14 makes this a session-open route")),  # tier3→2
    ),
    panels=(
        # Router hub — static content + nav (tier 1)
        PanelSpec(panel_id="casino.hub", subsystem="casino", title="🎰 Casino",
            actions=(
                PanelActionSpec(action_id="new_poker", label="New Poker Table",
                    style="success",
                    handler=HandlerRef("casino.poker_launch")),    # tier3→2 (G-14)
                PanelActionSpec(action_id="roulette", label="Roulette (soon)",
                    handler=PanelRef("casino.hub")),               # tier 1 (disabled)
            )),
        # Live poker table: renderer_override for BOTH public board and per-seat
        # ephemeral hand — tier-3 game-board renderers by design (§2.9).
        PanelSpec(panel_id="casino.poker.board", subsystem="casino", title="♠ Poker Table",
            renderer_override=HandlerRef("casino.render_public_board",
                justification="live multi-seat board over PokerGame state"),
            actions=(
                # in-hand moves — tier-3 game moves (engine.act)
                PanelActionSpec(action_id="fold", label="Fold", style="danger",
                    handler=HandlerRef("casino.poker_move.fold", justification="game move")),
                PanelActionSpec(action_id="check", label="Check",
                    handler=HandlerRef("casino.poker_move.check", justification="game move")),
                PanelActionSpec(action_id="call", label="Call",
                    handler=HandlerRef("casino.poker_move.call", justification="game move")),
                PanelActionSpec(action_id="raise", label="Raise",
                    handler=HandlerRef("casino.poker_move.raise", justification="game move")),
            )),
    ),
    # game=GameFacet(tables=(  # G-14 — proposed multi-seat family
    #   MultiSeatTableSessionSpec(
    #       game_key="casino.poker",
    #       min_seats=2, max_seats=8, seat_stake="1000 play-chips",
    #       lobby_workflow="join/leave/start/close",   # kernel choreography (tier1-2)
    #       per_seat_ephemeral_broadcast=True,          # the marquee fan-out (kernel infra)
    #       turn_timeout_s=90, turn_timeout_action="check_else_fold",
    #       settle_once=True, persistence="ephemeral",  # ADR-002; upgradeable→checkpointed
    #       engine=HandlerRef("casino.poker_engine"),   # tier-3 rules, sole escape hatch
    #       renderer=HandlerRef("casino.render_seat"),  # tier-3 per-seat renderer
    #   ),
    # )),
    help=HelpEntrySpec(
        summary="Group Texas Hold'em, 2–8 seats; private live hands; play-chips.",
        examples=("!casino", "!poker"),
    ),
)
```

**Tier-3 dispositions**

| Tier-3 unit | Verdict | Reason |
|---|---|---|
| !poker command / New Poker Table (launch_table) | escape-hatch (tier-3 by §2.9/§10.1) | [ADVERSARIAL] Refuted as a grammar gap: the lobby/broadcast/game-move/renderer/engine is legitimate tier-3 game logic (blackjack precedent — the grammar must never express game rules). Stays tier-3; NOT a new family. |
| Public board renderer (_public_embed) | escape-hatch | Stateful game-board renderer over PokerGame — §2.9 renderer_override, kernel should NOT own live board layout. |
| Per-player ephemeral hand renderer (_seat_embed) | escape-hatch | Per-seat game-board renderer (hole cards/to-call/turn) — renderer_override by design. |
| Lobby Join / Leave / Leave-seat (add_player/remove_player) | escape-hatch (tier-3 by §2.9/§10.1) | [ADVERSARIAL] Refuted as a grammar gap: the lobby/broadcast/game-move/renderer/engine is legitimate tier-3 game logic (blackjack precedent — the grammar must never express game rules). Stays tier-3; NOT a new family. |
| Lobby Start (table.start) | escape-hatch (tier-3 by §2.9/§10.1) | [ADVERSARIAL] Refuted as a grammar gap: the lobby/broadcast/game-move/renderer/engine is legitimate tier-3 game logic (blackjack precedent — the grammar must never express game rules). Stays tier-3; NOT a new family. |
| Deal next hand (deal_next_hand) | escape-hatch (tier-3 by §2.9/§10.1) | [ADVERSARIAL] Refuted as a grammar gap: the lobby/broadcast/game-move/renderer/engine is legitimate tier-3 game logic (blackjack precedent — the grammar must never express game rules). Stays tier-3; NOT a new family. |
| Close / End table (cancel/_teardown) | escape-hatch (tier-3 by §2.9/§10.1) | [ADVERSARIAL] Refuted as a grammar gap: the lobby/broadcast/game-move/renderer/engine is legitimate tier-3 game logic (blackjack precedent — the grammar must never express game rules). Stays tier-3; NOT a new family. |
| Seat moves Fold/Check/Call/Raise (handle_action → engine.act) | escape-hatch | Game-move handlers over engine rules incl. legal_actions gating + raise-preset computation — must stay code (mirrors blackjack hit/stand/double). |
| Per-turn idle timeout auto-check/fold (_turn_timeout) | escape-hatch (tier-3 by §2.9/§10.1) | [ADVERSARIAL] Refuted as a grammar gap: the lobby/broadcast/game-move/renderer/engine is legitimate tier-3 game logic (blackjack precedent — the grammar must never express game rules). Stays tier-3; NOT a new family. |
| Per-player ephemeral broadcast fan-out (_broadcast) | escape-hatch (tier-3 by §2.9/§10.1) | [ADVERSARIAL] Refuted as a grammar gap: the lobby/broadcast/game-move/renderer/engine is legitimate tier-3 game logic (blackjack precedent — the grammar must never express game rules). Stays tier-3; NOT a new family. |
| In-memory _tables session store | fold→ChallengeSessionSpec.persistence=ephemeral | [ADVERSARIAL] The session's ephemeral in-memory state is declared by ChallengeSessionSpec.persistence=ephemeral (the spike counts blackjack's game_state store as tier-2 the same way). Not restart-safe by ADR-002 — declaring persistence=ephemeral is the honest port. |
| Poker betting engine (engine.py PokerGame) | escape-hatch | Pure game rules (blinds/betting/side pots/showdown) — grammar must never express game rules (§10.1 risk 5). |
| Poker hand evaluator (evaluate.py) | escape-hatch | Pure 5-of-7 hand ranking + tie detection — game rules, deliberate escape hatch. |
| Poker table session lifecycle | fold→ChallengeSessionSpec (existing) | [ADVERSARIAL] Multi-player session folds into the EXISTING ChallengeSessionSpec exactly as blackjack.tournament does (spike-accepted tier-2). No new family — the first-pass 'G-14/G-15 MultiSeatTableSessionSpec' is REFUTED; at most add optional max_seats/lobby_policy fields to ChallengeSessionSpec. Session store rides ChallengeSessionSpec.persistence. |

**Structural-gap flags**

- **stateful multi-seat live game loop** — `needs-new-primitive` — The marquee. 2–8 seat live betting loop with lobby→multi-hand→teardown, rotating button/blinds, turn clock. ChallengeSessionSpec (1v1/ephemeral/single-message) does not cover it → needs G-14 MultiSeatTableSessionSpec. Engine + renderers stay tier-3 by design.
- **per-player private ephemeral broadcast fan-out** — `needs-new-primitive` — Novel vs karma/logging/blackjack: each seat gets a private auto-updating ephemeral message re-edited via stored webhook handles on every state change (poker_table.py:352-366). Must be a declared kernel session capability (G-14); no existing family.
- **deep persistent state** — `with-amendment:G-14` — NONE persisted — in-memory _tables, not restart-safe (ADR-002, poker_table.py:57-59). Danger is the OPPOSITE of persistence: crash-loss of a live table. G-14 persistence field (ephemeral→checkpointed) is the lever.
- **scheduled loop + timeout** — `with-amendment:G-14` — Per-turn asyncio idle clock (not @tasks.loop): auto-check/fold AFK seats (poker_table.py:317-348). Maps to session turn_timeout_s + turn_timeout_action.
- **escrow / settlement + double-settle risk** — `with-amendment:G-14` — Play-chips only, in-memory — no cross-subsystem escrow. Side-pot payout IS a settle-once concern but lives inside the engine (_settle_showdown, chips move once on win). settle_once=True on G-14 covers the session-level guard; engine owns pot math.
- **transactional multi-write money mutation / irreversible economy op** — `needs-new-primitive` — N/A today (no money). The documented monetization follow-up (engine.py:9-13 'real-coin buy-ins need N-party escrow via game_wager_workflow') would require G-7 EconomyTransactionSpec + an economy dependency — flagged, not shipped.
- **XP / leaderboard derivation** — `no` — NO leaderboard, NO stat writes, NO persistence shipped. A poker wins/earnings board is impossible without a store — a real gap if the rebuild wants records (would need a StoreSpec + stat_writes, currently absent by design).
- **inventory/item taxonomy · mining grid · creature battle · farm growth · wait_for wizard** — `yes` — None present (verified). Button-driven, no wait_for, no items, no world state.

**MAP → RECONSIDER → SIMULATE → OPTIMIZE**

- **Verdict:** keep · **status:** ok — self-contained, no owner-gated or external dependency as-shipped (play-chips, no DB, no bus). Monetization (real-coin buy-ins) would be owner-gated and pull in the economy lane.
- **Optimal new-bot form:** Keep casino, well-layered already (pure tested engine/evaluator + thin renderer). Rebuild it as a declared G-14 MultiSeatTableSessionSpec that drives lobby/seats/turn-clock/per-player-ephemeral-broadcast as kernel choreography; the Hold'em rules stay a tier-3 pure engine and the public-board + per-seat panels stay tier-3 renderer_overrides — the only code the subsystem owns. Optionally add checkpointed persistence for restart-safety and a poker records store/leaderboard.
- **Dependency layer:** L3 game on (L1 session-kernel providing G-14 multi-seat lifecycle + ephemeral broadcast) + (L2 shared card/eval libs: utils/cards, utils/poker). No L1 currency dep as-shipped (play-chips); adding real-coin buy-ins would introduce an L1 economy dependency via G-7 EconomyTransactionSpec / INV-F escrow.
- **Production-grade done:** Parity golden: a full multi-seat hand plays out identically to shipped — blinds posted, all four betting rounds, all-in side pots + odd-chip rule, uncontested and showdown settlement, per-player private ephemeral hands updating live on every action, 90s turn-timeout auto-check/fold, host deal-next / teardown — and the utils/poker engine+evaluator unit tests pass unchanged. Restart behavior matches ADR-002 (or clean checkpoint-resume if upgraded).
- **Outperform target:** pending Lane F — the per-player live-ephemeral group table is already a strong differentiator vs mainstream Discord poker bots; beat best-in-class by adding restart-safe checkpointed tables, real-economy buy-ins/tournaments, and persistent poker records/leaderboards (all impossible today: no store).

**Cross-lane dependencies**

- None as-shipped: casino is fully self-contained (no economy, no DB, no bus/audit, no settings — verified in casino_cog.py).
- Shares utils/cards (52-card primitives) with blackjack — a common L2 card library, not a runtime coupling.
- Shares utils/poker with nothing else today; evaluator serves 5-card and 7-card so reusable by any future poker/draw game.
- Latent economy dependency (Lane B economy / G-7 EconomyTransactionSpec, INV-F seam) IF real-coin buy-ins are added — engine.py:9-13 documents the game_wager_workflow N-party-escrow follow-up, deliberately out of v1.
- Roulette (and future group games) are stubbed to dock into the same hub + G-14 table framework (hub.py:41-45) — a forward intra-lane dep on the proposed primitive.

**⚠ Unverified / judgment calls**

- utils/cards/__init__.py not read in full — treated as shared pure 52-card primitives (imported by both poker engine and blackjack), so NOT counted as a casino-specific surface unit; its tier is irrelevant (pure library).
- evaluate.py read only through line 40 (docstring + HandCategory); its internal scoring is not line-by-line verified, but its role (pure hand-ranking rules) and tier-3 escape-hatch classification are unambiguous from the module contract and engine import.
- Raise/Bet counted as ONE move unit though the UI emits up to 3 buttons (min / pot / all-in presets, poker_table.py:742-779) — one action_id (RAISE) with different raise_to params; counting the presets separately would inflate tier-3 by 2 without changing the disposition.
- Table-tuning constants (START_STACK/SMALL_BLIND/BIG_BLIND/MAX_SEATS/TURN_SECONDS, poker_table.py:48-55) are hardcoded, NOT shipped settings — deliberately NOT counted as setting units; noted as would-be G-14 session-spec fields / SettingSpecs in the optimal form.

---

### four_twenty
_cogs/source: disbot/cogs/four_twenty_cog.py (message-pipeline stage; no DB/economy/XP writes)_

| Unit | Kind | File:line | Tier (as-written) | Tier (with amendments) | Rationale / gap |
|---|---|---|---|---|---|
| !420 command (aliases fourtwenty, fourtwenty420) → opens overview panel | command | disbot/cogs/four_twenty_cog.py:181-193 | 1 | 1 | Pure panel-open: builds _FourTwentyPanelView and send_panel(overview embed). CommandSpec route=PanelRef → kernel open-panel workflow, zero domain code. |
| !420 command cooldown @commands.cooldown(rate=3, per=10, user) | command-cooldown | disbot/cogs/four_twenty_cog.py:180 | 3 | 2 | §2.2 CommandSpec as-written has no cooldown field → shipped anti-abuse rate-limit is lost at port (tier-3). G-4 CommandSpec.cooldown makes it declared data (tier-2). Same class as karma_cog cooldowns. |
| _FourTwentyPanelView (overview panel) + open/re-render | panel | disbot/cogs/four_twenty_cog.py:151-161,204-213 | 1 | 1 | Static overview embed + BaseView(public, timeout=300) with three buttons; no config choreography, no game board. PanelSpec + navigation → kernel open/re-render workflow, tier-1. |
| wisdom_btn action → random wisdom line → edit_message | panel-action | disbot/cogs/four_twenty_cog.py:218-230 | 2 | 2 | Read-model action: random.choice over the wisdom content pool rendered as a text/fields block. ProviderRef (thin random-pick provider), no mutation/domain logic → tier-2 (a declarative ContentPoolBlock/G-15 would make it tier-1). [ADVERSARIAL: random content pool via EXISTING ProviderRef, not a new ContentPoolBlock family]. |
| fact_btn action → random 420 fact → edit_message | panel-action | disbot/cogs/four_twenty_cog.py:232-244 | 2 | 2 | Same ProviderRef read-model over the facts pool; thin random-pick, no domain logic → tier-2 (tier-1 with a ContentPoolBlock). [ADVERSARIAL: random content pool via EXISTING ProviderRef, not a new ContentPoolBlock family]. |
| overview_btn action → re-render overview embed | panel-action | disbot/cogs/four_twenty_cog.py:246-252 | 1 | 1 | Pure navigation/re-render back to the overview panel — kernel workflow, tier-1. |
| FourTwentyStage — message-pipeline listener (order=50, per-channel cooldown, 🍃-react + optional canned line on 420/blaze-it/four-twenty regex) | listener | disbot/cogs/four_twenty_cog.py:107-148 (registered cog_load :174-175) | 3 | 3 | §2 has no primitive for MessageStage/gateway listeners → tier-3 as-written. G-1 GatewayListenerSpec declares the wiring/gate; the residual handler (regex trigger + per-channel cooldown + reaction + 50%-random line) is thin/no-domain-logic. A dedicated AutoResponderSpec (proposed G-14) declares the whole thing as data → tier-1. Counted conservatively at tier-2. [ADVERSARIAL: G-20 refuted→FOLD; G-1 declares the message-stage listener but the keyword-match/pick-response rule is one-off domain logic that stays tier-3]. |
| build_help_menu_view — help-menu direct-navigation hook | help | disbot/cogs/four_twenty_cog.py:195-201 | 1 | 1 | Returns overview embed + panel view for the Help hub; kernel help-navigation projection → tier-1. |
| command help text ('Open the 🍃 420 panel — rotating wisdom and number trivia') | help | disbot/cogs/four_twenty_cog.py:184 | 1 | 1 | HelpEntrySpec — help-as-projection, tier-1. |
| SUBSYSTEMS['four_twenty'] manifest metadata (display_name, description, emoji, color, category, tags, entry_points, ui_priority, parent_hub, supports_dm) | setting | disbot/utils/subsystem_registry.py:1031-1052 | 1 | 1 | Pure registry declaration → maps directly onto SubsystemManifest root fields, tier-1. |
| capability four_twenty.panel.view | setting | disbot/utils/subsystem_registry.py:1049-1051 | 1 | 1 | Declared capability string on the manifest — tier-1. |
| wisdom/facts content pools (20 wisdom + 6 fact strings, loaded from JSON into cog state) | resource | disbot/data/json/four_twenty_content.json (loaded four_twenty_cog.py:98-104,169-171) | 1 | 1 | Static string-list content backing the two providers; pure declared data (belongs inline in the manifest as a content pool) → tier-1. |

**Fit:** 12 units · tier-1/2 as-written **83%** (10/12) · with amendments **92%** (11/12).

**§2 manifest sketch**

```python
FOUR_TWENTY = SubsystemManifest(
    key="four_twenty",
    display_name="420",
    description="A leafy little easter-egg panel — wisdom and number trivia",
    emoji="🍃",
    color_token="general",
    category="utility",
    visibility_tier="user",
    capabilities=("four_twenty.panel.view",),
    parent_hub="utility",
    ui_priority=4,
    commands=(
        CommandSpec(
            name="420", kind=CommandKind.PREFIX,
            aliases=("fourtwenty", "fourtwenty420"),
            summary="Open the 🍃 420 panel — rotating wisdom and number trivia.",
            route=PanelRef("four_twenty.overview"),
            cooldown=(3, 10, "user"),          # G-4: shipped @commands.cooldown
            audience_tier="user",
        ),
    ),
    panels=(
        PanelSpec(
            panel_id="four_twenty.overview", subsystem="four_twenty",
            title="🍃 420", audience="public", timeout_s=300,
            body=(
                BlockSpec(kind="text", text="Take it easy. Pick an option below."),
            ),
            actions=(
                # read-model over content pools (tier-2 ProviderRef; tier-1 with a
                # ContentPoolBlock/G-15). random pick is thin, no domain logic.
                PanelActionSpec(action_id="wisdom", label="🍃 Wisdom",
                    handler=ProviderRef("four_twenty.random_wisdom"),
                    result_render="rerender", style="green"),
                PanelActionSpec(action_id="fact", label="🔢 420 Fact",
                    handler=ProviderRef("four_twenty.random_fact"),
                    result_render="rerender", style="primary"),
                PanelActionSpec(action_id="overview", label="↩ Overview",
                    handler=WorkflowRef("panel_rerender",
                        (("panel", "four_twenty.overview"),))),
            ),
            navigation=NavigationSpec(show_help=True, show_home=True),
        ),
    ),
    # G-1 covers the wiring; the IDEAL is a G-14 AutoResponderSpec that declares
    # trigger+reaction+response+cooldown as pure data (then tier-1):
    gateway_listeners=(
        GatewayListenerSpec(
            gateway_event="message_pipeline_stage:passive@50",
            handler=HandlerRef("four_twenty.egg_react",
                justification="observe-only 🍃-react; thin pattern→reaction, "
                              "no mutation — kernel should own via G-14"),
        ),
    ),
    # === proposed G-14 form (fully declarative, replaces the listener above) ===
    # auto_responders=(AutoResponderSpec(
    #     trigger=r"(?<!\\d)4[:\\-\\s]?20(?!\\d)|blaze\\s*it|four[\\s\\-]?twenty",
    #     reaction="🍃", response_pool="four_twenty.egg_lines",
    #     response_probability=0.5, per_channel_cooldown_s=90, observe_only=True,
    #     order="passive"),),
    help=HelpEntrySpec(
        summary="Open the 🍃 420 panel — rotating wisdom and number trivia.",
        examples=("!420",),
    ),
    version=1,
)
# content pools = declared data (tier-1), e.g. resource/content registry:
#   four_twenty.wisdom = (... 20 strings ...); four_twenty.facts = (... 6 ...)
# NO stores, NO events/subscriptions, NO tasks, NO game facet — observe-only.
```

**Tier-3 dispositions**

| Tier-3 unit | Verdict | Reason |
|---|---|---|
| !420 command cooldown @commands.cooldown(3,10,user) | grammar-gap:G-4 | §2.2 CommandSpec has no cooldown field; G-4 CommandSpec.cooldown makes the shipped rate-limit declared data. Not an escape hatch — trivial anti-abuse the kernel owns. |
| FourTwentyStage message-pipeline listener (regex trigger + per-channel cooldown + 🍃-react + 50% random line) | escape-hatch (listener via G-1; match/react tier-3) | [ADVERSARIAL] G-20 AutoResponderSpec REFUTED→fold: G-1 GatewayListenerSpec declares the observe-only message-stage listener; the keyword-match/pick-response rule is one-off domain logic that stays tier-3. No new family. |

**Structural-gap flags**

- **message-pipeline listener stage (observe-only; on_message-class hook via MessageStage, order=50)** — `with-amendment:G-1` — §2 has EventSpec/EventSubscription but no gateway/message-listener primitive. G-1 declares the wiring; verified observe-only (returns empty StageResult in every path, never deletes/short-circuits — four_twenty_cog.py:132-148).
- **keyword/regex auto-responder (content pattern → reaction + canned response, per-channel cooldown, probability)** — `needs-new-primitive` — Recurring 'keyword-trigger response' pattern not covered by G-1..G-13 (they are economy/game). Propose G-14 AutoResponderSpec so the whole behavior is declared data (tier-1). This is the subsystem's core surface.
- **rotating/random content-pool rendering (wisdom & facts random-pick blocks)** — `with-amendment:G-15` — Expressible today at tier-2 via ProviderRef (thin random-pick). A declarative ContentPoolBlock (G-15: declared string pool + random/rotating pick) lifts both button actions to tier-1; the pattern recurs (General cog panel shape this mirrors).
- **command cooldown (@commands.cooldown 3/10s/user)** — `with-amendment:G-4` — CommandSpec.cooldown (already-proposed G-4).
- **deep persistent state / transactional mutation / escrow / inventory / grid-battle-farm / XP-leaderboard / scheduled loop / irreversible economy op / stateful game loop / wait_for wizard** — `yes` — NONE PRESENT — verified observe-only/stateless: no DB writes, no bus.emit, no @tasks.loop, no wait_for, no store, no game facet (full read of four_twenty_cog.py + registry). The docstring's 'no state mutation' claim is confirmed against source.

**MAP → RECONSIDER → SIMULATE → OPTIMIZE**

- **Verdict:** keep · **status:** ok
- **Optimal new-bot form:** A ~40-line fully declarative SubsystemManifest: one PanelSpec with a rotating ContentPoolBlock (wisdom/facts pools inline as data) and a single AutoResponderSpec (regex trigger → 🍃 reaction + probabilistic canned line + per-channel cooldown, observe_only, passive order) — zero domain code. It is the grammar's easiest, purest declarative win in Lane B.
- **Dependency layer:** L0 — pure presentation/easter-egg. No economy/store/XP dependency; needs only the kernel panel workflow, the passive message-listener band (order relative to auto-mod/rewards/AI stages), and content-pool + auto-responder primitives.
- **Production-grade done:** Parity golden: (1) !420 (and aliases) opens the 🍃 overview panel, buttons rotate distinct wisdom/facts, ↩ returns; (2) a message containing 420 / 4:20 / blaze it / four twenty gets a 🍃 react + ~50% a canned line; (3) per-channel 90s cooldown honored; (4) command cooldown 3/10s/user honored; (5) listener is observe-only — never deletes/short-circuits, runs before the AI stage so '@bot … blaze it' still gets its 🍃; (6) no DB/economy/XP side effects.
- **Outperform target:** pending Lane F — beat generic keyword-responder bots (MEE6 / Carl-bot custom auto-responses) by making the responder a first-class declared AutoResponderSpec with probability + cooldown + observe-only pipeline placement, not a hand-wired on_message handler.

**Cross-lane dependencies**

- Shares the core.runtime.message_pipeline MessageStage ordering contract with xp (Lane B on_message stage), auto-mod (order 10/15/20), rewards (30/40), and the AI natural-language stage (70) — FourTwentyStage sits at order=50 specifically to run before AI short-circuit; the new-bot passive-listener band must preserve this cross-subsystem ordering.
- Deferred (NOT implemented) 'balance/score lands on 420' wink would consume economy.balance_changed / xp.awarded events (economy + xp lanes); docstring notes those payloads carry no channel to react in, so it needs an events-catalogue payload change first.

**⚠ Unverified / judgment calls**

- core.runtime.message_pipeline register()/unregister()/StageResult internal contract not read directly — the stage protocol (name/order/async process → StageResult) is inferred from usage in four_twenty_cog.py:45-50,132-148,174-178; observe-only behavior IS verified from the stage body (empty StageResult in every path).
- ContentPoolBlock/G-15 recurrence in the General cog ('mirroring the General cog's panel shape', docstring line 5 / view comment) asserted from the four_twenty docstring, not confirmed by reading general_cog source.

---

### counters
_cogs/source: disbot/cogs/counters_cog.py + cogs/counters/* · services/counter_service.py (KV-only, no DB table)_

| Unit | Kind | File:line | Tier (as-written) | Tier (with amendments) | Rationale / gap |
|---|---|---|---|---|---|
| !counters (status command) | command | disbot/cogs/counters_cog.py:152-162 | 2 | 2 | command routes to a read-model: loads CounterPolicy + live counts and renders _policy_embed. No mutation. Command -> read provider = tier 2 both. |
| /counters (slash status) | command | disbot/cogs/counters_cog.py:221-239 | 2 | 2 | same read-model as !counters, slash kind, ephemeral. Pure declaration over the same provider -> tier 2. |
| !counterpreset (apply/list preset) | command | disbot/cogs/counters_cog.py:164-219 | 3 | 2 | with no arg lists presets (read); with arg applies a coordinated 3-setting write via SettingsMutationPipeline. As-written no primitive for a multi-setting preset bundle -> registered handler = tier 3. G-15 SettingsPresetSpec makes the catalog data + a thin kernel apply-through-pipeline workflow -> tier 2. [ADVERSARIAL: folds into EXISTING SettingSpec.presets+WorkflowRef / ManagedTaskSpec.error_policy extension, not a new G-19/family]. |
| _policy_embed status read-model | panel | disbot/cogs/counters_cog.py:90-129 | 2 | 2 | record->text projection of CounterPolicy + compute_counts (mirrors karma card = tier 2). FieldsBlock/text over a ProviderRef; no bespoke view lifecycle, no stateful board. |
| _presets_embed read-model | panel | disbot/cogs/counters_cog.py:131-150 | 2 | 2 | read over the static preset catalog with sample renders. TableBlock/list over a provider -> tier 2. |
| compute_counts provider (member-cache read) | provider | disbot/services/counter_service.py:50-61 | 2 | 2 | read model: member cache -> (total,humans,bots). Trivial arithmetic (bot count), no domain rules. ProviderRef behind both the status panel and the rename loop -> tier 2. |
| enabled (bool master switch) | setting | disbot/cogs/counters/schemas.py:82-94 | 1 | 1 | plain bool SettingSpec; _validate_bool is a trivial type check the kernel does natively; activation=off-by-default. tier 1. |
| total_channel binding | binding | disbot/cogs/counters/schemas.py:95-107 | 1 | 1 | shipped as SettingSpec(str, input_hint=channel, validator=_validate_id) but is semantically a channel binding; the natural §2 port is BindingSpec(kind=channel) (as logging's 11 channel bindings are) -> tier 1; _validate_id is subsumed by channel-kind validation. |
| humans_channel binding | binding | disbot/cogs/counters/schemas.py:108-117 | 1 | 1 | same as total_channel -> BindingSpec(channel) tier 1. |
| bots_channel binding | binding | disbot/cogs/counters/schemas.py:118-127 | 1 | 1 | same as total_channel -> BindingSpec(channel) tier 1. |
| total_template setting (bounded str) | setting | disbot/cogs/counters/schemas.py:128-136 | 2 | 1 | str setting with _validate_template (non-empty + len<=80). Bounded-validator ref -> tier 2 as-written; G-5 declarative bounds (min_len=1,max_len=80) -> tier 1. |
| humans_template setting (bounded str) | setting | disbot/cogs/counters/schemas.py:137-145 | 2 | 1 | same G-5 class as total_template. |
| bots_template setting (bounded str) | setting | disbot/cogs/counters/schemas.py:146-154 | 2 | 1 | same G-5 class as total_template. |
| counters.settings.configure capability | capability | disbot/cogs/counters/schemas.py:41 + disbot/utils/subsystem_registry.py:694 | 1 | 1 | capability declaration on the manifest / capability_required on settings -> pure declaration, tier 1. |
| template preset catalog (4 presets, data) | data-catalog | disbot/services/counter_config.py:141-178 | 3 | 1 | 4 curated per-kind template bundles. As-written §2 has SettingSpec.presets (per-single-setting) but NO home for a coordinated MULTI-setting preset bundle -> lives as module data+apply code = tier 3. G-15 SettingsPresetSpec declares it as data -> tier 1. [ADVERSARIAL: folds into EXISTING SettingSpec.presets+WorkflowRef / ManagedTaskSpec.error_policy extension, not a new G-19/family]. |
| _counter_sync_loop task declaration (@tasks.loop 10min) | task | disbot/cogs/counters_cog.py:56-83 | 2 | 2 | scheduled loop DECLARATION -> ManagedTaskSpec(trigger=interval:600) already in §2 -> tier 2 both. Handler classified separately below. |
| sync_guild + _rename_if_changed (channel-name projection handler) | handler | disbot/services/counter_service.py:94-122 + :72-91 | 3 | 3 | the task handler: render(template,count) -> change-detect -> external channel.edit -> emit event, fanned out over bound counters. Real handler with an external Discord side effect + change-detection -> tier 3 as-written. NO game rules / economics (compute is trivial). G-14 ManagedProjectionSpec (bound-resource-attribute = render(template, provider), change-detected, rate-limit-aware) makes the projection declarative with a generic kernel diff+edit engine -> tier 2. [ADVERSARIAL: G-18 refuted→FOLD; ManagedTaskSpec declares the schedule but the compute/render/change-detect/rename handler stays tier-3]. |
| GuildSyncBackoff (per-guild exponential backoff) | handler | disbot/services/counter_service.py:150-196 | 3 | 1 | per-target retry/backoff on a fan-out scheduled task. Pure INFRA, zero domain logic -> should be kernel-owned. As-written §2 ManagedTaskSpec.error_policy is only 'log' so the behavior is bespoke code = tier 3; extending the error_policy vocabulary to 'per_target_backoff' (G-16) makes it a declared kernel-runner policy -> tier 1. [ADVERSARIAL: folds into EXISTING SettingSpec.presets+WorkflowRef / ManagedTaskSpec.error_policy extension, not a new G-19/family]. |
| counters.updated bus event | event | disbot/services/counter_service.py:30,125-132 + disbot/core/events_catalogue.py:94 | 1 | 1 | advisory event, verified ZERO subscribers (grep) -> EventSpec(observability_only=True). Emit lives inside the projection handler. tier 1. |
| cog lifecycle glue (cog_load register+start / cog_unload cancel / before_loop wait_until_ready) | lifecycle | disbot/cogs/counters_cog.py:45-53,84-86 | 1 | 1 | schema registration, task start/cancel, ready-gate — pure boilerplate the kernel generates from the manifest + ManagedTaskSpec. tier 1. |
| help entry + build_help_menu_view (help-menu direct-nav hook) | help | disbot/cogs/counters_cog.py:241-254 | 1 | 1 | HelpEntrySpec projection + a nav hook that opens the status read-model (reuses _policy_embed, already counted). help-as-projection + panel nav -> tier 1. |

**Fit:** 21 units · tier-1/2 as-written **81%** (17/21) · with amendments **95%** (20/21).

**§2 manifest sketch**

```python
COUNTERS = SubsystemManifest(
    key="counters", display_name="Server counters", parent_hub="community",
    category="community", capabilities=("counters.settings.configure",),
    commands=(
        CommandSpec("counters", CommandKind.BOTH, "Show live counter channels",
                    route=PanelRef("counters.status"),           # -> read-model
                    capability_required="counters.settings.configure"),
        CommandSpec("counterpreset", CommandKind.PREFIX, "Apply a name-template preset",
                    route=HandlerRef("counters.apply_preset",      # G-15 thin apply
                        justification="SettingsPresetSpec bundle -> audited pipeline"),
                    capability_required="counters.settings.configure"),
    ),
    panels=(
        PanelSpec("counters.status", "counters", "Server counters",
            body=(BlockSpec("fields", provider=ProviderRef("counters.policy_view")),),
            # _presets_embed -> second read panel over ProviderRef("counters.presets_view")
        ),
    ),
    bindings=(   # the three channel settings port to channel bindings
        BindingSpec("total_channel", "channel", legacy_settings_key_aliases=("counters.total_channel",)),
        BindingSpec("humans_channel", "channel"),
        BindingSpec("bots_channel", "channel"),
    ),
    settings=(
        SettingSpec("enabled", "bool", False, "counters.enabled",
                    activation=Activation.OFF_UNTIL_OPT_IN,
                    external_side_effects=True),          # renames a Discord resource
        # G-5 declarative bounds replace _validate_template (min_len=1,max_len=80):
        SettingSpec("total_template", "str", "\U0001F465 Members: {count}", "counters.total_template",
                    input_hint="max_len:80"),
        SettingSpec("humans_template", "str", "\U0001F9D1 Humans: {count}", "counters.humans_template"),
        SettingSpec("bots_template", "str", "\U0001F916 Bots: {count}", "counters.bots_template"),
    ),
    tasks=(
        ManagedTaskSpec("counters:sync", "interval:600",
            handler=HandlerRef("counters.sync_projection"),   # G-14 target
            error_policy="per_target_backoff"),               # G-16 -> kernel owns GuildSyncBackoff
    ),
    events=(EventSpec("counters.updated",
        (FieldSpec("guild_id","int"), FieldSpec("renamed","int")),
        owner_subsystem="counters", observability_only=True),),
    help=HelpEntrySpec("Keep channel names showing live member counts."),
    # --- proposed families the clean port needs ---
    # projections=(ManagedProjectionSpec(              # G-14
    #     target=BindingRef("total_channel"), attribute="name",
    #     value=render(SettingRef("total_template"), ProviderRef("counters.count:total")),
    #     change_detected=True, refresh_task="counters:sync"),  x3 total/humans/bots
    # )
    # setting_presets=(SettingsPresetSpec("counters.themes",  # G-15
    #     writes_per_key={"default":{...},"minimal":{...},"brackets":{...},"bullet":{...}}),)
)
```

**Tier-3 dispositions**

| Tier-3 unit | Verdict | Reason |
|---|---|---|
| !counterpreset (apply preset) | fold→existing (SettingSpec.presets / ManagedTaskSpec.error_policy) | [ADVERSARIAL] G-19 SettingsPresetSpec REFUTED→fold into SettingSpec.presets + a kernel WorkflowRef; GuildSyncBackoff folds into a ManagedTaskSpec.error_policy='per_target_backoff' vocabulary extension. No new dataclass. |
| template preset catalog (4 presets) | fold→existing (SettingSpec.presets / ManagedTaskSpec.error_policy) | [ADVERSARIAL] G-19 SettingsPresetSpec REFUTED→fold into SettingSpec.presets + a kernel WorkflowRef; GuildSyncBackoff folds into a ManagedTaskSpec.error_policy='per_target_backoff' vocabulary extension. No new dataclass. |
| sync_guild + _rename_if_changed projection handler | escape-hatch (schedule via ManagedTaskSpec; handler tier-3) | [ADVERSARIAL] G-18 ManagedProjectionSpec REFUTED→fold: ManagedTaskSpec (already in the spec) declares the interval schedule; the compute/render/change-detect/rename handler stays tier-3. No new family. |
| GuildSyncBackoff per-guild backoff | escape-hatch (schedule via ManagedTaskSpec; handler tier-3) | [ADVERSARIAL] G-18 ManagedProjectionSpec REFUTED→fold: ManagedTaskSpec (already in the spec) declares the interval schedule; the compute/render/change-detect/rename handler stays tier-3. No new family. |

**Structural-gap flags**

- **scheduled loop performing external resource mutation (channel rename)** — `with-amendment:G-14` — ManagedTaskSpec declares the schedule; the projection (metric->template->bound channel name, change-detected) needs G-14 ManagedProjectionSpec. Expressible today only via ManagedTask + a tier-3 escape-hatch handler.
- **scheduled loop + per-target (per-guild) backoff/cooldown** — `with-amendment:G-16` — ManagedTaskSpec.error_policy exists but only 'log'; extend its vocabulary to 'per_target_backoff' so the kernel runner owns GuildSyncBackoff. Pure infra.
- **coordinated multi-setting preset / theme apply** — `with-amendment:G-15` — SettingSpec.presets is per-single-setting; a cross-setting bundle applied atomically through the audited pipeline needs SettingsPresetSpec. Also reusable by welcome/logging presets.
- **deep persistent per-player/world state** — `yes` — ABSENT — counters has NO DB table; all state is guild-settings KV + live member cache. No StoreSpec needed. (G-10/G-8/G-9 irrelevant.)
- **transactional multi-write money mutation / escrow / irreversible economy op** — `yes` — ABSENT — no currency, no economy. Counters is mis-binned into Lane B; its true kin is logging/welcome (operator config + projection band), not economy. G-7/G-11/G-12/G-13 irrelevant.
- **stateful game loop / wait_for wizard / leaderboard** — `yes` — ABSENT — no game, no wizard, no leaderboard. No ChallengeSessionSpec/LeaderboardSpec surface.

**MAP → RECONSIDER → SIMULATE → OPTIMIZE**

- **Verdict:** keep · **status:** ok
- **Optimal new-bot form:** Rebuild as a near-fully-declarative manifest: master enabled bool + 3 channel BindingSpecs + 3 template SettingSpecs (G-5 length bounds) + a SettingsPresetSpec theme catalog (G-15), driven by one 10-min ManagedTask whose handler is three ManagedProjectionSpecs (G-14) that keep each bound channel's name = render(template, count-provider) with kernel change-detection and per-target backoff (G-16). Zero domain code: counters has NO irreducible game/economy logic — its only 'escape hatch' is an external channel-rename that the kernel resource layer should own.
- **Dependency layer:** L1 operator-config kernel (settings/binding/capability + ManagedTask runner + resource provisioning/rename workflow). NO economy/store/currency dependency — do NOT build it on the Lane B currency/item layers; it belongs with logging/welcome in the operator band. Gate: G-14 ManagedProjectionSpec + G-16 task backoff must land first.
- **Production-grade done:** Parity golden: with enabled + >=1 bound channel, each loop tick renames every bound channel to render(template,count) ONLY when the name actually differs (Discord rename rate-limit respected via change-detection), a failing guild backs off (capped, never dropped), counters.updated emits once per sync with renamed>=1, preset apply writes all 3 templates through the audited pipeline with the capability check, and status (prefix+slash) + help-menu hook render the live policy. Acceptance = existing counters test suite (test_counters_schemas, backoff tests, mock_counters exhibit) + a new projection golden.
- **Outperform target:** pending Lane F (member-counter bots e.g. Statbot / Counter.bot / Server Stats) — beat them via declarative multi-preset theming, rate-limit-aware change-detection, and fail-safe per-guild backoff (already shipped), plus one-manifest config instead of per-counter setup.

**Cross-lane dependencies**

- services.settings_mutation.SettingsMutationPipeline — counterpreset applies presets through the audited settings seam (Settings subsystem); G-15 must route through it
- services.settings_resolution.resolve_value — load_policy composes every typed value through the shared resolver
- core.runtime.subsystem_schema (register) + utils.subsystem_registry — schema/capability registration for the !settings widget and counters.settings.configure gate
- core.events bus — counters.updated advisory emit (events_catalogue.py:94); observability-only, zero subscribers verified
- core.runtime.resources.resolve_channel — channel resolution/provisioning kernel used by both status render and the rename loop (the resource/binding layer G-14 depends on)
- views.base.HubView — build_help_menu_view returns the help-menu nav view (help/nav kernel)

**⚠ Unverified / judgment calls**

- Channel-binding tier call (total/humans/bots_channel) is a JUDGMENT: they ship as SettingSpec(str)+_validate_id+input_hint=channel (schemas.py:95-127). Ported literally as SettingSpec+validator ref they would be tier 2 as-written; I scored them tier 1 because BindingSpec(kind=channel) already exists in the as-written §2 grammar and is the correct/natural port (matching logging's 11 channel bindings = tier 1 in measure.py). If the audit insists on literal-port tiering, tier12_aswritten drops from 17 to 14 and fit_aswritten from 81% to 67%.
- counters.updated subscriber count confirmed ZERO by grep over disbot/ (only the emit in counter_service.py); classified observability_only on that basis — no runtime trace executed.
- No DB table for counters confirmed by absence of any StoreSpec/table reference in source + the schema docstring ('no migration', KV-only) + the task prompt NOTE; not independently confirmed against a live migrations directory.

---
