# Ultracode — input-report reconciliation (2026-06-23)

> **Status:** `audit` — the verification verdict on the attached "SuperBot ownership and dependency
> map (verification report)" that seeded the [Ultracode map](shared-dependency-ownership-map.md). The
> report was built from a **ZIP archive with no `.git`**, so it could not check branch/commit, open
> PRs, or live state — it explicitly self-rated `PARTIAL_MAP_NEEDS_MORE_VERIFICATION`. This doc
> reconciles each claim against **live source @ `c23448f`**. Source + merged PRs win.

**Method.** Four read-only mapping agents re-derived counts (`git ls-files`), wiring
(`scripts/wiring_map.py`), ownership (`docs/ownership.md` + `utils/db/`), and doc state, then this
session reconciled them against the report. Every claim is classed **Confirmed / Corrected / Stale /
Unsupported / New finding**, with evidence.

---

## 1. Confirmed (verified accurate)

| Claim | Evidence |
|---|---|
| **All file counts** — 140 cog files, 54 `*_cog.py`, 189 services, 231 views, 175 utils, 64 `utils/db`, 67 core, 16 governance, 96 migrations, 997 tests, 82 scripts | `git ls-files` exact match on every one. The ZIP counts equalled this HEAD's totals. |
| **Held-set logic** — runtime core, resources core, governance, economy/xp/karma/moderation/settings/lifecycle/help/logging services are shared surfaces requiring coordination | Confirmed via `context_map.py` blast radius; matches the map's § 4. |
| **Sole-writer DB ownership** — economy owns coins + `economy_audit_log`; xp owns `xp`; karma owns `karma`; moderation owns `mod_logs`/`warnings`; settings owns `guild_settings`; lifecycle services own channel/role ops | Verified against `ownership.md` INV-E/F/G/K + AST invariant tests. |
| **`audit.action_recorded` invisible coupling** — emitted by `audit_events.py`, consumed by `server_logging.py` via the bus, with **no import edge** between them | Verified line-exact: `audit_events.py:75` emit, `server_logging.py:1271` `bus.on`, no import in `server_logging`'s import block. |
| **27 catalogued EventBus events** | `wiring_map.py --check` → pass; 27 distinct catalogued events confirmed. |
| **5 disjoint candidates** — ux_lab, general, four_twenty, leaderboard, utility are the safest independent units | Confirmed (the map adds paragon as a 6th 🟢, and notes four_twenty registers pipeline stage 50). |
| **`governance/writes.py` + `events.py` exist** as the governance write/event seam | Confirmed present. |
| **Dynamic-dispatch / registry seams** are invisible to import graphs (setup_sections, resource_provisioning_catalogue, persistent views, help catalogue, diagnostics) | Confirmed + extended (the map adds `hub_children`, `world_registry`, `subsystem_registry`, message-pipeline). |
| **Migrations are serial / collision-prone** | Confirmed — `001`–`096` contiguous, next free 097, `check_migration_collision.py` guards it. |

## 2. Corrected (real but wrong in a way that changes the map)

| Report claim | Correction | Evidence |
|---|---|---|
| **"36 product subsystems"** | **54 cog entry points** (or **41** registered `SUBSYSTEMS`). The report missed **18 newer cogs.** | `git ls-files 'disbot/cogs/*_cog.py'` = 54; `subsystem_registry.REGISTRY` = 41. |
| **"5 architecture_rules YAML"** | **7 YAML** (`canonical_helpers`, `command_reachability_exceptions`, `consistency_exceptions`, `duplicate_allowlist`, `extension_roles`, `layers`, `mutation_owners`) | `ls architecture_rules/`. |
| **`governance/resolution.py`** | The file is **`governance/resolver.py`** — `resolution.py` does not exist. | `ls disbot/governance/`. |
| **BTD6 "no DB module in current branch (tables live in future migrations)"** | BTD6 tables **now exist** — `utils/db/btd6_data.py`, `btd6_sources.py`, `btd6_strategies.py`. | `ls disbot/utils/db/`. |
| **`economy.balance_changed` "owned/emitted by economy service"** (implied single emitter) | True owner, but emitted from **18 sites across 6 services** (economy_service + farm/fishing/mining/shop/skill/treasury workflows). The payload is a shared contract across all of them. | `wiring_map.py` emit-site list. |
| **`services/governance_service.py` framed as the governance home** (consolidation plan) vs **`governance/writes.py`** (report) | Both real, **not in conflict**: `disbot/governance/` is the implementation; `services/governance_service.py` is a **thin legacy re-export shim** (no logic). | read both files. |
| **"creature" (one subsystem)** | **Two cogs** — `creature_cog.py` (catch/collect → `creatures`) and `creature_battle_cog.py` (PvP → `creature_battles`). | `git ls-files`. |
| **`cleanup`/`fishing`/`help` "no view package"** (echoing the nav-map cheat sheet) | Source **has** `views/cleanup/`, `views/fishing/`, `views/help/`. | `ls disbot/views/`. |

