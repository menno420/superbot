# Lane C — Games & Community (Axis 1)

> **Status:** `audit` — completed 2026-07-02 (Opus 4.8 ultracode, new-bot-capability-audit fleet). This
> file is the Lane C deliverable: every surface unit of the 10 Games & Community subsystems verified
> against source and tiered against the §2 manifest grammar, with manifest sketches, tier-3
> dispositions, fit numbers, structural-gap flags, and MAP→RECONSIDER→SIMULATE→OPTIMIZE
> recommendations. **Method:** [`../BRIEF.md`](../BRIEF.md) · [`../PARTITION.md`](../PARTITION.md) ·
> `tools/grammar_spike/{spec,measure}.py` + the 3 calibration manifests · `../ground-truth/`.
>
> **How this was produced (auditable):** 10 parallel deep source-verification agents (one per
> subsystem, every `file:line` re-verified against source, Q-0120) → a 4-lens adversarial re-check
> (blackjack calibration · every proposed game-state amendment · every tier-3-that-could-be-tier-2 ·
> every reward/settlement path) → synthesis. The adversarial pass **materially changed** four results;
> each correction is called out inline in a `> Synthesis correction` block, so the raw agent work and
> the adjudicated result are both visible.

**Subsystems:** games · blackjack · deathmatch · rps_tournament · counting · chain · leaderboard ·
community · community_spotlight · karma

---

## Verdict — GO-with-amendments (Lane C clears the 80% bar)

**Lane C measures 70% tier-1/2 as-written → 84% with amendments** (289 surface units). This is the
**hardest grammar-fit lane** (the spike measured blackjack at 44%), and it lands almost exactly where
the 3-subsystem spike sample predicted — **73%→85% (spike) vs 70%→84% (Lane C, 10 subsystems)**. The
two spike-anchored subsystems **reproduce the spike verbatim** (blackjack 44%→44%, karma 80%→87%),
which validates the measurement. **The declarative §2 grammar can express the game/community surface
as durable generated declarations** — *provided* three new tier-2 families are added (**G-7
MessagePipelineStageSpec · G-8 ChannelMatchSpec · G-9 TournamentLobbySpec**) and game engines / rules /
board renderers / move handlers stay **deliberate tier-3 escape hatches by design** (design-spec §10.1
risk 5). No structural rethink of the grammar is required; the game facet's `ChallengeSessionSpec`
already carries the hard part (session choreography, escrow, settle-once, recovery).

### Fit table (roll-up)

| Subsystem | Surface units | Fit — as-written | Fit — with amendments | Verdict |
|---|---:|---:|---:|---|
| games | 20 | **100%** | **100%** | improve (unify hubs) |
| blackjack | 18 | **44%** | **44%** | keep (the anchor) |
| deathmatch | 49 | **45%** | **76%** | keep (+ settle-once bug) |
| rps_tournament | 59 | **56%** | **78%** | improve |
| counting | 48 | **69%** | **85%** | keep / improve |
| chain | 30 | **93%** | **97%** | improve (merge w/ counting) |
| leaderboard | 24 | **96%** | **96%** | **merge into kernel** |
| community | 10 | **100%** | **100%** | keep (pure-router ceiling) |
| community_spotlight | 16 | **88%** | **94%** | improve |
| karma | 15 | **80%** | **87%** | keep |
| **OVERALL** | **289** | **70%** | **84%** | **GO-with-amendments** |

*Amended = with **ratified** amendments only (G-1…G-9). Two provisional lifts (P-1 EventFeedProjectionSpec
in spotlight; treating the rps bracket as declarable) are **not** counted — they would raise spotlight
94%→100% and are held pending a 2nd instance. So 84% is the disciplined floor, not the ceiling.*

---

## Central question — every stateful game/community loop, answered

The brief requires each stateful loop to resolve to exactly one of: **(a)** tier-1/2 with existing
grammar/amendments · **(b)** needs a reusable primitive family · **(c)** deliberate tier-3 escape hatch.

| Stateful loop | Subsystem(s) | Answer | Primitive |
|---|---|---|---|
| Single-player vs-house hand | blackjack solo | **(a)** session choreography + **(c)** engine/board/moves | `ChallengeSessionSpec` + deliberate tier-3 rules |
| Two-player **turn alternation** (attack/defend) | deathmatch | **(a)** — `ChallengeSessionSpec` covers the turn loop; moves/engine stay **(c)** | `ChallengeSessionSpec` (NO `TurnLoopSpec` — adversary-confirmed) |
| Two-sided PvP wager | blackjack/rps/deathmatch pvp | **(a)** escrow-at-accept + idempotent settle | `ChallengeSessionSpec.escrow`/`settle_once`/`refund_policy` |
| Tournament **lobby + pot** | blackjack + rps | **(b)** recurs (≥2) | **G-9 TournamentLobbySpec** (NEW) |
| Single-elimination **bracket topology** | rps only | **(c)** 1 instance → deliberate escape hatch | rps-owned tier-3 (pairing/byes/round-graph) |
| **Message-driven** count/word game | counting + chain | **(b)** ordered pipeline stage (≥3 uses) | **G-7 MessagePipelineStageSpec** (NEW); validation handler stays **(c)** |
| Channel-bound **persistent match/config** | counting + chain | **(b)** recurs (≥2) | **G-8 ChannelMatchSpec** (NEW) |
| Community **activity feed** (level-up) | community_spotlight | **(b) provisional** — 1 instance in Lane C | **P-1 EventFeedProjectionSpec** (hold for a 2nd) |
| Leaderboard/records aggregation | leaderboard + every game | **(a)** — dissolve into a generated kernel | `LeaderboardSpec` (+ enrichment: stat_source/value_template/card) |
| Registry-driven navigation **hub** | games, community | **(a)** core §2 `parent_hub`/`hub_group` | already generated — **no new amendment** |
| Scheduled/periodic **loops** | spotlight cache-trim; recovery sweeps | **(a)** `ManagedTaskSpec` (periodic) + `ChallengeSessionSpec` persistence (recovery) | existing |

---

## Consolidated amendment ledger

### Reused from the spike (G-1…G-6)
- **G-1 GatewayListenerSpec** — karma react-to-thank, blackjack/rps reaction-join + `on_guild_remove`
  (wiring only; a handler carrying real lobby logic stays tier-3).
- **G-3 AnnouncementRouteSpec** — rps tournament winner announce + registration reminder.
- **G-4 CommandSpec.cooldown** — karma, deathmatch, chain, leaderboard, community_spotlight (shipped
  `@commands.cooldown` that is silently *dropped* without a declared field).
- **G-5 declarative validator bounds** — karma (cooldown/daily_cap), blackjack/rps/deathmatch entry-fee
  & turn-timeout, counting skip-step, chain word-limit.
- *(G-2 list-valued settings, G-6 per-kind namespaces: not materially exercised in Lane C.)*

### NEW — ratified (recurs ≥2 subsystems, not covered by any existing family)
- **G-7 `MessagePipelineStageSpec`** `{stage_name, order, short_circuit, gate, handler}` — declares an
  **ordered** `core.runtime.message_pipeline` stage. **Recurs:** counting (order 15), chain (20),
  rps_tournament (40); **11 stages repo-wide.** Distinct from G-1: the shipped pipeline *deliberately
  replaced 5 concurrent `on_message` listeners* to fix message-ordering races
  (`message_pipeline.py:8-13`), so declaring N raw `on_message` G-1 listeners would re-introduce that
  race. The wiring becomes tier-1 data; the validation **handler stays tier-3** (game rules).
