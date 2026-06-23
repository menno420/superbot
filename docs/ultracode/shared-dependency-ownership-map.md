# Ultracode — shared-dependency / ownership map

> **Status:** `reference` — the **parallel-safety partition** of the repo: which units a fleet
> of agents can build at once without colliding, which surfaces must be edited serially, and the
> touch policy for each. It **operationalizes** [`repo-review-map.md`](../repo-review-map.md)
> (Axis B: B-slice vs B-platform) by adding a parallel-safety rating + a held-set touch policy on
> top of it. It is **not** a competing taxonomy and it is **not** a path inventory — it links to
> the existing homes for paths ([`repo-navigation-map.md`](../repo-navigation-map.md)), ownership
> ([`ownership.md`](../ownership.md)), and layering ([`architecture.md`](../architecture.md)).
>
> **Source code + merged PRs win over this file.** This is a dated snapshot — re-verify the
> § "Reverify before an Ultracode run" checklist before dispatching a fleet.

See also: [`README.md`](README.md) (entry point + unit-class contracts) ·
[`conflict-matrix.md`](conflict-matrix.md) (the collision table) ·
[`worker-scope-template.md`](worker-scope-template.md) (the paste-in worker prompt) ·
[`report-reconciliation-2026-06-23.md`](report-reconciliation-2026-06-23.md) (how the input report
was verified).

---

## 1. Status &amp; trust model

