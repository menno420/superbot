# FINAL REVIEW — the grammar go/no-go (capstone deliverable 1)

> **Status:** `verdict` — the gate between planning/discovery and creating the new repo.
> **Prepared:** 2026-07-03 (Fable 5 capstone, PR #1674) per
> [`../FINAL-REVIEW-HANDOFF.md`](../FINAL-REVIEW-HANDOFF.md).
> **Inputs:** all seven merged lanes (A–G + F), the grammar spike
> ([`tools/grammar_spike/RESULTS.md`](../../../../../tools/grammar_spike/RESULTS.md)), the design spec
> ([`rebuild-design-spec-2026-07-02.md`](../../../../planning/rebuild-design-spec-2026-07-02.md)), and the
> [preserve-map synthesis](../../codex-preserve-map-synthesis-2026-07-02.md). Lane claims were
> re-verified against source per Q-0120 (§6 verification record).
> **Companion:** [`NEW-BOT-BUILD-PLAN.md`](./NEW-BOT-BUILD-PLAN.md) (deliverable 2 — the ordered plan).

---

## 1. VERDICT: **GO-with-amendments**

The §2 manifest grammar **can durably express the whole intended surface**. The measured all-43
tier-1/2 fit is **63.8% as-written → 85.1% with amendments** (1,635 surface units) — clearing the
spec's 80% exit bar with margin. Every tier-3 unit across all 43 subsystems is dispositioned
(named grammar amendment **or** documented deliberate escape hatch), and every structural danger
zone has a design answer (§4). No subsystem class lacks a clean answer — there is **no NO-GO
signal anywhere in the corpus**.

It is *GO-with-amendments*, not plain GO, because the consolidated amendment set is real work:
**14 ratified new tier-2 spec families + ~15 soft field/vocabulary riders** (§3). All of them are
**additive** — not one redesigns an existing §2 primitive, changes a semantic, or touches a frozen
compat contract — so the required pass is a bounded spec-amendment PR (a docs pass in kind), but a
substantial one. **Build starts after that pass**, per the exit bar.

What the four exit-bar conditions measured:

| Exit-bar condition | Result |
|---|---|
| 1. Tier-1/2 fit measured (not extrapolated) across all 43, ≥ 80% | ✅ **85.1% with amendments** (63.8% as-written); 36/43 subsystems ≥ 80%; median 88.9% |
| 2. Every tier-3 unit dispositioned | ✅ every lane shipped per-unit dispositions; A/B/C ran independent adversarial refute passes (10 over-eager amendments refuted, recorded in §3.4 so they are never re-proposed) |
| 3. Danger zones each have a design answer | ✅ §4 — stateful games (declared lifecycle + priced-in engine hatch), gateway listeners (G-1 + G-11), `wait_for` wizards (pattern nearly extinct in source; G-19 closes the remainder), scheduled loops (ManagedTaskSpec + G-9), voice (verified absent; deliberate omission) |
| 4. Amendments fold into the spec as a docs pass, no redesign | ✅ in kind (all additive) — but non-trivial in size → **GO-with-amendments**, and §7 is the concrete spec-pass plan |

**The bet the spike made holds at scale.** The spike predicted 73% → 85% from 3 subsystems; the
full corpus measures 64% → 85% from 43. The two spike anchors reproduce verbatim in Lane C
(blackjack 44→44, karma 80→87), validating the measurement method. The stateful-game floor the
spike feared is real but **priced in by design**: casino (24%) and blackjack (44%) are ~85% game
logic by unit — exactly the §2.9/§10.1-risk-5 escape hatch, counted and ratcheted, not a grammar
failure.

---

## 2. The measured all-43 fit table

Mirrors `RESULTS.md`. "As-written" = the §2 grammar as spiked (before amendments); "with
amendments" = with the consolidated set of §3 folded in (ratified items only — provisional lifts
are *excluded*, so these are disciplined floors, not ceilings).