- **G-8 `ChannelMatchSpec`** — per-channel-keyed **persistent, open-ended** message-game with declared
  config fields + create/reset/end lifecycle + a state store, and **deliberately NOT**
  `ChallengeSessionSpec` (no accept phase, no turn clock, no escrow, no settle-once). **Recurs:**
  counting + chain. (Unifies the agents' separately-minted `ChannelMatchSpec` + `ChannelConfigSpec`.)
- **G-9 `TournamentLobbySpec`** — tournament **lobby + pot-escrow** choreography only: registration
  (reaction+button, `countdown_s`, `reminder_at_s`), entry-fee `CostVector`, idempotent pot payout,
  one-per-guild mutex, refund. **Recurs:** blackjack + rps tournaments. **Scope is narrowed by the
  adversary split** — the single-elimination **bracket topology stays tier-3** (see rps §), because it
  exists in exactly one subsystem.

### Provisional (do NOT ratify yet — single instance; flagged for Lane E / capstone)
- **P-1 `EventFeedProjectionSpec`** — event→template→scope-bounded ring, the read-side analog of G-3
  (sink is a durable projection, not a channel post). One instance in Lane C (spotlight level-up feed).
  Hold until a 2nd activity-feed appears (welcome joins / Lane E dashboards). Also fixes a real
  restart-fragility bug (the feed is an ephemeral module global today).
- **`LeaderboardSpec` enrichment** — extend the **existing** tier-2 `LeaderboardSpec` with
  `stat_source` / `value_template` / `card` so the 12 real rank providers (non-flat JSON aggregates,
  W/L templates, themed image cards) express as data. A refinement of a shipped family, **not** a new
  G-number.

### Rejected
- **`RegistryHubSpec`** (originally proposed by the games agent) — a registry-driven navigation hub is
  the kernel's **existing** generated-hub behaviour via §2 `parent_hub`/`hub_group` + declared
  `cross_links` + a `governance_filter` flag. The `community` subsystem scores **100% tier-1** on the
  identical pattern, so it is core §2, not a new amendment. (An explicit `HubPanelSpec` is a spec
  *clarification* of `parent_hub` worth making, but it moves no fit numbers.)

---

## Structural danger-zone flags (lane summary)

| Danger-zone pattern | Present in | Grammar answer |
|---|---|---|
| Stateful turn/round loop | deathmatch (turn), rps (bracket), blackjack, counting | `ChallengeSessionSpec` (turn) ✓ · bracket = deliberate tier-3 (1 instance) |
| Timers / timeouts | all games (accept/turn), rps countdown, blackjack autostart | `ChallengeSessionSpec` timeouts + G-9 countdown ✓ |
| `wait_for` flows | **none found** in Lane C (reaction/component/pipeline instead) | n/a — this lane uses views + reactions + pipeline stages, not `wait_for` |
| Component/session recovery on restart | blackjack, rps, deathmatch (ephemeral), counting (persisted) | `persistence=checkpointed/authoritative` + cog_load sweeps ✓ (⚠ rps **cannot resume an in-flight bracket** — refund-only; a genuine new capability to spec) |
| Escrow / settlement / payout | blackjack, rps, deathmatch(no coin) | `ChallengeSessionSpec.escrow`/`settle_once`/`refund_policy` + G-9 pot — via the audited `game_wager_workflow` seam ✓ (Lane B dep) |
| **Anti-double-settle (settle_once)** | blackjack, rps, deathmatch | `settle_once=True` kernel seam ✓ — **but 2 shipped paths lack it → 2 live bugs (below)** |
| Leaderboards / records | leaderboard + every game, karma | `LeaderboardSpec` (+ enrichment) — leaderboard cog should dissolve into a generated kernel ✓ |
| Social / community moderation | counting/chain deletes | route through the shared `moderation_service.auto_delete` seam ✓ (cross-lane) |

### ⚑ Two live runtime bugs surfaced (documented, NOT fixed — docs-only audit)

The reward-settlement and tier3-could-be-tier2 adversaries **independently** found two reachable
anti-double-settle defects in shipped source. They are **not** audit artifacts and are **out of scope
to fix here** (this PR is documentation-only); they are recorded because they are the empirical case
for making `settle_once` a **kernel-owned** `ChallengeSessionSpec` field in the rebuild (both close *by
construction* under a single kernel settle-once seam). **Flagged for the owner** to spin a separate fix PR:

1. **Deathmatch PvP double-settle** — `_DuelView._resolve`/`on_timeout` (`deathmatch_cog.py:214`/`:151`)
   guard only on `duel.is_over` + `active_duels.pop`, with no atomic claim, while `interaction_check`
   gates only on turn. Two finishing interactions (or a click racing the turn-timeout) can each run
   `update_leaderboard` → **double W/L records write + double gear-wear**. (The bot path already uses
   `SettleOnceMixin.claim_settlement`; the PvP path does not.)
2. **Blackjack free-tournament double-pay** — `payout_tournament`'s `free_reward` leg
   (`game_wager_workflow.py:330-333`) is explicitly *not* row-guarded ("single-call by construction"),
   but `_check_tourn_done` (`tournament_views.py:222`) has no aggregate settle-once and its completion
   guard is separated from the payout by an `await channel.send`. Two players finishing concurrently in
   a **free** tournament (entry_fee=0 is allowed) **double-pay the fixed consolation reward**. (Paid
   tournaments are safe — the escrow-row deletion is idempotent.)

---

## Deliberate tier-3 escape hatches (by design — NOT gaps)

The grammar **must never express game rules** (the "worse programming language" failure). These stay
tier-3 code behind stable `HandlerRef`/`renderer_override` seams, and that is the *correct* design:
blackjack/rps/counting **engines** (`blackjack_engine`, `rps.rules.determine_winner`,
`counting.handler.compute_decision` + the DoS-bounded `parsing` AST evaluator), all **game-move
handlers** (hit/stand/double, attack/defend, rps play), all **board renderers**
(`renderer_override`), the **karma grant seam** (5 typed error shapes + cooldown/daily-cap anti-abuse),
the **rps single-elimination bracket** (1 instance), and blackjack/rps **reaction-join lobby bodies**
(G-1 declares the wiring, the body is real lobby logic). The leaderboard **image-card renderer** is
tier-3 but **kernel-shared across all 12 boards** — it does not multiply per subsystem.

## Cross-lane dependencies (recorded; audit stays anchored to Lane C)

- **Lane B (economy)** — the escrow/coin ledger under every wager, via the audited
  `services.game_wager_workflow` (`open_pvp_wager`/`settle_pvp`/`refund_pvp`/`enter_tournament`/
  `payout_tournament`/`recover_escrow`) → `economy_service` INV-F seam. deathmatch gear-wear → mining.
- **games-core / L0** — `ChallengeSessionSpec` kernel, `game_state_service` restart-safe checkpoints
  (migration 015, ADR-002), `tournament_state_service` one-per-guild mutex, `SettleOnceMixin`
  (`utils/terminal_guard.py`), `core.runtime.message_pipeline` + `scope_locks` + `tasks`.
- **Lane C internal** — `rank_providers` aggregates 12 subsystems' boards (leaderboard reads them all);
  `game_xp_service` backs the world card; spotlight reads xp/coins/game providers.
- **moderation (Lane A)** — counting/chain rule-deletes route through `moderation_service.auto_delete`.

## Capstone carry-forward (per BRIEF)

Every subsystem below carries its **dependency-layer guess · production-grade done-definition (the
`parity/` golden it must pass) · outperform target (or `pending Lane F`)** in its
`MAP → RECONSIDER → SIMULATE → OPTIMIZE` block. Build-order signal for the capstone: **L0 runtime**
(message_pipeline, game_state, tasks, scope_locks) → **economy/escrow** (Lane B) → **games-core**
(`ChallengeSessionSpec`, `LeaderboardSpec`, tournament mutex, `SettleOnceMixin`, **G-7/G-8/G-9**) →
**each subsystem** (its rules engine + hub). Leaderboard and the two hubs are *generated kernels*, not
subsystems to build. `Outperform` bars are provisional pending Lane F (MEE6/Carl-bot/Dank Memer/etc.).

## Unverified / drift (⚠)

- **blackjack wins leaderboard + `stat_writes`** — in the spike manifest but **NOT in current source**
  (no stat/xp/leaderboard write in any blackjack file). Counted as a forward "decision 10" tier-2 unit
  and flagged; it cannot ship until games-core stat plumbing exists.
- **rps in-memory settings** (`default_mode`/`default_best_of`) are a runtime dict, **not persisted** —
  a drift the manifest fixes by making them `SettingSpec`s.
- **deathmatch `deathmatch_stats`** DDL lacks a `guild_id` column though CRUD uses it — a StoreSpec
  column declaration would surface this at build time (a grammar *benefit*).
- **chain `chain_count`** is written every allowed message but **never surfaced** — a latent
  `LeaderboardSpec` or a dead field.
- **karma help** surfaces via `subsystem_registry` entry_points, not a `help_catalogue` row (not a tier
  change).
- Command `file:line` cited at the `@commands.*` **decorator** line throughout; the ground-truth JSON
  cites the `async def` line (1–2 lines below). Same commands; benign, noted per subsystem.

---


---

### games
_cogs: disbot/cogs/games_cog.py · disbot/views/games/hub.py · disbot/views/explore/world_hub.py · disbot/views/explore/world_card.py · disbot/utils/settings_keys/games.py · (backing: disbot/services/world_registry.py, disbot/views/hub_children.py, disbot/services/game_xp_service.py)_

> **Scaffold drift corrected.** The scaffold `_cogs:` line named `games_cog.py, blackjack_cog.py, rps_tournament_cog.py` and then inlined ~30 child-game rows (blackjack/rps/deathmatch panels, views, listeners, escrow, stores). Those belong to the **blackjack / rps_tournament / deathmatch** sections (Q-0120: their internals are re-tiered there, not here). The **games-hub** section audits only: the four `games_cog` commands + help hook, the two registry-driven navigation hubs (Games hub, Explore world hub), the world card read, and the games `settings_keys` module. The scaffold also **omitted** `views/explore/world_hub.py`, `views/explore/world_card.py`, and `views/games/hub.py` from the cog line. All four `games_cog.py` command line numbers (39/45/59/84) verify correct against source.

#### Surface-unit ledger
| Unit | Kind | File:line | Tier (as-written) | Tier (with amendments) | Rationale / gap |
|---|---|---|---|---|---|
| !games | command | disbot/cogs/games_cog.py:38-42 | tier-1 | tier-1 | Route = PanelRef(GamesHubView) via `build_games_hub_panel`→`send_panel`; open-panel workflow, zero domain code. |
| /games (slash) | command | disbot/cogs/games_cog.py:80-101 | tier-1 | tier-1 | Same PanelRef open-panel, ephemeral; reuses `build_games_hub_panel` so governance filter applies identically. |
| !world | command | disbot/cogs/games_cog.py:44-56 | tier-1 | tier-1 | Route = PanelRef(ExploreWorldHubView) + static hub embed; open-panel workflow. |
| !worldcard (alias mystats) | command | disbot/cogs/games_cog.py:58-70 | tier-2 | tier-2 | Read-model command: `build_world_card_embed` over `game_xp_service.world_identity` ProviderRef; provider-shaped status read. |
| build_help_menu_view (hub direct-nav hook) | help | disbot/cogs/games_cog.py:72-78 | tier-1 | tier-1 | Help projection returning the Games hub panel; kernel help entry. |
| GamesHubView | panel/view | disbot/views/games/hub.py:304-377 | tier-1 | tier-1 | Registry-driven navigation hub: discovers `parent_hub=="games"` children from SUBSYSTEMS, groups (competitive/activities), row-packs, forwards each to child `build_help_menu_view`. Dynamic child-source + governance filter is **not** a static PanelSpec → grammar GAP, **core §2 generated hub (`parent_hub`/`hub_group`) — NO new amendment (community proves it 100% tier-1)**. NOT domain logic (pure navigation), so not a deliberate escape hatch. |
| _GameHubButton | panel/action | disbot/views/games/hub.py:269-301 | tier-2 | tier-1 | Thin binding over shared `HubChildButton` (hub_key + back_attacher + no-panel fallback); forwarding + click-time governance recheck live in the shared kernel button. Generated hub (parent_hub) → tier-1. |
| build_games_hub_panel (governance-filtered factory) | workflow | disbot/views/games/hub.py:155-198 | tier-2 | tier-1 | Resolve visibility (`governance_service.resolve_visibility`) → filter children → build embed+view. Governance = kernel BindingSpec; with the generated hub the spec generates the filtered child list → tier-1. |
| ExploreWorldHubView | panel/view | disbot/views/explore/world_hub.py:243-269 | tier-2 | tier-2 | Second flavor of the same pattern: one `_WorldButton` per registered `WorldEntry` from `world_registry`, click → `entry.opener`. Bespoke nav code today → grammar GAP, **core §2 generated hub — NO new amendment** (entry-registry variant). |
| _WorldButton | panel/action | disbot/views/explore/world_hub.py:167-198 | tier-2 | tier-1 | Thin defer→dispatch to `entry.opener` (coming-soon fallback when opener None). Generated hub → tier-1. |
| _WorldCardButton | panel/action | disbot/views/explore/world_hub.py:201-226 | tier-2 | tier-2 | Read-model button: defer → `build_world_card_embed` in place; provider read stays tier-2 (read-model). |
| _open_mining_world | nav handler | disbot/views/explore/world_hub.py:46-74 | tier-2 | tier-2 | Cross-subsystem opener: swaps panel to mining hub, builds `mining.main_panel.build_overview_embed` (guarded read). Thin extract-and-route into another subsystem's read → tier-2 (legitimate handler ref, cross-lane dep). |
| _open_fishing_world | nav handler | disbot/views/explore/world_hub.py:77-98 | tier-1 | tier-1 | Static fishing entry-card embed projection; no logic. |
| ensure_default_world_entries + _DEFAULT_ENTRIES | store/registration | disbot/views/explore/world_hub.py:105-133 | tier-1 | tier-1 | Two `WorldEntry` rows registered into `world_registry` (idempotent). Rows are DATA (key/label/emoji/description/order); openers are handler refs (rows 12-13). |
| world_registry (WorldEntry store + register/get) | store | disbot/services/world_registry.py:33,63,79 | tier-1 | tier-1 | In-process registry (`_ENTRIES` dict) backing the world hub; StoreSpec-shaped registration primitive. |
| build_world_card_embed | read-model panel | disbot/views/explore/world_card.py:42-108 | tier-2 | tier-2 | FieldsBlock over `game_xp_service.world_identity` ProviderRef; read-only, stranger-grade (Q-0080), no writes. Includes local `_progress_bar` (world_card.py:33) render helper. |
| ACTIVE_TOURNAMENT | setting | disbot/utils/settings_keys/games.py:12 | tier-1 | tier-1 | Shared str SettingSpec (written by both rps + blackjack tournament cogs — intentional, blueprint §8). |
| RPS_DEFAULT_ENTRY_FEE | setting | disbot/utils/settings_keys/games.py:16 | tier-1 | tier-1 | int SettingSpec (default entry fee). G-5 bounds (min≥0) keep it tier-1 if a validator is added. |
| BLACKJACK_DEFAULT_ENTRY_FEE | setting | disbot/utils/settings_keys/games.py:20 | tier-1 | tier-1 | int SettingSpec (default entry fee). G-5 candidate for min≥0 bounds. |
| DEATHMATCH_TURN_TIMEOUT | setting | disbot/utils/settings_keys/games.py:25 | tier-1 | tier-1 | int SettingSpec (per-turn timeout secs, falls back to 60). G-5 candidate for a bounded range. |

#### Manifest sketch (§2 grammar)
```python
SubsystemManifest(
    key="games",
    commands=[
        CommandSpec("games", route=PanelRef("games.hub")),              # tier-1
        CommandSpec("games", kind="slash", ephemeral=True,
                    route=PanelRef("games.hub")),                       # tier-1
        CommandSpec("world", route=PanelRef("explore.world_hub")),      # tier-1
        CommandSpec("worldcard", aliases=["mystats"],
                    route=ProviderRef("game_xp.world_identity"),        # tier-2 read-model
                    render="world_card"),
    ],
    help=HelpEntry(hook="build_help_menu_view", route=PanelRef("games.hub")),  # tier-1

    # ── core §2 generated hub: registry-driven navigation hub (the proposed primitive) ──
    panels=[
        HubPanelSpec(                                                   # GamesHubView → tier-1 (core §2 parent_hub)
            id="games.hub",
            source="subsystem_registry:parent_hub==games",
            groups=["competitive", "activities"],
            child_route="build_help_menu_view",
            governance_filter=True,                # kernel visibility recheck @ build + click
            fallback="no_panel_embed",
            back_nav="games:back",
        ),
        HubPanelSpec(                                                   # ExploreWorldHubView → tier-2 (entry-registry variant)
            id="explore.world_hub",
            source="world_registry",               # entry-registry variant
            child_route=OpenerRef,                 # per-entry handler ref
            extra_actions=[ActionRef("world_card", route=ProviderRef("game_xp.world_identity"))],  # tier-2
        ),
    ],
    openers=[                                       # WorldEntry opener handler refs
        HandlerRef("open_mining_world"),           # tier-2 — cross-subsystem read (Lane D mining)
        HandlerRef("open_fishing_world"),          # tier-1 — static entry card
    ],
    stores=[
        StoreSpec("world_registry", rows=_DEFAULT_ENTRIES),  # tier-1 registry rows (data)
    ],
    settings=[
        SettingSpec("active_tournament", type=str, shared_write=True),         # tier-1
        SettingSpec("rps_default_entry_fee", type=int, bounds=(0, None)),      # tier-1 (G-5)
        SettingSpec("blackjack_default_entry_fee", type=int, bounds=(0, None)),# tier-1 (G-5)
        SettingSpec("deathmatch_turn_timeout", type=int, default=60, bounds=(1, None)),  # tier-1 (G-5)
    ],
    # game=GameFacet(...) — NONE at hub level. All sessions/leaderboards/escrow/
    # move-handlers/engines live in the child sections (blackjack, rps_tournament,
    # deathmatch) and are recorded as cross-section deps, not re-tiered here.
)
```

#### Tier-3 dispositions
- **GamesHubView** (hub.py:304) — grammar GAP → **core §2 generated hub (parent_hub) — no new amendment**. Dynamic child discovery (SUBSYSTEMS filtered by `parent_hub`), group ordering, row-packing, governance filter, and forward-to-child-panel are pure navigation, NOT domain logic — so this is a missing declarative primitive, not a deliberate escape hatch. The same pattern is used by the Community and Utility hubs (the code explicitly mirrors `views.community.hub._format_child_label`) → recurring → a named amendment is justified.
- **ExploreWorldHubView** (world_hub.py:243) — grammar GAP → **core §2 generated hub** (entry-registry variant over `world_registry` with per-entry `OpenerRef` handlers). Second in-repo recurrence of the exact registry-driven-hub shape, confirming the registry-driven hub is core §2 behaviour (community proves it 100% tier-1), not a new primitive.
- **No deliberate escape hatches at hub level.** Every non-tier-1 unit here is navigation, a read-model, or a setting — all grammar-expressible. The deliberate tier-3 (game engines, board renderers, move handlers, escrow/settlement, settle_once) live entirely in the child game sections and are correctly kept as code there (design-spec §10.1 risk 5). The Games hub is the router that reaches them; it carries no rules itself (verified: `GamesCog` docstring "contains **zero** game logic", `GamesHubView` "pure routing").

#### Fit numbers
units total = **20** · tier-1/2 (as-written) = **20 (100%)** · tier-1/2 (with amendments) = **20 (100%)**.
> **Synthesis correction (cross-section consistency).** The originating agent tiered the two registry-driven hubs (`GamesHubView`, `ExploreWorldHubView`) tier-3-as-written and proposed a new `RegistryHubSpec` amendment to lift them. That is **overturned**: a registry-driven navigation hub is the kernel's **existing** generated-hub behaviour, declared via the §2 `parent_hub`/`hub_group` fields + a `cross_links` list + a `governance_filter` flag — the **same** primitive the `community` subsystem scores **100% tier-1** on. So `GamesHubView` is tier-1 (generated `parent_hub` hub, identical to `CommunityHubView`) and `ExploreWorldHubView` is tier-2 (the entry-registry variant over `world_registry` with per-entry `OpenerRef` handler refs). **No new amendment** (`RegistryHubSpec` rejected); an explicit `HubPanelSpec` is a spec *clarification* of `parent_hub`, not a fit-moving family.
Arithmetic (as-written): tier-1 = 12 (!games, /games, !world, help-hook, _open_fishing_world, WorldEntry-registration, world_registry, 4 settings, **GamesHubView**), tier-2 = 8 (!worldcard, _GameHubButton, build_games_hub_panel, _WorldButton, _WorldCardButton, _open_mining_world, build_world_card_embed, **ExploreWorldHubView**), tier-3 = 0. 20/20 = **100%**. Amended = 100% (unchanged). High fit is honest: the Games hub is a pure navigation/read surface with **no game rules** — unlike the blackjack anchor (44%), whose tier-3 engine/board/moves live in the child sections.

#### Structural-gap flags
- **Stateful turn/round loop · timers/timeouts · wait_for · escrow/settlement · settle_once · leaderboards** — **NONE at hub level** (verified: no `tasks.loop`, no `asyncio.sleep`, no `wait_for`, no escrow/`SettleOnceMixin`, no leaderboard write in the hub/world files). Every such danger zone is in a routed-to child game → recorded as cross-section deps, expressed there via `ChallengeSessionSpec` / `CostVector` / `LeaderboardSpec` + deliberate tier-3 engines.
- **Authority recheck (security)** — click-time governance re-resolution on the Games hub (`build_games_hub_panel` re-runs `resolve_visibility` on rebuild, hub.py:190-191, 227-231; shared `HubChildButton` rechecks on click). Grammar-expressible: kernel BindingSpec / `governance_filter=True` on core §2 generated hub. No new primitive needed.
- **Cross-subsystem coupling** — `_open_mining_world` reaches into `mining.main_panel.build_overview_embed` (world_hub.py:51,66), guarded by try/except so navigation never crashes on a read. Expressed as a tier-2 OpenerRef handler; acceptable coupling, not a gap.
- **Component/session recovery on restart** — N/A at hub level (hubs are stateless persistent-view anchors; `custom_id` schemes `games:open:{sub}` / `explore:open:{key}` re-route on restart with no state to recover).

#### MAP → RECONSIDER → SIMULATE → OPTIMIZE
- **RECONSIDER verdict: improve** — keep the router-only design (it is exemplary: zero game logic, registry-driven, governance-filtered), but **unify the two hand-written registry hubs** (Games hub + Explore world hub — and the sibling Community/Utility hubs) under one declarative **core §2 generated hub** so they stop being duplicated navigation code.
- **Optimal new-bot form:** a single **`HubPanelSpec`** (a spec *clarification* of the existing §2 `parent_hub`/`hub_group` mechanism — **not** a new amendment) parameterized by `source` (subsystem-registry-filter | named entry-registry), `groups/order`, `child_route` (child panel hook | per-entry OpenerRef), `governance_filter`, and `fallback`. The Games hub, Explore world hub, Community hub, and Utility hub all become ~10 lines of DATA; the world card stays a read-model `ProviderRef` panel. New games/worlds dock in by registering a row — no hub edit (already the design intent, now made declarative). *(The originating agent named this `RegistryHubSpec` and counted it as a new amendment; synthesis rejects that — it is core §2, proven by community scoring 100% tier-1 on the same pattern.)*
- **Dependency-layer guess:** L0 runtime navigation + governance kernel (the hub primitive), sitting **above** games-core; the world card sits on the shared progression layer (`game_xp`). The hub subsystem itself is a thin routing layer over the subsystem/world registries.
- **Production-grade done-definition:** parity golden = for a fixture SUBSYSTEMS/world_registry set, the generated `HubPanelSpec` renders the identical button set, grouping, row layout, governance-filtered visibility, and click-forward targets as today's `GamesHubView`/`ExploreWorldHubView` (custom_ids `games:open:{sub}`, `explore:open:{key}`, `games:back` preserved); `!worldcard` in a DM shows the "per-server" empty state and in-guild shows world level + per-game standings from `world_identity`.
- **Outperform target:** pending Lane F. Directionally: a governance-filtered, registry-driven game hub that also surfaces a **cross-game identity/world card** (shared world level + separate per-game ladders) already beats stock hub bots (MEE6/Dank Memer game menus are flat static command lists with no unified progression surface). The federated Explore "town square" + world card is the differentiator to press.
- **Cross-lane dependency notes:** routes into **blackjack / rps_tournament / deathmatch** (Lane C siblings — their engines/sessions/escrow re-tiered in their own sections); `_open_mining_world` and the fishing entry card depend on **mining/fishing** (Lane D economy/progression); the world card depends on `game_xp_service` shared-XP store (Lane D progression); hub filtering depends on `governance_service` + `subsystem_registry` (L0 governance/runtime).

---

### blackjack
_cogs: disbot/cogs/blackjack_cog.py · disbot/cogs/blackjack/{schemas,_state,_persistence,actions}.py · disbot/views/blackjack/{solo_view,pvp_view,tournament_views,embeds}.py · disbot/views/games/blackjack_panel.py · disbot/services/{blackjack_engine,blackjack_state,blackjack_persistence,game_wager_workflow,game_state_service}.py_

_Scaffold/spike drift corrected: (1) command **decorator** lines verify exactly (`blackjack` :431, `bjtournament` :516, `bjstart` :577, `bjstatus` :589); the ground-truth JSON `:432/:518/:579/:590` are the `async def` lines — same commands. (2) **Drift vs spike manifest:** the spike's `wins leaderboard` + `stat_writes=(blackjack.hands, blackjack.wins, blackjack.tournaments)` are **NOT in current source** — no `game_xp`/stat/leaderboard call exists in any blackjack file; they are the spike's forward "decision 10" port additions and are counted as tier-2 rebuild-design units, flagged ⚠. (3) `default_entry_fee` ships a **registered validator** `_validate_non_negative_int` + presets (schemas.py:23,39,41); the spike modeled it as a bare int — G-5 makes that non-negativity bound declarative (stays inside the tier-1/2 band, no fit change). (4) `actions.py` + `blackjack_panel.py` (a full hub launcher: 6 buttons, 2 modals, 1 UserSelect, 4 sub-views) are real surface the spike **condensed** into the session-start command + board/result renderer units; noted, not re-counted, to hold the 44% anchor._

This subsystem **is the spike's stateful-game calibration anchor** (`tools/grammar_spike/manifests/blackjack.py`, measured 8/18 = 44%). The ledger below re-derives the spike's 18 units, verified file:line against current source. Game moves, engine, and renderers are **deliberate tier-3 by design** — not gaps.

#### Surface-unit ledger
| Unit | Kind | File:line | Tier (as-written) | Tier (with amendments) | Rationale / gap |
|---|---|---|---|---|---|
| `!blackjack` (+`bj`) | command | blackjack_cog.py:431 | 3 | 3 | session-start: bet parse + balance check + escrow + engine deal (solo & PvP branches); lifecycle is spec-owned after → **escape hatch** |
| `!bjtournament` (+`bjtourn`) | command | blackjack_cog.py:516 | 3 | 3 | multi-player lobby orchestration (registration view, autostart timer, singleton lock) → **escape hatch** |
| `!bjstart` | command | blackjack_cog.py:577 | 3 | 3 | force-start lobby op (cancels timer, calls `_launch_tournament`) → **escape hatch** |
| `!bjstatus` | command | blackjack_cog.py:589 | 2 | 2 | status read over session state (`_tournaments` → `_tourn_embed`) — provider-shaped read |
| board renderer | renderer | solo_view.py:38 + embeds.py:24 | 3 | 3 | `renderer_override` — §2.9 named escape-hatch class (cards, totals, hole-card reveal) |
| hit action | panel-action | solo_view.py:154 | 3 | 3 | game-move handler (draw + bust check) → **escape hatch**; declared surface carries auth/audit/namespace |
| stand action | panel-action | solo_view.py:179 | 3 | 3 | game-move handler (`_resolve` → dealer_play + payout) → **escape hatch** |
| double action | panel-action | solo_view.py:183 | 3 | 3 | game-move + second escrow leg (2× balance gate) → **escape hatch** |
| result renderer + replay | renderer | solo_view.py:245 (replay id :289) | 3 | 3 | outcome card + `blackjack:solo:replay` static id verbatim; replay re-enters start flow → **escape hatch** |
| `default_entry_fee` setting | setting | schemas.py:29 | 2 | 1 | ships a registered non-negative validator (schemas.py:23) → tier-2 as-written; **G-5** makes the `min=0` bound declarative → tier-1 (stays in tier-1/2 band) |
| reaction-join listener | gateway-listener | blackjack_cog.py:410 | 3 | 3 | `on_raw_reaction_add` — **G-1** declares the wiring, but the join body (`try_join`, dedup, bot filter, embed edit) is real lobby logic → **stays tier-3** |
| solo session lifecycle | session | _state.py:49; recovery cog:157 | 2 | 2 | `ChallengeSessionSpec`: no-accept, turn_timeout, stale cleanup, settle-once, checkpointed recovery — choreography is data |
| pvp session lifecycle | session | pvp_view.py:110; escrow :123 | 2 | 2 | same family: accept phase (`_ChallengeView`) + two-sided escrow-at-accept + `claim_settlement` |
| tournament session lifecycle | session | blackjack_cog.py:599; tournament_views.py:196 | 2 | 2 | same family: entry fee from setting, per-round chips, pot payout |
| game engine (rules) | engine | services/blackjack_engine.py:51-86 | 3 | 3 | pure-function `hand_value`/`is_blackjack`/`new_deck` — **escape hatch BY DESIGN**; grammar must never express game rules |
| wins leaderboard | game | ⚠ not shipped (spike port) | 2 | 2 | `LeaderboardSpec` + `stat_writes` — **drift**: no stat/xp/leaderboard write exists today; forward "decision 10" tier-2 unit |
| game_state checkpoints | store | services/game_state_service.py; _persistence.py:39 | 2 | 2 | `persistence=checkpointed` on the session spec; shared table (migration 015), blackjack owns no table (019 rule) |
| help entry | help | blackjack_cog.py:226 (spike) / panel Rules embed:140 | 1 | 1 | projection over declared metadata |

#### Manifest sketch (§2 grammar)
```python
SubsystemManifest(
    key="blackjack", display_name="Blackjack", category="games",
    dependencies=("economy",),  # escrow through the INV-F seam
    parent_hub="games",
    commands=(
        CommandSpec("blackjack", PREFIX, aliases=("bj",),
            route=HandlerRef("blackjack.start", "bet parse + deal")),      # T3 thin
        CommandSpec("bjtournament", PREFIX, aliases=("bjtourn",),
            route=HandlerRef("blackjack.tournament_open", "lobby orch")),  # T3
        CommandSpec("bjstart", PREFIX,
            route=HandlerRef("blackjack.tournament_start", "lobby op")),   # T3
        CommandSpec("bjstatus", PREFIX,
            route=HandlerRef("blackjack.tournament_status", "status read")), # T2 provider
    ),
    panels=(
        PanelSpec("blackjack.board",
            renderer_override=HandlerRef("blackjack.render_board", "live board"),  # T3
            actions=(
                PanelActionSpec("hit",    handler=HandlerRef("blackjack.hit")),    # T3 move
                PanelActionSpec("stand",  handler=HandlerRef("blackjack.stand")),  # T3 move
                PanelActionSpec("double", handler=HandlerRef("blackjack.double")), # T3 move
            )),
        PanelSpec("blackjack.result",
            renderer_override=HandlerRef("blackjack.render_result", "outcome card"), # T3
            actions=(PanelActionSpec("replay",
                custom_id_override="blackjack:solo:replay",
                handler=HandlerRef("blackjack.replay")),)),                          # T3
    ),
    settings=(
        SettingSpec("default_entry_fee", "int", 0,
            settings_key="blackjack_default_entry_fee",
            validator=HandlerRef("blackjack.non_negative")   # T2 as-written
            # → with G-5: bounds=(0, None) declarative → T1
        ),
    ),
    gateway_listeners=(   # G-1 family
        GatewayListenerSpec("on_raw_reaction_add",
            handler=HandlerRef("blackjack.reaction_join", "real lobby logic")),  # T3 (wiring declared, body code)
    ),
    game=GameFacet(
        sessions=(
            ChallengeSessionSpec("blackjack.solo", accept_timeout_s=0, turn_timeout_s=120,
                stale_after_s=900, settle_once=True, persistence="checkpointed",
                escrow=CostVector("coins", "arg"), refund_policy=HandlerRef("blackjack.refund")),  # T2
            ChallengeSessionSpec("blackjack.pvp", accept_timeout_s=60, turn_timeout_s=120, ...,   # T2
                settle_once=True, persistence="checkpointed", escrow=CostVector("coins","arg")),
            ChallengeSessionSpec("blackjack.tournament", accept_timeout_s=120, ...,                # T2
                escrow=CostVector("coins", "setting:blackjack_default_entry_fee")),
        ),
        leaderboards=(   # ⚠ FORWARD — needs stat_writes wired first
            LeaderboardSpec("blackjack.wins", stat_key="blackjack.wins", metric="sum"),  # T2
        ),
    ),
    stores=(),  # game_state checkpoints owned by games-core; session persistence field expresses them
    help=HelpEntrySpec("Blackjack vs house or friends; coins ride on it."),  # T1
)
```

#### Tier-3 dispositions
- **`blackjack.start` (`!blackjack`)** — deliberate escape hatch: bet parse + escrow + deal is thin session-start domain logic; lifecycle after is spec-owned. Should stay code.
- **`bjtournament` / `bjstart`** — deliberate escape hatch: lobby orchestration (registration, autostart timer, channel provisioning) is real logic; the *session shape* is `ChallengeSessionSpec`, the orchestration body is not.
- **board renderer / result renderer** — deliberate escape hatch (§2.9 `renderer_override`): stateful card board + reveal flow. Making this data would be the "worse programming language" failure.
- **hit / stand / double actions** — deliberate escape hatch: game-move handlers. Declared surface keeps auth/audit/namespace; the move body is rules.
- **game engine (blackjack_engine.py)** — deliberate escape hatch BY DESIGN: pure-function rules; grammar must never express these.
- **reaction-join listener** — grammar gap **reused G-1** for the wiring declaration; the join *handler* stays tier-3 (real dedup/bot-filter/embed logic). Correct outcome — G-1 declares the seam, not the body.
- No **new** `G-<n>` proposed: every gap here is either covered by an existing amendment (G-1 wiring, G-5 validator) or is a legitimate game-rules escape hatch.

#### Fit numbers
units total = **18**.
tier-1/2 (as-written): tier-1 = {help} ; tier-2 = {default_entry_fee (validator), bjstatus, solo, pvp, tournament, wins-leaderboard, game_state-checkpoints} → **8 (8/18 = 44%)**.
tier-1/2 (with G-1 + G-5): G-1 does **not** lift the reaction-join (handler stays tier-3); G-5 shifts default_entry_fee tier-2→tier-1 (still inside the band). Count unchanged → **8 (8/18 = 44%)**.
tier-3 (10): 3 lobby/start commands + board renderer + result renderer + hit + stand + double + engine + reaction-join. **Matches the spike anchor exactly — 44% must not drift, and does not.**

#### Structural-gap flags
- **Stateful turn loop / timeouts** — expressed: `ChallengeSessionSpec.turn_timeout_s` / `stale_after_s`. The move *bodies* stay tier-3 (correct).
- **Session recovery on restart** — expressed: `persistence="checkpointed"` + `refund_policy`. The recovery *sweep code* (cog:157-297, version-mismatch drops) is kernel-owned once declared.
- **Escrow / settlement / payout** — expressed: `escrow=CostVector` + dependency on economy INV-F seam; money moves through `game_wager_workflow` (Lane B). No new primitive needed.
- **Anti-double-settle** — expressed: `settle_once=True` maps to `SettleOnceMixin.claim_settlement()` — the mixin is at **`utils/terminal_guard.py:44/:49`** and blackjack's PvP claim site is **`views/blackjack/pvp_view.py:201`** (solo uses `safe_defer` + `_active.pop`) — plus `payout_tournament` row-deletion idempotency. *(Corrects the originating agent's stale `_state.py:106` citation — that file is a 57-line re-export shim with no such symbol, Q-0120 citation discipline.)*
- **Leaderboards/records** — grammar has `LeaderboardSpec`, but the **stat-write source does not exist in current source** — needs games-core stat wiring (Lane C dep) before the board is real. Grammar-expressible, not yet shipped.
- **No wait_for** — challenge accept is a view, not a gateway wait; no gap.

