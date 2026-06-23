# Ultracode — collision matrix

> **Status:** `reference` — the **collision table** companion to the
> [shared-dependency / ownership map](shared-dependency-ownership-map.md). For each shared
> file/path/service/seam, it names the units that depend on it, the conflict *type*, who may edit it,
> whether it needs serial coordination, and the verification command. Source + merged PRs win.
>
> Use this to answer, before dispatch: *"if I give unit A and unit B to two workers, what do they
> collide on?"* If a row lists both their units under "Units depending on it" and the edit policy is
> **serial**, they cannot run in parallel on that surface.

**Conflict types:** `import-dep` (shared import) · `mutation-path` (shared write seam) ·
`db/schema` (shared table / migration number) · `ui-primitive` (shared view base/nav) ·
`registry/route` (shared registry, help, settings, or pipeline-order route) · `event-contract`
(shared EventBus name/payload) · `test-fixture` (shared test helper) · `docs/SoT` (shared
source-of-truth doc) · `open-PR/claim` (in-flight overlap) · `owner-gated` (product decision).

---

## A. Structural collision surfaces (a fleet must serialize these)

| Shared surface | Conflict type | Units depending on it | Who may edit | Serial? | Verification |
|---|---|---|---|---|---|
| `disbot/migrations/` (next # = **097**) | db/schema | **any** unit adding a table/column | coordinator assigns the number; one worker per number | **YES — guaranteed collision** | `python3.10 scripts/check_migration_collision.py` |
| `disbot/views/base.py` (145 importers) | ui-primitive | ~every cog + view | coordinator only | **YES** | `check_quality.py --full` + `context_map.py` |
| `disbot/views/navigation.py` (42) | ui-primitive | every view package + `hub_children` | coordinator only | **YES** | `check_quality.py --full` |
| `disbot/utils/db/pool.py` (64) | import-dep | every `utils/db/*` + several services | coordinator only | **YES** | `check_quality.py --full` |
| `disbot/core/runtime/subsystem_schema.py` (51) | import-dep | every subsystem that declares a schema + the 2 catalogues | coordinator only | **YES** | `check_architecture.py --mode strict` |
| `disbot/core/events.py` (EventBus, 36) | event-contract | every emitter/subscriber | coordinator only | **YES** | `wiring_map.py --check` |
| `disbot/utils/subsystem_registry.py` (`SUBSYSTEMS`, 29) | registry/route | governance, command→subsystem map, identity contract | coordinator only (one literal) | **YES** | `check_architecture.py --mode strict` |
| `disbot/config.py` (`INITIAL_EXTENSIONS`) | registry/route | every cog (load order) | coordinator only (one list) | **YES** | boot test |
| `disbot/bot1.py` | import-dep | the orchestrator | coordinator only | **YES** | real-Postgres boot |
| `disbot/governance/` (incl. `__init__` re-export) | import-dep + mutation-path | admin, channel, role, help, settings, setup | coordinator only (strict layer order) | **YES** | `check_architecture.py --mode strict` |
| `disbot/core/runtime/message_pipeline.py` + every stage `order` | registry/route | automod, cleanup, counting, chain, image_moderation, xp, rps_tournament, four_twenty, ai, btd6 | coordinator owns the order map; workers edit only *their* stage body | **YES for order** | `test_message_pipeline.py` |

## B. Shared mutation paths (read-only to workers; coordinator edits the signature)

| Service (sole writer) | Conflict type | Units that CALL it | Who may edit the service | Serial? | Verification |
|---|---|---|---|---|---|
| `services/economy_service.py` (19) + `utils/db/economy.py` | mutation-path + db | economy, blackjack, rps_tournament, mining, fishing, farm, casino, treasury, proof_channel, shop | coordinator only | **YES** | `test_no_direct_economy_writes` (INV-F) |
| `services/audit_events.py::emit_audit_action` (21) | mutation-path | every audited mutation across the bot | coordinator only | **YES** | grep callers; payload is public API |
| `services/xp_service.py` + `utils/db/xp.py` | mutation-path + db | xp, community_spotlight, game workflows | coordinator only | **YES** | INV-G AST test |
| `services/game_xp_service.py` + `game_xp` table | mutation-path + db (**9+ readers**) | mining, fishing, creature, creature_battle, farm, skill, title, rank_providers | coordinator only | **YES** | game-xp tests |
| `services/moderation_service.py` + `mod_logs`/`warnings` | mutation-path + db | moderation, automod, image_moderation, security, cleanup | coordinator only | **YES** | `test_no_direct_moderation_writes` |
| `services/settings_mutation.py` + `guild_settings` | mutation-path + db | settings + every settings reader | coordinator only | **YES** | settings invariants |
| `services/channel_lifecycle_service.py` | mutation-path | channel, setup, server_management, resource_provisioning | coordinator only | **YES** | `test_no_direct_channel_mutations` |
| `services/role_lifecycle_service.py` | mutation-path | role, role_grants, setup, server_management | coordinator only | **YES** | `test_no_direct_role_mutations` |

## C. Shared registry / projection routes (registering ≠ editing the mechanics)

| Registry / route | Conflict type | Units that register into it | Edit policy | Serial? | Verification |
|---|---|---|---|---|---|
| `views/hub_children.py` (`discover_hub_children`/`HubChildButton`) | registry/route + ui-primitive | games, community, utility hubs | mechanics = coordinator; a hub binding a thin subclass = 🟡 | mechanics only | hub tests (68) |
| `services/help_catalogue.py` / `help_projection.py` | registry/route | **every** command (visibility) | coordinator only | **YES** | `check_command_reachability.py` + HLP tests |
| `services/setup_sections.py` (`REGISTRY`, 24) | registry/route | every setup section | new section = 🟡 disjoint slug; reorder/registry edit = 🔴 | reorder only | `test_setup_sections.py` |
| `services/diagnostics_service.py` (`register`, 35) | registry/route | many services self-register providers | new provider = 🟡; registry mechanics = 🔴 | mechanics only | diagnostics tests |
| `utils/hub_registry.py` (`HUBS`) | registry/route | hubs (presentation) | one shared tuple → 🔴 on same-hub edits | same-hub | hub-roster consistency test |
| `core/runtime/persistent_views.py` (`_REGISTRY`) | registry/route | every persistent-view subsystem | disjoint `SUBSYSTEM` keys = 🟡; base = 🔴 | base only | identity-contract validation |
| `services/customization_catalogue.py` | registry/route | settings/panel-declaring subsystems | new panel = 🟡; catalogue mechanics = 🔴 | mechanics only | customization drift test |

## D. Event-contract edges (rename/repayload = held-set change)

| Event | Conflict type | Emitter → subscriber | Edit policy | Verification |
|---|---|---|---|---|
| `audit.action_recorded` | event-contract | `audit_events` → `server_logging` (string-key, **no import edge**) | coordinator only | `wiring_map.py --check` |
| `moderation.action_taken` | event-contract | `moderation_service` → `server_logging` ×2 | coordinator only | `wiring_map.py --check` |
| `xp.level_up` | event-contract | `xp_service` → `community_spotlight_cog` | coordinator only | `wiring_map.py --check` |
| `btd6.version_detected` | event-contract | `btd6_patch_service` → `btd6_version_announce` | coordinator (btd6 cluster) | `wiring_map.py --check` |
| `governance.{visibility,cache,cleanup}.*` | event-contract | governance pipelines (**parametrized emit**) → `core/runtime/__init__` | coordinator only — **verify dynamic emit first** | grep `governance/events.py` |
| `economy.balance_changed` (18 emit sites) | event-contract | 6 services emit; no in-repo subscriber (advisory) | coordinator only (public payload) | grep emit sites |

## E. Cluster & cross-unit collisions (units that share a non-service file)

| Shared file/area | Conflict type | Units | Edit policy |
|---|---|---|---|
| `cogs/btd6/` + `views/btd6/` | import-dep | **btd6, btd6_events, btd6_ops, btd6_reference, btd6_strategy, paragon** | the **BTD6 cluster** coordinates among itself — assign the whole cluster to one worker, or partition the shared package edits to the coordinator |
| `utils/db/moderation.py` | db | moderation, cleanup, security (read) | writes only via `moderation_service`; cleanup's direct reads are fine |
| `game_xp` table | db | mining, fishing, creature ×2, farm (readers) | one writer (`game_xp_service`); readers don't collide |
| `economy_audit_log` | db | treasury, farm, fishing, mining, casino, shop (coin legs) | one writer (`economy_service._in_txn`); the cross-domain-transaction contract (Q-0071) |
| `tests/conftest.py` + shared fixtures (`roll_catch` mock, etc.) | test-fixture | any unit touching a consolidated fixture | a fixture edit is shared — coordinator or a dedicated test-infra unit |
| `current-state.md`, `current-state/*.md` | docs/SoT | **all** | workers never edit; coordinator reconciles in Phase 2 |
| `docs/owner/claims/<branch>.md` | (none — by design) | per-session | **one file per claim** → conflict-free (Q-0195); not a collision surface |

## F. In-flight / gated overlaps (reverify live before dispatch)

| Item | Conflict type | Status at 2026-06-23 |
|---|---|---|
| Consolidation/discoverability fleet (U1–U11) | open-PR/claim | Phase 0 rails shipped (#1370/#1371/#1373); Phase 1 not yet fanned out. A new fleet over the same cogs **must `check_lane_overlap.py` + `list_pull_requests` first**. |
| `views/hub_children.py` migration (Games U3) | registry/route | the one remaining "first consolidation" follow-on; serialize on that file during the consolidation fleet. |
| Settings-orphan guard (Phase 0.5) | registry/route | specced, not built — gates the settings/admin fleet units (U9) only. |
| AI / BTD6 feature expansion | owner-gated | gated on stability + provider/provenance + caching + AI-config (S2). |
| Website rollout, dashboard writes, reaction-roles web builder, creature-PvP art | owner-gated | owner/Hermes-executed; not a Claude-fleet lane. |

---

## How to read a parallel-safety question off this matrix

1. Find every row whose "Units depending on it" includes **both** candidate units.
2. If any such row is **serial / coordinator-only**, the two units **cannot both edit that surface in
   parallel** — give the surface to the coordinator (Phase 0/2) and the slices to the workers.
3. If they only co-depend on a **read-only** shared service contract (§ B/D) or **disjoint registry
   keys** (§ C), they are parallel-safe — each owns its own files.
4. Always re-run the live overlap check (§ F) — this matrix is a 2026-06-23 snapshot.
