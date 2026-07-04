# Lane G — Foundations & Runtime Skeleton, L0 (Axis 1)

> **Status:** `audit` — the Lane G foundation audit. The **L0 substrate** under all 43 subsystems and
> the first layer the new bot builds. Read-only: no `disbot/` change, no new-repo code. Every
> foundation claim cites `file:line`; uncertain rows are marked `⚠ unverified`. Method + contract:
> [`../BRIEF.md`](../BRIEF.md) · [`../PARTITION.md`](../PARTITION.md). Target architecture:
> [`rebuild-design-spec-2026-07-02.md`](../../../../planning/rebuild-design-spec-2026-07-02.md)
> §1/§3/§6/§9 · linchpin evidence:
> [`rebuild-linchpin-validation-2026-07-02.md`](../../../../planning/rebuild-linchpin-validation-2026-07-02.md).
>
> **Prepared:** 2026-07-02 (Opus 4.8 ultracode). Source code wins over docs; where they conflict it is
> recorded. Citations were verified first-hand against live source this session; a background
> fan-out (10 area maps + external benchmarks + adversarial citation-verify) corroborates and is
> folded into §5 (benchmark) and the verification notes.

---

## 1. L0 executive summary

**What L0 is.** The runtime skeleton every subsystem sits on: the bootstrap (`disbot/bot1.py`), the
env/config leaf (`disbot/config.py`), the extension loader, and the platform primitives in
`disbot/core/` (event bus, lifecycle state machine, managed-task supervisor, health/observability,
DB/state init, the interaction/panel/settings engines the manifest would generate into) plus the
identity registry in `disbot/utils/subsystem_registry.py`. In the rebuild this becomes the `sb/`
kernel — `spec` + `namespace` (leaves), `kernel/{observability,events,lifecycle,authority,workflow,
settings,interaction,help,diagnostics,ai}`, `adapters`, `app` (design spec §1.1) — built K0–K10
**before any feature** (§9.1).

**The headline finding: the current L0 is unusually strong in its *primitives* and unusually weak in
its *composition root*.** Six primitives are production-grade and should be **preserved
field-for-field**: the lifecycle state machine (`core/runtime/lifecycle.py`), the managed-task
supervisor (`core/runtime/tasks.py`), the publish-accepted EventBus (`core/events.py`), the
startup-outcome recorder (`core/runtime/startup_outcome.py`), the health/probe server
(`healthserver.py`), and the asyncpg-only DB seam (`utils/db/`). The discipline around them is real:
the **only** bare `asyncio.create_task` in all of `disbot/` production code is `bot1.py:1005` (grep
verified) — the codebase already lives by INV-K (`docs/architecture.md:136`). Against that, the
**composition root itself is the debt**: `bot1.py` is a **1463-line module** mixing logging config,
6 event handlers, the typo-resolution command UX, the cog loader, health-bind coordination, **seven
sequential catalogue/manifest builds**, the lifecycle close-driver, and exit-code policy. And two things the
new bot's own directive names are **structurally absent today**: (a) there is **no dynamic cog
discovery** — cogs are a **hardcoded 60-entry list** (`config.py:79-143`); (b) there is **no central
namespace reservation** — identity collisions are caught *reactively* (a boot-time `validate_registry`
freeze + an advisory async identity cross-check), which is exactly why two command-name collisions
crash-looped production (Q-0211 `give`, BUG-0030 `dock`/`sail`; design spec §0).

**The L0 disposition in one line:** *preserve the primitives, extract the composition root into
kernel engines, replace the hardcoded loader with manifest-driven discovery, and add the one thing
that does not exist yet — a central pre-boot namespace registry that turns the crash-loop class into
a red deploy.* Grammar-fit evidence says this is the right bet: the operator/config band (the bulk of
the surface) measures **97%** tier-1/2 fit, overall **85% with six amendments** (linchpin validation
§2.2) — i.e. the kernel-generated foundation carries the vast majority of the real surface, and the
escape hatch is the priced-in minority.

**Verdict for the capstone's L0 layer: GO — the foundation is buildable as designed, K0–K10, with
the amendments already folded into the spec.** The specific L0-blocking risks are named in §10 (the
loader failure-mode "INTERNAL-hiding" ambiguity, config validation coverage, and the
observability-leaf relocation that dissolves the one live layer break).

---

## 2. Current foundation map (source-cited)

Every row verified against live source this session. `disbot/` paths are relative to the repo root.

### 2.1 Bootstrap — `disbot/bot1.py` (1463 lines)

| Concern | Where | Note |
|---|---|---|
| Structured logging setup (JSON via `python-json-logger`, plain-text fallback), `boot_id` on every record | `bot1.py:29-60` | Module-level side effect at import; `install_boot_id_logging` (`services/runtime.py`) |
| Webhook reporter init (optional) | `bot1.py:65-69` | `WebhookReporter(config.WEBHOOK_URL)` or `None` |
| `commands.Bot` construction + intents | `bot1.py:80-94` | `message_content`+`members` intents; `max_messages=5000`; `case_insensitive=True`; `help_command=None` |
| SIGTERM handler → lifecycle | `bot1.py:97-103`, `:184` | Routes to `lifecycle.request_shutdown` (records intent only) |
| `on_ready` (anchors restore, role-menu reattach, scheduler, RUNNING transition, one-shot health + command-sync) | `bot1.py:312-339` | Reconnect-safe one-shot guards (`_startup_health_reported`, `_commands_auto_synced`) |
| `on_interaction` → router | `bot1.py:349-353` | `interaction_router.dispatch(interaction)` |
| `on_command` / `on_command_completion` / `on_command_error` | `bot1.py:356-603` | latency metric + slow-path record; the fuzzy typo re-dispatch UX (`:541-586`) |
| `before_invoke` governance guard | `bot1.py:633-674` | Enforces subsystem visibility per command (`resolve_command_policy`) |
| `!force` admin channel-bypass | `bot1.py:682-690` | |
| Fuzzy command-resolution cache | `bot1.py:448-479` | keyed on `len(bot.all_commands)` so it rebuilds if cogs (un)load |
| `_load_cogs` | `bot1.py:698-737` | per-extension `try/except`; failed → subsystem INTERNAL (§2.3) |
| Lifecycle close-driver (SIGTERM + `!restart` → `bot.close()`, bounded, `os._exit` fallback) | `bot1.py:794-931` | LP-4 fast lock handoff at `:864-865` |
| `main()` — the boot sequence | `bot1.py:934-1311` | detailed in §2.2 |
| `finally` teardown (drain tasks, release lock, close DB + reporter, terminal phase) | `bot1.py:1312-1409` | runs on every exit path |
| `__main__` exit-code policy (`RESTART_EXIT_CODE=42`, 429 backoff) | `bot1.py:1418-1463` | |

### 2.2 The boot sequence — `bot1.main()` (`bot1.py:934-1311`)

Ordered, with citations:

1. `validate_registry()` → freeze SUBSYSTEMS, abort on `GovernanceError` (`bot1.py:938-943`).
2. `await db.init()` — connect pool + **run migrations** (`bot1.py:945`).
3. `await _runtime.acquire_lock_or_exit()` — single-replica runtime lock; `SystemExit(0)` if another
   replica holds it (`bot1.py:953`).