#### MAP → RECONSIDER → SIMULATE → OPTIMIZE
- **RECONSIDER verdict: keep.** This is the spike's honest calibration anchor; the grammar carries the choreography (sessions, escrow, settle-once, recovery, refund) as data and correctly leaves rules/renderer/moves as tier-3. No merge/redesign warranted.
- **Optimal new-bot form:** three `ChallengeSessionSpec`s (solo/pvp/tournament) + one `GameFacet` with the wins `LeaderboardSpec` **actually backed by declared `stat_writes`** (close the shipped drift), one `default_entry_fee` SettingSpec with G-5 declarative bounds, one G-1 gateway listener for reaction-join, and a small tier-3 kernel of {engine, board renderer, result renderer, hit/stand/double, start/lobby handlers}. Net: the bespoke recovery loops, singleton lock, and escrow plumbing become generated kernel behavior; only ~10 rules/render/move units remain code.
- **Dependency-layer guess:** L0 runtime (game_state, tasks, resources, channels) → economy/escrow (Lane B) → games-core (ChallengeSession kernel, stats/leaderboard, tournament lock) → **blackjack** (this subsystem, top).
- **Production-grade done-definition:** parity golden must reproduce, on the rebuilt kernel: (a) natural-blackjack 1.5× payout & free-win 50-coin path; (b) PvP escrow-at-accept, single settle under concurrent finish callbacks (settle-once), tie-refund; (c) tournament entry-fee debit + pot payout + crash-recovery refund (no double-pay); (d) restart drops stranded solo/pvp rows and refunds stranded escrow; (e) turn/registration timeouts forfeit correctly. All must match current `blackjack_engine` + `game_wager_workflow` behavior byte-for-byte on payouts.
- **Outperform target:** pending Lane F (competitor benchmark). Candidate edge: most Discord casino bots (e.g. Dank Memer, UnbelievaBoat) lack crash-safe escrow with idempotent settle-once + automatic refund-on-restart — our declared `ChallengeSessionSpec(settle_once, checkpointed, refund_policy)` makes that money-safety a kernel guarantee, not per-game code.
- **Cross-lane dependency notes:** economy escrow/ledger (Lane B); game_state persistence + tournament lock + stat/leaderboard writes (games-core, Lane C); channel/resource provisioning (L0). The wins leaderboard cannot ship until games-core stat-write plumbing exists — anchor this as a Lane C games-core prerequisite, not a blackjack task.

---

### deathmatch
_cogs: disbot/cogs/deathmatch_cog.py, disbot/views/games/deathmatch_panel.py, disbot/cogs/deathmatch/actions.py, disbot/cogs/deathmatch/schemas.py, disbot/utils/db/games/deathmatch.py, disbot/services/rank_providers.py (DeathmatchProvider), disbot/utils/subsystem_registry.py (deathmatch entry :838)_

_Scaffold drift corrected: (1) `!dm_challenge` command decorator opens at cog:438 (`@commands.command`), `@cooldown(1,30,user)` at :444, `def challenge` at :445 — the scaffold's :445 is the def line, correct but the cooldown/aliases live above it. (2) Scaffold marked the db lines "⚠ unverified" — now verified: `get_deathmatch_stats` db:8, `update_deathmatch` db:16, `get_deathmatch_leaderboard` db:46. (3) Scaffold omitted the whole `cogs/deathmatch/actions.py` helper module, `_tick_duel_gear_wear`, the `DeathmatchProvider` leaderboard read model, `build_help_menu_view`, and the challenge/prompt embed builders — all added below. (4) `related_subsystems` for the deathmatch entry is `["economy","blackjack"]` (registry:849), not the `["economy","deathmatch"]` the scaffold showed (that line is a *different* entry at :738)._

#### Surface-unit ledger
| Unit | Kind | File:line | Tier (as-written) | Tier (with amendments) | Rationale / gap |
|---|---|---|---|---|---|
| !dm_challenge (aliases deathmatch/challenge/dm) | command | deathmatch_cog.py:438 | tier-3 | tier-2 | Session-START command: conflict-checks + opens the challenge session. ChallengeSessionSpec accept phase → tier-2 (like blackjack bet-parse deal). |
| @cooldown(1,30,user) on challenge | command cooldown | deathmatch_cog.py:444 | tier-3 | tier-1 | Shipped anti-abuse; undeclarable without amendment → **G-4** declares (rate,per,bucket) as data. |
| challenge_error | command error handler | deathmatch_cog.py:485 | tier-2 | tier-1 | Thin exception→message map (cooldown/BadArgument). With G-4 + kernel error projection → generated tier-1. |
| !dm_help (alias deathmatch_help) | command / help | deathmatch_cog.py:497 | tier-1 | tier-1 | Static help embed = help projection. |
| Deathmatch.cog_load → register_schemas | lifecycle wiring | deathmatch_cog.py:411 | tier-1 | tier-1 | Kernel schema-registration; subsumed by the manifest declaring settings. |
| build_help_menu_view | nav hook (→ panel) | deathmatch_cog.py:420 | tier-1 | tier-1 | Returns the hub panel = PanelRef open-panel workflow. |
| _Duel (engine: attack/defend/crit/armor/HP) | game engine | deathmatch_cog.py:20 | tier-3 | tier-3 | **Deliberate escape hatch** — pure game rules; grammar must never express these (design-spec §10.1 risk 5). |
| _ChallengeView (accept-phase lifecycle) | session view | deathmatch_cog.py:274 | tier-3 | tier-2 | Accept/decline + 30s timeout = ChallengeSessionSpec `accept_timeout_s`. |
| _ChallengeView.btn_accept | session control | deathmatch_cog.py:329 | tier-3 | tier-2 | Accept→active transition: loads gear (EffectiveStats), reads turn_timeout, spawns _DuelView = session-start choreography (tier-2), not game rules. |
| _ChallengeView.btn_decline | session control | deathmatch_cog.py:385 | tier-3 | tier-2 | Decline → result view; session terminal + kernel re-render. |
| _ChallengeView.on_timeout | session lifecycle | deathmatch_cog.py:306 | tier-3 | tier-2 | Accept-expiry (30s) with `_resolved` race guard = ChallengeSessionSpec accept_timeout_s + settle_once. |
| _DuelView (turn-loop container) | session view | deathmatch_cog.py:94 | tier-3 | tier-2 | interaction_check = turn gating; custom_id/turn_timeout = ChallengeSessionSpec. The two-player **turn loop is session choreography**, not a new primitive. |
| _DuelView.interaction_check (turn gate) | access control | deathmatch_cog.py:125 | tier-3 | tier-2 | "not your turn" gate = ChallengeSessionSpec custom_id_scheme/turn ownership. |
| _DuelView.build_embed | board renderer | deathmatch_cog.py:134 | tier-3 | tier-3 | **Deliberate escape hatch** — stateful board renderer. |
| _DuelView.btn_attack | game-move handler | deathmatch_cog.py:193 | tier-3 | tier-3 | **Deliberate escape hatch** — game move. |
| _DuelView.btn_defend | game-move handler | deathmatch_cog.py:204 | tier-3 | tier-3 | **Deliberate escape hatch** — game move. |
| _DuelView._resolve | game logic + settle | deathmatch_cog.py:214 | tier-3 | tier-3 | Turn-alternation + win-detection = game rules (escape hatch); the leaderboard/gear-wear calls it makes are declared stat_writes (tier-2 wiring) but the rule stays tier-3. |
| _DuelView.on_timeout | session settle | deathmatch_cog.py:151 | tier-3 | tier-2 | Turn-timeout win-by-default + settlement = ChallengeSessionSpec turn_timeout_s + stat_writes. |
| _tick_duel_gear_wear | settlement side-effect | deathmatch_cog.py:68 | tier-3 | tier-2 | Post-settle hook: loop fighters, skip bots, route to mining_workflow.wear_tick, collect notes = thin extract-and-route → tier-2 as a ChallengeSessionSpec settlement hook. Cross-lane (mining). |
| update_leaderboard | stat-write wrapper | deathmatch_cog.py:477 | tier-2 | tier-2 | Thin wrapper over db.update_deathmatch = ChallengeSessionSpec stat_writes / LeaderboardSpec write. |
| DeathmatchPanelView (hub) | panel | deathmatch_panel.py:603 | tier-1 | tier-1 | Open-panel workflow (PanelRef), 3 buttons. |
| DeathmatchPanelView.btn_fight_bot | panel action (session start) | deathmatch_panel.py:616 | tier-3 | tier-2 | Starts a solo session (gear read + spawn) = ChallengeSessionSpec solo persistence start. |
| DeathmatchPanelView.btn_challenge | panel action | deathmatch_panel.py:644 | tier-1 | tier-1 | Re-render to opponent picker = kernel re-render. |
| DeathmatchPanelView.btn_rules | panel action | deathmatch_panel.py:660 | tier-1 | tier-1 | Re-render rules embed = re-render/help projection. |
| _BotDuelView (solo session view) | session view | deathmatch_panel.py:192 | tier-3 | tier-2 | Container/lifecycle (SettleOnceMixin, 120s timeout) = ChallengeSessionSpec solo. |
| _BotDuelView.btn_attack | game-move handler | deathmatch_panel.py:236 | tier-3 | tier-3 | **Deliberate escape hatch** — game move. |
| _BotDuelView.btn_defend | game-move handler | deathmatch_panel.py:251 | tier-3 | tier-3 | **Deliberate escape hatch** — game move. |
| _BotDuelView._bot_turn | game AI logic | deathmatch_panel.py:261 | tier-3 | tier-3 | **Deliberate escape hatch** — drives pick_bot_action + resolves. |
| _BotDuelView._finish | settle + render | deathmatch_panel.py:296 | tier-3 | tier-3 | claim_settlement() = ChallengeSessionSpec settle_once (tier-2 wiring); the winner-render stays tier-3 escape hatch. |
| _BotDuelView.on_timeout | session settle | deathmatch_panel.py:322 | tier-3 | tier-2 | Settle-once timeout terminal = ChallengeSessionSpec turn_timeout_s + settle_once. |
| pick_bot_action | game AI | deathmatch/actions.py:40 | tier-3 | tier-3 | **Deliberate escape hatch** — bot combat strategy = game rules. |
| make_duel_key | session key helper | deathmatch/actions.py:62 | tier-1 | tier-1 | Stable sorted-pair key = ChallengeSessionSpec custom_id/session key scheme. |
| has_existing_duel | uniqueness guard | deathmatch/actions.py:70 | tier-3 | tier-2 | "one active session per participant" invariant = ChallengeSessionSpec matchmaking uniqueness. |
| can_challenge_human | validation | deathmatch/actions.py:97 | tier-2 | tier-2 | Thin self/bot validator = declared thin validator. |
| build_bot_duel_embed | board renderer | deathmatch_panel.py:108 | tier-3 | tier-3 | **Deliberate escape hatch** — board renderer. |
| build_bot_duel_result_embed | board renderer | deathmatch_panel.py:134 | tier-3 | tier-3 | **Deliberate escape hatch** — terminal board renderer. |
| build_deathmatch_challenge_embed / picker_embed | prompt render | deathmatch_panel.py:167 / :156 | tier-1 | tier-1 | Session accept-prompt render = kernel template. |
| build_deathmatch_overview_embed | help render | deathmatch_panel.py:52 | tier-1 | tier-1 | Overview projection. |
| build_deathmatch_rules_embed | help render | deathmatch_panel.py:67 | tier-1 | tier-1 | Rules projection. |
| _BotDuelResultView + btn_again | result view / rematch | deathmatch_panel.py:347 / :368 | tier-3 | tier-2 | Play-again re-runs solo session = ChallengeSessionSpec rematch. |
| _PvpDuelResultView + interaction_check | result view (dual-owner) | deathmatch_panel.py:391 / :423 | tier-2 | tier-2 | Two-owner terminal HubView = session access + nav (kernel). |
| _PvpDuelResultView.btn_rematch | rematch control | deathmatch_panel.py:432 | tier-3 | tier-2 | Re-issues challenge (consent preserved) = ChallengeSessionSpec rematch. |
| _DeathmatchChallengeSelectView / _DeathmatchOpponentSelect | selector (UserSelect) | deathmatch_panel.py:493 / :500 | tier-3 | tier-2 | Opponent picker → validate + spawn challenge = declared selector → session start. |
| turn_timeout | setting (bounded int) | deathmatch/schemas.py:33 | tier-2 | tier-1 | Registered _validate_positive_int HandlerRef → **G-5** declarative min bound makes it tier-1. presets/input_hint already data. |
| deathmatch.game.challenge | capability | subsystem_registry.py:858 | tier-1 | tier-1 | Capability declaration (BindingSpec-shaped). |
| deathmatch.stat.view | capability | subsystem_registry.py:859 | tier-1 | tier-1 | Capability declaration (⚠ no runtime read path found). |
| deathmatch_stats | store (table) | migrations.py:313 | tier-1 | tier-1 | StoreSpec. ⚠ guild_id column drift (see flags). |
| update_deathmatch | store mutation | db/games/deathmatch.py:16 | tier-2 | tier-2 | Atomic 2-side win/loss increment = ChallengeSessionSpec stat_writes / LeaderboardSpec write. |
| get_deathmatch_stats | store read | db/games/deathmatch.py:8 | tier-2 | tier-2 | Provider read (ProviderRef). |
| get_deathmatch_leaderboard | store read | db/games/deathmatch.py:46 | tier-2 | tier-2 | LeaderboardSpec-backed read. |
| DeathmatchProvider | leaderboard read model | rank_providers.py:443 | tier-2 | tier-2 | Rank/leaderboard read model = LeaderboardSpec. |
| !leaderboard deathmatch (cross-cog arg) | help/reference | leaderboard_cog.py:217 | tier-1 | tier-1 | Cross-cog leaderboard arg = projection/reference. |
| deathmatch registry entry (entry_points deathmatch/dm) | registry/help | subsystem_registry.py:838 | tier-1 | tier-1 | Declarative registry entry. |

#### Manifest sketch (§2 grammar)
```python
SubsystemManifest(
    key="deathmatch",
    commands=[
        CommandSpec("dm_challenge", aliases=["deathmatch","challenge","dm"],
            route=WorkflowRef("start_challenge_session"),   # tier-2: opens ChallengeSessionSpec accept phase
            cooldown=Cooldown(1, 30, bucket="user")),       # G-4
        CommandSpec("dm_help", aliases=["deathmatch_help"], route=HelpRef("deathmatch")),  # tier-1
    ],
    panels=[
        PanelSpec("deathmatch_hub", overview=EmbedRef("overview"),
            actions=[
                PanelAction("fight_bot",  StartSession("bot")),      # tier-2 solo start
                PanelAction("challenge",  ReRender("opponent_picker")),  # tier-1
                PanelAction("rules",      ReRender("rules")),        # tier-1
            ]),
        SelectorSpec("opponent_select", kind="UserSelect",
            route=WorkflowRef("start_challenge_session")),           # tier-2
    ],
    game=GameFacet(
        sessions=[ChallengeSessionSpec(
            game_key="deathmatch",
            accept_timeout_s=30,          # _ChallengeView
            turn_timeout_s="setting:turn_timeout",   # _DuelView (60s default)
            stale_after_s=None,
            settle_once=True,             # SettleOnceMixin (bot) + is_over guard (pvp)
            persistence="ephemeral",      # in-memory active_duels — lost on restart
            custom_id_scheme="deathmatch_panel:*",
            escrow=None,                  # no currency; gear-wear is a settlement hook, not escrow
            stat_writes=[StatWrite("deathmatch_stats", on="pvp_settle")],  # update_deathmatch
            refund_policy=None,
            modes=["solo_vs_bot","pvp","rematch"],
            # settlement hook (thin route → mining) — tier-2:
            on_settle=[HandlerRef("tick_duel_gear_wear")],
            # --- tier-3 escape hatches wired in by ref (game rules / renderers) ---
            engine=HandlerRef("_Duel"),               # tier-3 BY DESIGN
            bot_ai=HandlerRef("pick_bot_action"),     # tier-3 BY DESIGN
            move_handlers={"attack": HandlerRef("btn_attack"),   # tier-3 BY DESIGN
                           "defend": HandlerRef("btn_defend")},  # tier-3 BY DESIGN
            renderer_override=HandlerRef("build_duel_embed"),    # tier-3 BY DESIGN
        )],
        leaderboards=[LeaderboardSpec(board_id="deathmatch", stat_key="wins",
            metric="count", scope="guild")],   # DeathmatchProvider + get_deathmatch_leaderboard
    ),
    settings=[
        SettingSpec("turn_timeout", int, default=60, min=1,   # G-5 → tier-1
            presets=(30,60,120,300), capability="deathmatch.game.challenge"),
    ],
    bindings=[Capability("deathmatch.game.challenge"), Capability("deathmatch.stat.view")],
    stores=[StoreSpec("deathmatch_stats", cols=["user_id","guild_id","wins","losses"])],  # ⚠ guild_id drift
    help=[HelpEntry("deathmatch", overview=..., rules=...)],
)
```

#### Tier-3 dispositions
- **_Duel engine** (attack/defend/crit/armor) — *deliberate escape hatch*: pure game rules. Grammar must never encode combat math (worse-programming-language failure).
- **pick_bot_action** — *deliberate escape hatch*: bot combat AI = game rules.
- **_DuelView.btn_attack/btn_defend, _BotDuelView.btn_attack/btn_defend** — *deliberate escape hatch*: game-move handlers (calibrated exactly to blackjack hit/stand).
- **_DuelView._resolve, _BotDuelView._bot_turn** — *deliberate escape hatch*: turn-alternation + win-detection game logic (the settlement calls they make are declared stat_writes; the *rule* stays code).
- **_DuelView.build_embed, build_bot_duel_embed, build_bot_duel_result_embed, _BotDuelView._finish render** — *deliberate escape hatch*: stateful board renderers.
- **Everything else that was tier-3 as-written resolves to tier-2/1 by REUSING existing primitives** — no new G-<n> needed:
  - session accept/decline/turn/timeout/settle/rematch/uniqueness → **GameFacet.ChallengeSessionSpec** (already in spec). This subsystem is the direct test of "does ChallengeSessionSpec cover a genuine two-player turn loop?" — **it does**: the loop = session choreography (tier-2) + move handlers that advance `duel.turn` (tier-3 rules). **No TurnLoopSpec primitive is warranted.**
  - turn_timeout bounded validator → **G-5** (declarative bounds) → tier-1.
  - @cooldown → **G-4** → tier-1.
  - leaderboard read/write → **LeaderboardSpec** (already in spec).
  - gear-wear settlement → thin `on_settle` handler ref (extract-and-route to mining_workflow); single occurrence, does **not** recur enough to justify a new primitive.

#### Fit numbers
units total = **49**.
tier-1/2 (as-written) = **22 (45%)**. The 22 already-good: dm_help, challenge_error, cog_load, build_help_menu_view, update_leaderboard, panel + btn_challenge + btn_rules, _PvpDuelResultView(+check), challenge/picker/overview/rules/help embeds, make_duel_key, can_challenge_human, turn_timeout, 2 capabilities, deathmatch_stats, update_deathmatch, get_deathmatch_stats, get_deathmatch_leaderboard, DeathmatchProvider, !leaderboard arg, registry entry. → 22/49 = 45%.
tier-1/2 (with amendments) = **37 (76%)**. The 12 that *stay* tier-3 are all deliberate game rules/renderers: _Duel engine, pick_bot_action, _resolve, _bot_turn, _finish-render, _DuelView.build_embed, build_bot_duel_embed, build_bot_duel_result_embed, and the 4 move handlers (attack/defend × 2 views). 49 − 12 = 37 → 37/49 = 76%.
Arithmetic: as-written 22/49 = 44.9% ≈ 45%; amended 37/49 = 75.5% ≈ 76%. Calibrates cleanly to the blackjack 44% anchor — a game is declared session + declared money/stat flow + irreducible tier-3 engine/renderer/moves.

#### Structural-gap flags
- **Two-player stateful turn loop** — present (active_duels dict, alternating `duel.turn`). Expressed by ChallengeSessionSpec (accept/turn/settle) + tier-3 move handlers. **No new primitive family needed.**
- **Timers/timeouts** — 3 (30s accept / 60s turn / 120s bot). All map to ChallengeSessionSpec `accept_timeout_s` + `turn_timeout_s`. Expressed.
- **Component/session recovery on restart** — NOT handled: active_duels is in-memory → duels vanish on restart. ChallengeSessionSpec `persistence="ephemeral"` *names* this honestly; a production rebuild wanting resumable duels would set `persistence="checkpointed"` — grammar already has the knob.
- **Escrow/settlement/reward payout** — leaderboard win/loss (declared stat_writes) + gear-wear side-effect (thin settlement hook → mining). Expressed as data; the wear *rule* is a cross-lane call, not game math.
- **Anti-double-settle (settle_once)** — bot path uses SettleOnceMixin.claim_settlement; PvP path relies only on `is_over` + `active_duels.pop`. ChallengeSessionSpec `settle_once=True` would *formalize both uniformly* — a real hardening the grammar delivers for free.
- **Leaderboards/records** — LeaderboardSpec covers it.
- **Schema drift** — deathmatch_stats CREATE lacks guild_id though CRUD uses it; StoreSpec column declaration would surface this at build time (a grammar *benefit*, not gap).