| Subsystem | Lane | Units | Tier-1/2 as-written | Fit as-written | Tier-1/2 amended | Fit amended |
|---|---|---:|---:|---:|---:|---:|
| admin | A | 40 | 18 | 45.0% | 29 | 72.5% ⚠ |
| server_management | A | 17 | 10 | 58.8% | 15 | 88.2% |
| moderation | A | 53 | 22 | 41.5% | 34 | 64.2% ⚠ |
| automod | A | 21 | 13 | 61.9% | 19 | 90.5% |
| image_moderation | A | 15 | 11 | 73.3% | 14 | 93.3% |
| security | A | 27 | 21 | 77.8% | 24 | 88.9% |
| cleanup | A | 53 | 29 | 54.7% | 44 | 83.0% |
| role | A | 108 | 54 | 50.0% | 75 | 69.4% ⚠ |
| channel | A | 41 | 13 | 31.7% | 35 | 85.4% |
| welcome | A | 24 | 17 | 70.8% | 23 | 95.8% |
| ticket | A | 58 | 32 | 55.2% | 48 | 82.8% |
| **Lane A subtotal** | | **457** | **240** | **52.5%** | **360** | **78.8%** |
| economy | B | 54 | 34 | 63.0% | 50 | 92.6% |
| inventory | B | 21 | 14 | 66.7% | 21 | 100% |
| treasury | B | 15 | 12 | 80.0% | 15 | 100% |
| mining | B | 108 | 72 | 66.7% | 100 | 92.6% |
| fishing | B | 89 | 63 | 70.8% | 81 | 91.0% |
| creature | B | 28 | 21 | 75.0% | 26 | 92.9% |
| farm | B | 19 | 13 | 68.4% | 19 | 100% |
| xp | B | 57 | 43 | 75.4% | 47 | 82.5% |
| casino | B | 25 | 4 | 16.0% | 6 | 24.0% ⚠ |
| four_twenty | B | 12 | 10 | 83.3% | 11 | 91.7% |
| counters | B | 21 | 17 | 81.0% | 20 | 95.2% |
| **Lane B subtotal** | | **449** | **303** | **67.5%** | **396** | **88.2%** |
| games (hub) | C | 20 | 20 | 100% | 20 | 100% |
| blackjack | C | 18 | 8 | 44.4% | 8 | 44.4% ⚠ |
| deathmatch | C | 49 | 22 | 44.9% | 37 | 75.5% ⚠ |
| rps_tournament | C | 59 | 33 | 55.9% | 46 | 78.0% ⚠ |
| counting | C | 48 | 33 | 68.8% | 41 | 85.4% |
| chain | C | 30 | 28 | 93.3% | 29 | 96.7% |
| leaderboard | C | 24 | 23 | 95.8% | 23 | 95.8% |
| community (hub) | C | 10 | 10 | 100% | 10 | 100% |
| community_spotlight | C | 16 | 14 | 87.5% | 15 | 93.8% |
| karma | C | 15 | 12 | 80.0% | 13 | 86.7% |
| **Lane C subtotal** | | **289** | **203** | **70.2%** | **242** | **83.7%** |
| ai | D | 70 | 43 | 61.4% | 62 | 88.6% |
| btd6 | D | 78 | 42 | 53.8% | 66 | 84.6% |
| project_moon | D | 22 | 14 | 63.6% | 20 | 90.9% |
| help | D | 24 | 22 | 91.7% | 23 | 95.8% |
| settings | D | 28 | 26 | 92.9% | 27 | 96.4% |
| logging | D | 62 | 49 | 79.0% | 60 | 96.8% |
| diagnostic | D | 65 | 39 | 60.0% | 56 | 86.2% |
| ux_lab | D | 27 | 17 | 63.0% | 24 | 88.9% |
| utility | D | 21 | 15 | 71.4% | 18 | 85.7% |
| general | D | 22 | 16 | 72.7% | 19 | 86.4% |
| proof_channel | D | 21 | 14 | 66.7% | 18 | 85.7% |
| **Lane D subtotal** | | **440** | **297** | **67.5%** | **393** | **89.3%** |
| **ALL 43 — OVERALL** | | **1,635** | **1,043** | **63.8%** | **1,391** | **85.1%** |

### 2.1 Honest weighting notes (read before quoting the headline number)

- **The mean is not carried by a lucky tail.** Median amended fit is **88.9%**; 36 of 43
  subsystems clear 80%. The two big-unit subsystems pull in opposite directions (mining 108u @
  92.6% vs role 108u @ 69.4%), roughly cancelling.
- **The 7 below-bar subsystems (⚠) split into exactly two clusters, both dispositioned:**
  - *Stateful games* — casino 24%, blackjack 44%, deathmatch 75.5%, rps 78%. These are the
    §10.1-risk-5 floor **by design**: the residual tier-3 is game rules/boards/moves/bracket
    topology, the named escape hatch. The money/lifecycle choreography — the dangerous part — IS
    declared (ChallengeSessionSpec + G-12/G-17). Two live money bugs found by the audit
    (deathmatch PvP double-settle, blackjack free-tournament double-pay, §6.3) would both be
    **structurally impossible under the kernel-owned `settle_once` seam** — the strongest
    empirical argument *for* the grammar bet in the whole corpus.
  - *Governance* — moderation 64.2%, role 69.4%, admin 72.5%. The residual tier-3 is audited
    mutation seams, operator/process controls (cog lifecycle, restart, log level), and
    automation engines — individually dispositioned deliberate escape hatches (the karma-`!thanks`
    precedent: an audited domain seam is tier-3 no matter how thin). No further primitive family
    was found by Lane A's own search, and none emerged cross-lane.