4. `await runtime.setup()` — wire EventBus subscriptions + runtime registries (`bot1.py:958`).
5. `message_pipeline.setup(bot)` (`:959`); `server_logging.setup(bot)` (`:967`); `reporter.start()` (`:969`).
6. `async with bot:` → spawn `runtime_lock_heartbeat` (`:986`), `health_server` + **bind-ready gate**
   (wait ≤5 s; a bind failure aborts startup, `:993-1031`), `game_state_cleanup.install()` (`:1039`),
   back-to-help wiring (`:1048`), `session_gc.start()` (`:1053`), `process_memory_sampler` (`:1059`),
   `lifecycle_close_driver` (`:1071`), `spawn_scheduler(bot)` (`:1090`).
7. `await _load_cogs()` (`:1092`).
8. Identity-contract cross-check — `validate_identity_contract(bot)`; **advisory unless STRICT**, then
   `SystemExit(1)` on fatal findings (`bot1.py:1110-1172`).
9. **Seven catalogue/manifest builds**, each in its own `try/except`, all non-fatal:
   `command_surface_ledger` (`:1183`), `panel_manifest` (`:1200`), `command_manifest` (`:1217`),
   `command_descriptions` (`:1233`), `settings_registry` (`:1243`), `customization_catalogue`
   (`:1260`), `resource_provisioning_catalogue` (`:1277`) (six are tracked in
   `startup_outcome.KNOWN_PHASES`, `startup_outcome.py:50-57`).
10. `reporter.on_startup_summary(...)` (`:1299`) → `await bot.start(config.DISCORD_BOT_TOKEN)` (`:1311`).

**Observation (key):** the **gateway connects at step 10, but the namespace/identity checks at steps
1 + 8 are partial and one is advisory** — the fail-before-connect posture the rebuild wants (§3.2)
exists only for the `SUBSYSTEMS` freeze, not for the full identity surface, and not for command/
custom_id/event/settings-key collisions. This is the central L0 gap the namespace registry closes.

### 2.3 Cog discovery + loader — `config.INITIAL_EXTENSIONS` + `bot1._load_cogs`

- **Hardcoded extension list**: `config.INITIAL_EXTENSIONS` is a **literal list of ~60 cog module
  paths** (`config.py:79-143`). There is **no folder scan, no entry-point discovery, no manifest
  registry** — adding a cog means editing this list (grep confirms no dynamic loader anywhere).
- **Load ordering is a hand-ordered constraint**: `bootstrap_access_cog` MUST be
  `INITIAL_EXTENSIONS[0]` because it installs the command-access guard before any command registers
  (`config.py:84-85`; explained again at `bot1.py:606-618`). Ordering is *positional*, not *declared*.