#### MAP → RECONSIDER → SIMULATE → OPTIMIZE
- **RECONSIDER verdict: keep.** Well-factored: engine (_Duel) separated from views, shared actions helpers, settle-once on the bot path, configurable turn timeout, fair bot-duel-off-leaderboard rule. It is a clean instance of the game shape the grammar already targets.
- **Optimal new-bot form:** one `ChallengeSessionSpec(game_key="deathmatch", modes=["solo","pvp","rematch"], settle_once=True, persistence="ephemeral")` + `LeaderboardSpec` + a tier-3 `_Duel` engine module + tier-3 move/renderer refs. Fold the PvP `is_over` guard into the kernel `settle_once` claim so both paths share one anti-double-settle seam. Fix the deathmatch_stats guild_id column at the StoreSpec level.
- **Dependency-layer guess:** games-core (ChallengeSessionSpec + LeaderboardSpec kernel) → **this subsystem** (deathmatch engine/renderers) → depends on economy/mining (Lane B, gear-wear + EffectiveStats).
- **Production-grade done-definition:** parity golden — solo bot duel and PvP duel each play to a terminal result; accept/turn/bot timeouts each resolve to the correct win-by-default; a double-click on the finishing blow settles exactly once (no double leaderboard write, verified by a settle_once test); a rematch re-issues consent; leaderboard reflects exactly one W/one L per PvP settle; bot duels never touch the leaderboard; gear wears once per fighter per finished PvP duel (bots skipped).
- **Outperform target:** pending Lane F. Provisional: most Discord "duel" bots (e.g. Tatsu/Idle-RPG minis) are RNG-only, no defend mechanic, no gear coupling, no rematch/consent flow. Ours already beats them on gear-integrated stats + consent-gated PvP + fair anti-farm leaderboard; the new-bot win is the declarative session guaranteeing settle-once + resumability the ad-hoc bots lack.
- **Cross-lane dependency notes:** gear-wear + EffectiveStats bind to Lane B (economy/mining); leaderboard read model + `!leaderboard` arg bind to the shared Lane C games-core. Recorded — this audit stays anchored to the deathmatch subsystem; those seams are consumed, not owned here.

---

### rps_tournament
_cogs: cogs/rps_tournament_cog.py (+ cogs/rps_tournament/{schemas,rules,_persistence,_bot_matches,_stage,_quickplay,_helpers}.py); views/rps/{__init__,_helpers,move_picker,pvp_challenge,pvp_play,registration,solo_play}.py; views/games/rps_panel.py; utils/db/games/rps.py; utils/settings_keys/games.py:16; utils/subsystem_registry.py:862; cogs/help/route.py:72; utils/db/migrations.py:291_
_Scaffold drift: the ground-truth command file:lines point at the `async def` line; the `@commands.command` decorator sits 1–2 lines above (rpsregister@198/def199 · rpsstart@367/def369 · rpsbot@410/def411 · rpsmatchup@422/def424 · rpshelp@723/def724 · rpssettings@739/def741 · rps@771/def772). Cited decorator lines below. `rps_players` baseline CREATE at migrations.py:291 shows a single-col PK; the effective PK is `(user_id, guild_id)` after migration 005 (per rps.py header). The `rps_get_leaderboard` provider is NOT unexposed — it is consumed cross-lane by services/rank_providers.py:502,523._

#### Surface-unit ledger
| Unit | Kind | File:line | Tier (as-written) | Tier (with amendments) | Rationale / gap |
|---|---|---|---|---|---|
| !rpsregister (alias rpsreg) | command | rps_tournament_cog.py:198 | tier-3 | **tier-3** | Opens the bracket registration lobby: sets mutex, resolves entry fee, posts embed, spawns countdown → **bracket-lobby orchestration**. G-9 declares the lobby DATA (countdown/entry-fee/mutex) but the open **handler stays tier-3** (mirrors blackjack `!bjtournament`). |
| !rpsstart (alias rpsbegin) | command | :367 | tier-3 | **tier-3** | admin-gated bracket START → `start_round` (pairing). **Bracket-orchestration handler stays tier-3** (mirrors blackjack `!bjstart`). |
| !rpsbot | command | :410 | tier-3 | tier-2 | Delegates to `run_rps_bot_command`: resolve members/roles, provision per-player channels, seed bot-match session. → ChallengeSessionSpec (bot-match session start); move loop stays tier-3. |
| !rpsmatchup | command | :422 | tier-3 | **tier-3** | admin-gated manual pairing: create channel, seed two match records. **Real bracket orchestration → stays tier-3.** |
| !rpshelp | command | :723 | tier-1 | tier-1 | Static help embed = help projection. |
| !rpssettings | command | :739 | tier-3 | tier-1 | Bespoke mutator over an **in-memory** `self.settings` dict (default_mode/default_best_of) with hand-rolled validation — DRIFT: these are NOT persisted SettingSpecs. → model as enum/int SettingSpec; kernel settings-set workflow. |
| !rps (quickrps) | command | :771 | tier-3 | tier-2 | Bet-parse + balance precheck + spawn solo or PvP-challenge view = game session START. → ChallengeSessionSpec (session start / escrow CostVector arg). |
| on_guild_remove | listener (gateway) | :183 (body _persistence.py:213) | tier-3 | tier-2 | Wipes both rps subsystems + refunds tournament escrow + PvP escrow for departed guild = refund domain logic. → G-1 (wiring) + ChallengeSessionSpec refund_policy / kernel guild-remove hook. |
| on_reaction_add | listener (gateway) | :534 | tier-3 | tier-2 | Reaction-based tournament join → `try_register_player` (entry-fee debit). Blackjack-reaction-join analog. → G-1 (wiring) + G-9 (registration reaction) + escrow CostVector. |
| RpsTournamentStage | listener (message_pipeline) | _stage.py:32 (reg :163) | tier-3 | tier-2 | Stage wrapper is thin extract-and-route (`process` → `_process_tournament_message`); register/unregister is boilerplate wiring. → G-7 MessagePipelineStageSpec; handler stays tier-3. |
| registration_countdown | task (scheduled loop) | :266 | tier-3 | tier-2 | `tasks.spawn` asyncio loop: 5 s tick, reminder-at-half, cancellation, then `end_registration`. → G-9 (countdown_s + reminder_at declared). |
| send_reminder | announce | :282 | tier-2 | tier-1 | Posts reminder (optionally role-mention) to the reg channel. → G-3 AnnouncementRouteSpec / G-9 reminder template. |
| end_registration | orchestration | :293 | tier-3 | **tier-3** | Fetch reactors, register each, gate on <2 → bracket lobby-close orchestration → **stays tier-3** (the countdown timer + mutex it consumes are G-9 data). |
| try_register_player (escrow-entry seam) | mutation/escrow | :330 | tier-3 | tier-2 | Dedup → `game_wager_workflow.enter_tournament` (fee debit, InsufficientFundsError) → roster + `add_player_to_db`. Audited escrow-entry seam. → ChallengeSessionSpec escrow + G-9. |
| start_round | orchestration | :476 | tier-3 | **tier-3** | Pop-pair pairing + per-match channel provisioning + bye/odd-player advance + seed match records. **Single-elimination BRACKET topology — 1 instance in the lane → deliberate tier-3 escape hatch** (adversary ruling; the per-match channel = ResourceRequirement, the mutex = G-9, but the pairing/bye/round-graph stays code). |
| _process_tournament_message | game handler | :556 | tier-3 | tier-3 | Move-capture dispatch (bot vs PvP), `normalize_move`, one-move-per-player guard, calls `resolve_match`. Engine-adjacent move logic. **Deliberate escape hatch.** |
| resolve_match | game engine | :596 | tier-3 | tier-3 | `determine_winner` + best-of tally + tie-replay + advance + stat writes. Contains game rules. **Deliberate** (advance choreography is G-9 but the win-determination is rules). |
| check_tournament_progress | settlement/announce | :664 | tier-3 | **tier-3** | Round-over detection + `payout_tournament` pot settle (idempotent, G-9) + winner announce (G-3) + round-graph teardown. The pot-settle + announce **legs** are G-9/G-3 data, but the **round-graph advance/teardown stays tier-3** (bracket topology). |
| run_rps_bot_command | orchestration | _bot_matches.py:55 | tier-3 | tier-2 | Resolve members/roles, provision channels, seed bot-match session state. → ChallengeSessionSpec (bot session start). |
| handle_bot_match_move | game engine | _bot_matches.py:136 | tier-3 | tier-3 | Move parse + random bot pick + `determine_winner` + settle + channel cleanup. Bot-match engine. **Deliberate escape hatch.** |
| determine_winner | game engine | rules.py:76 | tier-3 | tier-3 | Pure-function win logic. **Deliberate by design (design-spec §10.1 risk 5).** |
| normalize_move + GAME_MODES/WIN_CONDITIONS/MOVE_ALIASES | game rules data | rules.py:23–58 | tier-3 | tier-3 | Rules tables (4 modes) + alias resolution. **Deliberate** — grammar must not become the rules language. |
| _RpsView (solo game) | view (game move+settle) | views/rps/solo_play.py:37 | tier-3 | tier-3 | 3 move buttons → `_play`: random bot, `_RPS_WINS` matrix, `economy_service` credit/debit. Game-move handler + rules. **Deliberate**; session/escrow is ChallengeSessionSpec. |
| _RpsSoloResultView | view (terminal nav) | solo_play.py:141 | tier-1 | tier-1 | Disabled shells + Play-again/Back = re-render/nav; rematch = ChallengeSessionSpec. |
| _RpsMovePickerView | view (move capture) | views/rps/move_picker.py:12 | tier-2 | tier-2 | Ephemeral picker records move back to parent — thin turn-input, no rules. → ChallengeSessionSpec custom_id move scheme. |
| _RpsPvpChallengeView | view (accept phase + escrow) | views/rps/pvp_challenge.py:28 | tier-3 | tier-2 | Accept → `open_pvp_wager` escrow-at-accept + persist pending + spawn play view. The accept phase ChallengeSessionSpec models. → ChallengeSessionSpec (accept_timeout + escrow + persistence). |
| _RpsPvpPlayView (pick→resolve) | view (game move+settle) | views/rps/pvp_play.py:72 | tier-3 | tier-3 | SettleOnceMixin, `_wins` matrix, forfeit-on-timeout, `settle_pvp`/`refund_pvp`, persist/clear. Choreography (settle_once/escrow/persistence) is ChallengeSessionSpec tier-2 but win-determination is rules. **Deliberate.** |
| _RpsPvpResultView | view (terminal nav) | pvp_play.py:30 | tier-1 | tier-1 | Back-to-RPS affordance = nav. |
| _RpsRegistrationView | view (join route) | views/rps/registration.py:15 | tier-1 | tier-1 | Join button → `try_register_player` (logic counted at :330). Thin panel-action route. |
| RPSPanelView hub + 5 buttons (quick/bet/challenge/tournament/rules) | panel/actions ×6 | rps_panel.py:567,580,598,616,634,668 | tier-1 | tier-1 | Hub + open-panel/re-render workflows; Tournament button reads live cog state (status provider). |
| _RpsBetPresetView + PresetButton + CustomButton | panel/actions ×3 | rps_panel.py:212,229,248 | tier-1 | tier-1 | Nav + session-spawn (preset bet → solo view). |
| _RpsCustomBetModal | modal | rps_panel.py:261 | tier-2 | tier-1 | Bet int-parse/validate → spawn solo session. → CostVector amount_source="arg". |
| _RpsChallengeSelectView + OpponentSelect | selector ×2 | rps_panel.py:293,308 | tier-1 | tier-1 | User-select → validate (self/bot) → spawn PvP challenge session. |
| _RpsTournamentSubView + Start/Join/Matchup buttons + MatchupSelect | panel/selector ×5 | rps_panel.py:353,379,413,447,483 | tier-1 | tier-1 | Conditional-render nav + thin routes to bracket workflows (register/join/matchup). |
| default_entry_fee | setting (bounded int) | schemas.py:33 | tier-2 | tier-1 | Real SettingSpec but carries a `_validate_non_negative_int` HandlerRef. → G-5 (declarative min=0). |
| default_mode | setting (enum, in-memory) | rps_tournament_cog.py:113,748 | tier-3 | tier-1 | 4-value enum, mutated only via `!rpssettings` runtime dict (not persisted). → enum SettingSpec. |
| default_best_of | setting (odd-positive int, in-memory) | rps_tournament_cog.py:113,754 | tier-3 | tier-2 | Runtime dict; "odd positive" validation. G-5 gives min but parity needs a validator HandlerRef → tier-2. |
| rps_players table + CRUD (ensure/update/leaderboard) | store + stat_writes | migrations.py:291; rps.py:27,35,64 | tier-1 | tier-1 | StoreSpec + ChallengeSessionSpec stat_writes (win/loss/tie). |
| game_state persistence + recovery (rps_tournament / rps_pvp_pending / rps_pvp_escrow) | store + recovery | _persistence.py:44,82,155,213; _helpers.py:155,168; cog:148–162 | tier-3 | tier-2 | Checkpoint save + cog_load refund/clear sweeps + guild-remove refund. → ChallengeSessionSpec persistence(authoritative) + refund_policy + kernel escrow recovery. |
| rps_get_leaderboard | leaderboard provider | rps.py:64 (consumed rank_providers.py:502) | tier-2 | tier-2 | ORDER BY wins → LeaderboardSpec. Exposed cross-lane via rank_providers, no direct rps command. |
| channel provisioning group (create/schedule-delete/delete-all/cleanup-orphaned) | resource/provisioning | _helpers.py:88,106,124,139,168 | tier-2 | tier-2 | Private per-match channels + delayed delete + startup category sweep. → ResourceRequirement + G-9 per-match provisioning/cleanup. |
| help route aliases (rps / rock paper scissors) + build_help_menu_view hook | help | route.py:72–73; cog:120 | tier-1 | tier-1 | Help projection + hub-panel direct-nav hook. |
| build_rps_rules_embed (rules_text) | help | rps_panel.py:157 | tier-1 | tier-1 | HelpFacet rules projection. |
| capabilities game.join + tournament.manage | capability ×2 | subsystem_registry.py:882–883 | tier-1 | tier-1 | Declarative capability strings. |
| subsystem_registry entry (manifest header) | manifest | subsystem_registry.py:862 | tier-1 | tier-1 | Display/category/tags/hub metadata. |
| tournament_state_service active-flag (set/get/clear_active) | cross-lane mutex | cog:216,231,328,693; _helpers.py:155 | tier-2 | tier-2 | One-tournament-per-guild mutex. → G-9 could own the declaration; cross-lane state service. |

#### Manifest sketch (§2 grammar)
```python
SubsystemManifest(
  key="rps_tournament", display_name="Rock Paper Scissors", emoji="✂️",
  category="games", visibility_tier="user",
  capabilities=("rps_tournament.game.join", "rps_tournament.tournament.manage"),
  commands=(
    CommandSpec("rps",         route=PanelRef("rps_hub")),          # tier-1 open-panel
    CommandSpec("rpshelp",     route=HelpRef("rps")),               # tier-1 projection
    CommandSpec("rpsbot",      route=SessionStartRef("rps_bot")),   # tier-2 ChallengeSessionSpec start (move loop tier-3)
    # bracket commands become thin routes into the bracket spec:
    CommandSpec("rpsregister", route=BracketRef("rps.register_open"), aliases=("rpsreg",)),
    CommandSpec("rpsstart",    route=BracketRef("rps.start"),        aliases=("rpsbegin",), gate="tournament.manage"),
    CommandSpec("rpsmatchup",  route=BracketRef("rps.manual_pair"),  gate="tournament.manage"),
    # rpssettings collapses into the kernel settings-set workflow once default_mode/best_of are SettingSpecs
  ),
  panels=(PanelSpec("rps_hub", actions=(  # all tier-1 re-render/spawn
    Action("quick_play", spawn="rps_solo"), Action("bet_match", open="rps_bet"),
    Action("challenge", open="rps_challenge"), Action("tournament", open="rps_tourn", status_provider="rps.tourn_status"),
    Action("rules", render="rules_text"))),),
  settings=(
    SettingSpec("default_entry_fee", int, default=0, min=0),                 # tier-1 (G-5)
    SettingSpec("default_mode", enum=("classic","lizard_spock","chess","elemental"), default="classic"),  # tier-1
    SettingSpec("default_best_of", int, default=3, validator=OddPositive),   # tier-2 (parity validator)
  ),
  game=GameFacet(
    sessions=(
      ChallengeSessionSpec(game_key="rps_pvp", accept_timeout_s=60, turn_timeout_s=55, stale_after_s=86400,
        settle_once=True, persistence="checkpointed", escrow=CostVector("coins","arg"),
        stat_writes=("win","loss","tie"), refund_policy=HandlerRef("rps.pvp_refund")),   # tier-2 choreography
      ChallengeSessionSpec(game_key="rps_solo", accept_timeout_s=0, turn_timeout_s=60, stale_after_s=0,
        settle_once=True, persistence="ephemeral", escrow=CostVector("coins","arg")),    # tier-2
      ChallengeSessionSpec(game_key="rps_bot",  turn_timeout_s=300, persistence="ephemeral", settle_once=True),
    ),
    leaderboards=(LeaderboardSpec("rps_wins","wins","count",scope="guild"),),            # tier-2 (via rank_providers)
  ),
  # PROPOSED G-9 — the multi-round bracket the game facet cannot express:
  tournament=TournamentLobbySpec(                                                       # NEW
    game_key="rps", mutex="tournament_state_service",
    registration=RegistrationSpec(reaction="✅", button=True, countdown_s=600, reminder_at_s=300,
                                  entry_fee=CostVector("coins","setting:default_entry_fee")),
    pairing="single_elim", bye_policy="advance", best_of_setting="default_best_of",
    match_channel=ResourceRequirement("private_channel", per="match", category="RPS Tournaments"),
    match_session=SessionRef("rps_tourn_match"), payout=PayoutSpec(pot_source="escrow_rows", free_reward=100),
    persistence="authoritative", refund_policy=HandlerRef("rps.tourn_refund")),
  gateway_listeners=(                                                                     # G-1
    GatewayListenerSpec("on_guild_remove", handler=HandlerRef("rps.on_guild_remove"), gate=None),
    GatewayListenerSpec("on_reaction_add", handler=HandlerRef("rps.reg_reaction"), gate="registration_active"),
  ),
  pipeline_stages=(                                                                       # PROPOSED G-7
    MessagePipelineStageSpec(name="rps_tournament", order=40, handler=HandlerRef("rps.capture_move")),  # thin route; handler tier-3
  ),
  stores=(StoreSpec("rps_players", pk=("user_id","guild_id")),),                          # tier-1
  # DELIBERATE tier-3 escape hatches (registered handler refs, NOT expressed in grammar):
  #   rps.engine.determine_winner + rules tables   — game rules
  #   rps.solo_move / rps.pvp_resolve / rps.bot_move — game-move handlers (win determination)
  #   rps.capture_move (resolve_match dispatch)     — engine-adjacent move parse
  help=HelpFacet(summary="Rock·Paper·Scissors: quick play, PvP, bot, tournaments", rules_text="…"),
)
```

#### Tier-3 dispositions
- **determine_winner + rules tables (rules.py:23–87)** — deliberate escape hatch: pure-function game ENGINE. Design-spec §10.1 risk 5 forbids the grammar expressing rules.
- **_RpsView._play (solo_play.py:54)** — deliberate: solo move handler (bot pick + `_RPS_WINS` + settle). Session/escrow is ChallengeSessionSpec; the move+rules stay code.
- **_RpsPvpPlayView._resolve (pvp_play.py:150)** — deliberate: PvP win-determination (`_wins`) + forfeit rules. Its settle_once / escrow-settle / persistence choreography IS declarable (ChallengeSessionSpec), but the rules are not.
- **handle_bot_match_move (_bot_matches.py:136)** — deliberate: bot-match engine (random pick + win + settle).
- **resolve_match (cog:596) + _process_tournament_message (cog:556)** — deliberate for the win-determination/move-parse core; the round-advance + payout choreography around them → G-9.
- **Tournament lobby vs. bracket — the SPLIT (adversary ruling).** The lobby/pot-escrow choreography — `registration_countdown` (countdown_s/reminder_at), `try_register_player` (entry-fee CostVector), `send_reminder` (G-3), the idempotent `payout_tournament` pot settle, and the one-per-guild `tournament_state_service` mutex — **recurs** across blackjack + rps tournaments → **ratify G-9 TournamentLobbySpec** (these units are tier-1/2 with amendments). BUT the **single-elimination bracket topology** (rpsregister/rpsstart/rpsmatchup/start_round/end_registration/check_tournament_progress: pop-pair pairing, byes, per-match channels, round-graph advance/teardown) exists in **exactly one** subsystem — blackjack's tournament is score-accumulation, not a bracket — so it **fails the ≥2 bar and stays a deliberate rps-owned tier-3 escape hatch**, exactly as blackjack keeps its lobby handlers tier-3. Making the bracket a ratified kernel primitive on a single instance would risk the grammar becoming a worse programming language for one game.
- **RpsTournamentStage register/unregister wiring (_stage.py:32, cog:163)** — NOT deliberate: thin extract-and-route boilerplate over the internal message_pipeline seam, shared by cleanup/counting/chain/xp/rps → **propose G-7 MessagePipelineStageSpec** (handler stays tier-3).
- **on_guild_remove / on_reaction_add (cog:183,534)** — reuse G-1 for wiring; the refund/join bodies fold into ChallengeSessionSpec.refund_policy + G-9 registration.
- **!rpssettings + in-memory default_mode/default_best_of (cog:113,739)** — NOT deliberate: a hand-rolled runtime-dict settings mutator that should be SettingSpecs (drift — only default_entry_fee is a real persisted setting today).