## 3. Stale (was true once; superseded by a merged change)

| Report claim | Current truth |
|---|---|
| **"never edit `docs/owner/active-work.md`" (shared ledger)** | `active-work.md` is a **retired tombstone** (Q-0195, 2026-06-22). Claims are now **one-file-per-claim** under `docs/owner/claims/` — *conflict-free*, no shared index. The real (now-gone) collision was the shared append. |
| **`needs-hermes-review`** referenced as a live gate (echoed from the 2026-06-19 fleet plan) | **Retired entirely** (Q-0197, 2026-06-22). Every PR auto-merges on green CI; the only hold is `do-not-automerge`. The map's merge model is born-red card → coordinator merges on green. |
| **Subsystem inventory of 36** (admin … xp) | Missing the 18 cogs shipped since: automod, image_moderation, role_grants, bootstrap_access, farm, casino, treasury, creature, creature_battle, starboard, paragon, hermes, health_maintenance, media_maintenance, btd6_events/ops/reference/strategy. All verified shipped (current-state Recently-shipped: farm #1328, karma #1332, casino #1333, treasury #1334, fishing #1296–#1304, starboard #1259/#1270). |
| **"no `.git` → cannot check branch/PRs"** | Resolved — live repo @ `c23448f`, branch `claude/laughing-bohr-xdlits`, **zero open PRs** at session start. |

## 4. Unsupported / over-cautious (no source backing, or safe to downgrade)

| Report claim | Assessment |
|---|---|
| **"`help.catalogue.drift_detected` (implied) event"** | **No such event exists** in `events_catalogue.KNOWN_EVENTS` or any emit site. Help drift is reported as a `roster_drift` field by `help_catalogue.build_help_catalogue()`, not a bus event. Drop it. |
| **Blanket `NEEDS_COORDINATION` for `deathmatch`, `inventory`, `counting`** | Over-cautious. These own their own table and only call shared services via stable contracts → **🟡 yellow** (independent slice, claim + narrow scope), not orange. The report's own caveat ("errs on the side of NEEDS_COORDINATION") explains the inflation. |
| **`image_moderation` external-API risk as a coordination blocker** | Real dependency, but it routes through `moderation_service` and is a self-contained detector → 🟡 with a provider-abstraction note, not a fleet-wide blocker. |

## 5. New findings (not in the report, material to a fleet)

| Finding | Why it matters |
|---|---|
| **`disbot/views/base.py` = 145 importers (hottest file), `utils/db/pool.py` = 64, `subsystem_schema.py` = 51, `navigation.py` = 42** | The report named the held sets but not their **blast-radius ranking** — this is the serialize-priority order for a coordinator. |
| **EventBus lives at `disbot/core/events.py`** (singleton `bus`), **not** `core/runtime/event_bus.py` as the report guessed | A worker grepping the wrong path misses the real seam. |
| **Only 4 events have in-repo bus subscribers** (audit/moderation/xp.level_up/btd6.version) + 3 parametrized governance subscribers | The other ~21 are advisory — but still public-payload contracts. Narrows what a rename actually breaks. |
| **Message pipeline = 10 stages, fixed `order` (5–80)** is a shared cross-slice contract | A cog refactor that changes its stage order is a cross-slice change the import graph won't show. |
| **`game_xp` is the widest cross-subsystem read (9+ readers)**; **`economy_audit_log` is the money trail for all coin legs** | The two real cross-domain coupling hubs for the idle-game cluster. |
| **The BTD6 sub-cog cluster** (btd6 + 4 sub-cogs + paragon) **shares `cogs/btd6/` + `views/btd6/`** | They must coordinate *among themselves* — a hidden intra-cluster collision the per-cog view misses. |
| **`ownership.md` tables lag** treasury/farm/casino/creature/starboard | The code follows the ownership pattern; the ledger doesn't list them yet (flagged follow-up). |

## 6. Uncertainty to reverify before an Ultracode run

Carried into the map's § 7. The load-bearing ones: the **6 parametrized `emit()` sites** (event name
is a variable — rename-unsafe), the **3 governance events'** dynamic emitters, and the two **doc-lag
follow-ups** (`ownership.md` + `repo-navigation-map.md` cheat-sheet tables missing the newer
subsystems). None blocks a green/yellow fleet; all matter before touching events or the held set.

---

## Verdict

The input report is **a sound, source-honest snapshot whose *logic* holds and whose *counts* were
exact — but whose *subsystem inventory* and *coordination-mechanism references were stale* (36→54
cogs; `active-work.md` / `needs-hermes-review` retired).** Re-grounded against live source, its
held-set + coordination thesis stands and is **operationalized** by the
[shared-dependency / ownership map](shared-dependency-ownership-map.md). Its own headline verdict
(`PARTIAL_MAP_NEEDS_MORE_VERIFICATION`) is now discharged: the verification it asked for is this
session's map + this reconciliation.