- **Failure isolation exists**: `_load_cogs` wraps each `load_extension` in `try/except`, records the
  outcome (`startup_outcome.record_extension_success/failure`, `bot1.py:707/710`), and continues —
  one bad cog does not down the bot (INV-J, `docs/architecture.md:135`). A **boot smoke-test CI guard**
  (#1601, `docs/current-state.md:299-304`) fails the *build* when a cog won't load — defense in depth.
- **The failure-mode ambiguity (a real finding)**: after the load loop, for each subsystem that
  declares `entry_points`, if **none** of those entry-point command names appear in the loaded command
  set the subsystem is registered failed and marked **INTERNAL** via
  `governance_service.register_failed_subsystems` (`bot1.py:722-736`); subsystems with empty
  `entry_points` are skipped by the `if entry_points and …` guard. This *hides* the subsystem from
  users rather than surfacing "this feature is broken in production" — it degrades silently. The health
  snapshot's `extensions` adapter reads the outcomes (`startup_outcome.py:238-291`), so the state is
  *observable*, but the default user-facing behavior is concealment, not a visible degraded banner.
  (It is also an *inference* — "no commands registered" — not a direct "this extension raised" signal,
  so a cog that loads but registers no command reads the same as a crashed one.)

### 2.4 Env / config / secrets — `disbot/config.py`

- `dotenv.load_dotenv()` at import (`config.py:7`).
- **Only one value is validated**: the token (`DISCORD_BOT_TOKEN` from `DISCORD_BOT_TOKEN_PRODUCTION`,
  fail-fast `ValueError` if missing/empty, `config.py:19-23`). `DATABASE_URL` is validated later inside
  `db.init` (`config.py:12-14` comment).
- Flat module of module-level `os.getenv` calls mixing **secrets** (`OPENAI_API_KEY`,
  `ANTHROPIC_API_KEY`, `PARAGON_API_KEY`, `config.py:185-216`), **feature flags** (`AI_ENABLED` off by
  default `:202`, `AUTO_SYNC_COMMANDS` `:249`, `BTD6_AUTO_SEED` `:241`), **identity**
  (`BOT_OWNER_USER_ID` hardcoded default `340415158583296000`, `:38-43`), and **data-backend URLs**.
- `is_platform_owner()` is the single owner-identity seam, correctly a layer-free leaf importable from
  every layer (`config.py:46-73`).
- **Config reads are scattered, not centralized**: `HEALTH_PORT`/`HEALTH_HOST` are read in
  `healthserver.py:64-70`; `STRICT_DISABLED`/`IDENTITY_CONTRACT_STRICT` in `bot1.py:177-181`;
  `CONTROL_API_TOKEN` in `control_api.py`; `AUTOMATION_SCHEDULER_ENABLED` in `automation_scheduler`.
  There is no single typed config object and no "validate all required config before connect" gate.

### 2.5 Event bus — `disbot/core/events.py`

- `EventBus` (`events.py:52`): `emit` is **publish-accepted** — a subscriber failure/timeout is
  isolated per handler and **never raises** (`events.py:100-137`); each handler runs under a 5 s
  timeout (`_HANDLER_TIMEOUT`, `:116`). Delivery outcomes are observable via `delivery_stats`
  (`:147`) + `event_handler_failures_total`; a diagnostics provider is registered (`:174-204`). This
  is the RS05 contract (`docs/runtime_contracts.md` §2).
- **Catalogue is hand-maintained and non-fatal**: an uncatalogued `emit`/`on` logs a **one-shot
  WARNING** + increments `unknown_event_total` and **keeps running** (`events.py:22-49`); the
  catalogue is a frozenset `KNOWN_EVENTS` in `core/events_catalogue.py` (47 events, linchpin §1.1).
  INV-A (`docs/architecture.md:126`).
- **Some subscriptions are import- and call-invisible**: they are wired inside `runtime.setup()`
  closures — verified `core/runtime/__init__.py:181-183` (`bus.on(EVT_VISIBILITY_CHANGED, …)`,
  `EVT_CACHE_INVALIDATED`, `EVT_CLEANUP_CHANGED`). Neither the import graph nor the call graph
  connects emitter→subscriber (design spec §1.6; `.claude/CLAUDE.md` CodeGraph rule 5).
- **In-process only** by design (no Redis, ADR-001); the `events.py:74-79` "future sharding" note is
  aspirational.

### 2.6 Task supervisor — `disbot/core/runtime/tasks.py`

- `spawn(name, coro, *, on_error)` holds a strong ref, logs exceptions at ERROR, increments
  `task_outcome_total{name,outcome}`, and supports an `on_error` hook (`tasks.py:55-111`).
  `cancel_all` / `cancel_by_prefix` for cooperative shutdown + cog-unload cleanup (`:124-171`). Self-
  registers a `!platform tasks` diagnostics provider (`:190`).
- **Discipline is already near-complete**: the only bare `asyncio.create_task` in `disbot/` production
  is `bot1.py:1005` (a one-shot inside `asyncio.wait`; grep verified). INV-K
  (`docs/architecture.md:136`) codifies "every task outside the entry point uses `tasks.spawn`".
- **`from services import metrics` at module level** (`tasks.py:38`) — a `core → services` edge, but
  **explicitly sanctioned** by `docs/helper-policy.md` §3.7 (runtime primitives may import
  `services/metrics` only). It is the symptom the design spec §1.4 fixes structurally by relocating
  metrics to a `kernel/observability` leaf.
- Scheduled loops: `session_gc`, `live_update_scheduler`, and `automation_scheduler` (gated behind
  `AUTOMATION_SCHEDULER_ENABLED`, `bot1.py:1077-1090`) are all spawned through the same supervisor.

### 2.7 Lifecycle — `disbot/core/runtime/lifecycle.py`

- 7-phase state machine (`Phase`: `STARTING/RUNNING/DRAINING/SHUTTING_DOWN/RESTARTING/STOPPED/
  FAILED_STARTUP`, `lifecycle.py:49-56`), `can_accept_commands()` admission gate (`:182-188`),
  coalescing `request_shutdown`/`request_restart` (`:191-254`), a 128-entry event ring buffer, a
  `lifecycle_phase` Prometheus gauge, and a diagnostics provider (`:397-449`). **Records intent only;
  `bot1.py` owns exec** (`lifecycle.py:8-10`). `FAILED_STARTUP` exists but is reserved/unused today.

### 2.8 Health / metrics / observability — `healthserver.py`, `services/metrics.py`, diagnostics

- `healthserver.py` runs an aiohttp server on `[::]:8080` (IPv6 dual-stack for Railway private net,
  `:70`) exposing `/health` (liveness), `/ready` (**readiness = `bot.is_ready()` AND
  `lifecycle.can_accept_commands()`; 503 during draining**, `:92-139`), `/lifecycle` (diag dump), and
  `/metrics` (Prometheus, `:162-164`). **Bind-ready gating** makes a bind failure abort startup
  (`:210-211` + `bot1.py:1011-1031`). `control_api` routes register here, dormant unless
  `CONTROL_API_TOKEN` (`:197-202`).
- `services/metrics.py` is a large Prometheus registry (46 metric families — command, lifecycle,
  governance, task, health, scope-lock, guild-config, AI, etc.; e.g. `command_total` `:84`,
  `lifecycle_phase` `:211`, `task_outcome_total` `:130`). Its only external import is
  `prometheus_client` — i.e. it is **misfiled observability** (design spec §1.4).
- `services/diagnostics_service.py` is a `register(name, snapshot)` provider registry consumed by
  `!platform`; `core/runtime/startup_outcome.py` records per-phase boot health;
  `core/runtime/slow_path_log.py` rings slow paths; `services/health_snapshot_service.py` builds the
  settled-startup snapshot off the readiness path (`bot1.py:202-273`). Observability contract:
  `docs/runtime_contracts.md` §10.

### 2.9 DB / state init — `disbot/utils/db/` + runtime lock

- `utils/db/` is the **only** SQL layer (asyncpg-only): ~45 per-table submodules + `pool.py`,
  `codec.py`, `migrations.py`, `runtime_lock.py`, and a `games/` subtree. `db.init()` connects the
  pool and runs migrations at boot (`bot1.py:945`). **103 migration `.sql` files.** INV-I: migrations
  are idempotent and run under `pg_advisory_lock` (`docs/architecture.md:134`,
  `utils/db/migrations.run_migrations`).
- **Runtime instance lock** (single-replica): `acquire_lock_or_exit` (`SystemExit(0)` for the loser,
  `bot1.py:953`), `run_heartbeat_loop` (30 s heartbeat, 90 s TTL), `release_lock_best_effort`
  (idempotent, boot-scoped; LP-4 fast handoff drops the lock before the slow drain, `bot1.py:851-865`).
- No external state store (ADR-001); game state is not restart-safe by design (ADR-002).

### 2.10 Namespace / registry — `disbot/utils/subsystem_registry.py` + `hub_registry.py`

- `SUBSYSTEMS` dict — 43 persisted keys (`subsystem_registry.py:58`); deep-frozen after
  `validate_registry()` (INV-H, `docs/architecture.md:133`). `validate_registry()` is a **1309-line-in
  god-function** the design spec measures at cognitive 83 (`subsystem_registry.py:1309`; file is 1928
  lines).
- Capability strings are `{subsystem}.{resource}.{action}`, three parts enforced, reserved prefixes
  `_internal.*`/`system.*`/`governance.*` (`subsystem_registry.py:7`).
- Identity is cross-checked across **five surfaces** (SUBSYSTEMS keys vs bot commands vs
  PersistentView SUBSYSTEM vs interaction_router prefixes vs `panel_anchors` rows) by
  `validate_identity_contract` (`subsystem_registry.py:1603`) + `summarize_findings` (`:1573`), run at
  boot **advisory unless STRICT** (INV-B, `docs/architecture.md:127`; STRICT default-on per
  `docs/runtime_contracts.md` §12).
- **The gap**: there is **no central reservation** of command names, custom_ids, event names, or
  settings keys. Collisions surface *reactively* — discord.py raises at command registration **after
  the gateway connects**, which is exactly how `give` (Q-0211) and `dock`/`sail` (BUG-0030)
  crash-looped production (design spec §0). Q-0200 (a second same-name `def` silently shadowing the
  first) is a *different*, Python-symbol class the runtime registry structurally cannot catch.

---

## 3. Preserve / improve / replace / centralize / drop

Per-piece verdict for the L0 rebuild. **Preserve = carry field-for-field; Improve = keep shape, harden;
Replace = re-architect; Centralize = one home; Drop = remove.**

| # | L0 piece | Verdict | Rationale |
|---|---|---|---|
| P1 | Lifecycle state machine (`lifecycle.py`) | **Preserve** | 7 phases + admission gate + coalescing + ring buffer + gauge are exactly the `kernel/lifecycle` §1.2 target. Carry field-for-field; wire `FAILED_STARTUP` to the namespace-validation abort (it's reserved today). |
| P2 | Managed-task supervisor (`tasks.py`) | **Preserve + improve** | Solid supervisor; improve = declare tasks as `ManagedTaskSpec` in the manifest, reserve the name-prefix in the namespace, and AST-fence bare `create_task` as **INV-T** (spec §1.2). |
| P3 | EventBus (`events.py`) | **Preserve + improve** | Keep publish-accepted + per-handler timeout + isolation + delivery stats verbatim. Improve = **generate** the catalogue from manifest `EventSpec`s and make an undeclared emit/`on` a **pre-boot failure** (not a one-shot WARNING); add the ≥1-subscriber-or-`observability_only` drift check (spec §1.2/§2.8). |
| P4 | Startup-outcome recorder (`startup_outcome.py`) | **Preserve** | The "invisible try/except → observable record" pattern is the day-one observability seam; carry it as the boot-phase + extension recorder. |
| P5 | Health/probe server (`healthserver.py`) | **Preserve** | Liveness/readiness split, lifecycle-aware `/ready`, `/lifecycle` diag dump, bind-ready fail-fast — production-grade. Carry as an `adapters/http` edge over `kernel/lifecycle` + `kernel/observability`. |
| P6 | asyncpg-only DB seam + migrations + runtime lock (`utils/db/`) | **Preserve + improve** | Keep asyncpg-only, idempotent migrations under advisory lock, single-replica lock. Improve = one `StoreSpec` per table naming its sole writer + a generated seam-authority test (spec §1.3). |
| I1 | Structured logging w/ `boot_id` (`bot1.py:29-60`) | **Improve → centralize** | Correct behavior; move out of the bootstrap module into `kernel/observability` so it is the leaf every layer imports. |
| I2 | Prometheus metrics (`services/metrics.py`) | **Centralize (relocate)** | Relocate to `kernel/observability` — a dependency-free leaf. This **dissolves the one live layer break** (`core/runtime/ai/gateway.py:51 from services import metrics`, verified) at its root (spec §1.4). |
| I3 | Diagnostics provider registry (`diagnostics_service`) | **Preserve + improve** | Generalize into a manifest `DiagnosticProviderSpec`; keep the register/snapshot shape. |
| R1 | `bot1.py` composition root (1463 lines) | **Replace** | Extract every non-composition concern into kernel engines; the new `app/` root is "load manifests → validate namespace → build → boot" (spec §1.1). Concrete extraction examples: the cross-cutting `on_guild_remove → guild_lifecycle.teardown` hand-wired in the bootstrap (`bot1.py:342-346`) becomes a manifest-declared lifecycle subscription; the 6 event handlers become kernel event/interaction wiring. See §7. |
| R2 | `config.INITIAL_EXTENSIONS` hardcoded loader (`config.py:79-143`) | **Replace** | Manifest-driven dynamic discovery, no hardcoded list, declared dependency order, failure isolation (see §4). |
| R3 | `config.py` flat env module | **Replace → centralize** | One typed, validated config/secrets object loaded + validated **before gateway connect**; scattered `os.getenv` banned by a checker; secrets separated from config (see §6.2). |
| R4 | `validate_registry` god-function (cognitive 83, `subsystem_registry.py:1309`) | **Replace** | Becomes a linear pass over the derived namespace index (spec §1.5); the three registry fragments (`SUBSYSTEMS` + `HUBS` + `SubsystemSchema`) consolidate into one `SubsystemManifest` (spec §2.1). |
| C1 | Identity contract (`validate_identity_contract`) | **Centralize + promote** | Promote from advisory-cross-check to the **central namespace registry** with two-phase (CI + pre-boot) fail-before-connect validation across **all** id kinds (see §6.1). |
| D1 | Fuzzy typo-resolution cache in the bootstrap (`bot1.py:448-479`) | **Drop from L0 (relocate)** | Useful UX, but it does not belong in the composition root; it is a `kernel/interaction` command-resolution concern. |
| D2 | The failed-cog → INTERNAL silent-hide default (`bot1.py:722-736`) | **Replace** | See §4 failure isolation: a failed host should be *visibly* degraded, not silently hidden. |

---

## 4. Dynamic loader recommendation

**Directive (Lane G):** *"the skeleton must find and load every cog dynamically, with NO hardcoded
initial-extensions list."* The rebuild makes this cleaner than a folder scan, because **there is no
per-feature cog file** — a subsystem is one `SubsystemManifest` and the loader builds one generic
`SubsystemHost` per manifest (spec §1.1). So "cog discovery" becomes **manifest discovery**.

**Recommendation: manifest-registry discovery + declared-dependency topological load + per-host
failure isolation + fail-before-connect namespace validation.** Concretely:

1. **Discovery — scan `sb/manifest/*.py`** (one module per subsystem), collect each exported
   `SubsystemManifest`. No hardcoded list; adding a subsystem = adding a manifest module. This
   replaces `config.INITIAL_EXTENSIONS` (`config.py:79-143`) entirely. *(Folder-scan vs entry-points
   is a minor call — see §5 benchmark; a package scan is simplest and avoids the `importlib.metadata`
   install-step coupling for an in-repo bot. Entry-points earn their keep only for out-of-tree
   plugins, which this bot does not have.)*
2. **Dependency-ordered startup** — each manifest declares `dependencies=("economy",)` (spec §1.3).
   The loader topologically sorts hosts by declared deps and **validates the graph** (a cycle or a
   missing dependency is a **compile/boot error**, not a runtime surprise). This *replaces* the
   positional "`bootstrap_access_cog` must be index 0" coupling (`config.py:84-85`) with a declared
   ordering constraint the checker can see — the access-guard host declares itself a dependency of
   every command-owning host, or the kernel installs the admission gate structurally before any host
   loads (the generated component callback already resolves authority, spec §1.2, so the ordering
   coupling largely evaporates).
3. **Per-host failure isolation, made *visible*** — keep the per-extension `try/except` +
   `startup_outcome` recording (`bot1.py:704-720`), but **change the default failure surface**: a
   failed host is recorded, its subsystem is marked **degraded and surfaced** (a visible "this feature
   failed to load" state in `!platform`/health), **not silently INTERNAL-hidden** (the `bot1.py:722-736`
   behavior). Keep the boot smoke-test CI guard (#1601) so a load failure also goes red in CI. The
   principle: *one failed cog must not down the bot, and must not hide broken production state either.*
4. **Fail-before-gateway-connect** — the namespace validation (§6.1) recompiles + revalidates the full
   manifest set at boot and exits `FAILED_STARTUP` with a two-claimants report **before any network
   I/O** (spec §3.2 phase 3). A colliding manifest is a red deploy with a named culprit pair, never a
   post-connect crash-loop.

**What is preserved:** the failure-isolation instinct (INV-J), the startup-outcome observability, and
the smoke-test guard. **What is replaced:** the hardcoded list, the positional ordering, and the
silent-hide default.

---

## 5. Benchmark — external foundation patterns

> External facts, clearly labeled **[external]** with source URLs; gathered by the Lane G benchmark
> fan-out (context7 + web) and folded in here. Relevance verdict = ADOPT / ADAPT / REJECT for *our*
> manifest-driven L0.

### 5.1 discord.py 2.x extension loading (the loader contract)

- **[external] `setup_hook()`, not `on_ready`, is the load window; loads are coroutines.** In
  discord.py 2.x `load_extension`/`unload`/`reload`/`add_cog` are all `await`-able; the canonical place
  to load is `setup_hook` (runs once after login, **before the gateway READY**), so cogs + their
  app-commands register before the bot is live. Source: discordpy.readthedocs.io
  `/ext/commands/extensions.html`, `/migrating.html`. **ADOPT** — and note our current `_load_cogs`
  already runs in that window (`bot1.py:1092`, inside `async with bot` before `bot.start`), so the
  rebuild keeps the *timing* and only changes *what* it loads (manifest scan, not a literal list).
- **[external] Distinct load-failure exception types.** `commands.ExtensionError` is the catch-base;
  its children `NoEntryPointError` / `ExtensionFailed` / `ExtensionNotFound` / `ExtensionAlreadyLoaded`
  name distinct failure modes. Source: discordpy.readthedocs.io `/ext/commands/api.html`. **ADOPT** —
  the L0 loader's failure-isolation should record *which* failure per host (a richer signal than our
  current inferred "no commands registered", §2.3).
- **[external] Dynamic folder-scan discovery.** `pathlib.Path('cogs').rglob('*.py')` (or
  `pkgutil.iter_modules` over a package), skipping `_`-prefixed files, is the standard no-hardcoded-list
  pattern. Source: fallendeity.github.io/discord.py-masterclass/cogs/. **ADOPT** — maps directly to
  scanning `sb/manifest/*.py`; `pkgutil` is cleaner when `manifest` is an importable package.
- **[external] Atomic `reload_extension` (rollback-on-error).** "If an error occurred during the
  reloading process, the bot will pretend as if the reload never happened" — the old module is cached
  and restored on failure. Source: discordpy.readthedocs.io `/ext/commands/extensions.html`;
  github.com/Rapptz/discord.py issue #1658. **ADOPT** as the L0 hot-reload primitive for a
  `SubsystemHost`: snapshot the live host, rebuild from the re-read manifest, swap in only on success.
- **[external] discord.py has NO built-in dependency/ordering system** — extensions load in feed order
  and nothing is resolved; the docs recommend a hardcoded list. Source: discordpy.readthedocs.io
  `/ext/commands/cogs.html`. **This is the exact gap our L0 must fill** (§4) — and REJECT the
  filename-prefix ordering hack (fragile, invisible) that today's `bootstrap_access_cog`-must-be-first
  positional rule (`config.py:84-85`) is an instance of.

### 5.2 Large OSS bot skeletons + Python plugin systems

- **[external] Red-DiscordBot `info.json` cog manifest** declares `requirements` (pip), `required_cogs`
  (name → repo URL), `min_bot_version`. Source: docs.discord.red `/framework_downloader.html`.
  **ADAPT** — our `dependencies=("economy",)` is Red's `required_cogs` but pointing at *in-repo
  siblings*, which is strictly simpler (no repo-URL resolution).
- **[external] Red declares `required_cogs` but does NOT enforce it** — "Downloader will not deal with
  this functionality"; there is no topological load ordering. Source: docs.discord.red
  `/framework_downloader.html`. **REJECT Red's punt — this is precisely the gap our design closes:** our
  `dependencies` are machine-readable *and* in-process, so the `SubsystemHost` loader builds the
  dependency DAG and toposorts (§4), doing what even the mature OSS skeleton declined to.
- **[external] Red CogManager folder-scan with priority path list** (install_path > user > core) +
  cache invalidation. Source: edu-discordbot.readthedocs.io redbot cog_manager. **ADOPT** the
  folder-scan model; our single-directory `sb/manifest/*` glob is simpler (no path-priority ambiguity).
- **[external] stevedore (OpenStack) `on_load_failure_callback(manager, entrypoint, exception)`** fires
  per failed plugin so one bad plugin never crashes the host. Source: docs.openstack.org/stevedore.
  **ADOPT** the per-host failure-callback shape (collect the exception, keep loading) — the mature form
  of our `startup_outcome` isolation.
- **[external] `importlib.metadata.entry_points`** is the packaging-standard discovery (pytest's
  `pytest11`, etc.). Source: packaging.python.org "creating-and-discovering-plugins". **REJECT for our
  loader** — entry-points earn their keep only for *separately-distributed third-party* plugins; our
  subsystems are first-party in-repo, so a package scan is simpler and avoids the install-step coupling.
- **[external] pluggy (`tryfirst`/`trylast` relative-ordering hints).** Source: pluggy.readthedocs.io.
  **ADAPT the philosophy, not the machinery** — lighter than a DAG, but our explicit `dependencies=(...)`
  DAG is more auditable; note the hint pattern as a fallback for order ties.

### 5.3 Fail-before-connect / typed config / born-red deploy

- **[external] The "12.1-factor" rule** — read all config from the env at boot and **refuse to start
  (exit non-zero) if any required value is missing/malformed**. Source: 12factor.net/config +
  marmelab/medium "12.1-factor apps". **ADOPT** as the backbone of the boot order — it *is* our
  "validate before gateway connect" (§3.2 + §6.2).
- **[external] `pydantic-settings` typed validation at boot** — one `BaseSettings` model instantiated
  once coerces + validates all env, raising a `ValidationError` list instead of failing lazily deep in
  a request path. Source: github.com/pydantic/pydantic-settings. **ADOPT** the pattern (library optional
  — owner decision §11.3).
- **[external] Kubernetes three-probe split** — startup ("init done?") gates readiness ("serve
  traffic?") and liveness ("restart me?"). Source: kubernetes.io "Configure Liveness, Readiness and
  Startup Probes". **ADAPT** — Railway single-worker has no literal probes, but the three-question model
  maps cleanly onto our `/health` (liveness) + `/ready` (readiness, lifecycle-aware) split
  (`healthserver.py:92-139`), with boot config+namespace validation as the "startup" gate.
- **[external] "Red deploy, not crash-loop"** — on invalid config, `sys.exit(non-zero)` exactly once so
  the orchestrator halts the rollout and keeps the previous version serving; no internal retry loop.
  Source: kubernetes.io probes docs. **ADOPT** — this is our born-red deploy (§3.2 phase 3).
- **[external] Registration-time name-collision detection** — key each entry on its name as it
  registers; a second registration of a seen key **raises, naming both sources**. Sources: craftcms
  issue #3457; philsturgeon "global namespace class collisions". **ADOPT directly for §6.1** — the
  runtime-registry analogue of our compile-time namespace check, and the pattern nobody in the bot
  ecosystem applies pre-connect.

### 5.4 Outperform reading

Most bots (MEE6/Dyno/Carl-bot as closed products; **Red as the mature OSS skeleton**) do dynamic
discovery + isolated load — but **two edges are ours alone**: (1) Red *declares* inter-cog dependencies
yet **does not enforce ordering** (its own docs say so); our machine-readable, in-process
`dependencies=(...)` + toposort closes that gap. (2) **No bot in the field has a pre-connect
name/identity collision gate** — collisions are a runtime failure everywhere (the exact class that
crash-looped us). The rebuild's namespace registry (compile + merge-result + pre-boot, §6.1) makes that
class **structurally unshippable**. Those two, plus the generated-panel/settings/help foundation (97%
operator-band fit) that removes the per-feature UI layer these bots hand-maintain, are the concrete L0
outperform targets.

---

## 6. Helper / util architecture recommendation, config, and namespace

### 6.1 The central namespace registry (the L0 collision-prevention spine)

This is the one L0 capability that **does not exist today** and must be built early (K1, before the
grammar). The rebuild's `sb/namespace/` (spec §3):

- **One derived reservation index over typed kinds** — `command` (per-`kind` scoped so prefix `!karma`
  and slash `/karma` don't false-collide, amendment **G-6**), `custom_id`, `event`, `setting_key`,
  `subsystem_key`, `capability`, `panel`, `handler_ref`, `task_prefix`, `stat_key`, `item_key`,
  `ai_task`, `table` (spec §3.1). It is **derived from the manifests** (no hand-maintained list to
  drift), plus a frozen `legacy_reservations.json` compat core (the 43 subsystem keys, verbatim
  custom_ids, catalogued events, all settings keys, capabilities, actor types).
- **Two-phase, earliest-wins validation** (spec §3.2): (1) intra-manifest at import (`__post_init__`,
  stdlib-only); (2) full cross-manifest set in CI **including on the `git merge-tree` result** (two
  green PRs that collide together are caught before either merges); (3) at boot, `app/` re-validates
  and exits `FAILED_STARTUP` with a two-claimants report **before the gateway connects**.
- **Preserve from today:** the identity-contract *concept* (five-surface cross-check,
  `validate_identity_contract`, `subsystem_registry.py:1603`) and the capability-string format rule
  (`subsystem_registry.py:7`). **Replace:** the reactive, advisory, post-connect timing — the crash-loop
  class (Q-0211/BUG-0030) dies at phase 2/3, ahead of production impact.
- **Companion static pass** for the Q-0200 symbol-shadowing class (a second same-name `def`), which the
  runtime registry cannot catch — `tools/check_symbol_shadowing.py` (spec §3.5). The two mechanisms are
  deliberately non-overlapping.

### 6.2 Config / env / secrets

- **One typed config object, loaded + validated once, before connect.** Replace the flat `config.py`
  (`config.py:1-249`) with a typed settings contract (fields grouped: secrets, runtime, per-env,
  feature flags). All required values (token, `DATABASE_URL`, any required secret) validate **before
  the gateway connects** — extend today's token-only fail-fast (`config.py:19-23`) to the whole
  required set. **[external]** this is the `pydantic-settings` / 12-factor pattern (§5).
- **Ban scattered `os.getenv`** with an architecture checker: config is read in one place, not in
  `healthserver.py:64-70` / `bot1.py:177-181` / `control_api` (§2.4). Env is the *process*-config
  boundary; **per-guild runtime settings are a different lane** — the `kernel/settings` read-side
  resolution (per-guild → global → default, spec §4.1), never conflated with env.
- **Separate secrets from config**: tokens/API keys are a distinct, never-logged category (the redaction
  choke point already exists for AI, spec §1.4); config values are diffable/loggable.

### 6.3 Helper / util architecture

The binding policy is `docs/helper-policy.md` (10 rungs, promote-one-rung-on-evidence). **Boundaries to
preserve** (strong today):

- `utils/db/` asyncpg-only, one file per table, the terminal DB-helper leaf (helper-policy §3.8) — carry
  as `adapters/db` (spec §1.1, the only SQL package).
- `config.is_platform_owner` as a layer-free leaf (`config.py:46-73`).
- The audited `*_mutation.py` / `services/*_service.py` seams as the sole writers (INV-E/F/G,
  `docs/architecture.md:130-132`) — carry as the four `kernel/workflow` lanes (spec §1.3).
- `core/runtime/*` as platform primitives whose *only* services import is `metrics` (helper-policy
  §3.7) — the rebuild removes even that by making metrics a `kernel/observability` leaf.

**Mis-homed / debt to fix at the L0 build** (do not carry forward):

- `utils/helpers.py` — a documented grab-bag; **do not carry as-is** (helper-policy §3.9 "Do not add to
  it"). Re-home each function to its domain at port time.
- `utils/embeds.py` — two consumers while every other cog builds embeds inline; the rebuild's
  `EmbedFrameSpec`/kernel renderer (spec §2.3) replaces ad-hoc embed building entirely, so this dies.
- `services/metrics.py` — **misfiled observability** (§2.8/§3-I2); relocate to `kernel/observability`.
- `validate_registry` (cognitive 83) and `AINaturalLanguageStage.process` (cognitive 135, spec §1.5) —
  the two worst god-functions; decomposed at design time (namespace validator + manifest NL router).
- The Q-0200 exact-name guard (helper-policy §2) becomes the CI symbol-shadowing pass (§6.1).

**The rebuild's structural upgrade:** the checker runs **from commit 1 with an *empty* grandfathered-
violations file** (spec §1.1) — today's `architecture_rules/` known-violation ledger starts at zero, so
the "tracked violation" drift never accumulates.

---

## 7. Manifest-host requirements (what the kernel must provide)

For the §2 manifest grammar to generate **into** L0 without any feature-specific UI code, the kernel
must provide these engines/hosts (each is the "generated into" target for a manifest facet):

| Manifest facet (spec §2) | Kernel host it generates into | L0 requirement |
|---|---|---|
| `CommandSpec` | command registration + the generated component callback that resolves declared authority before any handler | one generic `SubsystemHost` per manifest; **no per-feature cog** (spec §1.1) |
| `PanelSpec`/`PanelActionSpec`/`SelectorSpec`/`NavigationSpec` | `kernel/interaction` — `PanelRuntimeView`, custom-id router (versioned `g1:` + frozen legacy table), EmbedFrame, Table/List/Browser, navigation | one panel engine interpreting the spec; no per-panel view class (spec §2.3) |
| `SettingSpec`/`BindingSpec`/`ResourceRequirement` | `kernel/settings` (read-side resolve) + `kernel/workflow` (the four write lanes) | one mutation executor, one audit fan-out (spec §1.3) |
| `EventSpec`/`EventSubscription` | `kernel/events` — generated catalogue + declared subscriptions | wiring map complete-by-construction (spec §1.6) |
| `ManagedTaskSpec` | `kernel/lifecycle` task supervisor + INV-T fence | reserved task-prefix, no bare `create_task` |
| `StoreSpec` | `adapters/db` sole-writer projection + seam-authority test | one writer per table (spec §1.3) |
| `DiagnosticProviderSpec` | `kernel/diagnostics` provider registry + health-findings persistence | generalizes today's `diagnostics_service` |
| `HelpEntrySpec` | `kernel/help` help-as-projection | help generated, never hand-maintained |
| `capabilities` | `kernel/authority` — `actor_holds_capability` + `CapabilityDecision` | ported field-for-field (spec §1.2) |

**Two kernel requirements the linchpin work surfaced that L0 must build in from day one:**

- **Injectable clock + RNG** (`kernel/clock.now()`, seedable `kernel/rng`) — a direct
  `datetime.now()`/`random`/`time.time()` outside them is AST-fenced (spec §1.2). This is what makes
  *every* surface golden-testable, not just the ones that happened to avoid wall-clock/randomness
  (linchpin validation §1.3/§3 item 6). The current bot has nondeterministic-by-construction paths
  the harness had to exclude.
- **The golden-parity oracle wiring** — `parity/` consumed read-only as a pinned external dependency
  (spec §6); L0's CI must provision a **Postgres service container** from K10 (linchpin §2.3 item 4;
  this repo's `code-quality` runs none, so the harness skips there today).

**Manifest-host non-goals for L0:** the grammar must never express game *rules* or *renderers* — those
are the §2.9 named escape hatch (blackjack measured 44% *by design*, linchpin §2.2). L0 provides the
`renderer_override`/`legacy_view` ref seam, counted and ratcheted; it does not try to make games
declarative.

---

## 8. Dependency-ordered L0 build sequence

This refines the design spec's K0–K10 (spec §9.1) with the Lane G foundation findings. Each layer is
**production-grade and done before the next begins**; each depends only on those above it.

| Layer | Builds | Depends on | Lane-G-added done criterion |
|---|---|---|---|
| **L0.0 — substrate + observability** (K0) | repo substrate, rulesets/OIDC, named-gate CI, `kernel/observability` (metrics + structured `boot_id` logging — the leaf everything imports) | — | `kernel/observability` is a dependency-free leaf; **relocating metrics here dissolves the `gateway.py:51` live break** |
| **L0.1 — namespace registry** (K1) | `sb/namespace/` reservation kinds, `legacy_reservations.json` (43 keys + verbatim custom_ids/events/settings-keys), `check_namespace`, symbol-shadowing AST pass, tombstones | L0.0 | two green PRs colliding on the merge-tree result are caught; the Q-0211/BUG-0030 class is red in CI |
| **L0.2 — the grammar** (K2) | `sb/spec/` dataclasses (extend shipped types verbatim), S/A/O metadata, manifest compiler + snapshot, validators, arrangement-invariance test | L0.1 | every spec field classified exactly once; snapshot is 100% data (unregistered callable = compile error) |
| **L0.3 — DB seam + migrations** (K3) | `adapters/db` (asyncpg-only), fresh migration runner (idempotent, advisory-lock — carry INV-I), `StoreSpec` ownership projection + seam-authority fences | L0.2 | a generated per-store test asserts no other module writes the table |
| **L0.4 — event bus** (K4) | `kernel/events` — carry publish-accepted + timeout + isolation verbatim; **generated catalogue**; undeclared emit/`on` = pre-boot fail; subscriber-drift check | L0.3 | an uncatalogued event fails **before boot**, not a one-shot WARNING |
| **L0.5 — lifecycle + task supervisor** (K5) | carry `lifecycle.py` field-for-field (7 phases + admission gate); carry `tasks.py` supervisor; INV-T fence on bare `create_task`; **injectable clock + RNG** | L0.4 | `FAILED_STARTUP` wired to namespace abort; only the entry point may spawn unmanaged |
| **L0.6 — authority** (K6) | `kernel/authority` — `actor_holds_capability` + `CapabilityDecision` ported field-for-field; capability strings namespace-validated | L0.5 | the generated callback resolves declared authority before any handler (no skip path) |
| **L0.7 — the dynamic loader + app root** (spans K5→K8) | manifest discovery (scan `sb/manifest/*`), topological dependency load, per-host **visible** failure isolation, the lean `app/` composition root ("load manifests → validate namespace → build → boot") | L0.5–L0.6 | **no hardcoded extension list**; a bad manifest is a red deploy pre-connect; a failed host is *visibly* degraded, never silently INTERNAL-hidden |
| **L0.8 — workflow engine** (K7) | audit spine + `WorkflowResult`/`MutationPreview`/`ConfirmationSpec` + four lane strategies + settings read-resolution | L0.6 | every mutation flows one audited seam (INV-E/F/G carried as AST fences) |
| **L0.9 — interaction runtime** (K8) | custom-id router (`g1:` + legacy table), `PanelRuntimeView`, EmbedFrame, Table/List/Browser, selectors, navigation, generated settings panels, help-as-projection, diagnostics + health | L0.8 | typed config + health probes + dashboard control-API contract defined at entry (spec §6) |
| **L0.10 — AI gateway** (K9) | `kernel/ai` gateway extended in place; contracts in `spec/ai`; provider port + adapters; egress guard | L0.9 | `kernel/ai` imports nothing above itself (the break *class* is dead) |
| **L0.11 — the loops** (K10) | `sim/` runner + `check_sim_gate`; golden harness wired as `golden-parity` (all-`pending`); `check_compat_frozen`; **Postgres service container in CI** | L0.0–L0.10 | repo is **born red on parity, green on everything else** |

**Config/env validation (R3, §6.2) lands with L0.0/L0.7** — the typed config object is validated in
`app/` before the gateway connects (step in the lean boot order below).

**The lean boot order the `app/` root should contain** (replacing `bot1.main`'s 1300 lines,
per spec §1.2): load manifests → **validate config** → **validate namespace (fail here, before I/O)**
→ DB pool + migration check → catalogue freeze → host construction (topological) → gateway connect →
persistent-component re-registration → admit commands. Everything else in today's `bot1.main` (the 9
catalogue builds, the close-driver, the health-bind dance) becomes kernel-engine behavior, not
bootstrap code.

---

## 9. Production-grade done-definition per L0 component

Each L0 component's "done" = the acceptance gate it must pass (the capstone's per-capability
done-definition field).

- **Bootstrap / `app/` root** — done when `app/` contains only the lean boot order (§8), no per-feature
  logic; boot is covered by a boot smoke test (carry #1601) that fails CI if any host won't build; the
  8-step order is asserted by an integration test.
- **Dynamic loader** — done when there is **no hardcoded extension list**; discovery is a manifest scan;
  the dependency graph is toposorted and a cycle/missing-dep fails the build; a per-host load failure is
  isolated **and surfaced** in health (not silently hidden) and records the *specific* failure (the
  discord.py `ExtensionError` family, `[external]` §5.1 — not an inferred "no commands registered");
  the namespace revalidation runs pre-connect.
- **Config/env/secrets** — done when one typed config object loads + validates the full required set
  **before connect**; a checker bans scattered `os.getenv`; secrets are a separate never-logged
  category; per-env profiles resolve deterministically.
- **Namespace registry** — done when `check_namespace` is a required CI gate (incl. merge-tree result),
  the pre-boot validation exits `FAILED_STARTUP` with a two-claimants report, and the
  symbol-shadowing pass is green; the Q-0211/BUG-0030 collision is reproducibly red in CI.
- **Event bus** — done when the catalogue is generated from `EventSpec`s, an undeclared emit/`on`
  fails pre-boot, the ≥1-subscriber-or-`observability_only` drift check passes, and the RS05
  publish-accepted contract is carried with its tests.
- **Task supervisor + lifecycle** — done when INV-T fences bare `create_task`, every `ManagedTaskSpec`
  prefix is namespace-reserved, the 7-phase machine + admission gate carry with their tests, and
  clock/RNG are injectable (a direct `datetime.now()`/`random` outside the kernel is AST-red).
- **DB/state init** — done when `adapters/db` is the sole SQL package, migrations are idempotent under
  advisory lock (carry INV-I), each `StoreSpec` has a generated sole-writer test, and the runtime lock
  gives clean single-replica handoff.
- **Health/observability** — done when `/health` + `/ready` (lifecycle-aware) + `/lifecycle` +
  `/metrics` are served with bind-ready fail-fast; the diagnostics provider registry, startup-outcome
  recorder, slow-path log, and boot-`id` structured logging exist from day one; `kernel/observability`
  is a dependency-free leaf.
- **Manifest host** — done when a subsystem with zero hand-written UI code renders its panels/settings/
  help entirely from its manifest (the generated-panel payoff), proven by a settings/diagnostic/help
  subsystem passing `golden-parity` first (spec §9.2 band 1).

---

## 10. Risks and stop conditions

- **R-A (loader failure-mode hides broken state).** Today a failed cog → silently INTERNAL
  (`bot1.py:722-736`). If the rebuild carries that default, a broken production feature is concealed
  rather than flagged. **Stop condition:** ship the loader only when a failed host is *visibly*
  degraded in health/`!platform`, not hidden. (Design fix in §4.)
- **R-B (namespace registry is new — highest-leverage, unbuilt).** The central pre-boot reservation
  across all id kinds does not exist today; it is the single most valuable L0 addition and the most
  novel. **Stop condition:** K1 lands with `check_namespace` reproducibly catching the Q-0211/BUG-0030
  collision before it can ship. If the derived-index approach proves brittle, that is a NO-GO signal
  for the "declaring is reserving" bet — but the grammar spike's validator already caught G-6 on its
  first real manifest, which is positive evidence.
- **R-C (config validation coverage).** Only the token is validated today (`config.py:19-23`). A missing
  required secret currently fails late/opaquely. **Stop condition:** the typed config gate validates the
  full required set before connect, or a missing secret still crash-loops.
- **R-D (observability-leaf relocation).** The metrics relocation (§3-I2) is what dissolves the one live
  layer break (`gateway.py:51`); if it is deferred, `kernel/ai` cannot satisfy "imports nothing above
  itself" and the break *class* survives. **Stop condition:** metrics is a leaf before K9.
- **R-E (engine-bug blast radius).** A kernel-engine bug hits every subsystem at once (design spec
  §10.1). Mitigation: the golden-parity oracle + the empty-grandfathered-violations checker from commit
  1; but the blast radius is real and is the reason L0 is built + parity-gated before any feature.
- **R-F (determinism cost for loops).** Command capture required pinning 8 nondeterminism classes;
  scheduled-loop capture (session_gc, schedulers) will pay again (linchpin §3 item 5). **Budget it in
  K10**, don't treat command-capture cost as the whole bill.
- **Hard stop (owner gate):** this is planning evidence, **not build approval**. No `sb/` code until the
  owner ratifies the design spec (BRIEF §"Phase-3 hard stop"). L0 does not start on a lane finding.

---

## 11. Open owner decisions

1. **Loader discovery mechanism** — folder/package scan of `sb/manifest/*` (recommended, simplest) vs
   `importlib.metadata` entry-points (only earns its keep for out-of-tree plugins, which this bot has
   none of) vs a hybrid. *Recommendation: package scan.* Low-risk, reversible; naming here for the
   record since it is an architectural default.
2. **Failed-host default behavior** — confirm the §4 change from *silent INTERNAL-hide* to *visible
   degraded*. This is a small but real behavior change to the current INV-J contract
   (`docs/architecture.md:135`) and worth an explicit owner nod.
3. **Config object shape** — adopt a typed settings library (`pydantic-settings`, a pinned **runtime**
   dep) vs a hand-rolled typed dataclass loader (no new dep). *Recommendation: hand-rolled typed loader*
   to keep the runtime dependency surface minimal, unless the owner prefers the library's validation
   ergonomics. Either satisfies the "validate before connect" done-definition.
4. **Invariant renaming** — the current `INV-K` is the **task-spawn** rule (`docs/architecture.md:136`);
   the design spec reassigns `INV-K` to karma and renames task-spawn to **INV-T** (spec §1.2/§8
   decision 4). This is a documentation reconciliation the capstone should confirm so citations don't
   drift across the two invariant vocabularies.
5. **Where the fuzzy typo-resolution UX lives** (`bot1.py:448-586`) — relocate from the bootstrap into
   `kernel/interaction` (recommended) vs keep it as an app-level concern. Cosmetic to the user, but it
   is currently ~140 lines of the composition root that should not be there.

---

## Capstone carry-forward (per BRIEF §"Launch preconditions")

- **Dependency-layer:** this whole document **is** L0 — it sits *below* L1 (core bot/server management)
  and everything else in the build plan (§8 maps directly onto K0–K10). Nothing above an unbuilt L0
  dependency.
- **Production-grade done-definition:** per component in §9.
- **Outperform target:** §5 — the concrete edge over MEE6/Dyno/Carl-bot/Red is the **pre-connect
  name-collision gate** (nobody else has one; collisions are a runtime failure everywhere) plus the
  **generated-panel/settings/help foundation** (97% operator-band fit) that removes the per-feature UI
  layer these bots all hand-maintain.
- **Owner-gated / blocked status:** the whole L0 build is behind the Phase-3 owner gate (§10 hard stop).
  Five open owner decisions in §11 (all low-risk, recommendations given).

## Verification notes

- Every `disbot/` citation in §2 was opened and read first-hand this session. Load-bearing spot-checks
  independently confirmed: `config.INITIAL_EXTENSIONS` is a hardcoded 60-cog list (`config.py:79-143`);
  the only bare `asyncio.create_task` in `disbot/` production is `bot1.py:1005` (grep); the one live
  layer break is `core/runtime/ai/gateway.py:51 from services import metrics`; `validate_registry` is at
  `subsystem_registry.py:1309` (file 1928 lines, `SUBSYSTEMS` at `:58`); `core/runtime/__init__.py`
  subscribes the governance events via `bus.on(...)` inside `setup()` (~`:181-183`); 103 migration
  `.sql` files; 46 metric families in `services/metrics.py`.
- **Adversarial-verify pass (Q-0120 discipline):** a background fleet (10 area-map agents + 3 external
  benchmark agents + 10 adversarial citation-verify batches, 23 agents, 0 errors, ~1.46M tokens)
  re-opened the cited source. Of 80 spot-checked citations, **79 CONFIRMED, 1 FALSE** — the FALSE was a
  *sub-agent's* over-claim (that `server_management`/`ux_lab` have empty `entry_points`; source shows
  both declare non-empty `entry_points`), which prompted the §2.3 wording correction above; no citation
  in this document failed verification.
- **⚠ unverified:** the exact cognitive-complexity numbers for `validate_registry` (83) and
  `AINaturalLanguageStage.process` (135) are the design spec's measurements (§1.5), not re-measured this
  session — carried as cited, not independently confirmed. The "47 `KNOWN_EVENTS`" count is the linchpin
  doc's figure (§1.1), not recounted here.
- External (§5) benchmark facts are labeled `[external]` with source URLs; treat as best-practice
  references, not repo source.