#### Fit numbers
units total = **59** (×N-weighted: RPSPanelView+5 buttons=6, bet views=3, challenge views=2, tournament sub-views=5, capabilities=2; all others weight 1).
- tier-1/2 (as-written) = **33 (56%)**. Weighted tier-1/2 rows: rpshelp(1)+send_reminder(1)+SoloResult(1)+MovePicker(1)+PvpResult(1)+RegistrationView(1)+RPSPanel×6+BetPreset×3+CustomBetModal(1)+ChallengeSelect×2+TournamentSub×5+default_entry_fee(1)+rps_players(1)+leaderboard(1)+channel-provision(1)+help-route(1)+rules-embed(1)+capabilities×2+registry(1)+tourn-mutex(1) = 33. → 33/59 = 55.9% ≈ 56%.
- tier-1/2 (with amendments) = **46 (78%)**.
> **Synthesis correction (adversary ruling — the bracket SPLIT).** The originating agent proposed one `TournamentBracketSpec` lifting the *entire* bracket to tier-2, giving 88%. The adversarial re-check **split** it: the tournament **lobby/pot-escrow choreography** (registration countdown, entry-fee-at-register, idempotent `payout_tournament` pot settle, one-per-guild mutex) genuinely **recurs** across blackjack + rps → ratified as **G-9 TournamentLobbySpec**; but the **single-elimination BRACKET topology** (pop-pair pairing, byes, per-match channels, round-graph) exists in **exactly ONE** subsystem (blackjack's tournament is score-accumulation, *not* a bracket) → **fails the ≥2 recurrence bar → stays a deliberate rps-owned tier-3 escape hatch.** So the **six bracket-orchestration handlers** (rpsregister, rpsstart, rpsmatchup, start_round, end_registration, check_tournament_progress) stay **tier-3** with amendments — exactly as blackjack keeps `!bjtournament`/`!bjstart` tier-3 to hold the anchor.
Irreducible tier-3 with amendments = **13** (weight 1 each): the 7 game-rules cores (`_process_tournament_message`, `resolve_match`, `handle_bot_match_move`, `determine_winner`, `normalize_move`+tables, `_RpsView`, `_RpsPvpPlayView`) **+ the 6 bracket-orchestration handlers** above. → 59 − 13 = **46** → 46/59 = 77.9% ≈ **78%**.
- Note: still well above the blackjack 44% anchor and consistent with it — RPS carries a large declarative hub/panel/selector surface, but its genuine single-elimination bracket is *more* irreducible orchestration than blackjack's score-accumulation tournament, so it honestly lands a bit lower than the agent's first pass.

#### Structural-gap flags
- **Stateful multi-round bracket state machine** (`self.players/scores/matches/current_round/match_channels`, cog:92–96) — held in per-cog memory; a restart loses the live bracket. Recovery only refunds entries (`recover_rps_tournament`), it CANNOT resume a mid-bracket tournament. **G-9 declares the bracket structure + persistence("authoritative") but resumability of an in-flight bracket is a genuine new capability the grammar must specify (checkpoint the round graph, not just entry rows).**
- **Scheduled countdown loop** (`registration_countdown`, cog:266, `tasks.spawn`) with reminder-at-half + cancellation → G-9 registration(countdown_s, reminder_at). Expressible.
- **Entry-fee escrow + pot payout with anti-double-settle** — `enter_tournament`/`payout_tournament` (idempotent), `open_pvp_wager`/`settle_pvp` + `SettleOnceMixin.claim_settlement` (pvp_play.py:157). ChallengeSessionSpec settle_once + escrow express it; **but the tournament POT (sum of escrow rows → single winner) is a bracket-level settle G-9 must own, distinct from a 2-party PvP settle.**
- **Component/session recovery on restart** — three game_state subsystems (rps_tournament / rps_pvp_pending / rps_pvp_escrow); live views are explicitly NOT restorable (clear+refund only, _persistence.py docstrings). ChallengeSessionSpec persistence + kernel recovery cover the clear/refund; view resumption is deliberately out of scope.
- **Text-message move input** — moves are typed in match channels via the message_pipeline stage (`_process_tournament_message`), NOT component clicks. ChallengeSessionSpec's custom_id_scheme is component-based → **G-7 + a text-move binding is needed; the move-parse (`normalize_move`) is rules (tier-3).**
- **Per-match private channel provisioning + delayed deletion** (`create_match_channel`, `asyncio.sleep(300)` delete) → ResourceRequirement + G-9 per-match provisioning.
- **Active-tournament mutex** (`tournament_state_service`, one tournament per guild, shared with blackjack) — cross-subsystem; G-9 should reference it.
- **Leaderboard/records** (`rps_players` → `rank_providers`) — LeaderboardSpec expresses it; cross-lane consumer.

#### MAP → RECONSIDER → SIMULATE → OPTIMIZE
- **RECONSIDER verdict: improve.** The engine is sound and correctly tier-3; the gap is that a genuine single-elimination bracket (registration lobby, dynamic pairing, byes, per-round channels, countdown, pot payout, mutex) is hand-rolled as ~350 lines of cog state-machine that ChallengeSessionSpec cannot reach. Extract it into a declared **G-9 TournamentLobbySpec** + ChallengeSessionSpec match sessions; keep the rules engine as the deliberate escape hatch.
- **Optimal new-bot form:** `TournamentLobbySpec` = { mutex, RegistrationSpec(reaction+button, countdown_s, reminder_at_s, entry_fee:CostVector), pairing="single_elim", bye_policy, best_of_setting, per-match ResourceRequirement, match_session:SessionRef, PayoutSpec(pot_source, free_reward), persistence="authoritative", refund_policy } — with the 4 game modes/rules staying in a registered engine HandlerRef. This collapses items 1,2,4,11–15,18,42,47 into data and makes the bracket resumable (round graph checkpointed).
- **Dependency-layer guess:** L0 runtime (message_pipeline, game_state_service, tasks) → economy/escrow (game_wager_workflow, Lane B) → games-core (ChallengeSessionSpec, tournament_state_service mutex, SettleOnceMixin, LeaderboardSpec/rank_providers) → **G-9 TournamentLobbySpec (games-core)** → this subsystem (rps rules engine + hub panel).
- **Production-grade done-definition:** parity golden = (a) 8-player bracket with an odd bye at round 2 resolves to exactly one winner and pays the summed escrow pot once (settle-once holds under the double-`record_choice`/timeout race); (b) bot bounce mid-round refunds every un-settled entry exactly once (no double-refund vs GC sweep) AND — target — resumes the in-flight round; (c) entry fee debits exactly once across reaction+button+panel join paths; (d) `default_mode`/`default_best_of` persist across restart (fixes current in-memory drift); (e) all 4 game modes' win tables match `WIN_CONDITIONS` byte-for-byte.
- **Outperform target:** pending Lane F. Provisional: beats generic RPS/tournament bots (e.g. tournament-bracket bots that require a web dashboard) by running the entire lifecycle in-channel with escrow-backed entry fees, 4 rule variants, auto-refund on crash, and a resumable bracket — no external site, money-safe by construction.
- **Cross-lane dependency notes:** economy escrow (`game_wager_workflow.{enter_tournament,payout_tournament,open_pvp_wager,settle_pvp,refund_pvp,recover_escrow}`, Lane B); `tournament_state_service` active-flag mutex (games-core, shared with blackjack); `rank_providers` leaderboard consumer (ranks/Lane B); `message_pipeline` stage seam (shared with counting/chain, Lane C — G-7 ownership likely lands there); `game_state_service` + `SettleOnceMixin` (games-core / L0). Audit stays anchored to rps_tournament; deps recorded, not chased.

---

### counting
_cogs: disbot/cogs/counting_cog.py · disbot/cogs/counting/{_stage,handler,parsing,game_logic,_channel_manager,leaderboard}.py · disbot/views/counting/hub_panel.py · disbot/utils/db/games/counting.py · disbot/utils/subsystem_registry.py:886_

_Scaffold drift corrected: (1) command rows cited def-lines; the `@commands.command` **declaration** lines are countingmenu:179, start_match:196, end_match:383, reset_count:432, toggle_turns:487, count_info:517, counttop:572, count_rules:604, set_skip_numbers:635, toggle_reset_on_wrong_count:686 (def lines are +1/+2). (2) The listener wiring the scaffold marked "⚠ unverified / elsewhere" is now VERIFIED: `CountingStage` (disbot/cogs/counting/_stage.py:37) is registered in `cog_load` at counting_cog.py:68 via `message_pipeline.register(CountingStage(self))` and unregistered in `cog_unload` at :780 — it is a **message-pipeline stage (order=15), not a raw on_message gateway listener**. (3) counting_state table DDL confirmed at disbot/utils/db/migrations.py:325._

#### Surface-unit ledger
| Unit | Kind | File:line | Tier (as-written) | Tier (with amendments) | Rationale / gap |
|---|---|---|---|---|---|
| !countingmenu (cm) | command | counting_cog.py:179 | tier-1 | tier-1 | PanelRef open-panel workflow (opens `_CountingHubView`) |
| !start_match (sm) | command | counting_cog.py:196 | tier-3 | tier-3 | Deliberate escape hatch — parses mode + custom-comma-sequence + multiples-factor + skip-step, creates a Discord channel, inits mode config (blackjack bet-parse+deal analog) |
| !end_match (em) | command | counting_cog.py:383 | tier-1 | tier-1 | Declarative route → deprovision (delete channel + drop match) workflow |
| !reset_count (rc) | command | counting_cog.py:432 | tier-1 | tier-1 | Route → reset-match workflow |
| !toggle_turns (tt) | command | counting_cog.py:487 | tier-1 | tier-1 | Route → binding-set (per-channel bool) workflow |
| !count_info (ci) | command | counting_cog.py:517 | tier-2 | tier-2 | Read-model status render over per-channel state (provider-shaped) |
| !counttop (ct, counting_top) | command | counting_cog.py:572 | tier-2 | tier-2 | LeaderboardSpec read over per-channel tally |
| !count_rules (cr) | command | counting_cog.py:604 | tier-1 | tier-1 | Static rules embed — help projection |
| !set_skip_numbers (ssn) | command | counting_cog.py:635 | tier-2 | tier-1 | Int-set with `mode=="skip"` guard + bound (step≥1); G-5 bounds + G-8 config → tier-1 |
| !toggle_reset_on_wrong_count (trwc) | command | counting_cog.py:686 | tier-1 | tier-1 | Route → binding-set workflow |
| _CountingHubView + build_embed | panel/view | views/counting/hub_panel.py:168,225 | tier-2 | tier-2 | HubView shell + read-model render over `count_data` |
| _ChannelPick (ChannelSelect) | panel selector | views/counting/hub_panel.py:35 | tier-1 | tier-1 | Selector → set target + re-render |
| _ModePick (enable) | panel selector | views/counting/hub_panel.py:53 | tier-1 | tier-1 | Panel action → provisioning workflow (enable_channel) |
| _ToggleTurnsButton | panel action | views/counting/hub_panel.py:78 | tier-1 | tier-1 | Panel binding-set + re-render |
| _ToggleResetButton | panel action | views/counting/hub_panel.py:96 | tier-1 | tier-1 | Panel binding-set + re-render |
| _ResetCountButton | panel action | views/counting/hub_panel.py:114 | tier-1 | tier-1 | Panel reset workflow + re-render |
| _DisableButton | panel action | views/counting/hub_panel.py:131 | tier-1 | tier-1 | Panel deprovision workflow |
| _RefreshButton | panel action | views/counting/hub_panel.py:155 | tier-1 | tier-1 | Re-render |
| enable_channel | workflow | cogs/counting/_channel_manager.py:67 | tier-3 | tier-1 | Thin per-channel match provision; no spec family as-written (G-2-style promotion) → G-8 |
| disable_channel | workflow | cogs/counting/_channel_manager.py:84 | tier-3 | tier-1 | Thin deprovision; → G-8 |
| toggle_channel_flag | workflow | cogs/counting/_channel_manager.py:99 | tier-3 | tier-1 | Thin per-channel bool set; → G-8 |
| reset_channel_count | workflow | cogs/counting/_channel_manager.py:110 | tier-3 | tier-1 | Thin state reset; → G-8 |
| default_channel_config | config schema | cogs/counting/_channel_manager.py:40 | tier-3 | tier-1 | Match-config template; becomes G-8 ChannelMatchSpec.config_fields |
| CountingStage + register/unregister | listener (pipeline stage) | cogs/counting/_stage.py:37; counting_cog.py:68,780 | tier-3 | tier-1 | **KEY**: ordered message-pipeline stage, NOT raw on_message → G-7 makes order/tier/short-circuit/wiring DATA |
| _process_counting_message (V/M/A coordinator) | listener body | counting_cog.py:727 | tier-3 | tier-2 | Lock→compute→save-spawn→apply-outside; G-7 stage runtime owns the V/M/A wrapper; routes to tier-3 engine |
| handler.compute_decision | engine | cogs/counting/handler.py:76 | tier-3 | tier-3 | Deliberate — counting rules (count/turn/multiples/prime validation + state+leaderboard mutation) |
| handler._decide_random | engine | cogs/counting/handler.py:194 | tier-3 | tier-3 | Deliberate — random guess-the-number mini-game rules |
| handler.apply_decision | apply/render | cogs/counting/handler.py:251 | tier-2 | tier-2 | Thin Discord apply (delete via moderation_service, reply, reaction) |
| handler._reset_channel_data | state helper | cogs/counting/handler.py:178 | tier-3 | tier-1 | Mechanical state wipe; → G-8 reset |
| parse_message + AST math evaluator | engine | cogs/counting/parsing.py:50 (+eval_expr:220, safe_eval:250, _eval_ast:302, _expand_factorials:261) | tier-3 | tier-3 | Deliberate — input engine (word/roman/emoji/expression, hardened AST, DoS bounds); grammar MUST NOT express this |
| game_logic.calculate_expected_count | engine | cogs/counting/game_logic.py:12 | tier-3 | tier-3 | Deliberate — mode arithmetic (fib/squares/cubes/factorials/custom/skip/reverse/random) |
| game_logic random-round engine | engine | cogs/counting/game_logic.py:98,108,85 | tier-3 | tier-3 | Deliberate — random mini-game window rules |
| game_logic.is_prime | engine | cogs/counting/game_logic.py:58 | tier-3 | tier-3 | Deliberate — rule helper |
| game_logic.top_counters | leaderboard metric | cogs/counting/game_logic.py:120 | tier-2 | tier-2 | LeaderboardSpec ranking (pure) |
| leaderboard render (build_leaderboard_embed / top_field_value) | read-model render | cogs/counting/leaderboard.py:44,62 | tier-2 | tier-2 | FieldsBlock/provider render for !counttop + !count_info |
| counting_state StoreSpec (table + get/set) | store | utils/db/games/counting.py:8,16; migrations.py:325 | tier-1 | tier-1 | Per-guild JSONB blob — StoreSpec |
| _save_guild (+ tasks.spawn counting:save) | persistence workflow | counting_cog.py:91 | tier-1 | tier-1 | StoreSpec-backed save via managed task |
| _load_when_ready | recovery workflow | counting_cog.py:86 | tier-1 | tier-1 | Kernel state-load on ready |
| cog_load (spawn/hook/register-stage) | lifecycle | counting_cog.py:60 | tier-2 | tier-1 | Wiring; G-7 for the stage register |
| cog_unload | lifecycle | counting_cog.py:775 | tier-1 | tier-1 | Cancel tasks + unregister stage |
| _drop_scope_locks_for_guild | resource-teardown hook | counting_cog.py:70 | tier-2 | tier-2 | Thin guild→scope_id translation (ResourceRequirement) |
| scope_locks per-channel lock | resource (concurrency) | counting_cog.py:46,754 | tier-1 | tier-1 | ResourceRequirement — per-channel `lock_for` |
| is_staff_or_owner / staff_or_owner() | gate | counting_cog.py:144,166 | tier-1 | tier-1 | BindingSpec — moderator-tier gate on admin commands |
| subsystem_registry "counting" entry | registry/setting | subsystem_registry.py:886 | tier-1 | tier-1 | Declaration/projection |
| capabilities counting.game.play / .configure | capability | subsystem_registry.py:909 | tier-1 | tier-1 | Capability BindingSpecs |
| build_help_menu_view hook | help | counting_cog.py:187 | tier-1 | tier-1 | Help direct-nav → hub panel projection |
| entry_points (count_info/counttop/countingmenu) | help | subsystem_registry.py:898 | tier-1 | tier-1 | Help projection |
| deletion audit (via moderation_service.auto_delete) | event (delegated) | cogs/counting/handler.py:267 | tier-2 | tier-2 | No owned event; rule-deletes route to shared moderation seam (cross-lane) |

#### Manifest sketch (§2 grammar)
```python
SubsystemManifest(
    key="counting",
    registry=RegistryEntry(display="Counting", emoji="🔢", category="games",
                           parent_hub="games", entry_points=["count_info","counttop","countingmenu"],
                           capabilities=["counting.game.play","counting.game.configure"]),
    commands=[
        Command("countingmenu", aliases=["cm"], route=PanelRef("counting_hub"), gate=Gate.MODERATOR),
        Command("count_rules", aliases=["cr"], route=HelpRef("counting_rules")),        # static projection
        Command("count_info", aliases=["ci"], route=ReadModelRef("counting_status")),   # tier-2 provider read
        Command("counttop", aliases=["ct","counting_top"], route=LeaderboardRef("counting_channel")),
        # config/lifecycle routes → G-8 ChannelMatchSpec workflows (declarative):
        Command("end_match", aliases=["em"], route=WorkflowRef("counting.match.end"), gate=Gate.MODERATOR),
        Command("reset_count", aliases=["rc"], route=WorkflowRef("counting.match.reset"), gate=Gate.MODERATOR),
        Command("toggle_turns", aliases=["tt"], route=BindingSet("counting.match.taking_turns"), gate=Gate.MODERATOR),
        Command("toggle_reset_on_wrong_count", aliases=["trwc"], route=BindingSet("counting.match.reset_on_wrong"), gate=Gate.MODERATOR),
        Command("set_skip_numbers", aliases=["ssn"], route=BindingSet("counting.match.skip_step", bounds=(1,None)), gate=Gate.MODERATOR),  # G-5
        # deliberate tier-3: mode-arg / custom-sequence parse + channel provision
        Command("start_match", aliases=["sm"], route=HandlerRef("counting.match.start"), gate=Gate.MODERATOR),  # tier-3 ENGINE
    ],
    panels=[Panel("counting_hub", view="HubView", actions=[  # every action tier-1: selector/binding-set/provision/re-render
        Selector("channel"), Selector("enable_mode", route=WorkflowRef("counting.match.enable")),
        Action("toggle_turns", BindingSet(...)), Action("toggle_reset", BindingSet(...)),
        Action("reset", WorkflowRef("counting.match.reset")), Action("disable", WorkflowRef("counting.match.disable")),
        Action("refresh", ReRender())])],
    channel_matches=[ChannelMatchSpec(          # G-8 (NEW) — carries config + lifecycle as DATA
        match_key="counting:channel:{channel_id}",
        config_fields={"mode": Enum(MODES), "taking_turns": Bool(False), "reset_on_wrong": Bool(False),
                       "skip_step": Int(1, min=1), "multiple": Int(), "custom_sequence": List(int)},
        lifecycle=Lifecycle(create="counting.match.start", reset="counting.match.reset", end="counting.match.end"),
        state_store=StoreRef("counting_state"), scope_lock=True)],
    gateway_stages=[MessagePipelineStageSpec(   # G-7 (NEW) — replaces the bespoke CountingStage wiring
        stage="counting", order=15, tier="automod", short_circuit_on_delete=True,
        handler=HandlerRef("counting.validate"))],   # handler → the DELIBERATE tier-3 engine below
    leaderboards=[LeaderboardSpec(board_id="counting_channel", stat_key="correct_counts",
                                  metric="count", scope="channel")],
    stores=[StoreSpec("counting_state", shape="jsonb_per_guild")],
    help=[HelpEntry("counting_rules"), HelpNav("build_help_menu_view")],
    # --- DELIBERATE tier-3 ENGINE (hand-written module behind counting.validate / counting.match.start) ---
    #   parsing.parse_message + AST evaluator  (input engine, DoS-bounded)
    #   game_logic.calculate_expected_count / is_prime / random-round rules  (mode arithmetic)
    #   handler.compute_decision / _decide_random  (validation + state transition)
    #   start_match custom-sequence / multiples / skip parse  (session-start domain parse)
    #   -> grammar MUST NOT try to express these (design-spec §10.1 risk 5)
)
```

#### Tier-3 dispositions
- **CountingStage + register/unregister** — grammar gap → **propose G-7 MessagePipelineStageSpec**. It is NOT a raw on_message (so G-1 doesn't fit); it is an ordered pipeline stage (order=15, short-circuit-on-delete). Recurs in counting/chain/rps_tournament. G-7 makes wiring tier-1; handler ref → the engine.
- **enable/disable/toggle/reset/default_channel_config + config commands + _reset_channel_data** — grammar gap → **propose G-8 ChannelMatchSpec**. Channel-bound persistent match; ChallengeSessionSpec doesn't fit (no accept/turn/escrow/settle). Thin config/lifecycle promotes to tier-1 as DATA (same shape as G-2 for lists). Recurs in chain.
- **set_skip_numbers bound** — reuse **G-5** (declarative min=1) → tier-1.
- **start_match mode-arg / custom-sequence / multiples parse** — **deliberate escape hatch**. Parsing free-text into a validated integer sequence / factor is domain input logic (blackjack bet-parse analog). Stays tier-3.
- **compute_decision / _decide_random** — **deliberate escape hatch** (the counting ENGINE / move-validator). Marking tier-3 is CORRECT.
- **parse_message + AST evaluator** — **deliberate escape hatch**. A hardened math/word/roman parser is exactly the "worse programming language" trap; must stay code.
- **calculate_expected_count / is_prime / random-round rules** — **deliberate escape hatch** (game rules).

#### Fit numbers
units total = **48**. tier-3 as-written = 15 (start_match; 5 channel-manager workflows; CountingStage; _process_counting_message; _reset_channel_data; compute_decision; _decide_random; parse_message; calculate_expected_count; random-round; is_prime). tier-1/2 (as-written) = 48 − 15 = **33 (69%)**. With G-5 + G-7 + G-8, tier-3 drops to the 7 deliberate engine units (start_match parse, compute_decision, _decide_random, parse_message, calculate_expected_count, random-round, is_prime). tier-1/2 (with amendments) = 48 − 7 = **41 (85%)**.

#### Structural-gap flags
- **Stateful per-channel match state machine** — present; G-8 expresses config+lifecycle, engine stays tier-3.
- **Concurrency (per-channel scope_lock, V/M/A mutate-under-lock/apply-outside)** — present; ResourceRequirement + G-7 stage runtime must enforce the mutate-under-lock contract.
- **Message-pipeline stage ordering + short-circuit-on-delete** — present; needs G-7 (order/tier/short_circuit as data).
- **Hot-path untrusted-input AST eval** — present (bounded); deliberate tier-3, grammar must not express.
- **Restart recovery** — present; StoreSpec JSONB + recovery workflow (tier-1); admin hub view intentionally ephemeral (no persistent-view recovery needed).
- **Escrow/settlement/settle_once** — ABSENT (no economy) — a real simplification vs blackjack; nothing to express.
- **Leaderboard/records** — present; LeaderboardSpec covers read, but the metric source is embedded in the match JSONB rather than a stat_key store (minor — G-8 state_store can expose it).

#### MAP → RECONSIDER → SIMULATE → OPTIMIZE
- **RECONSIDER verdict: keep (improve).** Well-decomposed (V/M/A split, scope_locks, moderation-audited deletes); the engine is legitimately tier-3. Improve by adopting G-7 + G-8 to generate the ~65% non-engine surface.
- **Optimal new-bot form:** SubsystemManifest with a ChannelMatchSpec (G-8) for the channel-bound match, a MessagePipelineStageSpec (G-7, order=15, short-circuit) whose handler_ref points at a hand-written counting engine module (parse_message + mode arithmetic + compute_decision), a LeaderboardSpec, an all-tier-1 admin HubView, StoreSpec(counting_state), and help/registry projections. Engine stays code behind a stable handler interface.
- **Dependency-layer guess:** L2 "this subsystem" on L0 runtime (message_pipeline, scope_locks, tasks); L1 governance (visibility gate) + moderation (audited delete) + persistence (StoreSpec). Shares G-7/G-8 games-core primitives with chain.
- **Production-grade done-definition:** a parity golden that replays a scripted message stream (valid/wrong/out-of-turn counts; word/roman/emoji/expression inputs; every mode incl. random) through the pipeline stage and asserts the exact accept/delete/reply/reaction decision + resulting state + leaderboard tally match the current bot; PLUS a concurrency test (two simultaneous same-channel messages resolve deterministically under scope_lock, no double-accept), a restart test (persist→reload→state identical), and a hot-path DoS test (crafted expression stays bounded).
- **Outperform target:** MEE6 / Carl-bot counting are single-mode (increment-by-1, no-double-count, wrong-resets). Ours already wins with 11 modes + expression/word/roman/emoji parsing + random guessing mini-game + per-channel leaderboard. New-bot edge: keep the rich engine, add declarative multi-channel/multi-mode no-code admin setup competitors lack. (Full bench pending Lane F.)
- **Cross-lane dependency notes:** deletes couple to moderation_service.auto_delete/EVT_MOD_ACTION/mod_logs (moderation lane); staff gate uses governance visibility_rules; message_pipeline/scope_locks/tasks are L0 runtime shared with chain/rps/xp/cleanup; rank_providers has a counting provider (Lane C leaderboard aggregates this). Audit stays anchored to counting.

---

### chain
_cogs: disbot/cogs/chain_cog.py · disbot/services/chain_service.py · disbot/utils/db/games/chain.py · disbot/utils/subsystem_registry.py:913 (chain entry)_
_Scaffold drift corrected: `!chain` group decorator is at :69 but `def chain` at :70; `!chainmenu` `def` is at :255 (:252 `@commands.cooldown`, :253 `@commands.command`, :254 `@admin_or_owner`). Capabilities scaffold cited `subsystem_registry.py:930`; the two capabilities are actually at :933–934 inside the entry that opens at :913. Scaffold also omitted: the `@commands.cooldown` on `chainmenu` (G-4), `build_help_menu_view` (:261), `record_chain_progress` store write, the `moderation_service.auto_delete`→`EVT_MOD_ACTION` removal seam (:357), the audited `_emit` companion (chain_service.py:89), the panel `interaction_check` admin re-gate (:588), `_resolve_channel` (:388), and the latent `chain_count` stat (written, never surfaced)._

#### Surface-unit ledger
| Unit | Kind | File:line | Tier (as-written) | Tier (with amendments) | Rationale / gap |
|---|---|---|---|---|---|
| `!chain` (group router) | command (group) | chain_cog.py:69 | tier-1 | tier-1 | `invoke_without_command` → static usage projection; kernel group dispatch. |
| `!chain create` | command (subcommand) | chain_cog.py:79 | tier-2 | tier-1 | Thin parse+route to audited config-write; carries word-normalize + already_exists + preserve-limit invariant → tier-2. With G-8 ChannelMatchSpec (create+merge semantics) → tier-1. |
| `!chain delete` | command (subcommand) | chain_cog.py:134 | tier-2 | tier-1 | Existence-check + delete + audit = generic CRUD. G-8 delete workflow → tier-1. |
| `!chain setlimit` | command (subcommand) | chain_cog.py:167 | tier-2 | tier-1 | `limit>0` guard + not_found/no_change; G-5 (bounds) + G-8 (update) → tier-1. |
| `!chain removelimit` | command (subcommand) | chain_cog.py:216 | tier-2 | tier-1 | Alias of `set_word_limit(0)` — kernel remove workflow; G-8 remove → tier-1. |
| `!chain list` | command (subcommand) | chain_cog.py:270 | tier-2 | tier-2 | Read-model embed over `get_all_chain_channels` (FieldsBlock over ProviderRef) — standard tier-2 read pattern; stays tier-2. |
| `!chainmenu` | command (prefix) | chain_cog.py:255 | tier-1 | tier-1 | Open-panel PanelRef workflow. |
| `chainmenu` cooldown (2/10s/user) | command modifier | chain_cog.py:252 | tier-1 | tier-1 | `@commands.cooldown` → declared G-4 field; not a tier changer, prevents dropping anti-abuse. |
| `_ChainMenuView` | panel/view (HubView) | chain_cog.py:580 | tier-1 | tier-1 | PanelSpec: read-model embed + action buttons; open-panel/re-render. |
| `interaction_check` (admin re-gate) | panel gate | chain_cog.py:588 | tier-1 | tier-1 | Authority re-check at callback time (help-menu reachable, not admin-gated) — declared gate. |
| btn_create / btn_delete / btn_setlimit / btn_clearlimit | panel action ×4 | chain_cog.py:622–648 | tier-1 | tier-1 | Open-modal actions (send_modal) — declarative. |
| `btn_refresh` | panel action | chain_cog.py:650 | tier-1 | tier-1 | Re-render action. |
| `_CreateChainModal` | modal | chain_cog.py:408 | tier-2 | tier-1 | Form → `create_chain`; thin route+render. G-8 config form → tier-1. |
| `_DeleteChainModal` | modal | chain_cog.py:452 | tier-2 | tier-1 | Form → `delete_chain`. G-8 → tier-1. |
| `_SetLimitModal` | modal | chain_cog.py:488 | tier-2 | tier-1 | isdigit guard + `set_word_limit`; int field + G-8 → tier-1. |
| `_ClearLimitModal` | modal | chain_cog.py:542 | tier-2 | tier-1 | `set_word_limit(0)`. G-8 remove → tier-1. |
| `_resolve_channel` | helper | chain_cog.py:388 | tier-1 | tier-1 | Channel mention/ID/name resolution via `resources.resolve_channel` — kernel resolver. |
| `ChainStage` register/unregister | listener (pipeline-stage wiring) | chain_cog.py:29, 59–67 | tier-3 | tier-2 | Bespoke stage registration into message pipeline (order=20, short-circuit-on-delete). No pipeline-stage primitive today → tier-3. **→ propose G-7 MessagePipelineStageSpec** makes the wiring DATA → tier-2 (handler stays tier-3). |
| `_process_chain_message` (chain rules) | message-validation handler | chain_cog.py:311 | tier-3 | tier-3 | Word-match + word-count-limit + delete decision = message-validation domain logic (explicit tier-3 example). **Deliberate escape hatch** — grammar must not encode game/validation rules. Even with G-7, handler stays code (like G-1). |
| warn-then-`sleep(5)`-delete | timer (in handler) | chain_cog.py:366–368 | tier-3 | tier-3 | Transient warning auto-delete; part of the tier-3 handler. |
| `moderation_service.auto_delete` → `EVT_MOD_ACTION` | event emit (cross-subsystem) | chain_cog.py:357 | tier-1 | tier-1 | Removal routed through moderation seam emitting `moderation.action_taken` + `audit.action_recorded` — the EventSpec emit is declared; fired from the tier-3 handler. |
| `record_chain_progress` | store mutation | chain_service.py:274; db/games/chain.py:46 | tier-1 | tier-1 | `chain_count+1` StoreSpec write; trivial, unaudited hot path. |
| audited `_emit` companion | event (audit) | chain_service.py:89–113 | tier-1 | tier-1 | `emit_audit_action` companion for config writes — standard audited-mutation projection. |
| `chain_channels` store | store | db/games/chain.py:1–61 | tier-1 | tier-1 | StoreSpec: PK channel_id, guild_id, word, word_limit, chain_count + 6 CRUD fns. |
| `chain_count` stat field | store field (latent stat) | db/games/chain.py:57; chain_service.py:274 | tier-1 | tier-1 | Incremented per allowed message but **never surfaced** in any read (`list`/panel show word+limit only). Latent LeaderboardSpec candidate or dead field. |
| `on_ready` listener | listener | chain_cog.py:382 | tier-1 | tier-1 | Logs readiness only — no behavior; effectively droppable. |
| `subsystem_registry["chain"]` | registry metadata | subsystem_registry.py:913 | tier-1 | tier-1 | Declared metadata projection (display, hub, tags, channels). |
| `chain.game.play` / `chain.game.configure` | capability ×2 | subsystem_registry.py:933–934 | tier-1 | tier-1 | Declared capability/access projection. |
| help projection + `build_help_menu_view` | help | chain_cog.py:261 | tier-1 | tier-1 | Help is projection from registry + docstrings; direct-nav hook returns the PanelRef — no dedicated catalogue row. |

#### Manifest sketch (§2 grammar)
```python
SubsystemManifest(
    key="chain",
    commands=[
        CommandSpec("chain", route=GroupRouter(usage_projection=True)),   # tier-1
        CommandSpec("chain create", route=WorkflowRef("channelconfig.create"),      # G-8, tier-1
                    gate=Gate.ADMIN),
        CommandSpec("chain delete", route=WorkflowRef("channelconfig.delete"),      # G-8, tier-1
                    gate=Gate.ADMIN),
        CommandSpec("chain setlimit", route=WorkflowRef("channelconfig.set"),       # G-8+G-5, tier-1
                    gate=Gate.ADMIN, field="word_limit", bounds=Bounds(min=1)),
        CommandSpec("chain removelimit", route=WorkflowRef("channelconfig.clear"),  # G-8, tier-1
                    gate=Gate.ADMIN),
        CommandSpec("chain list", route=PanelRef("chain.list")),                    # tier-2 read-model
        CommandSpec("chainmenu", route=PanelRef("chain.menu"),                      # tier-1 open-panel
                    gate=Gate.ADMIN, cooldown=Cooldown(2, 10, "user")),             # G-4
    ],
    panels=[
        PanelSpec("chain.menu", gate=Gate.ADMIN_RECHECK,                            # tier-1
            body=FieldsBlock(ProviderRef("chain.channels")),                        # read-model
            actions=[
                OpenModal("chain.create"), OpenModal("chain.delete"),               # tier-1 ×4
                OpenModal("chain.setlimit"), OpenModal("chain.clearlimit"),
                ReRender(),                                                         # btn_refresh
            ]),
        PanelSpec("chain.list", body=FieldsBlock(ProviderRef("chain.channels"))),  # tier-2
    ],
    # G-8 ChannelMatchSpec — per-channel keyed config CRUD (word + word_limit),
    # audited, with create/merge/delete/set/clear/list workflows + typed results.
    channel_config=ChannelMatchSpec(                                              # NEW G-8
        store="chain_channels", key="channel_id",
        fields={"word": Field(str, normalize="strip_lower"),
                "word_limit": Field(int, bounds=Bounds(min=0), default=0)},
        merge_on_create=["word_limit"],   # preserve existing limit (pinned invariant)
        unique="word", audited=True),
    settings=[],  # none (config is per-channel via ChannelMatchSpec, not guild SettingSpec)
    gateway_listeners=[],  # fed via the shared message pipeline, not a raw on_message
    # G-7 MessagePipelineStageSpec — declares stage wiring; handler stays tier-3.
    pipeline_stages=[                                                              # NEW G-7
        MessagePipelineStageSpec(
            name="chain", order=20, short_circuit_on_delete=True,
            handler=HandlerRef("chain.validate"),   # tier-3 ESCAPE HATCH: word/limit rules
            gate=SkipCommands()),
    ],
    events=[EventSpec("audit.action_recorded"), EventSpec("moderation.action_taken")],  # tier-1 emits
    stores=[StoreSpec("chain_channels",
                      cols=["channel_id","guild_id","word","word_limit","chain_count"])],
    # chain_count: latent — declare LeaderboardSpec("chain","chain_count") to surface, or drop.
    help=HelpProjection(direct_nav="chain.menu"),   # tier-1
    diagnostics=[],  # on_ready log is a no-op; drop
)
# game=GameFacet(...) — NOT USED: chain has no session/turn/escrow/board. It is a
# channel automod feature, not a stateful game. ChallengeSessionSpec does not apply.
```

#### Tier-3 dispositions
- **`_process_chain_message` (chain validation rules), chain_cog.py:311** — **deliberate escape hatch.** Word-equality + word-count-limit + delete decision is message-validation domain logic (an explicit tier-3 example). Encoding it declaratively would make the grammar a worse programming language (design-spec §10.1 risk 5). Stays code.
- **`ChainStage` register/unregister, chain_cog.py:29/59–67** — **grammar gap → propose G-7 MessagePipelineStageSpec.** The wiring (stage name + order + short-circuit-on-delete + gate) is pure DATA and recurs across every pipeline stage (cleanup=10, counting=15, chain=20). G-7 makes the wiring tier-2; the handler it points at stays tier-3 (identical shape to G-1 for gateway listeners).
- **warn-then-`sleep(5)`-delete, chain_cog.py:366–368** — part of the tier-3 handler (transient UX); not separately generatable, and shouldn't be — it's incidental to the validation escape hatch.
- **The four config-write commands + four modals (as-written tier-2)** are *not* escape hatches — **grammar gap → propose G-8 ChannelMatchSpec** (per-channel keyed audited CRUD with field normalize/bounds + merge-on-create). This is CRUD DATA, not domain logic, and recurs (chain + counting both do channel-config CRUD), so it does not become a worse programming language. Pulls all eight to tier-1.

#### Fit numbers
units total = **30** (×N-weighted: modal-launch buttons ×4, config commands ×4, modals ×4, capabilities ×2, all others ×1).
- tier-3 as-written = 2 (`ChainStage` wiring + `_process_chain_message`). tier-1/2 (as-written) = 30 − 2 = **28 (93%)**.
- tier-3 with amendments = 1 (`_process_chain_message` only; `ChainStage`→tier-2 via G-7). tier-1/2 (amended) = 30 − 1 = **29 (97%)**.

Arithmetic: 28/30 = 0.933 → 93%; 29/30 = 0.967 → 97%. Chain scores far above the blackjack 44% anchor **because it is not a real game** — no session, turn loop, board, engine, or money. It is a channel automod feature (config CRUD + one message-validation stage); its single irreducible tier-3 unit is the word/limit rule, which is correctly code.

#### Structural-gap flags
- **Stateful turn/round loop:** NONE. `chain_count` is a monotonic counter, not a turn state — grammar-expressible (StoreSpec field). No session choreography → ChallengeSessionSpec deliberately unused.
- **Timers/timeouts:** one `asyncio.sleep(5)` warning auto-delete inside the tier-3 handler; no scheduled loop, no wait_for. Not a session timeout. Grammar covers it only as part of the escape-hatch handler.
- **Component/session recovery on restart:** N/A — config is durable in `chain_channels`; the panel is a non-persistent HubView (times out, no custom_id recovery needed). No recovery gap.
- **Escrow/settlement/reward/anti-double-settle:** NONE — no money, no `settle_once`. Not applicable.
- **Message-pipeline stage:** present (`ChainStage`, order=20, short-circuit-on-delete). Ordering dependency on cleanup(10)/counting(15). **Needs new primitive G-7** for the wiring; the validation handler is a legitimate tier-3.
- **Leaderboards/records:** `chain_count` is written every allowed message but has **no read surface** — a latent LeaderboardSpec (grammar-expressible) or a dead field to drop. Structural inconsistency, not a grammar gap.
- **Social/community moderation:** removals route through `moderation_service.auto_delete` emitting `EVT_MOD_ACTION` — cross-subsystem moderation seam; the emit is declarative (EventSpec) but fired from tier-3 logic.

#### MAP → RECONSIDER → SIMULATE → OPTIMIZE
- **RECONSIDER verdict: improve (candidate merge with counting).** Chain is a thin channel-automod feature miscategorized as a game. It works and is ~97% generatable with G-7+G-8. Two concrete improvements: (1) surface or drop `chain_count` (dead stat); (2) it shares the *exact* structural shape as counting (pipeline stage + per-channel config CRUD + admin panel/modals) — the two are strong merge candidates into one "channel message-rule" family.
- **Optimal new-bot form:** a declared `ChannelRuleSpec` = ChannelMatchSpec (G-8) fields {allowed_word, word_limit} + a MessagePipelineStageSpec (G-7) whose handler is the only hand-written unit (the pure validation predicate). Everything else — commands, modals, panel, list, audit, registry, help — is generated data. Optionally a LeaderboardSpec over `chain_count`.
- **Dependency-layer guess:** L0 runtime (message pipeline, moderation seam, audit) → then this subsystem. No economy/games-core dependency. Sits alongside counting in a shared "channel-automod" layer.
- **Production-grade done-definition:** parity golden — for a chain-configured channel, a non-matching or over-limit non-command message is deleted, a warning posts and self-deletes after 5s, `EVT_MOD_ACTION` + `audit.action_recorded` both fire, command messages pass through untouched, `chain_count` increments only on allowed messages, and create-over-an-existing-limit preserves the limit (`test_create_chain_preserves_existing_limit`).
- **Outperform target:** pending Lane F. Chain is a niche automod primitive; closest comparators are generic automod bots (MEE6/Dyno keyword filters). Ours wins by unifying it with the audited mutation ledger + hub UI; a leaderboard over `chain_count` would make it a genuine mini-game rather than a filter.
- **Cross-lane dependency notes:** consumes `moderation_service.auto_delete`/`EVT_MOD_ACTION` (moderation lane) and `emit_audit_action` (governance/audit); depends on `core.runtime.message_pipeline` + `resources` (L0 runtime); `chain_count` could feed the leaderboard subsystem (same Lane C). Audit stays anchored to chain.

---

### leaderboard
_cogs: disbot/cogs/leaderboard_cog.py · disbot/services/rank_providers.py · disbot/utils/ux_patterns/image_builders.py · disbot/utils/subsystem_registry.py:937 (leaderboard entry)_
_Scaffold drift corrected: scaffold cited only `leaderboard_cog.py` and left both tier columns blank. It **missed** the `@commands.cooldown(rate=2,per=10)` (line 194, G-4), the embed-vs-image-card renderer split (`_build_provider_response`/`_render_card`), and the 25-entry `rank_providers.ALIASES` map (distinct from the 11 command-decorator aliases). Scaffold marked `render_leaderboard_image` "⚠ unverified — helper"; **verified** at `image_builders.py:90` — it is a discrete tier-3 renderer unit. Scaffold's "no owned table" store note is **correct**._

#### Surface-unit ledger
| Unit | Kind | File:line | Tier (as-written) | Tier (with amendments) | Rationale / gap |
|---|---|---|---|---|---|
| `!leaderboard` (+11 decorator aliases: lb, rankings, minelb, miningleaderboard, fishlb, dm_leaderboard, dm_lb, rpslb, farmlb, countlb, counting_leaderboard) | command | leaderboard_cog.py:216 | tier-2 | tier-1 | Route resolves a board from `invoked_with`/`category` then opens hub or pre-renders a board. No domain logic → read-model route. With kernel: route=PanelRef (open hub) / LeaderboardSpec pre-select → tier-1. |
| `@commands.cooldown(rate=2, per=10, user)` | cooldown | leaderboard_cog.py:194 | tier-1 | tier-1 | Declared anti-abuse field → **G-4** CommandSpec.cooldown. Doesn't change command tier; must not be dropped. |
| `LeaderboardView(BaseView)` | panel/view | leaderboard_cog.py:137 | tier-2 | tier-1 | Read-model hub panel holding the selector; re-renders on select (timeout=120, standard panel). Generated hub panel. |
| `_CategorySelect` + `callback` | selector | leaderboard_cog.py:152 / :161 | tier-2 | tier-1 | Options built from provider registry (`_select_options`); callback defers, resolves board, re-renders response. "Panel action that re-renders" → tier-1 with a declared board list. |
| `build_help_menu_view` | help/nav hook | leaderboard_cog.py:243 | tier-2 | tier-1 | Returns the hub panel + overview embed → PanelRef nav target (help projection). |
| `_build_provider_response` / `_embed_from_entries` / `_build_overview_embed` | embed render | leaderboard_cog.py:90 / :35 / :108 | tier-2 | tier-1 | Generic embed projection over provider rows (rank/medal + `label`). list-block over a ProviderRef → tier-1 generated. |
| `_render_card` + `render_leaderboard_image` | image renderer | leaderboard_cog.py:52 + image_builders.py:90 | **tier-3** | **tier-3** | Bar-chart pixel layout: outlier-safe `sqrt` scaling (`_bar_fraction`), podium tints, reserved value column, theme skins. **Deliberate escape hatch** — image layout stays code (the "board renderer" analogue), BUT it is ONE kernel-shared renderer for all boards, not per-subsystem. Opt-in (`card_theme`) is DATA via a **LeaderboardSpec enrichment** (extends the existing tier-2 family — NOT a new G-number). |
| RankProvider boards `top()` ×12 (xp, coins, mining, creatures, fishing, farm, gamexp, crafting, deathmatch, rps, counting, karma) | leaderboard ×12 | rank_providers.py:107–619 | tier-2 | tier-2 | Each = ranked read (`SELECT … ORDER BY stat DESC LIMIT 10` / pre-aggregated db fn) + row format. No game rules, no mutation → **LeaderboardSpec** (tier-2). This registry **is the LeaderboardSpec vocabulary generalized**. As-written = hand-written class; amended = declaration (code→data, same tier). |
| RankProvider `member_rank()` (per-user rank read) ×12 | provider read | rank_providers.py:87 | tier-2 | tier-2 | Derived from the same board ordering (position of user_id). Kernel derives it from one LeaderboardSpec. **Consumed by xp `!rank`/`!profile`** (cross-lane). |
| `rank_providers.ALIASES` map (25 category→board entries) | command aliases | rank_providers.py:647 | tier-1 | tier-1 | Declarative alias-routing data (legacy per-board shortcuts). NB: superset of the 11 decorator aliases — `craftlb`/`gxp`/`rep`/`creature` resolve only as a `category` **arg**, not as bare commands. |
| `SUBSYSTEMS["leaderboard"]` entry (entry_points leaderboard/lb, parent_hub economy, tags) | manifest metadata | subsystem_registry.py:937 | tier-1 | tier-1 | Declarative subsystem descriptor. |
| Capabilities `leaderboard.xp.view`, `leaderboard.economy.view` | capability/binding ×2 | subsystem_registry.py:956–957 | tier-1 | tier-1 | Declared capability strings (BindingSpec-shaped data). |
| **Owned store: NONE** | store (absent) | — | n/a | n/a | Pure aggregator — owns no table; reads 12 other subsystems' stores. Structural finding, not a unit; no StoreSpec needed. |

#### Manifest sketch (§2 grammar)
```python
SubsystemManifest(
    key="leaderboard",
    commands=[
        CommandSpec(
            name="leaderboard",
            aliases=("lb","rankings","minelb","miningleaderboard","fishlb",
                     "dm_leaderboard","dm_lb","rpslb","farmlb","countlb",
                     "counting_leaderboard"),          # + 14 arg-only via ALIASES data
            route=PanelRef("leaderboard.hub"),          # bare → hub; tier-1
            arg_route=LeaderboardSelect(from_arg="category"),  # pre-select a board
            cooldown=Cooldown(rate=2, per=10, bucket="user"),  # G-4
        ),
    ],
    panels=[
        PanelSpec(                                      # tier-1 generated hub
            panel_id="leaderboard.hub", subsystem="leaderboard",
            title="📊 Leaderboards",
            body=(BlockSpec(kind="list", provider=ProviderRef("board.rows")),),
            selectors=(SelectorSpec(                    # _CategorySelect → tier-1
                selector_id="category",
                options_source=ProviderRef("leaderboard.boards"),  # from registry
                on_select=Rerender("board", card_from="LeaderboardSpec.card"),
            ),),
        ),
    ],
    game=GameFacet(
        leaderboards=(                                  # the 12 boards as DATA
            LeaderboardSpec(board_id="xp",        stat_key="xp.xp",        metric="max",
                            value_template="Level {level} ({xp} XP)",
                            card=CardSpec(theme="midnight")),           # LeaderboardSpec enrichment
            LeaderboardSpec(board_id="coins",     stat_key="xp.coins",     metric="max"),
            LeaderboardSpec(board_id="mining",    stat_key="mining.total", metric="sum",
                            card=CardSpec(theme="abyss")),
            LeaderboardSpec(board_id="creatures", stat_key="collectors.caught",
                            metric="roster_scoped", card=CardSpec(theme="verdant")),  # LeaderboardSpec enrichment: stat_source
            LeaderboardSpec(board_id="fishing",   stat_key="fishers.caught",
                            metric="roster_scoped", card=CardSpec(theme="tidal")),
            LeaderboardSpec(board_id="farm",      stat_key="farm.chickens", metric="max",
                            value_template="{chickens} hens (coop Lv {coop})",
                            card=CardSpec(theme="harvest")),
            LeaderboardSpec(board_id="gamexp",    stat_key="game_xp.total", metric="max",
                            value_template="Lv {level} · {xp} XP"),
            LeaderboardSpec(board_id="crafting",  stat_key="game_xp.crafting", metric="max",
                            card=CardSpec(theme="ember")),
            LeaderboardSpec(board_id="deathmatch",stat_key="dm.wins", metric="max",
                            value_template="{wins}W / {losses}L", card=CardSpec(theme="ember")),
            LeaderboardSpec(board_id="rps",       stat_key="rps.wins", metric="max",
                            value_template="{wins}W / {losses}L / {ties}T"),
            LeaderboardSpec(board_id="counting",  stat_source=ProviderRef("counting.totals"),  # LeaderboardSpec enrichment: non-flat JSON agg
                            metric="sum"),
            LeaderboardSpec(board_id="karma",     stat_key="karma.points", metric="max"),
        ),
    ),
    # DELIBERATE tier-3, kernel-shared (NOT per-subsystem): the bar-chart image renderer.
    renderers=[HandlerRef("leaderboard.card_image")],   # render_leaderboard_image — escape hatch
    settings=[],                                        # owns none
    stores=[],                                          # owns NO table — pure aggregator
    bindings=[Capability("leaderboard.xp.view"), Capability("leaderboard.economy.view")],
    help=HelpEntrySpec(summary="Server leaderboards for XP, coins, and games"),
    # member_rank is DERIVED by the kernel from each LeaderboardSpec (consumed by xp !rank).
)
```

#### Tier-3 dispositions
- **`render_leaderboard_image` + `_render_card`** (image renderer) — **deliberate escape hatch**. Pixel layout (outlier-safe sqrt bar scaling, podium tints, reserved value column, theme skins) is genuine rendering code; expressing it in the grammar would make it a "worse programming language" (design-spec §10.1 risk 5), exactly the board-renderer carve-out. **Crucially it is ONE kernel-shared renderer for all 12 boards**, not per-subsystem code — so it does not multiply with subsystems. The per-board *opt-in* (`card_theme`) is DATA via a **LeaderboardSpec enrichment** (`.card`/`.stat_source`/`.value_template` — extends the existing tier-2 family, NOT a new G-number).
- **The 12 providers stay tier-2** by design — `LeaderboardSpec` is a tier-2 primitive. This is NOT a gap: they carry no game rules and no mutations, so tier-2 is the correct "grammar expresses it" floor. The enrichment converts them from hand-written classes (as-written tier-2) to declarations (amended tier-2) — code→data at the same tier, which is the *merge-into-kernel* win even though the fit % is unchanged.

#### Fit numbers
Weighted units (×N): command 1 · cooldown 1 · view 1 · selector 1 · help-nav 1 · embed-render 1 · **image-renderer 1 (tier-3)** · providers ×12 · member_rank seam 1 · ALIASES map 1 · subsystem entry 1 · capabilities ×2.
**units total = 24.**
tier-1/2 (as-written) = 24 − 1 (image renderer) = **23 (96%)**.
tier-1/2 (with amendments) = **23 (96%)** — the only tier-3 is the deliberate kernel-shared image renderer, which stays code by design. The LeaderboardSpec enrichment moves provider code→data within tier-2 (fit unchanged, but bespoke code eliminated).

#### Structural-gap flags
- **Leaderboards / records (named danger zone): PRESENT.** Fully expressed by `LeaderboardSpec` + a **LeaderboardSpec enrichment** (stat_source / value_template / card). This subsystem IS the leaderboard primitive generalized.
- **No owned store — pure cross-subsystem read aggregator.** Reads 12 other subsystems' tables via `db.*` fns. Expressed as `stores=[]` + LeaderboardSpec `stat_key` pointing at the *producing* subsystem's StoreSpec. No new primitive needed; it is a read-model kernel.
- **Image-card renderer = tier-3 rendering code.** Deliberate; kernel-shared, so it does not scale per subsystem.
- **Absent danger patterns (verified):** no stateful turn/round loop, no timers/scheduled loops (view timeout=120 is a standard panel timeout), no `wait_for`, no session recovery, no escrow/settlement/`settle_once`, no gateway/bus listeners, no moderation. This is a stateless read-model subsystem.

#### MAP → RECONSIDER → SIMULATE → OPTIMIZE
- **RECONSIDER verdict: MERGE.** The `RankProvider` registry is `LeaderboardSpec` in disguise; the whole subsystem should dissolve into a generated leaderboard **kernel** (command + hub panel + selector + embed/card renderer) fed by per-subsystem `LeaderboardSpec` declarations owned by the producing subsystems.
- **Optimal new-bot form:** No `leaderboard_cog` / `rank_providers` at all. Each stat-producing subsystem (xp, economy, mining, …) declares its board(s) as `LeaderboardSpec` in its own manifest; a runtime kernel aggregates every declared board into the `!leaderboard` hub + category selector, derives `member_rank` for free, and renders the shared image card. New category = one declaration, zero code.
- **Dependency-layer guess:** read-model / projection **kernel** — sits beside the panel + image-card kernels (L0/L1 runtime), *above* every producing subsystem's StoreSpec (needs their tables to read).
- **Production-grade done-definition:** a parity golden that, from the 12 `LeaderboardSpec` declarations, byte-matches the current top-10 embeds **and** image cards **and** empty-states for a fixed fixture guild, derives `member_rank` identically, and resolves the full alias table (25 arg aliases + 11 command aliases, incl. the `craftlb`-arg-only nuance) to the same board.
- **Outperform target:** MEE6 / Arcane (single paywalled XP board, web-only). Ours: 12 unified categories, themed image cards, one command + dropdown, all generated from declarations — no per-board code, no paywall. (Full benchmark pending Lane F.)
- **Cross-lane dependency notes:** reads stores owned by economy/coins (Lane B) and xp/karma/counting (Lane C community) and mining/creatures/fishing/farm/gamexp/crafting/deathmatch/rps (Lane C games); `member_rank` is consumed by the xp `!rank`/`!profile` surface (Lane C xp). Board declarations must move to those subsystems' manifests — anchor this audit to the kernel, but the LeaderboardSpec rows are cross-lane emitted.

---

### community
_cogs: disbot/cogs/community_cog.py, disbot/views/community/hub.py (hub-level only; community_spotlight_cog.py is a SEPARATE subsystem/section)_
_Scaffold drift: `!community` decorator is at community_cog.py:41 (`def community_menu` :42); `/community` decorator at :55 (`def community_slash` :59) — ground-truth cites the def lines (:42/:59), scaffold cites the decorator lines (:41/:55). Both are correct; ledger below cites decorator + def. All spotlight rows in the scaffold belong to the community_spotlight section, not here._

#### Surface-unit ledger
| Unit | Kind | File:line | Tier (as-written) | Tier (with amendments) | Rationale / gap |
|---|---|---|---|---|---|
| !community | command | community_cog.py:41 (def :42) | tier-1 | tier-1 | Route is a PanelRef (open-hub workflow), zero domain code — kernel `send_panel(build_community_hub_panel())`. |
| /community | command | community_cog.py:55 (def :59) | tier-1 | tier-1 | Same PanelRef target, ephemeral slash front door; reuses the identical builder so governance filtering is shared. |
| CommunityCog.build_help_menu_view | help hook | community_cog.py:47 | tier-1 | tier-1 | Help-menu direct-nav projection — returns the same hub panel via `help_ctx_shim`. Pure projection. |
| CommunityHubView | panel/view (generated hub) | views/community/hub.py:259 | tier-1 | tier-1 | Router-only HubView; children come from `parent_hub == "community"` + registry cross_links. No business logic (class docstring says so). |
| build_community_hub_panel | panel builder | views/community/hub.py:144 | tier-1 | tier-1 | Resolves governance visibility (kernel), filters children, builds embed+view. All generic hub plumbing, no domain rules. |
| build_community_hub_embed | embed render | views/community/hub.py:98 | tier-1 | tier-1 | Description generated from discovered child metadata; group headings are presentational constants. Projection of registry data. |
| discover_community_children | registry discovery | views/community/hub.py:54 | tier-1 | tier-1 | Pure deterministic read: primary from `SUBSYSTEMS.parent_hub`, cross_links from `hub_registry.get_hub("community").cross_link_children`. Data, no I/O. |
| _CommunityChildButton | panel/view (hub child button) | views/community/hub.py:230 | tier-1 | tier-1 | Thin subclass of shared `HubChildButton` binding hub_key + back_attacher; inherits generic forward-to-child logic. No community-specific logic. |
| attach_back_to_community_button | nav control | views/community/hub.py:192 | tier-1 | tier-1 | Generated Back-to-hub button via shared `attach_back_button`/`chain_back`; parent builder re-runs the same hub panel. |
| _format_child_label | presentational helper | views/community/hub.py:87 | tier-1 | tier-1 | Emoji + display_name string from registry meta. Trivial projection. |

#### Manifest sketch (§2 grammar)
```python
SubsystemManifest(
    key="community",
    kind="parent_hub",                       # router-only hub, no store/settings/game
    commands=[
        CommandSpec(name="community", surface="prefix",
                    route=PanelRef("community.hub")),   # tier-1
        CommandSpec(name="community", surface="slash", ephemeral=True,
                    route=PanelRef("community.hub")),   # tier-1 (G-6 namespaces !community vs /community)
    ],
    panels=[
        HubPanelSpec(
            panel_id="community.hub",
            title="🌱 Community Hub",
            # primary children auto-discovered from other subsystems'
            # parent_hub=="community"; explicit cross-links declared as DATA:
            cross_links=["counting", "chain", "leaderboard"],
            child_order="ui_priority",       # deterministic
            governance_filter=True,          # kernel resolve_visibility at render + click
            back_nav="generated",            # attach_back_to_community_button
        ),
    ],
    help=[HelpEntry(panel=PanelRef("community.hub"))],   # tier-1 projection
    # NO settings, NO stores, NO events, NO subscriptions,
    # NO gateway_listeners, NO tasks, NO game=GameFacet.
    stores=[], settings=[], events=[], subscriptions=[],
    gateway_listeners=[], tasks=[],
)
```

#### Tier-3 dispositions
- None. Every unit is generated kernel/hub workflow (open-panel, registry discovery, governance filter, back-nav, help projection). There is no domain logic, no game rule, no stateful loop, no money flow, no store to escape-hatch.

#### Fit numbers
units total = 10 (all ×1). tier-1/2 (as-written) = 10 (100%). tier-1/2 (with amendments) = 10 (100%). Arithmetic: 10/10 = 100% both columns; zero tier-3, so no amendment moves the needle. This subsystem is the pure-router **ceiling** — answers the KEY QUESTION affirmatively: a pure router hub is 100% tier-1, fully generated from a `parent_hub` HubPanelSpec + declared `cross_links`.

#### Structural-gap flags
- Stateful turn/round loop: ABSENT.
- Timers/timeouts/scheduled loops: ABSENT (no `@tasks.loop` here — the cache-trim loop lives in community_spotlight, a separate subsystem).
- wait_for flows / component recovery on restart: ABSENT (buttons use stable `custom_id=f"community:open:{sub}"` but carry no session state).
- Escrow/settlement/reward/anti-double-settle: ABSENT.
- Leaderboards/records: ABSENT here (leaderboard appears only as a cross-link to another subsystem).
- Social/community moderation: ABSENT (router only).
- One structural note (NOT a gap): governance visibility is re-checked at both render time and click time (`HubChildButton.callback` → `resolve_visibility`). The grammar expresses this as a kernel `governance_filter=True` flag on the HubPanelSpec — it is generic, not domain code, so it stays tier-1.

#### MAP → RECONSIDER → SIMULATE → OPTIMIZE
- RECONSIDER verdict: **keep** — a correct, minimal router hub; it is exactly what the grammar wants a hub to be (declaration-only). Nothing to improve, merge, or drop.
- Optimal new-bot form: a single `HubPanelSpec` primitive (auto-discovered `parent_hub` children + a declared `cross_links` list + a `governance_filter` flag + generated back-nav). The whole `disbot/views/community/hub.py` file collapses to ~8 lines of manifest data; the child-forwarding button, discovery, and back-nav become shared kernel code owned once, not per-hub.
- Dependency-layer guess: **navigation/hub layer** on top of L0 runtime — depends on governance_service (L0), subsystem_registry, hub_registry (kernel), and the shared `views/hub_children.py` seam. Owns nothing itself.
- Production-grade done-definition: a golden test proving the hub renders exactly the governance-visible `parent_hub=="community"` children (primary style) + declared cross_links (secondary style) in deterministic `ui_priority`-then-key order, wraps at 5 buttons/row, drops hidden/unknown cross_links with a warning, and that a child hidden between render and click fails closed with an ephemeral.
- Outperform target: pending Lane F (navigation/UX comparison). The differentiator is registry-driven, governance-filtered hubs that never drift from the shipped feature set — most competitor bots hardcode menu trees.
- Cross-lane dependency notes: primary children **xp** and **roles** (progression); cross-links **counting** and **chain** (Lane C Games) and **leaderboard** (Lane B economy). This section audits only the hub shell; each child is audited in its own section. The hub is a consumer of those subsystems' `build_help_menu_view` hooks and their registry metadata.

---

### community_spotlight
_cogs: disbot/cogs/community_spotlight_cog.py · registry: disbot/utils/subsystem_registry.py:621-643 (entry) · reads only (no owned table): db.get_guild_xp_totals + services.rank_providers.get_provider_
_Scaffold check: file:line rows all VERIFY against source. Command def is at :304 (ground-truth correct); the decorator stack is `@commands.cooldown(rate=2, per=15, user)` :299 + `@commands.command(name="spotlight", aliases=["activity"])` :300-303. No drift; scaffold was missing the cooldown, the two embed-builder read-models, and the tier columns._

#### Surface-unit ledger
| Unit | Kind | File:line | Tier (as-written) | Tier (with amendments) | Rationale / gap |
|---|---|---|---|---|---|
| !spotlight (alias !activity) | command | community_spotlight_cog.py:304 | tier-1 | tier-1 | Route is an open-panel workflow (builds SpotlightView + main embed) → PanelRef. Zero domain code. |
| @commands.cooldown(rate=2, per=15, user) | command anti-abuse | community_spotlight_cog.py:299 | — (dropped) | tier-1 | Not expressible as-written → shipped rate-limit silently lost. Reuse **G-4** CommandSpec.cooldown to keep it as declared data. |
| SpotlightView (main dashboard embed) | panel/read-model | community_spotlight_cog.py:129 / builder :41 | tier-2 | tier-2 | Read-model panel = FieldsBlock over ProviderRefs (guild totals + xp/coins providers + level-up feed). No writes. |
| xp_leaders button | panel action (provider read) | community_spotlight_cog.py:141 | tier-2 | tier-2 | Renders full top-10 read-model over ProviderRef("xp") via _build_provider_embed. |
| richest button | panel action (provider read) | community_spotlight_cog.py:151 | tier-2 | tier-2 | Read-model over ProviderRef("coins"). |
| games button | panel action (navigate) | community_spotlight_cog.py:162 | tier-1 | tier-1 | Re-render/open sub-panel (GamesView) with a static embed. Kernel navigation workflow. |
| refresh button | panel action (re-render) | community_spotlight_cog.py:179 | tier-1 | tier-1 | Rebuilds the same main read-model embed → tier-1 re-render. |
| GamesView (sub-panel) | panel/view | community_spotlight_cog.py:191 | tier-1 | tier-1 | Navigation panel: static embed + Back button + selector. No domain logic. |
| GamesView.back button | panel action (re-render) | community_spotlight_cog.py:199 | tier-1 | tier-1 | Re-renders main read-model / restores SpotlightView → tier-1. |
| _GameSelect (×4 game options) | selector (provider read) | community_spotlight_cog.py:213 | tier-2 | tier-2 | SelectorSpec: static options tuple (mining/rps/deathmatch/counting); callback renders ProviderRef read-model per pick. |
| _build_main_embed | provider read-model (helper) | community_spotlight_cog.py:41 | tier-2 | tier-2 | Aggregates db.get_guild_xp_totals + xp/coins provider tops + feed. Underlies SpotlightView; provider-shaped. |
| _build_provider_embed | provider read-model (helper) | community_spotlight_cog.py:103 | tier-2 | tier-2 | Generic top-N ProviderRef render. Underlies buttons/select. |
| build_help_menu_view | help/hub entry | community_spotlight_cog.py:278 | tier-1 | tier-1 | Hub direct-nav hook returning the panel (open-panel projection). |
| community_spotlight.dashboard.view | capability/registry | subsystem_registry.py:641 | tier-1 | tier-1 | Registry declaration (help/capability projection). No settings declared. |
| bus.on(xp_service.EVT_LEVEL_UP, _on_level_up) | event subscription | community_spotlight_cog.py:252 | tier-1 | tier-1 | Pure EventSubscription declaration {event, handler}. |
| _on_level_up handler | event handler (feed projection) | community_spotlight_cog.py:260 | tier-3 | tier-2 | Extracts payload, resolves member_display, formats blurb, appends to per-guild bounded deque. Not a channel post (not G-3). → **propose *provisional* P-1 EventFeedProjectionSpec** (event→template→scoped bounded ring). |
| _cache_trim_loop (@tasks.loop hours=1) | scheduled task | community_spotlight_cog.py:271 | tier-2 | tier-1 | ManagedTaskSpec(trigger=interval:3600) already in §2 + thin janitor handler → tier-2. With P-1 the feed is a kernel-owned scope-keyed ring evicted on guild-leave → loop **eliminated** → tier-1. |
| cog_load / cog_unload lifecycle wiring | listener/task setup+teardown | community_spotlight_cog.py:251,256 | tier-1 | tier-1 | Generated wiring from the EventSubscription + ManagedTaskSpec declarations. |

#### Manifest sketch (§2 grammar)
```python
SubsystemManifest(
    key="community_spotlight",
    commands=(
        CommandSpec(name="spotlight", aliases=("activity",),
                    route=PanelRef("spotlight_main"),
                    cooldown=(2, 15, "user")),          # G-4 keeps shipped rate-limit
    ),
    panels=(
        PanelSpec(id="spotlight_main",                  # tier-2 read-model
            blocks=(BlockSpec(provider=ProviderRef("spotlight.overview")),   # guild totals
                    BlockSpec(provider=ProviderRef("xp.top3")),
                    BlockSpec(provider=ProviderRef("coins.top3")),
                    BlockSpec(provider=ProviderRef("spotlight.levelup_feed"))),  # P-1 read side (provisional)
            actions=(
                PanelActionSpec("xp_leaders",  render=ProviderRef("xp.top10")),    # tier-2
                PanelActionSpec("richest",     render=ProviderRef("coins.top10")), # tier-2
                PanelActionSpec("games",       route=PanelRef("spotlight_games")), # tier-1 nav
                PanelActionSpec("refresh",     rerender=True),                     # tier-1
            )),
        PanelSpec(id="spotlight_games",                 # tier-1 nav sub-panel
            selectors=(SelectorSpec(id="game_select",
                options_source=("mining","rps","deathmatch","counting"),
                render=ProviderRef("game.top10")),),    # tier-2 read-model per pick
            actions=(PanelActionSpec("back", route=PanelRef("spotlight_main")),)),
    ),
    settings=(),                                        # none shipped
    stores=(),                                          # owns no table (reads only)
    events=(),                                          # emits none
    subscriptions=(
        EventSubscription(event="xp.level_up",          # tier-1 declaration
                          handler=HandlerRef("spotlight_on_levelup")),
    ),
    # PROPOSED P-1 (PROVISIONAL) — turns _on_level_up (tier-3) into DATA and deletes the trim loop:
    feeds=(
        EventFeedProjectionSpec(                # P-1 (PROVISIONAL — 1 instance)
            id="spotlight.levelup_feed",
            event="xp.level_up",
            template="**{member_display}** reached Level **{new_level}**",
            scope="guild", max_entries=5,
            persistence="checkpointed"),                # new-bot: survive restart
    ),
    tasks=(),                                           # _cache_trim_loop absorbed by P-1 scope eviction
    help=(HelpEntrySpec(route=PanelRef("spotlight_main")),),
    # NB: NO GameFacet — spotlight owns no session/leaderboard; it only READS
    # foreign rank_providers (xp/coins/game boards). Leaderboards belong to
    # their owning subsystems, consumed here as ProviderRefs.
)
```

#### Tier-3 dispositions
- **_on_level_up handler (:260)** — grammar gap → **propose *provisional* P-1 EventFeedProjectionSpec** (event → template → scope-bounded ring buffer, read by a panel FieldsBlock). This is the read-side analog of G-3 (which routes to a *channel*); here the sink is a durable in-memory/checkpointed projection surfaced in the dashboard. Constrained data, not arbitrary code — does NOT make the grammar a worse programming language. Recurs as the canonical community "recent activity" feed (recent joins / level-ups / big wins). *Single confirmed instance in Lane C — confirm recurrence in Lane E/community dashboards before ratifying.*
- **_cache_trim_loop (:271)** — NOT an independent escape hatch: it exists only to bound the ad-hoc `_levelup_feed` dict. Under P-1 the ring is kernel-owned and scope-evicted on guild-leave, so the task disappears. As-written it is a ManagedTaskSpec (already §2) + a generic janitor handler → tier-2, not a durable gap.

#### Fit numbers
units total = 16 (weighted ×1 each; _GameSelect counts once, its 4 options folded in).
- tier-1 as-written: !spotlight, games btn, refresh btn, GamesView, back btn, build_help_menu_view, registry cap, EventSubscription, cog lifecycle = **9**
- tier-2 as-written: SpotlightView, xp_leaders, richest, _GameSelect, _build_main_embed, _build_provider_embed, _cache_trim_loop = **7**
- tier-3 as-written: _on_level_up = **1**; cooldown = not-expressible (dropped, 0 in tier-1/2)
- **tier-1/2 (as-written) = 9 + 7 = 16 − (2 non-fit: _on_level_up tier-3 + cooldown dropped) = 14 / 16 = 88%**
- With **ratified** amendments (G-4 only, since P-1 is provisional): cooldown → tier-1 (G-4); _cache_trim_loop is already tier-1/2 (existing ManagedTaskSpec). _on_level_up **stays tier-3** (its lift depends on the *provisional* P-1 EventFeedProjectionSpec). **tier-1/2 (with ratified amendments) = 15 / 16 = 94%.**
- With the **provisional** P-1 ratified (event-feed as a scope-bounded ring), _on_level_up → tier-2 ⇒ **16 / 16 = 100%**.

units total = 16 · tier-1/2 (as-written) = 14 (88%) · tier-1/2 (with ratified amendments) = **15 (94%)** · with provisional P-1 = 16 (100%)

#### Structural-gap flags
- **COMMUNITY FEED / SPOTLIGHT FLOW (target danger zone):** the level-up feed is a module-global `_levelup_feed: dict[int, deque]` (:33) — **ephemeral, not persisted → wiped on every bot restart** (falls back to "Waiting for the next level-up…" until new events arrive). P-1 with `persistence="checkpointed"` expresses the durable version the shipped bot lacks. This is a real component-recovery-on-restart gap.
- **Unbounded in-memory growth footgun:** guarded today by the hand-rolled `_cache_trim_loop`. Kernel-owned scoped ring (P-1) removes the class of bug entirely.
- **Scheduled/timer loop:** present (`@tasks.loop(hours=1)`), fully expressed by existing §2 ManagedTaskSpec.
- **Cross-subsystem provider coupling:** dashboard reads foreign providers by string name (`get_provider("xp"/"coins"/game)`); a renamed/removed provider silently degrades to "*No activity yet*". Declared ProviderRefs would make the dependency checkable — mild gap, not tier-3.
- **ABSENT danger zones (correctly):** no stateful turn/round loop, no wait_for, no escrow/settlement/payout, no settle_once, no owned leaderboard/records, no moderation. Spotlight is a pure read-model aggregator.

#### MAP → RECONSIDER → SIMULATE → OPTIMIZE
- **RECONSIDER verdict: improve.** High-value cross-domain community dashboard; keep it, but fix the restart-fragile feed and declare its provider reads.
- **Optimal new-bot form:** a settings-free `SubsystemManifest` — read-model panels over declared ProviderRefs, one **P-1 EventFeedProjectionSpec (provisional)** (scope=guild, max=5, persistence=checkpointed) replacing both `_on_level_up` and `_cache_trim_loop`, cooldown via G-4. No GameFacet, no store.
- **Dependency-layer guess:** a **dashboard/read-model layer** sitting ABOVE games-core, xp, and economy; depends on their ProviderRefs + the EventBus (L0 runtime). Owns nothing.
- **Production-grade done-definition:** parity golden — `!spotlight` renders identical embed fields (Server-at-a-Glance totals, top-3 XP, top-3 coins, last-5 level-ups), all four buttons + game select navigate identically, cooldown 2/15s enforced, AND the level-up feed **survives a restart** (new-bot improvement over the ephemeral original).
- **Outperform target:** pending Lane F — provisional: MEE6/Arcane surface XP and economy on separate commands; ours unifies XP + coins + game leaderboards + a live level-up feed in one restart-durable panel.
- **Cross-lane dependency notes:** consumes `xp_service.EVT_LEVEL_UP` + xp provider (Lane E leveling), coins provider (Lane B economy), game leaderboards mining/rps/deathmatch/counting (Lane C games-core), `resources.member_display`/`safe_defer` (L0). Anchored to Lane C as the community dashboard that reads these.

---

### karma
_cogs: disbot/cogs/karma_cog.py · disbot/cogs/karma/schemas.py · disbot/services/karma_service.py · disbot/services/karma_config.py · disbot/migrations/093_karma.sql · disbot/utils/db/karma.py · disbot/services/rank_providers.py:588 (shared karma leaderboard provider)_

_Line-citation drift vs scaffold/spike: scaffold cites decorator lines (:209/:224/:235/:248); ground-truth cites `def` lines. Verified against source: `thanks` `def` :210 (decorators `@commands.cooldown` :208, `@commands.command` :209); `karma` group `def` :225 (`@commands.group` :224); `karma add` `def` :236 (`@karma.command` :235); `karma_slash` `def` :254 (`@app_commands.command` :248). Both refer to the same units; no behavioral drift from the spike. The `karma.granted` emit is at karma_service.py:178 (const :38). Reproduces the spike's 80%→87% exactly._

#### Surface-unit ledger
| Unit | Kind | File:line | Tier (as-written) | Tier (with amendments) | Rationale / gap |
|---|---|---|---|---|---|
| !thanks (+rep/thank) | command | karma_cog.py:210 (dec :209) | 3 | 3 | route=HandlerRef(karma.grant): audited grant seam + typed-error copy (5 KarmaError shapes render via §2.7 Result grammar). Deliberate escape hatch — real domain mutation. |
| !karma (card) | command | karma_cog.py:225 (dec :224) | 2 | 2 | route=PanelRef(karma.card) → FieldsBlock over a read provider. Pure declaration. |
| !karma add | command | karma_cog.py:236 (dec :235) | 3 | 3 | same seam as !thanks (declared alias surface). Deliberate escape hatch. |
| /karma | command | karma_cog.py:254 (dec :248) | 2 | 2 | same panel, SLASH kind, ephemeral — pure declaration. |
| karma card embed | panel | karma_cog.py:40 `_karma_card` | 2 | 2 | FieldsBlock over ProviderRef(karma.record) (points/rank/received/given). No bespoke view class survives. |
| enabled setting | setting | karma/schemas.py:75 (key :78) | 1 | 1 | bool SettingSpec → kernel settings workflow + generated panel. |
| cooldown_seconds setting | setting | karma/schemas.py:87 | 2 | 1 | bounded-int, `_validate_cooldown` is a registered validator ref as-specced; G-5 makes min/max (0..604800) declarative data. |
| daily_cap setting | setting | karma/schemas.py:101 | 2 | 1 | same G-5 class (bounds 1..1000 via `_validate_daily_cap`). |
| reaction_emoji setting | setting | karma/schemas.py:112 | 1 | 1 | str SettingSpec; `_validate_reaction_emoji` is a trivial max-len(64)/type guard → declarable as SettingSpec max_len data, tier-1 (kept 1/1 per spike). |
| react-to-thank listener | listener (gateway) | karma_cog.py:96 `on_raw_reaction_add` | 3 | 2 | NO gateway-listener primitive in §2 as-written → tier-3. G-1 declares {on_raw_reaction_add, handler, gate="setting:karma_enabled AND setting:karma_reaction_emoji"}; handler is thin fetch-and-forward (fast-gate → fetch msg → author checks → route to the same seam) → tier-2. |
| karma.granted event | event | karma_service.py:38 / :178 | 1 | 1 | EventSpec declaration; `bus.emit` lives inside the audited seam. expected_subscribers = server_logging audit fanout. |
| karma table (INV-K) | store | 093_karma.sql:15; utils/db/karma.py:161 `credit_karma` | 1 | 1 | StoreSpec(sole_writer=karma.service, aggregate) → generated sole-writer fence. |
| karma_audit_log table | store | 093_karma.sql:32; utils/db/karma.py:207 `insert_karma_audit` | 1 | 1 | ledger-class StoreSpec; doubles as anti-abuse source (recent_grant_count :112 / grants_given_since :135). |
| karma rank / leaderboard read | game | rank_providers.py:588 (top_karma db/karma.py:58, karma_rank :80) | 2 | 2 | LeaderboardSpec(board_id=karma.top, stat_key=karma.points, metric=max) — decision-10 vocabulary; surfaced via shared !leaderboard cog. |
| help entry | help | (projection) | 1 | 1 | HelpEntrySpec → help-as-projection. ⚠ current surface is via subsystem_registry entry_points, not help_catalogue (see uncertainties) — not a tier change. |

_Subsumed (not separate escape hatches): `build_help_menu_view` (karma_cog.py:74) + the `HubView`-wrapped card (karma_cog.py:91) are the kernel hub-navigation projection of the same read-model card panel (tier-1, generated from `parent_hub="community"`) — folded into the panel/help rows, per the spike's 15-unit ledger._

#### Manifest sketch (§2 grammar)
```python
KARMA_MANIFEST = SubsystemManifest(
    key="karma", display_name="Karma", emoji="✨", category="community",
    parent_hub="community", capabilities=("karma.settings.configure",),
    commands=(
        CommandSpec(name="thanks", aliases=("rep","thank"), kind=PREFIX,
            route=HandlerRef("karma.grant",  # TIER-3: audited seam + 5 typed errors
                justification="domain mutation + typed-error copy"),
            cooldown=(5, 10, "user")),        # G-4: @commands.cooldown, no tier change
        CommandSpec(name="karma", kind=PREFIX, route=PanelRef("karma.card"),
            cooldown=(5, 10, "user")),        # tier-2
        CommandSpec(name="karma add", kind=PREFIX,
            route=HandlerRef("karma.grant")), # TIER-3: same seam alias
        CommandSpec(name="karma", kind=SLASH, route=PanelRef("karma.card")),  # tier-2
    ),
    panels=(PanelSpec(panel_id="karma.card",  # tier-2: FieldsBlock over provider
        body=(BlockSpec(kind="fields", provider=ProviderRef("karma.record")),)),),
    settings=(
        SettingSpec("enabled", "bool", default=True, settings_key="karma_enabled"),   # t1
        SettingSpec("cooldown_seconds", "int", default=3600,   # t2→t1 with G-5 bounds
            validator=HandlerRef("karma.validate_cooldown")),  # G-5: min=0 max=604800
        SettingSpec("daily_cap", "int", default=10,            # t2→t1 with G-5 bounds
            validator=HandlerRef("karma.validate_daily_cap")), # G-5: min=1 max=1000
        SettingSpec("reaction_emoji", "str", default=""),      # t1 (max_len=64 data)
    ),
    events=(EventSpec("karma.granted", audited=True,           # tier-1 declaration
        expected_subscribers=(HandlerRef("server_logging.on_audit_fanout"),)),),
    gateway_listeners=(                                        # G-1: tier-3 → tier-2
        GatewayListenerSpec(gateway_event="on_raw_reaction_add",
            handler=HandlerRef("karma.react_to_thank"),        # thin fetch-and-forward
            gate="setting:karma_enabled AND setting:karma_reaction_emoji"),),
    stores=(
        StoreSpec("karma", sole_writer="karma.service", checkpoint_class="aggregate"),
        StoreSpec("karma_audit_log", sole_writer="karma.service", checkpoint_class="ledger"),
    ),
    game=GameFacet(sessions=(), leaderboards=(                 # NO ChallengeSessionSpec —
        LeaderboardSpec("karma.top", "karma.points", metric="max"),)),  # karma isn't a game
    help=HelpEntrySpec(summary="Thank helpful members with !thanks — peer reputation."),
)
```

#### Tier-3 dispositions
- **!thanks grant seam** (karma_cog.py:210 → karma_service.give:105) — **deliberate escape hatch.** The seam carries genuine domain logic: self-grant guard, per-(giver→receiver) cooldown, per-giver rolling-24h daily cap, atomic credit, given_count bump, immutable audit append, event emit. This is anti-abuse business logic, not choreography — declaring it as data would make the grammar a "worse programming language" (§10.1 risk 5). Stays tier-3 with amendments. The typed-error copy (5 shapes) is §2.7 Result-grammar domain behavior.
- **!karma add** (karma_cog.py:236) — **deliberate escape hatch** (declared alias of the same seam; no separate logic).
- **react-to-thank listener** (karma_cog.py:96) — **grammar gap → reuse G-1 GatewayListenerSpec.** Without a gateway-listener primitive the whole feature is invisible to the manifest (tier-3). With G-1 the wiring + fast-gate become data and the handler is thin extract-and-route to the already-tier-3 seam → tier-2. (Contrast blackjack's reaction-join, which stays tier-3 because its handler carries lobby logic; karma's does not.)

#### Fit numbers
units total = **15** (×N-weighted; !thanks aliases rep/thank fold into one command unit).
tier-1/2 (as-written) = **12 (80%)** → tier-3 = {!thanks, !karma add, react-listener}; 15 − 3 = 12; 12/15 = 80.0%.
tier-1/2 (with amendments) = **13 (87%)** → G-1 lifts the react-listener to tier-2; G-5 lifts cooldown/daily_cap 2→1 (fraction-neutral, already tier-2); remaining tier-3 = {!thanks, !karma add}; 15 − 2 = 13; 13/15 = 86.7% ≈ 87%. Reproduces the spike verbatim.

#### Structural-gap flags
- **Anti-abuse / social-moderation (PRESENT):** cooldown + daily-cap enforced in the seam over audit-log reads (utils/db/karma.py:112, :135). The grammar expresses the *config* (G-5 bounds, tier-1) and the *fence* (StoreSpec sole-writer), but the *enforcement logic* is a deliberate tier-3 escape hatch — correct, not a gap. No new primitive family needed.
- **Leaderboard/records (PRESENT):** fully expressed by the existing `LeaderboardSpec` (tier-2, GameFacet) — read-model over karma.points. No gap.
- **Gateway listener (PRESENT):** react-to-thank — needs **G-1** (reused), which the spike already proposes. No new family.
- **Anti-double-settle / escrow / settlement / turn-loop / session recovery / timers / wait_for (ABSENT):** karma has no currency, no ChallengeSessionSpec, no stateful board, no scheduled loop, no `wait_for`. `game=GameFacet(sessions=())` is deliberate — karma is reputation, not a game. None of the money/session danger primitives apply.

#### MAP → RECONSIDER → SIMULATE → OPTIMIZE
- **RECONSIDER verdict: keep.** Highest-fit subsystem in the lane (80%→87%); the grammar already expresses all config, identities, stores, events, panel, leaderboard, and (with G-1) the listener as declarations. The only irreducible code is one audited mutation seam — exactly the right shape.
- **Optimal new-bot form:** identical manifest; the grant seam remains a single `karma.grant` HandlerRef behind the §2.7 Result grammar. Optional refinement: express reaction_emoji's max-len as declarative `SettingSpec(max_len=64)` data (removes the trivial validator ref) and fold cooldown/daily_cap into G-5 bounds — both already accounted for. Consider a declared `refund_policy`-style knob only if a future downvote lands (schema already reserves signed `delta`).
- **Dependency-layer guess:** this subsystem (community reputation), layered on **L0 runtime** (settings KV, settings_resolution, EventBus, audit fanout) and the **games-core/leaderboard** read layer (rank_providers). No economy layer.
- **Production-grade done-definition:** parity golden must prove — (1) self-grant, disabled-guild, cooldown-active, and daily-cap-hit each raise the correct typed error and write **nothing** (INV-K: no karma/audit row); (2) a successful grant atomically credits recipient total (floored ≥0), bumps giver given_count, appends exactly one audit row, and emits `karma.granted` once; (3) react-to-thank routes through the *same* seam (cooldown/cap/self-guard hold) and silently swallows blocked grants; (4) leaderboard ranks by points DESC, last_received ASC tie-break, excluding non-positive totals.
- **Outperform target:** vs **Carl-bot / MEE6 reputation** — ours adds per-(giver→receiver) cooldown *and* per-giver rolling-24h cap (both bots offer only a flat global cooldown), an immutable audit ledger that *is* the anti-abuse source (no separate cooldown table), and opt-in react-to-thank sharing the exact same guarded seam. Best-in-class ranking pending Lane F.
- **Cross-lane dependency notes:** shares the Lane-C `leaderboard` cog + `rank_providers` karma provider (rank_providers.py:588); emits `karma.granted` consumed by `server_logging` audit fanout; depends on L0 settings widget. No economy/escrow coupling. Audit anchored to this Lane-C karma subsystem.