- **Counting conventions differ by lane.** Lane A counts mutation seams, modals, and resolvers as
  their own ledger rows (per the BRIEF's unit-kind checklist); the spike folded seams into their
  calling commands. Folded, Lane A's moderation reads 73.9% rather than 64.2%. The all-43 totals
  are conservative because of this — the strictest-counted lane is also the lowest-scoring one.
- **Amended = ratified only.** Provisional lifts (P-1 EventFeedProjectionSpec; a declarable rps
  bracket) are excluded. Spotlight would read 100% with P-1; rps ~88% with a bracket spec.

### 2.2 What "as-written" measured — and what the merged spec already contains

The lanes measured "as-written" against the §2 grammar as spiked. **The merged design spec
(2026-07-02) already folds in G-1…G-6** (GatewayListenerSpec, list-valued settings, cooldown,
bounds, per-kind namespaces — §2.2/§2.5/§2.8) **plus several families lanes B/C re-derived
independently**: IdleAccrualSpec, ItemCatalogSpec/RewardSpec/CraftingRecipeSpec/CollectionDexSpec/
CostVector, ChallengeSessionSpec, LeaderboardSpec, TableSpec/ListSpec pagination + sort/filter
(with the BrowserView engine), the `storage=typed_column` field, and the KnowledgeDomainSpec facet
with TaskProfileSpec (most of Lane D's G-7/G-8). So the fit *against the spec as merged today*
sits well above the 63.8% as-written column — the with-amendments column is conditional **only on
the genuinely-new set in §3.2**, not on re-approving what the spec already has. Independent
re-derivation of already-specced families by lanes that hadn't read the merged spec is itself
convergent evidence the spec made the right calls.

---

## 3. The consolidated amendment list

Canonical numbering: **G-1…G-6** (spike) and **G-7…G-10** (Lane D / handoff) keep their IDs;
lanes A/B/C minted colliding local IDs (Lane B's "G-7…G-13", Lane C's "G-7…G-9", Lane A's
"G-A1…G-A15"), which are renumbered here **once, canonically** — the mapping is in each row.
Buckets: **(a)** already in the merged spec → no action; **(b)** ratified new spec work → *the*
amendment pass; **(c)** provisional → hold; **(d)** refuted → never re-propose.

### 3.1 Bucket (a) — already folded into the merged design spec (no spec work)

**G-1** GatewayListenerSpec · **G-2** list-valued settings · **G-3** AnnouncementRouteSpec ·
**G-4** CommandSpec.cooldown · **G-5** declarative bounds · **G-6** per-kind command namespaces —
all in the spec (§2.2/§2.5/§2.8). Also already present: ChallengeSessionSpec, LeaderboardSpec,
IdleAccrualSpec, the item/reward/recipe/dex/cost content declarations, Table/List pagination +
sort/filter (retires Lane A's proposed "PaginatedBlockSpec" — covered, not refuted),
`storage=typed_column` (field exists; semantics elaboration is R-4), egress-marked provider
adapters + `external_side_effects` (covers most of the "external-API metadata" flag), and
**G-7/G-8 cores**: the KnowledgeDomainSpec facet (sources/ingestion/context builders/intents/
eval suites) and TaskProfileSpec. Residual G-7/G-8 deltas are soft riders (R-13).

### 3.2 Bucket (b) — the ratified amendment set (the spec pass this verdict requires)

**New tier-2 families** (all additive; none touches an existing primitive's semantics). Ordered
by cross-lane convergence, then leverage:

| # | Family | What it adds | Who needs it | Evidence class |
|---|---|---|---|---|
| **G-9** | **DeferredActionSpec** (one-shot timed task) | "fire once, N seconds from now, closing over this call's state" + recovery semantics — ManagedTaskSpec's `Interval\|Cron\|Event` triggers can't express it | proof_channel timed unlock, utility reminders, security lockdown auto-restore; generic temp-ban/mute shape | **Convergent 2 lanes** (D + A "DeferredActionSpec"); capstone source-verified all 3 consumers |
| **G-10** | **ModalFormSpec / ModalFieldSpec** | declared modal field schemas (label/style/placeholder/max_length/prefill/bounds); submit side-effect stays a HandlerRef | **48 files** define `discord.ui.Modal` subclasses (capstone grep) — settings editors, moderation, roles, btd6, utility, proof, ux_lab… | **Convergent 2 lanes** (D + A, independently); highest-confidence item in the whole set |
| **G-11** | **MessagePipelineStageSpec** | an *ordered, fail-open, short-circuiting* on_message stage as data (`stage_name, order, gate, short_circuit, handler`) — deliberately distinct from G-1 (no order/pipeline semantics there; N raw listeners would re-introduce the race the pipeline exists to kill) | automod(5), cleanup(10), counting(15), chain(20), image_moderation(25), xp(30), four_twenty(50), rps(40) — **11 stages repo-wide** | **Convergent 3 lanes** (A "MessagePipelineStageSpec" + C "G-7" + B's stage evidence) |
| **G-12** | **EconomyTransactionSpec** | atomic multi-write money moves as data: debit/credit legs + audit row(s) + post-commit event in one transaction, `settle_once`/conditional-debit/refund_policy, composable in-txn legs. **Kernel-owned money atomicity — the load-bearing amendment**: a new subsystem structurally cannot get double-spend/partial-settle wrong | economy, treasury, mining (~10 legs), farm, fishing, inventory purchases — **6 subsystems**, plus every Lane C wager via `bet_and_settle` composition | Lane B (its "G-7"); the 2 live Lane C money bugs are the empirical case |
| **G-13** | **ProgressionSpec** | cooldown-gated earn + streak + level-curve *gates* as data (daily/work, xp `5L²+50L+100`, skill trees, structure tiers, creature earn maps); payouts stay tier-3 | economy, xp, mining, fishing, creature, farm — **6 subsystems** | Lane B ("G-9") |
| **G-14** | **ShopSpec** | priced catalog + declared buy/sell workflows (each a G-12 leg); price formulas as data | economy shop, mining market, fishing shops/structures, farm — **4 subsystems** | Lane B ("G-11") |
| **G-15** | **ItemCatalog audited-ops extension** | extends the spec's existing ItemCatalogSpec content declarations with kernel-owned **audited, atomic, unique-fenced grant/consume/has** ops (+ equip/loadout, durability facet) — closes the verified "item grants are unaudited" hole and the grant double-click race | inventory, mining, fishing, creature; economy cross-links | Lane B ("G-8"); extension of an existing family |
| **G-16** | **ChannelMatchSpec** | per-channel persistent open-ended message game: config fields (normalize/bounds/merge), create/reset/end lifecycle, state store — deliberately NOT ChallengeSessionSpec (no accept/turn/escrow) | counting + chain (which the plan merges into one family — see build plan) | Lane C ("G-8") |
| **G-17** | **TournamentLobbySpec** | tournament *lobby + pot* choreography only: registration (reaction+button, countdown, reminder), entry-fee CostVector, idempotent bracket-level pot settle, one-per-guild mutex, refunds. **Must specify round-graph checkpointing** (an in-flight rps bracket is unresumable today — a genuine new capability). Bracket *topology* stays rps-owned tier-3 (adversary ruling: recurrence = 1) | blackjack + rps tournaments | Lane C ("G-9"), adversarially narrowed |
| **G-18** | **ResourceLifecycleSpec** | declarative multi-op CRUD-with-audit: typed request → per-target StepResult → reversibility → audit+event → confirm gate; generalizes the shipped Channel/RoleLifecycleService twins (18 channel units alone) | channel + role (2-for-1) | Lane A ("G-A4") |
| **G-19** | **WizardSectionSpec + `SubsystemManifest.wizard_sections`** | declares a setup-wizard section (recommended-ops builder, customize target, detail panel, op kinds/depths) — today a second, uncoordinated registry (`setup_sections.REGISTRY`) invisible to the grammar. Closes the BRIEF's wizard danger zone *formally* (the runtime pattern is already the draft-op lane, §4.3) | cleanup, role ×2, ticket — every `views/setup/sections/*` registrant | Lane A ("G-A9" + its un-numbered manifest-field flag) |
| **G-20** | **InstanceLifecycleSpec** | channel-backed per-instance lifecycle (create dedicated channel, grant opener+staff ACL, open/claimed/closed state machine, declared close workflow: transcript/notify/teardown) — the non-game sibling of ChallengeSessionSpec; absorbs ~350 lines of ticket choreography | ticket (highest-leverage of its four asks); future instance-shaped features (e.g. giveaways use an adjacent shape) | Lane A ("G-A15") |
| **G-21** | **RecordTableSpec** | keyed table of typed records with declared add/edit/remove workflows + per-row audit (G-2 generalized from scalar lists to structured rows) | role today (exemptions, per-role config); likely 2nd instances post-port (btd6 sources, automod word-packs) | Lane A ("G-A5"); recurrence 1 today — ship in the pass but flag as lower-priority |
| **G-22** | **StagedBuilderSpec** | view-local multi-field in-memory draft with one atomic commit — a *third* staging lane beside direct-mutation and persisted setup-drafts. **Owner decision embedded: standardize (build it) or consciously bless three lanes** | role menu builder (12 field editors) | Lane A ("G-A6") |
| **G-23** | **CommandSpec argument schema / EntityResolverRef** | typed/bounded/resolved command arguments (channel/role by mention\|ID\|name; enum/bounded args) — CommandSpec has only a free-text `usage` today. Slash-native selects retire most of the need for *new* surfaces; this is the prefix back-compat lane | channel (12 of 17 commands); any ported prefix command with typed args | Lane A ("G-A7") |
| **G-24** | **PreviewConfirmApplySpec** | computed-diff preview → explicit confirm → audited apply as one declared flow (PanelActionSpec.confirm is a re-click flag, not a diff preview). *Spec-pass instruction: attempt to compose from §2.7 MutationPreview + ConfirmationSpec first; mint the family only if composition fails* | cleanup policy panel + `!cleanuphistory` (kills the repo's last true `bot.wait_for`) | Lane A ("G-A10") |

**Soft riders** (field additions / vocabulary extensions / enforcement tightenings — batch into
the same spec PR):

| # | Rider | What / who |
|---|---|---|
| R-1 | `GatewayListenerSpec.handler: WorkflowRef \| HandlerRef` (was HandlerRef-only) | welcome's fully-generic entry-role grant → tier-1; any autorole-shaped feature (Lane A "G-1x") |
| R-2 | Two-lane authority extension: `legacy_permission_floor` + resource-owner clause | moderation's 3 divergent mechanisms, ticket's 4 (incl. "or the opener"), admin/channel's owner-wrapped predicates (Lane A "G-A12") — the slash surface verifiably ignores configured moderator_role today; this rider is what fixes that class |
| R-3 | `value_type="template"` multi-variant text settings (placeholders + random-variant pick as a render contract) | welcome join/leave/DM messages (Lane A "G-A13") |
| R-4 | `storage=typed_column` generation-contract elaboration (dedicated config tables get the declarative settings path) | ticket — the only subsystem with no `schemas.py`; its bespoke settings table is its dominant tier-3 mass (Lane A "G-A14") |
| R-5 | LeaderboardSpec enrichment: `stat_source / value_template / card_theme` | all 12 boards; enables dissolving the leaderboard subsystem into the kernel (Lane C) |
| R-6 | ChallengeSessionSpec `max_seats / lobby_policy` (optional fields) | casino's multi-seat poker folds into the existing family — **not** a new session type (Lane B, adversarially settled) |
| R-7 | `ManagedTaskSpec.error_policy += "per_target_backoff"` | counters' per-guild rename backoff becomes kernel runner behavior (Lane B) |
| R-8 | IdleAccrualSpec invariants: `settle_before_mutate` + idempotent remainder-preserving settle + fresh-state normalization | farm's two anti-exploit invariants become spec law (Lane B) — load-bearing |
| R-9 | ProviderRef projection-args (sort/filter/page state re-invocation) | inventory browser + every dex/log/market browser; *spec-pass instruction: check overlap with TableSpec sort/filter first* (Lane B) |
| R-10 | `allowed_values` kernel enforcement at the mutation seam (today a widget hint only — registered validators are the only enforcement) | lane-wide for every enum-shaped str setting; moderation's 3 enum settings' tier-1 grades are conditional on this (Lane A, un-numbered) |
| R-11 | `HelpEntrySpec.dropdown_target: PanelRef` (declared cross-subsystem navigation) | retires the ~10 near-identical `build_help_menu_view` bodies + get_cog/getattr dispatch (Lane A "G-A3") |
| R-12 | Shared-seed world-position store *convention* (not a dataclass) | mining grid (fog/pos/seed); fishing venue toggle adjacent (Lane B "G-10", explicitly a design decision) |
| R-13 | G-7/G-8 residual deltas: declared refusal/denial semantics per intent; AIProviderGatewaySpec (provider set / fallback / secret requirements / diagnostics as declaration) | ai, btd6, project_moon (Lane D) — the facet cores are already in the spec |
| R-14 | HubPanelSpec spec *clarification* (source: registry-filter \| named entries; cross_links; governance_filter) | games/community/utility hubs — no fit change; documents existing §2 behavior (Lane C; its "RegistryHubSpec" was rejected) |
| R-15 | Column-scoped ownership notes on StoreSpec (`reader_domains` exists; add shared-writer columns) | xp table (xp.service writes xp/level; economy writes coins); fishing writes 2 mining-owned tables — sole-writer fences must name authorized sibling writers or the ownership model breaks (Lane B) |

### 3.3 Bucket (c) — provisional (hold; do not fold yet)

- **P-1 EventFeedProjectionSpec** (event → template → scope-bounded ring, read-side analog of
  G-3; would also fix spotlight's restart-fragile module-global feed). **One instance today** —
  held per the ≥2-recurrence bar. *The spec pass should check Lane E's feed-shaped plans (owner
  review inbox, feedback boards, per-command feedback threads — its proposed tagged-board
  family) for the second instance before deciding ratify-or-hold.*

### 3.4 Bucket (d) — refuted / do-not-re-propose (adversarially killed; recorded so no future session re-adds them)

From Lane B's refute pass: **LootTableSpec** (weighted-RNG rolls stay tier-3 by design — 4
distinct roll engines are not one family), **MultiSeatTableSessionSpec** (→ R-6 fold; the
first-pass 68% casino lift was unsupported, corrected to 24%), **ReadModelProjectionSpec** (→
R-9 fold), **ParticipationPrefSpec** (user-scoped SettingSpecs cover 3 of 4 concerns),
**ManagedProjectionSpec** (→ R-7 fold), **SettingsPresetSpec** (→ existing `presets` +
kernel WorkflowRef; its "atomic apply" claim was false), **AutoResponderSpec/ContentPoolBlock**
(→ G-1 + ProviderRef + one-off tier-3 handler; no user-configurable autoresponder exists to
generalize). From Lane C: **RegistryHubSpec** (community proves registry hubs are 100% tier-1
already), **TournamentBracketSpec** (split — lobby ratified as G-17, bracket topology stays
tier-3, dropping rps from a claimed 88% to an honest 78%). From Lane A: **PaginatedBlockSpec**
(not refuted — *already covered* by the merged spec's Table/List + BrowserView; recorded here so
it isn't re-minted).

---

## 4. The structural danger zones — answers

**4.1 Stateful games — expressible, with a priced-in escape hatch. Not a NO-GO.**
The lifecycle/money choreography (the part that breaks production) is declared:
ChallengeSessionSpec (accept/turn/stale timeouts, escrow CostVector, `settle_once`, persistence
class, refund_policy, stat_writes) + G-12 transactions + G-17 tournament lobbies + R-6 multi-seat.
The rules/boards/moves/bracket-topology stay counted, justified tier-3 — the §2.9 hatch working
as designed (adversary-tested: a genuine two-player turn loop maps onto ChallengeSessionSpec with
no new "TurnLoopSpec"). The floors are honest: casino 24%, blackjack 44% — ~85% game logic by
unit. Kernel-owned `settle_once` would have made both live money bugs found by this audit
(§6.3) structurally impossible; that is the empirical validation of the design.

**4.2 Gateway listeners — solved by G-1 (already in spec) + G-11 (this pass).**
The operator band's raw listeners (logging's 8, karma react-to-thank, security joins, welcome
join/leave, role reactions) declare via G-1 with the validated thin-vs-real handler split (karma's
thin forward → tier-2; blackjack's lobby-logic join → tier-3, honestly). The *ordered* on_message
band is a different, deliberately race-free shape → G-11 MessagePipelineStageSpec (11 stages,
3-lane convergence). R-1 widens G-1 handlers to WorkflowRefs for fully-generic actions.

**4.3 `wait_for` wizards — the danger zone as named is nearly extinct in source.**
Capstone grep: exactly **one** true interactive `bot.wait_for` in the runtime
(`cleanup_cog.py:439`, a reaction-confirm) — everything else is `asyncio.wait_for` timeouts. The
real wizard substrate is already the *panel + persisted SetupOperation draft-op* lane (setup
sections write through `apply_operations`, tier-2 today). The design answer: G-24 (or a §2.7
composition) replaces the one legacy confirm; G-19 gives wizard sections a declared home in the
manifest. No new interaction-model primitive is needed — the shipped bot already evolved past the
pattern the spike feared.

**4.4 Scheduled loops — covered; one genuine small gap, closed by G-9.**
Every recurring loop (role sweeps ×2, counters rename, spotlight trim, session_gc, schedulers)
is ManagedTaskSpec-shaped (already in spec); R-7 adds per-target backoff. The genuinely
inexpressible shape was the **one-shot deferred action** (proof unlock, reminders, lockdown
restore) → G-9. Notably the game economies are *deliberately loop-free* (energy/idle accrual is
settle-on-read → IdleAccrualSpec + R-8) — a restart-safe pattern the grammar should protect, not
replace.

**4.5 Voice — verified absent; deliberate omission, not a gap.**
Zero voice code in `disbot/` (grep: no VoiceClient/opus/lavalink/FFmpeg/AudioSource hits).
Consistent triple ruling: Lane F (deliberate omission — licensing/complexity), Lane E (defer;
owner-gated), design spec non-goals. A VoiceSessionSpec family is a *future design pass if the
owner ever green-lights voice* — nothing to express today, so nothing blocks GO.

---

## 5. Per-subsystem disposition roster (grammar layer over the preserve-map)

One line each; folds the [preserve-map synthesis](../../codex-preserve-map-synthesis-2026-07-02.md)
(structural layer) with the lanes (grammar layer). Full detail lives in each lane file.

| Subsystem | Disposition | One-line |
|---|---|---|
| admin | KEEP+IMPROVE | necessary bot-management primitives; close the operator-audit-trail gap; nav hub → PanelRefs; fix `bot_spam` binding bug |
| server_management | KEEP+IMPROVE | the operator hub shape is right; R-11 nav convention; register `setup` as a real subsystem |
| moderation | IMPROVE | unify 3 divergent authority mechanisms (R-2); modals → G-10; pointer settings → BindingSpecs; keep every capability |
| automod | KEEP+IMPROVE | model audit posture; stage → G-11; consider one operator-facing "auto-mod tier" surface with cleanup/image_mod |
| image_moderation | KEEP+IMPROVE | v1 (Q-0108) sound: off-by-default, fail-open, URL-only; G-2 lists; give it a real panel |
| security | KEEP+IMPROVE | Q-0111 tiers sound; route lockdown slowmode through the audited seam; G-9 for restore timers; build quarantine action |
| cleanup | KEEP domain, IMPROVE impl | fix the 2 unaudited mutation paths; G-24 kills the last wait_for; G-11 stage; add slash surface |
| role | IMPROVE | keep automation engines; collapse hidden legacy commands into panel actions; G-18/G-21/G-22; fix 3-table teardown gap; add slash mirrors |
| channel | IMPROVE | keep audited lifecycle seam; replace 17 prefix verbs with small slash set + G-18; wire or delete dead voice-create branch |
| welcome | IMPROVE encoding | behavior sound; re-encode channel/role as BindingSpecs; R-3 templates; R-1 role-grant workflow; card renderer stays hatch |
| ticket | KEEP+IMPROVE | cleanest audited seam in Lane A; G-20 lifecycle; R-4 typed-column config; expose dormant fields; add slash + auto-close |
| economy | KEEP | the currency kernel; G-12/G-13/G-14; wire the ready-but-unwired `transfer()` to `!give/!pay` (#1541) |
| inventory | REDESIGN | first-class audited item kernel (G-15); merge the two divergent item tables; zero legitimate escape hatches → 100% declarative |
| treasury | KEEP | well-guarded escrow; falls out free once G-12 lands |
| mining | REDESIGN (port LAST) | deepest subsystem (108u); exercises every new family — **the Lane B acceptance test**; engines/renderers stay hatches |
| fishing | KEEP | declared shell + small irreducible engine; Q-0175 (fish coin value) gates the sell leg |
| creature | KEEP | already unusually well-factored; coin-free ChallengeSessionSpec PvP; catch roll stays tier-3 |
| farm | KEEP | the clean end of Lane B; 100% declarative once G-12/G-13/G-14 + R-8 land |
| xp | KEEP | ProgressionSpec curve + G-11 stage earn; import tooling stays a registered hatch; split-column ownership → R-15 |
| casino | KEEP | the honest floor (24%); folds into ChallengeSessionSpec via R-6; records/leaderboard impossible today (no store) — build plan adds it |
| four_twenty | KEEP | easiest declarative win; G-11 stage + G-4 cooldown |
| counters | KEEP (re-bin) | **mis-binned**: operator band, not economy — build it with logging/welcome in L1, not on Lane B layers |
| games (hub) | IMPROVE | zero tier-3 already; unify the 4 registry hubs under the generated hub (R-14) |
| blackjack | KEEP | spike anchor; 3 ChallengeSessionSpecs + declared stat_writes (close the wins-leaderboard drift); fix free-tournament double-pay |
| deathmatch | KEEP (+bug) | clean instance of the target game shape; formalize both settle paths under kernel settle_once (fixes the PvP double-settle) |
| rps_tournament | IMPROVE | G-17 lobby + ChallengeSessionSpec matches; bracket stays owned tier-3; persist its in-memory settings |
| counting | KEEP (improve) | G-16 + G-11; the AST-evaluator engine stays tier-3 (the worse-programming-language trap, correctly fenced) |
| chain | IMPROVE (merge) | merge with counting into one channel-message-rule family on G-16; surface or drop the dead `chain_count` stat |
| leaderboard | **MERGE into kernel** | RankProvider registry IS LeaderboardSpec in disguise; dissolves into per-subsystem declarations + one kernel renderer |
| community (hub) | KEEP | the 100%-tier-1 proof that pure router hubs are fully generated |
| community_spotlight | IMPROVE | declared provider reads; P-1 (when ratified) makes the feed restart-durable and kills the trim loop |
| karma | KEEP | highest-fit non-hub (87%); the audited grant seam is the exemplar tier-3-by-design |
| ai | REDESIGN into platform specs | G-7/G-8 facets + R-13; NL monolith splits into router + per-domain intents; provider calls stay hatches |
| btd6 | KEEP+IMPROVE | the KnowledgeDomainSpec exemplar; source registry/freshness/evals as declarations |
| project_moon | IMPROVE/MERGE | same knowledge-domain family as btd6; raise eval parity |
| help | KEEP | generated projection + overlay mutations; G-10 for editor forms |
| settings | KEEP | the generated config hub proof; R-10 closes its one latent gap |
| logging | KEEP | the spike's 97% exemplar; G-1×8 + G-3 routes |
| diagnostic | IMPROVE | every platform command → declared provider id + schema + gate; stores as StoreSpecs |
| ux_lab | KEEP | zero-write UX gallery; G-10 modal gallery declarations |
| utility | MERGE (pack) | simple command pack; G-9 reminders + G-10 poll modal; keep destructive `clear` as audited hatch |
| general | MERGE (pack) | content command pack over declared providers |
| proof_channel | IMPROVE | binding + G-9 timed-unlock surface; prize actions stay audited handlers |

**L0 (Lane G) verdict, carried:** GO — preserve the six production-grade primitives
field-for-field (lifecycle, task supervisor, EventBus, startup-outcome, health server, DB seam);
replace the composition root, the hardcoded 60-cog loader, and the flat env module; build the one
thing that doesn't exist — the pre-boot namespace registry (K1). Full detail:
[`lane-G-foundations.md`](../lanes/lane-G-foundations.md) §3/§8/§9.

---

## 6. Verification record (Q-0120)

### 6.1 What this capstone re-verified against source first-hand

- **G-9 consumers**: `proof_channel_cog.py:201-216` (one-shot `asyncio.sleep` unlock via
  `tasks.spawn`), `utility_cog.py:61` (reminder sleep) — confirmed; plus Lane A's independent
  security-lockdown instance. ✅
- **G-10 breadth**: 48 files define `discord.ui.Modal` subclasses — *wider* than any single lane
  claimed. ✅
- **`wait_for` zone**: exactly one interactive `bot.wait_for` in runtime (`cleanup_cog.py:439`). ✅
- **Grouped self-roles**: `role_menu_view.py:91-144` `unique`/`verify`/`max_roles` modes +
  persisted reaction-role modes (`utils/db/roles.py:267`) — Lane F's ⚠ candidate is **already
  shipped** (per-menu scope); retired from the gap list. ✅
- **Merged-spec coverage**: G-1…G-6 fields/families verified present in the design spec §2.2/
  §2.5/§2.8; Table/List pagination + `storage` field + egress marking verified present (basis of
  bucket (a)). ✅
- **Lane fit arithmetic**: re-summed all four lanes' unit ledgers; every subtotal and the 1,635/
  1,043/1,391 totals check out. Lane D's internal sums verified row-by-row. ✅

### 6.2 Lane F ground-truth re-check (before any ADD-from-ecosystem is scheduled)

A dedicated verification agent re-checked every "genuine gap" and headline correction:
**7 CONFIRMED** (giveaways plan-only — no subsystem/command/cog; voice absent — zero
VoiceClient/opus/lavalink hits; no general feed primitive — `youtube_video_cache` is AI-grounding
cache, not a feed; ticket/casino/poll/8-logging-listeners all ship as corrected), **1 REFUTED**
(grouped self-roles — see §6.1), **2 PARTIAL** (the dashboard is **FastAPI/uvicorn, not Flask**;
the welcome-card renderer lives in `utils/welcome*`, invoked from the service — both attribution
errors in the benchmark doc, neither changes a verdict). Net: the ecosystem ADD list is exactly
**giveaways** (already planned, Lane E) + **feeds** (deferred known-option). The competitor
catalog stays directional, as the handoff ordered.

### 6.3 Live runtime bugs surfaced by the audit (docs-only session — routed, not fixed)

The lanes' source verification found **six** shipped defects, all out of this session's read-only
scope; they jump the queue per "bugs first" and are listed as immediate current-bot work in the
build plan §"now-lane":

1. **deathmatch PvP double-settle** — no atomic claim on the PvP path (`deathmatch_cog.py:214/:151`);
   double W/L write + double gear-wear possible (Lane C).
2. **blackjack FREE-tournament double-pay** — `free_reward` leg not row-guarded
   (`game_wager_workflow.py:330-333` + `tournament_views.py:222`); paid tournaments safe (Lane C).
3. **admin startup greeting likely dead** — hardcoded `bot_spam` (underscore) vs registry's
   `bot-spam` (hyphen) exact-string compare (Lane A).
4. **cleanup: two unaudited mutation paths** — word/strict toggles, and `!cleanuphistory`'s bulk
   delete (raw `message.delete()`, no mod_logs/EVT_MOD_ACTION) while the same function *is*
   audit-wrapped when called from moderation (Lane A).
5. **security: unaudited raid-lockdown slowmode edit** — direct `channel.edit()` while
   `!slowmode` routes the identical op through the audited seam (Lane A).
6. **role: guild-teardown gap on 3 of 8 tables** (`role_thresholds`, `role_automation_exemptions`,
   `reaction_roles` — the "self-cleans" comment is unimplemented) (Lane A).

Plus one ready-but-unwired feature: `economy_service.transfer()` is fully audited but has **no
command wiring** (`!give/!pay`, #1541).

### 6.4 Trust calibration on the lanes themselves

Lanes A/B/C each ran independent adversarial verify passes that **materially corrected their own
drafts** (A: admin 75→72.5, welcome 75→70.8, ticket re-counted; B: casino 68→24, 7 amendments
refuted; C: rps 88→78, RegistryHubSpec rejected) — the discipline the BRIEF demanded, visibly
executed. Remaining ⚠ items are carried per-subsystem in the lane files; none is load-bearing for
the verdict (the largest class is "internals read via grep, tiers inferred from call sites" in
Lane B's mining/fishing). Lane D reported no adversarial pass — its numbers are consistent with
the spike's logging anchor (79→97 reproduced exactly) and its G-7…G-10 evidence spot-checked
clean here (§6.1), but treat its per-unit tiers as one-agent judgment. The known ground-truth
tool defect (command-surface.json's `perm` column misses wrapped decorators and has no bot-owner
tier) is recorded for every future consumer.

---

## 7. The spec-amendment pass this verdict requires (the "plan for the PR")

One session, docs-only, editing `docs/planning/rebuild-design-spec-2026-07-02.md` (+ optionally
`tools/grammar_spike/spec.py` prototypes). Scope = §3.2 exactly: 14 families + 15 riders, three
embedded owner decisions (G-22 standardize-vs-bless; R-12 world-store convention; P-1
ratify-or-hold after checking Lane E's second instance). Order of work: the three cross-lane
convergent families first (G-10, G-11, G-9), then the money/game spine (G-12→G-17), then the
governance set (G-18→G-24), then riders. Each amendment lands in §2.8-style: fields + roles +
compile rules + which subsystems consume it. Nothing in the pass touches: existing field
semantics, the compat contracts (§5), the S/A/O model, or the namespace design — if an edit
wants to, that is redesign and must come back to the owner as its own question.

**What the owner is approving by accepting this review** (the go/no-go checklist):

1. The verdict: the grammar bet is validated at 85.1% measured fit; build may start **after** the
   §3.2 spec pass lands.
2. The amendment set §3.2 (14 families + 15 riders, all additive) as the complete, closed list —
   plus the §3.4 refuted list as permanently closed.
3. The escape-hatch economy: the stateful-game floor (casino 24%, blackjack 44%) and the
   governance cluster (moderation 64%, role 69%, admin 72.5%) are accepted, dispositioned tier-3
   — counted and ratcheted, never "fixed" by adding grammar conditionals.
4. The six live-bug fixes (§6.3) + the `transfer()` wiring as immediate *current-bot* work,
   independent of the rebuild gate.
5. Phase-3 (new-repo code) remains owner-gated behind the design spec + this amendment pass —
   this review is evidence, not build approval.