| Field | Value |
|---|---|
| **Date** | 2026-06-23 |
| **Branch / commit inspected** | `claude/laughing-bohr-xdlits` @ `c23448f` (parent `e3db40c`, #1373) |
| **Open PRs checked** | `list_pull_requests(state=open)` → **none** at session start (only this session's PR #1374) |
| **Claims checked** | `docs/owner/claims/` → only this session's claim; `check_lane_overlap.py` clean |
| **Verification method** | 4 read-only mapping agents over **live source** (`git ls-files`, `scripts/context_map.py`, `scripts/wiring_map.py`, `docs/ownership.md`, CodeGraph). Counts are `git ls-files` exact. |
| **Input report status** | The attached ZIP-based "ownership and dependency map" was treated as a **hypothesis set** and reconciled — see [`report-reconciliation-2026-06-23.md`](report-reconciliation-2026-06-23.md). Verdict: counts exact, held-set logic sound, **subsystem inventory stale** (36→54). |

**Truth precedence (highest first):** (1) source + merged PRs · (2) binding docs (`architecture.md`,
`ownership.md`, `runtime_contracts.md`) · (3) `current-state.md` + `current-state/*.md` · (4) active
plans/folios · (5) this map · (6) the input report / old chats.

**Known limitations.** Import graphs (Grimp/CodeGraph) are blind to the three dynamic seams in § 5.6
(EventBus string keys, registry callbacks, parametrized `emit`/`on`). Six `emit()` sites pass the
event name as a **variable** (not a literal) and are flagged `unverified` in § 7. The per-unit
ratings in § 6 are a *coordinator's starting partition*, not a guarantee — a worker that widens its
scope past its slice downgrades its own rating.

**Reverify before an Ultracode run** (the snapshot decays): re-run `list_pull_requests` (open +
recently-merged) **and** `scripts/check_lane_overlap.py <each lane scope>` (the #1133/#1128 lesson —
the claim ledger alone is necessary but insufficient); re-run `scripts/wiring_map.py --check`;
confirm no new migration landed (the next free number moves); confirm the held-set file list in § 4
still matches source (`scripts/context_map.py` importer counts drift as the bot grows).

---

## 2. Ultracode unit classes

Every unit a coordinator dispatches is one of these classes. The contract per class:

| Class | Rating | A worker MAY edit | A worker may only READ | Needs coordinator | Serial? | Required verification |
|---|---|---|---|---|---|---|
| **Independent vertical slice** | 🟢 green / 🟡 yellow | its own cog(s), `views/<x>/`, `services/<x>_*.py`, `utils/<x>/`, `settings_keys/<x>.py`, its tests | the shared services it *calls* (economy/xp/game_xp/moderation contracts), `views/base.py`, `utils/db/<other>` | no (green) / claim-only (yellow) | no | `check_quality.py --full` + `check_architecture.py --mode strict` |
| **Shared platform unit** | 🔴 red | nothing — **coordinator-owned** | all of it | **yes** | yes (one PR) | full suite + `context_map.py` blast-radius review |
| **Serial migration / schema unit** | 🔴 red | one migration at the **coordinator-assigned** next number | existing migrations | **yes** (assigns the number) | **yes — guaranteed collision otherwise** | `check_migration_collision.py` + real-Postgres boot |
| **Tooling / docs unit** | 🟢/🟡 | `scripts/`, `.github/`, `docs/`, `.claude/skills/` (file-disjoint from runtime) | runtime source | no | no | the relevant checker + `check_docs.py --strict` |
| **Blocked / gated unit** | 🔴 red | nothing until the gate clears | all of it | **yes (owner)** | n/a | n/a — do not dispatch |
| **Unsafe / unknown unit** | ⚠️ | nothing — verify first | all of it | **yes** | n/a | resolve the § 7 unknown before rating |

**Rating legend (used in § 6):** 🟢 **green** = independently executable (claim only). 🟡 **yellow** =
safe with a claim + narrow single-slice scope. 🟠 **orange** = coordinator-required (touches a held
set, a registry, or a shared event contract). 🔴 **red** = serial / shared platform / gated.

**The one collision rule that governs everything:** *two agents must never edit the same file.* The
partition below is built so a green/yellow fleet doesn't, and so every red surface funnels to one
worker.

---

## 3. The coordination model (born-red → coordinator merges)

This generalizes the two proven task-specific fleet plans
([`ultracode-fleet-plan-2026-06-19.md`](../planning/ultracode-fleet-plan-2026-06-19.md),
[`consolidation-fleet-plan-2026-06-23.md`](../planning/consolidation-fleet-plan-2026-06-23.md))
into a task-independent contract:

1. **Phase 0 (rails) — coordinator, serial.** Build the shared primitive/guard every worker
   converges on *first* (e.g. `views/hub_children.py` for the consolidation run). A convergence
   refactor is only safe when the shared pattern already exists.
2. **Phase 1 (leaves) — fleet, parallel.** Each worker owns ONLY its unit's files (§ 6) and follows
   the [worker-scope template](worker-scope-template.md). Workers **leave their PR born-red** (the
   session-gate holds it; `scripts/check_session_gate.py`).
3. **Phase 2 (reconcile) — coordinator, serial.** Inspect each red PR, fix misses, merge **in any
   order** (file-disjoint units don't conflict), each re-validated green on the **latest `main`
   head**, then reconcile `current-state.md` + sector files.

**Current truth on the shared-write hazards (do not inherit the input report's drift):**
- Claims are **one-file-per-claim** under `docs/owner/claims/` (Q-0195) — *conflict-free*, no shared
  index. (The fleet plans' "never edit `active-work.md`" line is **stale** — that file is a retired
  tombstone.)
- The merge gate is **born-red card → coordinator merges on green CI**. There is **no
  `needs-hermes-review` gate** (retired, Q-0197). The only manual hold is the `do-not-automerge`
  label (Q-0114).
- Workers still **never** edit the shared ledgers (`current-state.md`, `current-state/*.md`) or the
  held set (§ 4).

---

## 4. Shared platform surfaces (the held set — 🔴 coordinator/serial)

These are the B-platform surfaces many slices depend on. **Blast radius** = `scripts/context_map.py`
importer count (the number of files that import the key file). A fleet must funnel edits to **one**
worker (or strictly disjoint hunks) on each. Ranked by collision risk.

| # | Surface | Path(s) | Contract doc | Blast radius | Why held / touch policy |
|---|---|---|---|---|---|
| 1 | **Migrations numbering** | `disbot/migrations/` (96 files, `001`–`096`, next free **097**) | INV-I; `check_migration_collision.py` | every new migration grabs the *same* next number | **Guaranteed collision.** Coordinator assigns each migration's number; serialize creation. CI tests `refs/pull/N/merge`, so a collision reddens CI even when branch-local quality passes (#1279 renumbered 4×). |
| 2 | **Base views** | `disbot/views/base.py` (`BaseView`/`HubView`/`PersistentView`/`send_panel`) | `architecture.md` view rules; `helper-policy.md §3.5` | **145 importers — hottest file in repo** | Any signature/behavior change is repo-wide. Serialize absolutely; workers read-only. |
| 3 | **DB pool** | `disbot/utils/db/pool.py` | `architecture.md` (`utils/db/` = asyncpg only) | **64 importers** | Owns the asyncpg pool + primitives; every `utils/db/*` submodule depends on it. |
| 4 | **Subsystem schema** | `disbot/core/runtime/subsystem_schema.py` | `runtime_contracts.md` | **51 importers** | The `SubsystemSchema` declaration walked by the provisioning + customization catalogues; shape change ripples to every subsystem that declares one. |
| 5 | **Navigation** | `disbot/views/navigation.py` (back buttons, `BackTarget`) | `architecture.md`; `helper-policy.md` (no 2nd nav module w/o ADR) | **42 importers** | The canonical back-button seam; `hub_children` + every view package depend on it. |
| 6 | **EventBus** | `disbot/core/events.py` (singleton `bus`), allowlist `disbot/core/events_catalogue.py` | `runtime_contracts.md §2`; INV-A | **36 importers** | Singleton + dispatch table; renaming/repayloading an event breaks all subscribers (§ 5). The catalogue allowlist is append-only (🟡). |
| 7 | **Subsystem registry** | `disbot/utils/subsystem_registry.py` (`SUBSYSTEMS`/`REGISTRY` literal, **41 entries**) | `architecture.md` identity contract; INV-H | **29 importers** | One shared dict literal + the identity-contract anchor; frozen at startup. Two workers adding/editing a subsystem collide on the literal. |
| 8 | **Cog load order** | `disbot/config.py` (`INITIAL_EXTENSIONS`, 54 cogs; `bootstrap_access_cog` **first**) | `repo-navigation-map.md` entry rows | single shared list | Adding a cog = appending to one shared list → collision. Order is load-significant (the access gate loads first). |
| 9 | **Process entrypoint** | `disbot/bot1.py` | `runtime_contracts.md`; INV-J | the one orchestrator | Global checks, governance gate, `_load_cogs`, identity-contract validation at startup. Serialize. |
| 10 | **Governance package** | `disbot/governance/` (16 files; `writes.py`=`GovernanceMutationPipeline`, `resolver.py`, `events.py`; `__init__.py` re-exports) | `ownership.md` INV-E; strict internal layer order | `__init__` re-export `__all__` | Strict layer order (`models→events→cache→dependency→resolver→cleanup→execution→snapshot→health→writes`). `services/governance_service.py` is a **thin legacy re-export shim** — not a second implementation. Treat the whole package as one serial unit. |
| 11 | **Runtime core** | `disbot/core/runtime/` (39 modules: `message_pipeline`, `panel_manager`, `session_manager`, `interaction_router`, `persistent_views`, `command_access`, `tasks`, …) | `runtime_contracts.md` (all §) | `message_pipeline` 18, `persistent_views` 14, `panel_manager` 6 | Must **not** import cogs/services. Stage ordering + context dataclasses shared by every message-handling slice. |
| 12 | **Resources core** | `disbot/core/resources/` (6 files) | `runtime_contracts.md` | low (`discovery` 5, rest ≤2) | Small, low-traffic; a single worker per file is fine, but it's core-layer (no cogs/services). |
| 13 | **Shared mutation services** (signatures) | `services/economy_service.py` (19), `services/audit_events.py` `emit_audit_action` (21), `services/xp_service.py`, `services/game_xp_service.py`, `services/moderation_service.py`, `services/settings_mutation.py`, `services/channel_lifecycle_service.py`, `services/role_lifecycle_service.py` | `ownership.md` (INV-E/F/G/K) | 11–21 each | **Read-only to workers.** These are the sole writers of their tables (§ 5.5) and emit the cross-subsystem events. A signature/payload change is a coordinator-only, serial event. |
| 14 | **Help projection/catalogue** | `services/help_projection.py`, `services/help_catalogue.py`, `cogs/help/route.py` | HLP invariants; `check_command_reachability.py` | projection drives every command's visibility | Changing projection affects *user-facing help for the whole bot*. Coordinator-only. |
| 15 | **Server logging** | `services/server_logging.py` (+ subscribes `audit.action_recorded`, `moderation.action_taken`) | `ownership.md` | bus subscriber | No DB writes, but the embed schema is coupled to the moderation/audit event payloads. |
| 16 | **Registries** (register-into is 🟡, edit-the-mechanics is 🔴) | `utils/hub_registry.py`, `views/hub_children.py`, `core/runtime/persistent_views.py`, `services/setup_sections.py` (24 importers), `services/resource_provisioning_catalogue.py`, `services/diagnostics_service.py` (35), `services/customization_catalogue.py`, `services/world_registry.py` | per-registry | varies | *Registering a new entry* (a disjoint key) is yellow; *editing the registry mechanics/base* is red. Several register into one **shared literal** (`SUBSYSTEMS`, `HUBS`, `INITIAL_EXTENSIONS`) — those literals are the collision points even though the op is "additive." |
| 17 | **Shared utils / settings_keys** | `utils/helpers.py` (do-not-add policy), `utils/db/__init__.py` (re-export), `utils/settings_keys/__init__.py` (aggregator) | `helper-policy.md` | 12 / re-export | Per-domain files (`settings_keys/<x>.py`, `utils/db/<table>.py`) are 🟢 disjoint; the **aggregator `__init__` files** are 🟡 shared. |
| 18 | **Architecture rules / checkers / CI** | `architecture_rules/*.yaml` (7), `scripts/check_*.py` (29), `.github/workflows/code-quality.yml` (the required check) | `.claude/CLAUDE.md` CI-parity | per-file | The YAMLs are the **only legal bypass channel** (add a known violation there, never suppress the check). Per-file disjoint edits fine; `layers.yaml`/`mutation_owners.yaml`/`code-quality.yml` are serialize-on-edit. |

> **Layer fences a fleet must never break** (`check_architecture.py --mode strict`): **`services/ →
> views/` is the one rule with ZERO tolerance for new violations.** `views/ → cogs/` and cross-cog
> imports are also forbidden. All mutations go through the domain `*_mutation.py`/`*_service.py`/
> `*_workflow.py`; never `pool.execute()`/`conn.execute()` outside `utils/db/`; always
> `emit_audit_action()` on auditable mutations; always `settings_keys` constants, never raw strings.

---

## 5. Runtime wiring (the import-graph-invisible edges)

A static import graph misses the three dynamic seams below. **A refactor that renames an event,
reorders a pipeline stage, or changes a registry key breaks couplings no import graph shows** — grep
the string, never trust a blast-radius number alone.

### 5.1 EventBus events (27 catalogued; only 4 have in-repo bus subscribers)

`scripts/wiring_map.py --check` → pass. The **only** events with an in-repo `bus.on` subscriber:

| Event | Emitter | In-repo subscriber |
|---|---|---|
| `audit.action_recorded` | `services/audit_events.py` (`emit_audit_action`) | `services/server_logging.py::_on_audit_action` |
| `moderation.action_taken` | `services/moderation_service.py` | `server_logging.py` (`_on_moderation_action` + `_on_moderation_action_public`) |
| `xp.level_up` | `services/xp_service.py` | `cogs/community_spotlight_cog.py::_on_level_up` |
| `btd6.version_detected` | `services/btd6_patch_service.py` | `services/btd6_version_announce.py::_on_version_detected` |
| `governance.{visibility,cache,cleanup}.*` | governance pipelines (parametrized — see § 7) | `core/runtime/__init__.py` (`_on_visibility_changed`/`_on_cache_invalidated`/`_on_cleanup_changed`) |

The other ~21 events (`economy.balance_changed` — **18 emit sites across 6 services** — `xp.awarded`,
`karma.granted`, `settings.changed`, the lifecycle/`*.changed` events, `game_xp.*`) have **no in-repo
bus subscriber** but are advisory contracts (metrics / future consumers). **Renaming or re-payloading
any of them is still a held-set change** — treat the event name + payload as a public API.

> **Verified invisible coupling (the canonical case):** `audit.action_recorded` is emitted by
> `audit_events.py` and consumed by `server_logging.py` purely via the **string bus key** —
> `server_logging` does **not** import `audit_events`. No Grimp import edge, no CodeGraph call edge
> connects them. Same shape for `moderation.action_taken`.

### 5.2 Message-pipeline stages (10 stages; order is a shared contract)

`core/runtime/message_pipeline.py` is the single `on_message` orchestrator; each cog `register()`s a
stage with a fixed `order` int in its `cog_load`. **Reordering or renaming a stage is a cross-slice
change** (pinned by `test_message_pipeline.py::test_registered_stage_orders_are_distinct`):

| order | tier | stage | registered by | short-circuits |
|---|---|---|---|---|
| 5 / 10 / 15 / 20 / 25 | auto-mod (may delete) | automod · cleanup · counting · chain · image_moderation | the 5 cogs of the same name | on delete |
| 30 / 40 | rewards | xp · rps_tournament | `xp_cog` · `rps_tournament_cog` | no |
| 50 | passive | four_twenty (🍃) | `four_twenty_cog` | no |
| 70 / 80 | conversational | ai_nl · btd6_assistant | `ai_cog` · `btd6_cog` | on mention / on handle |

A worker editing one of these cogs may change *its stage's body* but **must not change its `order`**
(coordinator decision — it's the shared ordering contract).

### 5.3 Sole-writer DB ownership (verified vs `ownership.md`)

Each table has exactly one writer service (the audited seam). The cross-table reads are the
coordination signal:

| Table(s) | Sole writer | Audited | Cross-subsystem note |
|---|---|---|---|
| `economy`, `economy_audit_log`, `job_progress` (+ `xp.coins` col) | `economy_service` (INV-F) | `economy_audit_log` append-only | **`economy_audit_log` is the money trail for ALL coin legs** — treasury/farm/fishing/mining/casino/shop route their coin leg through `economy_service.*_in_txn`. |
| `xp` | `xp_service` (INV-G) | INV-G | `xp.coins` read widely, write-fenced to economy. |
| `game_xp` | `game_xp_service` | advisory | **Widest cross-subsystem read** — 9+ readers (mining, fishing, creature ×2, farm, skill, title, rank_providers). Shared progression track. |
| `karma`, `karma_audit_log` | `karma_service` (INV-K) | yes | audit log doubles as anti-abuse read. |
| `warnings`, `mod_logs` | `moderation_service` | yes | one writer, but **fanned into** by automod/image_moderation/security (they route *through* it). |
| `guild_settings`, `settings_mutation_audit` | `settings_mutation` | yes | universal config; read everywhere via `settings_resolution`. |
| `governance_audit_log`, `subsystem_visibility`, … | `governance/writes.py` (INV-E) | yes | one bypass carve-out: `execution.py::_audit_internal_bypass`. |
| game tables (chain/counting/deathmatch/mining_*/fishing_*/rps/creatures/creature_battles/chicken_farm) | per-game service or direct `utils/db/games/<x>.py` | game-specific | coin/xp legs always via the shared services above. |
| `operational_health_findings` | `health_findings_service` | partial | sole writer. |
| `help_overlay` | `help_overlay_mutation` | yes | presentation-only; import-fenced from admission. |
| `treasury`, `starboard` | `treasury_service`, `starboard_service` | config-audited | newer subsystems — **absent from `ownership.md` tables** (drift, § 7). |

### 5.4 Registries / dynamic-dispatch seams

`persistent_views._REGISTRY` (keyed by `SUBSYSTEM`), `views/hub_children.discover_hub_children` +
`HubChildButton`, `hub_registry.HUBS`, `subsystem_registry.SUBSYSTEMS`, `setup_sections.REGISTRY`,
`resource_provisioning_catalogue`, `diagnostics_service.register(name, provider)`,
`customization_catalogue`, `world_registry.register_world_entry`, and `message_pipeline.register`.
**Registering a disjoint key is 🟡-safe; editing the registry base/mechanics is 🔴.**

---

## 6. Per-unit parallel-safety map (all 54 cogs)

Rating per § 2. **Paths are not restated here** — the full slice path set is the
[`repo-navigation-map.md` cheat sheet](../repo-navigation-map.md) (⚠️ its table is currently stale —
missing the 18 newer cogs; § 7). This table owns the **parallel-safety rating + shared-dep edges**,
keyed by the verified owned service/table.

### 6a. 🔴 red — held-set front-ends (the cog is editable, but its service is a shared held set)

| Unit | Owned service / surface (held) | Why red | Worker boundary |
|---|---|---|---|
| **moderation** | `moderation_service` + `mod_logs`/`warnings` | sole moderation writer; automod/image_mod/security/cleanup delegate here; emits 2 subscribed events | coordinator-only on the service; cog UI work is 🟡 *if* it doesn't touch the service |
| **settings** | `settings_mutation` + `guild_settings` | universal config; every subsystem reads it; `settings.changed` | coordinator-only |
| **xp** | `xp_service` + `xp` table; pipeline stage 30; `xp.*` events | sole xp writer; community_spotlight subscribes `xp.level_up` | coordinator-only on service; **don't change stage 30** |
| **help** | `help_catalogue`/`help_projection` | decides visibility of *every* command | coordinator-only |
| **logging** | `server_logging` | embed schema coupled to moderation/audit event payloads | coordinator-only |
| **bootstrap_access** | `core/runtime/command_access` | the access gate; **loads first** in `INITIAL_EXTENSIONS` | coordinator-only |

### 6b. 🟠 orange — coordinator-required (touches a held set, registry, lifecycle service, or a shared cluster)

| Unit | Shared dep that forces coordination |
|---|---|
| **economy** | `economy_service`/`economy_audit_log` held set (19 importers; the money trail) — cog/views are 🟡 but service is 🔴 |
| **setup** | `setup_operations` + `setup_sections` registry + channel/role lifecycle services + governance (heaviest coupling) |
| **server_management** | composes setup + diagnostics + lifecycle services (a hub over held sets) |
| **channel** | `channel_lifecycle_service` (held) + governance + `resource_provisioning` |
| **role** | `role_lifecycle_service` (held) + governance + reaction-role/automation services |
| **admin** | governance capability checks (no own table; gates features across subsystems) |
| **diagnostic** | `diagnostics_service` provider **registry** (35 importers) |
| **games** / **community** | hub routers that render children via the shared `hub_children` + `hub_registry` |
| **btd6**, **btd6_events**, **btd6_ops**, **btd6_reference**, **btd6_strategy** | **shared-package cluster** — all 5 share `cogs/btd6/` + `views/btd6/` (so they coordinate *among themselves*); `btd6` also registers pipeline stage 80 and is under the BTD6 feature-expansion gate |
| **ai** | the AI-platform service family + pipeline stage 70; under the AI feature-expansion gate (§ "gated") |

### 6c. 🟡 yellow — independent slice, safe with a claim + narrow scope

Own their table / in-memory state and only *call* shared services via stable contracts:

`blackjack` · `automod`¹ · `image_moderation`¹ · `casino`² · `chain`¹ · `cleanup`¹ · `counters` ·
`counting`¹ · `creature` · `creature_battle` · `deathmatch` · `farm`³ · `fishing` · `inventory` ·
`karma` · `mining` · `proof_channel` · `role_grants` · `rps_tournament`¹ · `security` · `starboard` ·
`treasury`³ · `welcome` · `community_spotlight`⁴ · `health_maintenance`⁵ · `media_maintenance`⁵ ·
`hermes`⁶

¹ registers a message-pipeline stage — edit the body, **never the `order`** (§ 5.2). · ² writes via
`game_wager_workflow`→`game_state` (no `casino_service.py` exists). · ³ coin legs via
`economy_service` (read-only contract). · ⁴ read-only + subscribes `xp.level_up`. · ⁵ background
maintenance loop (calls a held service read-only). · ⁶ operator info surface, no own table.

### 6d. 🟢 green — independently executable (claim only)

| Unit | Why green |
|---|---|
| **ux_lab** | zero-write, CI-fenced (`test_ux_lab_zero_write.py`) |
| **general** | reads static `data/json/general_content.json`; no state |
| **utility** | ping/uptime; no state |
| **leaderboard** | pure read-only queries across tables |
| **paragon** | pure BTD6 calculator, zero DB (but shares `views/btd6/` → coordinate with the btd6 cluster on that package) |
| **four_twenty** | passive novelty; registers pipeline stage 50 — **don't change the order** |

### Gated / blocked (🔴 — do not dispatch until the gate clears)

- **AI tools that write / cost money / call external / add UI** — the AI feature-expansion gate
  (`current-state/S2-btd6.md`; Q-0048 lifts only read-only+deterministic tools). Affects `ai`, parts
  of `btd6`.
- **Owner-gated product lanes** — reaction-roles web builder, creature-PvP art (Q-0187), dashboard
  writes / control-API (security review), website rollout. (`current-state/S1`, `S5`.)
- **Off-limits refactors** — ADR-001 (no Redis/external state), ADR-002 (game state is **not**
  restart-safe by design — don't "fix" it), Q-0190 (no feature-gating monetization).
- **Owner-only files** — `.claude/CLAUDE.md`, `.claude/settings.json` (Q-0106 — propose via router,
  never self-edit).

---

## 7. Unknowns — reverify before an Ultracode run

| Unknown | Why it matters | Resolve by |
|---|---|---|
| **Parametrized `emit()`/`on()` sites** | 6 emit sites pass the event name as a **variable** (`participation_mutation.py:653`, `ai_instruction_mutation`, `ai_orchestration_mutation`, `ai_policy_mutation:375`, `security_service:290`, `governance/events.py:34`) + 1 parametrized subscriber (`live_update_scheduler.py:96`). Import graphs + `wiring_map` can't resolve these. | grep the computed-key call sites; confirm the dynamic event names before renaming any event. |
| **`governance.*` event emitters** | The 3 governance events have `core/runtime` subscribers but emitters the tool can't resolve (parametrized forwarder in `governance/events.py`). | confirmed dynamic, not dead — do not treat the governance subscribers as orphans. |
| **`ownership.md` table lag** | `treasury`, `farm`, `casino`, `creature`, `starboard` have shipped sole-writer services but are **absent from `ownership.md`'s tables** (only `fishing` of the new set is listed). Code follows the pattern; the ledger lags. | a follow-up `ownership.md` reconciliation (out of this session's scope — flagged in the reconciliation doc). |
| **`repo-navigation-map.md` cheat-sheet lag** | the subsystem cheat-sheet **table** lists ~36 and is missing the 18 newer cogs; marks `cleanup`/`fishing`/`help` as view-less (source has the view packages). | a follow-up nav-map reconciliation; until then, this map's § 6 is the current 54-unit inventory. |
| **CodeGraph `dead-unresolved`** | ~100% false-positive in this repo for command/event handlers (CLAUDE.md). | never treat a `@commands.command`/`@bot.event`/registered stage as dead. |

---

## 8. What a coordinator must hand each worker

Per the [worker-scope template](worker-scope-template.md): the assigned unit + its **exact allowed
file set** (from § 6 + the cheat sheet), the **read-only shared files** it may depend on (§ 4), the
**forbidden** held set, the active gates (§ 6 gated), the two required green checks
(`check_quality.py --full` + `check_architecture.py --mode strict`), the born-red session-card rule,
and the stop conditions. The coordinator owns Phase 0 + Phase 2; workers own only their Phase-1 leaf.
