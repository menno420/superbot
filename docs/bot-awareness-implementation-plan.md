# Bot-Awareness / AI-Assisted Diagnostics — Revised Implementation Plan

> **Status:** `living-ledger` — **Status (2026-06-06): PROGRAMME COMPLETE — all 6 PRs shipped.** PR1–PR3 merged in
> **#537** (typed health read model + deterministic `!platform health` + panel-only
> startup health); **PR4–PR6 merged in #541** (opt-in grouped recent-error findings,
> the owner-gated `diagnostics_health_snapshot` AI tool, and persistent findings with
> 30-day retention). Every PR shipped green on `check_architecture --mode strict`
> (0 errors) + `check_quality --full` (final suite 7565 passed). **Decision D1 is
> RESOLVED** (option a): `_derive_scope` maps `config.BOT_OWNER_USER_ID` →
> `AIScope.PLATFORM_OWNER` (owner-only). **The sections below are the original plan,
> kept for rationale — per-PR delivery status is in §5 and is the source of truth.**
> Remaining: maintainer live-test of the PR5 **AI path** on production (the sandbox has no
> AI-provider key; deterministic + DB paths are bootable in-sandbox); PR4 grouping is
> opt-in (`HEALTH_GROUPED_FINDINGS`, default off).
> **Inputs reconciled:** Codex map (PR #534), a ChatGPT revision pass, and the Codex
> AI-tool-orchestration successor plan (PR #536).
> **Execution authority:** this doc; the Codex map
> `docs/bot-awareness-diagnostics-plan.md` is the repository map.

---

## Context — why this exists

The maintainer wants AI-assisted operational diagnostics: an authorized operator asks
*"how healthy is the bot?"* and gets the **same trustworthy, bounded facts** through a
deterministic Platform surface **or** an optional AI explanation. The AI is an
**interpreter only**; deterministic services remain the source of facts and every
deterministic command must work with AI disabled, misconfigured, rate-limited, or
unhealthy. Implement this **over the existing observability stack** — *not* a parallel
`bot_awareness_service`.

```
existing diagnostics providers / startup outcomes / metrics / domain health readers
        │  (sync registry: diagnostics_service.snapshot_all(), isolated per-provider)
        ▼
services/health_snapshot_service.py   ← typed read-model aggregation (2 lanes)
   • collect_cached_snapshot()  (sync, process-local facts)
   • async collect_snapshot(req) (bounded async checks, per-source timeout)
   • project_for_audience(snap, audience) → redacted HealthSnapshot (PURE fn)
   • heavy-source adapters are FUNCTION-LOCAL imports (import-safe)
        │
        ├─────────────────────────────┬───────────────────────────────┐
        ▼                             ▼                               ▼
 deterministic DiagnosticCog/   Platform panel item            read-only AI tool
 !platform health (admin,       (same shared embed builder)    (PR5 ✅ #541, owner-gated)
 guild-redacted)
        ▼                                                             ▼
 operator-visible facts                                    optional AI explanation
                                                           (deterministic fallback)
```

---

## 1. Executive recommendation

**Codex's core plan (PR #534) is correct and source-aligned — adopt it unchanged:**
`diagnostics_service.snapshot_all()` is already sync + per-provider isolated;
`services.ai_tools` is already the read-only, scope-gated tool registry; the Platform
hub is already the right surface; startup outcomes + a one-shot lifecycle guard already
exist. **No architecture stop-condition triggered:** the first `!platform health` needs
**no refactor**.

**Required changes before/during implementation (verified this session):**

1. **BLOCKING for the AI phase — and a shared dependency.** The headline AI tool is
   *unreachable* as specified: `_derive_scope` (`natural_language_stage.py:894-922`)
   ceilings at `AIScope.SERVER_OWNER`; it never yields `PLATFORM_OWNER`, and it is the
   only scope source feeding the only `ai_tools.build_registry()` caller (L1098). A
   `min_scope=PLATFORM_OWNER` tool is filtered out for **every** message. **PR #536's
   own D5 hits the same gap** (it needs platform-owner config plumbing too), so fixing
   `_derive_scope` once unblocks *both* programmes. This is a product+security decision
   (§4-D1). **It only affects PR5 — not the unattended PR1→PR3 slice.**

2. **Merge Codex PR A+B** (contracts + aggregator). A pure-contracts PR ships no behavior
   and its redaction tests are weak against synthetic data; they are strong only against
   **real** `snapshot_all()` + adapter payloads, which exist once the aggregator does.

3. **Decouple deterministic health from AI vocabulary (ChatGPT revision, adopted).**
   Introduce a small `HealthAudience` enum in `health_contracts.py` (PUBLIC /
   GUILD_ADMIN / PLATFORM_OWNER). The deterministic `!platform health` derives audience
   from Discord context directly; only the PR5 AI adapter maps `AIScope → HealthAudience`.
   Net effect: `health_contracts.py` has **zero AI/core-AI dependency** — cleaner layering.

4. **Per-adapter redaction tests (ChatGPT revision, adopted).** Plant leaks in **every**
   source that enters `HealthSnapshot`, not just `snapshot_all()`: provider `_error`
   strings, `ResourceHealthFinding.message`/`target_id` (a Discord ID), AI config/audit
   fragments, startup/cog-load exception summaries, and (PR4) log snippets.

5. **Keep heavy-source adapters function-local + don't mutate pinned contracts.**
   `ai_config_projection_service` imports AI services + `utils.db.ai` at **module scope**
   (verified L38-45) and `platform_consistency` documents function-local imports to avoid
   re-entry (verified L8-9); so the aggregator's heavy adapters must import
   function-locally and stay import-safe. `ReadinessSnapshot` and `KNOWN_PHASES` are
   doc-test-pinned — *read/adapt* them; the extension-load recorder is a **sibling**.

6. **Severity mapping must handle the real vocabularies** — `ResourceHealthFinding`
   severity is `info|warn|error` (`warn`→`warning`); `SectionStatus` is
   `clean|warning|fatal|skipped`; `SummaryStatus` is `ok|degraded|failed|empty`.

**Unattended execution slice (per maintainer's "asleep" constraint):** **PR1 + PR2 +
PR3** — foundation, deterministic `!platform health`, and panel-only startup health.
All three are fully deterministic, need **no maintainer decision**, and are live-verifiable
by booting the test bot (runbook in `.session-journal.md`). **PR4** (structured
observations) is a **gated stretch** — include only if PR1-3 are green with session
appetite *and* fingerprints prove stable; otherwise stop. PR5 and PR6 were the
attended-session work. *(Historical: all of PR4–PR6 have since shipped in #541.)* This honors the
maintainer's explicit authorization to do "as much as can be safely executed in one
structured session" while protecting an unattended run.

---

## 2. Repo-verified findings

### 2.1 Already present (verified)

| Capability | Where | Shape |
|---|---|---|
| Sync, fail-isolated provider registry | `services/diagnostics_service.py` | `snapshot_all()->dict` sync; failed provider → `{"_error":"<type>: <msg>"}`; ~20 providers |
| Typed consistency + cached readiness | `services/platform_consistency.py` | frozen `SectionResult/ConsistencyReport/ReadinessSnapshot`; `SectionStatus=clean\|warning\|fatal\|skipped`; `async collect_report()`, `get_last_report()`/`build_readiness_snapshot()` sync; **function-local imports to avoid re-entry (L8-9)** |
| Typed startup outcomes | `core/runtime/startup_outcome.py` | frozen `StartupOutcome`; `SummaryStatus=ok\|degraded\|failed\|empty`; `KNOWN_PHASES`=4 phases (pinned by `test_startup_outcome.py` + `test_smoke_test_checklist.py`) |
| Lifecycle + reconnect one-shot guard | `core/runtime/lifecycle.py` | `Phase` enum; `_startup_duration_observed` one-shot fired on first→RUNNING; "lifecycle" provider |
| Managed task registry | `core/runtime/tasks.py` | `spawn(name,coro,*,on_error)` (INV-K); `task_outcome_total{name,outcome}`; "tasks" provider |
| Pre-connect startup webhook | `bot1.py` ~L1088 | `reporter.on_startup_summary(...)` before `bot.start()` |
| Reconnect-safe post-ready hook | `bot1.py::on_ready` L185-201 | after `restore_anchors`+`live_update_scheduler.setup`+`reporter.on_startup`; `if phase is STARTING: set_phase(RUNNING)` |
| Operator surface | `cogs/diagnostic_cog.py` **647/800 LOC** | `!platform` group (~30 subcmds), all `@has_permissions(administrator=True)`; `/platform` opens `HubView` |
| Shared embed builders + clamp | `cogs/diagnostic/_platform_embeds.py` 1815 LOC (**no ceiling**); `core/runtime/interaction_helpers.clamp_embed()` | ~28 `build_*_embed()`; soft caps 5800/1000/24 |
| Platform panel | `views/diagnostic/platform_panel.py` `HubView` | 4 category Selects + `_dispatch(name)`→builder; add item = tuple + dispatch case + builder |
| Guild-local resource findings | `services/resource_health.py` | frozen `ResourceHealthFinding(...,message,target_id, severity=info\|warn\|error)`; `async inspect(guild)` |
| Ring buffer | `cogs/diagnostic/_log_buffer.py` | maxlen 500, `{timestamp,level,message}`; **exposes message text**; no fingerprint |
| AI tool seam | `core/runtime/ai/contracts.py` (inert scaffold) + `services/ai_tools.py` | frozen `AIToolSpec(name,description,parameters,min_scope)`; `AIScope` USER<MOD<ADMIN<SERVER_OWNER<PLATFORM_OWNER<SYSTEM; `build_registry()` gates by `_scope_allows`; 22 USER/2 ADMIN tools |
| AI read models (adapt, never re-resolve) | `ai_config_projection_service.build_snapshot`→`AIConfigSnapshot`; `ai_readiness_service`→`AIReadinessReport`; `ai_diagnostics_service.snapshot_for_cog`→`AIDiagnosticsSnapshot` | AST-pinned read-only by `test_ai_readonly_invariants.py`; **module-scope AI+DB imports (L38-45)** |
| Event catalogue | `core/events_catalogue.py` | `KNOWN_EVENTS` frozenset; unknown→metric+one-shot warn; EventBus isolated +5s timeout |
| Migrations | `disbot/migrations/` | idempotent `NNN_*.sql`; latest **056**; next free **057** |

### 2.2 Missing (net-new; Codex is right these don't exist)

- No unified `HealthSnapshot` / `health_snapshot_service`.
- **No redaction/secret-stripping test harness anywhere** — net-new, highest-leverage testability item.
- No extension/cog-load outcome recorder; no persistent-view restoration outcome recorded.
- No `ai_monitor_service`. No persistent findings table/service. Ring buffer has no fingerprint/exception metadata.

### 2.3 Codex right vs. needs-correction

| Claim | Verdict |
|---|---|
| Extend observability, no `bot_awareness_service`; `snapshot_all()` isolated; use `ai_tools`; extend `!platform`/panel; `OperationalHealthFinding` name; two lanes; next migration 057 | ✅ all verified |
| "Ship AI tools PLATFORM_OWNER-first" | ⚠️ **unreachable today** (`_derive_scope` ceiling) — §4-D1 |
| PR A + PR B separate | ⚠️ **merge** (no behavior + weak redaction tests) |
| "Extend startup outcome contract" | ⚠️ `KNOWN_PHASES`/`ReadinessSnapshot` pinned → **sibling** recorder, read/adapt |
| `redaction_scope: AIScope` on the snapshot | ⚠️ **replace with `HealthAudience`** — deterministic health shouldn't depend on AI scope vocab |
| "prefer service-local dataclasses" | ⚠️ **make concrete**: standalone `services/health_contracts.py` (light, no AI dep) |
| Redaction tested against `snapshot_all()` | ⚠️ **expand to per-adapter** planted leaks |

### 2.4 Changed since Codex #534

- **#535** added the *registered-opaque-callable* precedent (`core/runtime/panel_manager` calls a hook wired from `bot1`, the `cleanup_registry` pattern) — the sanctioned way for core to trigger higher-layer behavior without importing it. Bot declared **fully tested as of #535**.
- **#536** (newer, on `main`) added `docs/ai-complex-request-tool-orchestration-plan.md` — a **successor** programme ("assumes the bot-awareness roadmap is already delivered"). It is mostly BTD6 AI orchestration (out of this session's scope) but defines reusable AI-tool primitives my PR5 must align with — see **§8**. It already reserves a **`diagnostics` toolset** for "future health snapshot tools" and hits the **same `_derive_scope` gap** (its D5 == my D1).

---

## 3. Final architecture

### 3.1 Modules to add / extend

| New module | Layer | Responsibility |
|---|---|---|
| `services/health_contracts.py` | services | Frozen `HealthSnapshot`, `SubsystemHealth`, `OperationalHealthFinding`, `HealthSnapshotRequest`; enums `SnapshotStatus`, `FindingSeverity`, **`HealthAudience`**. **No AI/core-AI import.** Light deps → safe for module-top import by cogs/views. |
| `services/health_snapshot_service.py` | services | Two-lane aggregator + deterministic severity + stable ordering + pure `project_for_audience()`. Heavy-source adapters **function-local**. Never mutates. |
| `services/health_findings_service.py` *(PR6 ✅ #541)* | services | **Sole writer** of findings table; dedupe/recurrence/lifecycle/retention. |
| `migrations/057_operational_health_findings.sql` *(PR6 ✅ #541)* | — | Additive `CREATE TABLE IF NOT EXISTS` (+ aggregates companion). |

Extend: `cogs/diagnostic_cog.py` (`!platform health` PR2, `!platform startup` PR3 — small methods, **function-local** service import), `cogs/diagnostic/_platform_embeds.py` (`build_health_embed`, `build_startup_health_embed`), `views/diagnostic/platform_panel.py` (Runtime-category item + `_dispatch`), `core/runtime/startup_outcome.py` (sibling extension-load recorder, PR3), `bot1.py` (per-extension recording + post-ready snapshot, PR3), `services/ai_tools.py` + `core/runtime/ai/natural_language_stage.py` (PR5 ✅ #541).

### 3.2 Read/write ownership, data flow, sync/async

- **Reads:** `health_snapshot_service` reads `diagnostics_service`, `platform_consistency` (cached + on-request fresh), `startup_outcome`, `lifecycle`, `tasks`, `resource_health`, AI read-models. **Owns no table** in PR1-PR5.
- **Writes:** none until PR6. `health_findings_service` is the **sole writer** (AST-guarded, modeled on `test_inv_f_economy_service.py`).
- **Sync lane** `collect_cached_snapshot()` — process-local facts (`snapshot_all()`, `get_last_report()`, `build_readiness_snapshot()`, lifecycle/tasks). Powers `!platform health` default + the PR5 tool.
- **Async lane** `async collect_snapshot(request)` — bounded checks per `HealthSnapshotRequest`: DB ping, **fresh** consistency *only on explicit request*, `resource_health.inspect(guild)`, AI readiness. Each source wrapped in its own `asyncio.wait_for`; `partial=True` on any timeout/failure. `snapshot_all()` stays **sync, non-mutating** (the lane *calls* it).
- **Import-safety:** the aggregator must not eagerly import the AI/DB graph. Heavy adapters use function-local imports (precedent: `platform_consistency`). A PR1 test asserts importing `health_snapshot_service` does not eagerly import heavy AI/DB modules (mirror `tests/unit/runtime/test_consistency_import_cycle.py`).

### 3.3 Severity mapping (pinned in `test_health_snapshot_service.py`)

`SnapshotStatus = healthy|degraded|critical|unknown` · `FindingSeverity = info|warning|error|critical`

| Source | → status / severity |
|---|---|
| `SectionStatus` clean / skipped / warning / fatal | healthy/info · unknown(or healthy if informational)/info · degraded/warning · (blocking) critical/critical else degraded/error |
| `SummaryStatus` ok/degraded/failed/empty | healthy/degraded/critical/unknown |
| `StartupOutcome.success=False` blocking phase/cog | critical · non-blocking → degraded |
| provider `{"_error":…}` required source | degraded → contributes to overall critical/unknown |
| `ResourceHealthFinding.severity` info/**warn**/error | info / **warning** / error (guild-local; not a global-critical driver) |
| `lifecycle.Phase` FAILED_STARTUP / DRAINING+ / RUNNING / STARTING | critical / degraded / healthy / unknown |
| AI `degraded=True` / `enabled=False` | AI subsystem degraded / disabled — **never** whole-bot critical |

**Overall:** critical if a required invariant failed (lifecycle FAILED_STARTUP, DB unavailable when required, no gateway readiness post-startup, required startup-phase/cog failure); degraded if ≥1 non-blocking failure / recent task terminal failure / unavailable guilds>0 / AI unhealthy / warning-error findings; unknown if no reliable core source / too partial; healthy only if all requested core sources completed and nothing degraded/critical matched.

### 3.4 Redaction boundary (per-audience, per-adapter; pure + testable)

`project_for_audience(snapshot, audience: HealthAudience) -> HealthSnapshot` — pure transform over frozen objects, returns a new frozen object. Tested for **omission** (not masking) with **per-adapter planted leaks**.

| `HealthAudience` | Visibility | Planted-leak omission asserted from |
|---|---|---|
| `GUILD_ADMIN` (`!platform health` default) | Guild-local subsystem statuses + bounded guild-local findings. **No** cross-guild data, provider internals, file/function hints, raw logs, stack traces, env/config, raw IDs. | provider `_error`, `ResourceHealthFinding.message`/`target_id`, AI audit/config fragments, startup/cog-load exception summaries |
| `PLATFORM_OWNER` (bot owner) | Full cross-process/provider summaries, sanitized file/function hints, fingerprints. Still **no** tokens, raw env, raw SQL, arbitrary DB rows, raw stack traces. | same adapters; assert tokens/SQL/traces still stripped even at full scope |
| `PUBLIC` (future AI user scopes) | Basic overall status only. | everything else omitted |

**Hard rule:** never put raw `snapshot_all()`, stack traces, env, tokens, message content, raw SQL, or unbounded IDs into `facts`, an embed, or AI context. `facts` is allowlisted + bounded.

### 3.5 AI boundary (PR5 ✅ #541)

Read-only, bounded, JSON-serializable, scope-gated, operates on the **already-redacted** projection. One coarse tool: `diagnostics_health_snapshot`. AI may explain/summarize/suggest commands+files; may **not** restart, mutate config, edit files, query arbitrary tables, ack/resolve findings, or remediate. Output separates **facts** (tied to a finding/fingerprint) from **suggestions**/**uncertainty**; deterministic fallback always available. **Shipped in #541** — D1 resolved; registered at `min_scope=PLATFORM_OWNER` via the current `build_registry` path (#536 primitives were doc-only; left a `TODO(#536)` to migrate into the `diagnostics` toolset later).

### 3.6 Event / metrics boundary

**No new events PR1-PR5.** Metrics only (collection duration, source-failure counts, redaction outcomes). PR6 may add `platform.health.finding_recorded/resolved` **only** with a real subscriber + `KNOWN_EVENTS` literal + ownership row + payload contract + drift test.

---

## 4. Product decisions

**Answered this session (folded in):** `!platform health` = **admin-gated + guild-local redaction** (owner sees full); startup report = **panel-only** (`!platform startup`), pre-connect webhook kept.

### Blocking — RESOLVED this session

- **D1 — AI scope reachability (before PR5; shared with #536-D5). DECIDED (2026-06-06, attended): option (a).** `_derive_scope` now recognizes the platform owner by verified id (`config.BOT_OWNER_USER_ID == message.author.id`, checked **first**, before guild-owner/permission checks) and returns `AIScope.PLATFORM_OWNER`, so the owner-gated `diagnostics_health_snapshot` tool (PR5) is reachable; this also unblocks #536's platform-owner config. Option (b) — register the tool at `SERVER_OWNER` — was rejected (broader audience). The AI scope seam uses `config.BOT_OWNER_USER_ID` (sync, id-gated, unspoofable) to match the other AI owner seams (`ai_tools.get_user_standing`, `bot_knowledge_service`); the deterministic surface keeps using `bot.is_owner` via `resolve_audience`. Pinned by `tests/unit/services/test_bot_owner_recognition.py`.

### Deferrable (recommended defaults — safe to apply unattended in PR1-PR3)

- **D2 DB criticality:** unavailable = **critical** (Postgres-backed runtime lock).
- **D3 Required cogs:** only `bootstrap_access_cog` failure is **critical**; others degraded.
- **D4 Unavailable guilds:** `>0` → degraded, never critical.
- **D5 Freshness:** cached consistency/readiness older than **300s** → `stale=True`; no core source in window → `unknown`.
- **D6 Optional AI failure:** degrades **AI subsystem only**.
- **D7 Stack traces in Discord:** **never**.
- **D8 Finding retention (PR6):** retain open; TTL resolved/ignored at **30d**; aggregate counters after expiry; per-fingerprint detail cap.
- **D9 Slash UX:** keep the `/platform` hub pattern.
- **D10 `ai_monitor_service`:** create only if a second consumer appears (default: don't, PR5).
- **D11 Findings scope (PR6, new — from ChatGPT):** persist **open + TTL'd resolved/ignored + aggregate-only after expiry** (bounded history aids debugging) rather than current-only. Confirm at PR6.

---

## 5. Final PR sequence

> **Delivery status (2026-06-06): ALL SHIPPED.** PR1 ✅, PR2 ✅, PR3 ✅ in **#537**
> (`1296d25`, `b052a4a`, `aa5b153`); PR4 ✅, PR5 ✅, PR6 ✅ in **#541**. D1 RESOLVED
> (option a, see §4). Remaining: maintainer live-test on the production bot.

Programme = **6 PRs**. **Unattended overnight slice = PR1 → PR2 → PR3** (+ PR4 gated stretch). Every PR ends with both gates: `python3.10 scripts/check_architecture.py --mode strict` (0 errors) **and** `python3.10 scripts/check_quality.py --full` (CI mirror). **If a gate cannot be made green within a PR's own scope, STOP — commit what is green, leave a note, and do not start the next PR.**

### PR1 — Health contracts + aggregator (Codex A+B merged) — ✅ SHIPPED (#537)

- **Goal:** frozen typed read-model + two-lane `health_snapshot_service` + deterministic severity + stable ordering + pure `project_for_audience`. No UI/AI/persistence/events.
- **Files:** NEW `services/health_contracts.py`, `services/health_snapshot_service.py`; read-only **function-local** adapters over the §3.2 sources; `docs/ownership.md` read-contract row.
- **Contracts:** `HealthSnapshot`, `SubsystemHealth`, `OperationalHealthFinding`, `HealthSnapshotRequest`; `SnapshotStatus`, `FindingSeverity`, **`HealthAudience`** (no AIScope import).
- **Tests:** `test_health_snapshot_service.py` (severity table; one failed sync provider → partial/degraded not exception; per-async-source timeout isolation; stable ordering; bounded facts/findings). `test_health_redaction.py` (**per-adapter planted leaks** → assert omission per audience). **Import-safety test** (mirror `test_consistency_import_cycle.py`: importing the service doesn't eagerly import heavy AI/DB). Read-only AST pin (model on `test_ai_readonly_invariants.py`, **not** the economy INV-F file).
- **Manual:** none (pure + unit). **Risks:** heterogeneous payloads → allowlist `facts`; LOC creep. **Rollback:** delete two modules + tests. **Stop:** prod LOC > ~700 → split by lane (ship sync lane + redaction first); any arch error; a projection that can't prove omission.

### PR2 — Deterministic `!platform health` UX — ✅ SHIPPED (#537)

- **Goal:** admin-gated, guild-redacted compact health embed, AI-independent.
- **Files:** `diagnostic_cog.py` (`!platform health`, `@has_permissions(administrator=True)`, **function-local** service import; derive `HealthAudience` from ctx), `_platform_embeds.py` (`build_health_embed`, reuse `clamp_embed`), `platform_panel.py` (Runtime tuple + `_dispatch` case).
- **Tests:** mirror `test_diagnostic_panels_data.py` (panel `_dispatch`) + a command test; `test_cog_size.py` green; `test_help_surface_map_doc.py` if catalogued.
- **Manual (boot the test bot):** embed within limits after `clamp_embed`; panel readable; degraded snapshot caps rows + drilldown (no JSON truncation); admin view hides cross-guild/provider internals.
- **Risks:** cog ceiling; accidental module-top heavy import; embed overflow. **Rollback:** revert 3 files. **Stop:** `diagnostic_cog.py` projected > ~760 LOC → **first** extract the `!platform` group into a `cogs/diagnostic/` submodule as a self-contained mechanical commit (test-covered), then add `health`.

### PR3 — Startup integration (panel-only) — ✅ SHIPPED (#537)

- **Goal:** record extension-load outcomes + reconnect-safe post-ready startup snapshot; `!platform startup`. Pre-connect webhook untouched.
- **Files:** `startup_outcome.py` (**sibling** `ExtensionLoadSnapshot`/`extension_load_recorder` — **do NOT** add to `KNOWN_PHASES`), `bot1.py` (record per-extension in `_load_cogs()`; collect `purpose="startup"` snapshot at the **end** of `on_ready` after `set_phase(RUNNING)`, guarded by a new module-level one-shot mirroring `_startup_duration_observed`), `diagnostic_cog.py` (`!platform startup`), `_platform_embeds.py` (`build_startup_health_embed`).
- **Tests:** one-shot guard test (reconnect re-firing `on_ready` must not double-report); boot-wiring tests; INV-K green if any delayed follow-up uses `tasks.spawn`.
- **Manual (boot + simulate reconnect):** captures a real cog-load failure without racing anchor restore/scheduler setup; multi-reconnect doesn't duplicate.
- **Risks:** **reconnect double-fire** (implement the one-shot, don't assume); document ordering vs `set_phase(RUNNING)` L200-201. **Rollback:** revert `on_ready` block + recorder. **Stop:** can't prove one-shot under simulated reconnect → don't merge PR3, keep PR1-PR2.

### PR4 — Structured observations / grouped errors — ✅ SHIPPED (#541)

> **Shipped (re-scoped from the sketch below):** the PR1 adapters already emit stable
> per-source fingerprints, so PR4 did **not** rewrite them — it ADDED an opt-in grouped
> recent-error subsystem (`services/health_observations.py` +
> `health_snapshot_service._errors_subsystem`) over a bounded `recent_errors` diagnostics
> provider, gated by `HEALTH_GROUPED_FINDINGS` (default off → legacy `!recent_errors` is
> the unchanged fallback). `!platform health` renders `(×N)`.

- **Goal:** safe classification/grouping of current-process failures; structured observations at a few high-value boundaries; bounded grouped-error adapter; ring buffer stays fallback.
- **Files:** `_log_buffer.py` or a new classifier; selected boundaries (provider-failure, cog-load, DB-timeout) emit structured observations; aggregator wiring.
- **Tests:** fingerprint determinism (`<category>:<subsystem>:<operation>:<exc-type>:<code>`; normalized repeats dedupe; meaningful diffs distinguish); redaction of IDs/tokens/SQL/user-text from fingerprints + messages.
- **Risks:** fragile log-parsing → prefer structured observations at source; never feed raw buffer messages to AI. **Stop (autonomy guard):** if fingerprints look unstable on real logs, ship grouping **disabled** (keep deterministic `recent_errors`) and stop — do **not** iterate on heuristics unattended.

### PR5 — AI tool + explainer — ✅ SHIPPED (#541)

✅ `diagnostics_health_snapshot` registered at `min_scope=PLATFORM_OWNER`; D1 resolved (`_derive_scope` → `PLATFORM_OWNER` by verified id); `_audience_for_scope` boundary + bounded `snapshot_to_payload` (`schema_version=1`); `build_registry` gained a `None`-tolerant `bot` kwarg. #536's `AIToolDescriptor`/`diagnostics` toolset were doc-only, so the current `build_registry` path is used with a `TODO(#536)` to migrate. The optional panel "Ask AI to explain" was **deferred** (the tool itself is reachable; an AI-on render path can't be sandbox-verified). Tests mirror `test_ai_tools.py`.

### PR6 — Persistent findings — ✅ SHIPPED (#541)

✅ Migration `057` (`operational_health_findings` + an `operational_health_finding_aggregates` companion), sole-writer `services/health_findings_service.py` over pool-only `utils/db/health_findings.py` (fingerprint dedupe, reopen-on-recurrence, keep-ignored), recorded + pruned best-effort from `bot1._report_startup_health` keyed to `services.runtime.BOOT_ID`, 30-day TTL with roll-up-to-aggregates (D8/D11), `!platform findings [open|resolved|ignored|all]`, metrics only (no new events). Sole-writer AST guard `test_inv_health_findings_service.py`.

---

## 6. Implementation checklist (executable top-to-bottom)

### Before coding (the unattended session)
- [ ] Read `.session-journal.md`, `.claude/CLAUDE.md`, `docs/AGENT_ORIENTATION.md`, this plan; confirm HEAD and "fully tested" state.
- [ ] Baseline both gates green on a clean tree.
- [ ] Re-confirm `ls disbot/migrations | tail -1`, `wc -l disbot/cogs/diagnostic_cog.py` (647), and that `core/runtime/ai/contracts.py` is still the inert `AIScope` home.
- [ ] Commit the approved plan as `docs/bot-awareness-implementation-plan.md` and add a cross-link banner atop `docs/bot-awareness-diagnostics-plan.md`.

### PR1
- [ ] `services/health_contracts.py` — frozen dataclasses + `SnapshotStatus`/`FindingSeverity`/`HealthAudience`; **no AI import**; confirm `check_architecture --mode strict` (no cycle/heavy-dep).
- [ ] `services/health_snapshot_service.py` — both lanes; each async source in its own `asyncio.wait_for`; **function-local** heavy adapters; allowlist `facts`; never mutate.
- [ ] Pin severity table (§3.3); per-adapter redaction omission tests; import-safety test; read-only AST pin.
- [ ] Docs: ownership read-contract row; note sync/async boundary in `docs/runtime_contracts.md` if warranted. **Gate.** LOC stop-check.

### PR2
- [ ] `build_health_embed()` (reuse `clamp_embed`; cap rows + drilldown). `!platform health` (function-local import; derive `HealthAudience` from ctx; keep small — re-check `wc -l` vs ~760). Runtime tuple + `_dispatch` case.
- [ ] Docs: `docs/help-command-surface-map.md` (+ pin test) if catalogued.
- [ ] **Boot test bot**; verify `!platform health` + panel item (limits + admin redaction). **Gate** + `test_cog_size.py`.

### PR3
- [ ] Sibling `ExtensionLoadSnapshot`/recorder (NOT `KNOWN_PHASES`). `bot1.py` per-extension recording + post-ready one-shot snapshot. `!platform startup` + embed.
- [ ] One-shot reconnect test; INV-K green. **Boot + simulate reconnect.** **Gate.**

### PR4 (only if gated-in)
- [ ] Structured observations at ≤3 boundaries + grouped-error adapter + fingerprint/redaction tests. If unstable → ship disabled + stop. **Gate.**

### Session close
- [ ] Append a dated `.session-journal.md` entry (union-merge safe). Open the end-of-session PR(s) for the slice.

---

## 7. Risks and mitigations

| Category | Risk | Mitigation |
|---|---|---|
| Architecture | "Health god service" | Thin adapters over canonical read seams; read-only AST pin |
| Privacy/redaction | Per-adapter leaks (IDs/SQL/traces/secrets) | `project_for_audience` pure transforms; **per-adapter** omission tests; allowlist `facts`; no traces in Discord |
| AI hallucination | Invented health / false root cause | Redacted bounded facts; facts vs suggestions; deterministic fallback; live "did it call the tool?" check (PR5) |
| AI reachability | PLATFORM_OWNER tool dead surface | Resolve D1 before PR5; shared with #536 |
| Performance/incident | Async probes slow/worsen incidents | Purpose-based checks; per-source + overall timeouts; fresh consistency only on request; cached default; partial snapshots |
| Startup race/reconnect | Duplicate startup reports | One-shot guard mirroring `_startup_duration_observed`; collect after `set_phase(RUNNING)`; simulated-reconnect check |
| Persistence/retention | Findings grow forever (PR6) | Sole-writer; TTL + caps + aggregate-only; label source/session; additive idempotent migration |
| Discord embed UX | Oversized/cluttered embeds | Reuse `clamp_embed`; cap rows + drilldown; live render check |
| Import-cycle/LOC/invariant | services→views slip; aggregator deps at startup; cog>800; pinned drift | arch gate; **function-local** heavy adapters + import-safety test; extract `!platform` group if >760; never mutate `ReadinessSnapshot`/`KNOWN_PHASES`; INV-K |
| **Unattended autonomy** | Agent iterates on a fragile/ambiguous step while maintainer sleeps | Hard per-PR stop-conditions; no PR5 (D1) / PR6 (durable) without input; PR4 ships disabled rather than heuristic-tuning; STOP and report instead of guessing |

---

## 8. Alignment with PR #536 (AI tool orchestration) — reuse, don't duplicate

#536 is a **later** programme (assumes this roadmap is delivered) and is mostly BTD6 — **out of this session's scope**. But it owns AI-tool primitives my **PR5** must align with, per the "no duplicate abstractions" rule:

- **`AIToolDescriptor`** (richer metadata wrapping `AIToolSpec`: toolsets, task_affinity, cost_class, freshness, parallel_safe, preflight_safe, result_contract) and a **named `diagnostics` toolset** that #536 *already reserves* for "future health snapshot tools." → **PR5 registers `diagnostics_health_snapshot` into that `diagnostics` toolset** if #536's catalogue has landed; otherwise via the current `build_registry` path with a TODO to migrate. Do **not** invent a second tool-metadata abstraction.
- **`AIToolBudget` / `AIToolChoice` / `ToolRequirementMode`** (provider-neutral request extensions). → PR5's tool is naturally `cost_class="cheap"`, `freshness="cached"` (sync lane) or `"live"` (async lane), `parallel_safe`, **not** `preflight_safe` (it takes a scope/audience argument). Consume these if present; don't build them.
- **`AIOrchestrationTrace` / safe trace summary** → the PR5 "explanation completed" audit/metric should emit a #536-style bounded trace (no raw reasoning/results), not a bespoke one.
- **Answer contracts** (`research_summary` / a future `diagnostics_explanation`) → the explainer's "facts vs suggestions vs uncertainty" should be a typed answer contract, aligning with #536 §10.
- **Shared dependency:** #536-**D5** ("who may configure toolsets — admin/server-owner/platform-owner") needs the same **platform-owner scope plumbing** as my **D1**. Fixing `_derive_scope` once serves both → consider a tiny standalone "platform-owner scope" PR ahead of either programme's AI phase.

**Net:** #536 changed **nothing** in PR1-PR3 (deterministic, no AI); it only constrained PR5, which shipped in #541 via the current `build_registry` path (#536's primitives were doc-only). Captured here so a future toolset migration reuses #536's contracts.

---

## 9. Final handoff prompt (copy-paste for the UNATTENDED implementation session)

> **HISTORICAL — superseded.** This was the prompt for the original unattended PR1–PR3
> session. PR4–PR6 and D1 have since been completed (#541); the "Do NOT start PR5/PR6"
> instruction below no longer applies. Kept for provenance.

```
You are Claude Opus 4.8 implementing the approved Bot-Awareness / AI-Assisted
Diagnostics plan for SuperBot. The maintainer is ASLEEP and has authorized an
unattended structured session. Execute the slice PR1 → PR2 → PR3 in order; do PR4
ONLY as a gated stretch (see stop rules). Do NOT start PR5 or PR6 — PR5 is blocked
on a product/security decision (D1), PR6 is durable state to defer. Branch:
claude/fervent-turing-J1giu.

Read first: .session-journal.md, .claude/CLAUDE.md, docs/AGENT_ORIENTATION.md, the
approved plan (docs/bot-awareness-implementation-plan.md — commit it from the plan
file first, and add a cross-link banner atop docs/bot-awareness-diagnostics-plan.md),
docs/architecture.md, docs/ownership.md, docs/runtime_contracts.md, docs/helper-policy.md.

NON-NEGOTIABLES
- AI-assisted diagnostics OVER the existing observability stack. No
  bot_awareness_service, no second provider registry. Do not make
  diagnostics_service.snapshot_all() async or mutating. core/runtime must not import
  services/cogs; services must not import views/cogs.
- Contracts: NEW services/health_contracts.py — frozen HealthSnapshot/SubsystemHealth/
  OperationalHealthFinding/HealthSnapshotRequest + enums SnapshotStatus{healthy,
  degraded,critical,unknown}, FindingSeverity{info,warning,error,critical},
  HealthAudience{PUBLIC,GUILD_ADMIN,PLATFORM_OWNER}. NO AIScope import (deterministic
  health must not depend on AI vocab).
- Aggregator: NEW services/health_snapshot_service.py — two lanes (collect_cached_snapshot
  sync + async collect_snapshot(request) with per-source asyncio.wait_for), deterministic
  severity per the pinned table, stable ordering, bounded allowlisted facts, pure
  project_for_audience(snapshot, audience). HEAVY-SOURCE ADAPTERS IMPORT FUNCTION-LOCALLY
  (ai_config_projection_service / utils.db import heavy graphs at module scope; do not
  pull them at import time). Never mutate.
- Redaction is a pure transform tested for OMISSION with PER-ADAPTER planted leaks:
  provider _error strings, ResourceHealthFinding.message/target_id, AI audit/config
  fragments, startup/cog-load exception summaries. GUILD_ADMIN hides cross-guild/provider
  internals/file hints/IDs; PLATFORM_OWNER full but still strips tokens/SQL/traces.
- !platform health is admin-gated; derive HealthAudience from Discord context (admin →
  GUILD_ADMIN, bot owner → PLATFORM_OWNER). Reuse core/runtime/interaction_helpers.
  clamp_embed; build_health_embed in cogs/diagnostic/_platform_embeds.py; Runtime-category
  item + _dispatch case in views/diagnostic/platform_panel.py; import the service
  FUNCTION-LOCALLY in the cog/embeds.
- PR3 startup is PANEL-ONLY (no webhook/admin-channel push for the post-ready report;
  keep the existing pre-connect webhook). Add a SIBLING extension-load recorder — do NOT
  add to startup_outcome.KNOWN_PHASES (doc-test-pinned). Collect the post-ready snapshot
  at the END of on_ready AFTER set_phase(RUNNING), guarded by a NEW module-level one-shot
  flag mirroring lifecycle._startup_duration_observed. Any delayed task uses
  core.runtime.tasks.spawn (INV-K).

VERIFIED TRAPS
- ResourceHealthFinding.severity is "warn" → map to "warning".
- Do NOT mutate ReadinessSnapshot or KNOWN_PHASES (both doc-pinned:
  test_smoke_test_checklist.py, test_startup_outcome.py).
- diagnostic_cog.py is 647/800 LOC. If PR2/PR3 projects it over ~760, FIRST extract the
  !platform group into a cogs/diagnostic/ submodule as a self-contained, test-covered
  mechanical commit, THEN add commands.
- Model the read-only AST pin on tests/unit/services/test_ai_readonly_invariants.py
  (NOT the economy INV-F file). Model the import-safety test on
  tests/unit/runtime/test_consistency_import_cycle.py.

GATES (after EACH PR, before the next): python3.10 scripts/check_architecture.py
--mode strict (0 errors) AND python3.10 scripts/check_quality.py --full (CI mirror).
Boot the test bot (runbook in .session-journal.md) for PR2 (render/redaction) and PR3
(simulated reconnect, no duplicate report).

UNATTENDED STOP-CONDITIONS (protect the sleeping maintainer):
- If a gate can't go green within a PR's own scope → STOP. Commit what's green, write a
  .session-journal.md note, open a PR for the completed PRs, and end. Do not thrash.
- PR1 prod LOC > ~700 → split by lane (sync lane + redaction first).
- PR3 can't prove the reconnect one-shot → ship PR1-PR2 only.
- PR4 fingerprints unstable on real logs → ship grouping DISABLED (keep deterministic
  recent_errors) and stop; do not tune heuristics unattended.
- Never start PR5 (needs D1 decision) or PR6 (durable state) without the maintainer.

DELIVER: commit each PR as cleanly-separated, independently-revertable commits on
claude/fervent-turing-J1giu; open the end-of-session PR(s) for the slice (foundation /
UX / startup clearly delineated). Append a dated .session-journal.md entry. If you
stopped early, say exactly where and why in the PR body and the journal.
```

---

## Verification (how this plan is validated end-to-end)

- **Per PR:** `check_architecture.py --mode strict` (0 errors) + `check_quality.py --full` (CI mirror on Python 3.10).
- **PR1:** unit + AST — severity table, source-failure isolation, async-timeout isolation, stable ordering, bounds, **per-adapter redaction omission**, **import-safety**, read-only pin.
- **PR2:** panel/command tests + `test_cog_size.py`; **live** boot — `!platform health` + panel within Discord limits; admin redaction confirmed.
- **PR3:** reconnect one-shot test + **live** multi-reconnect (no duplicate).
- **PR4 (if gated-in):** fingerprint determinism + redaction; ships disabled if unstable.
- **PR5/PR6 (✅ #541):** D1 resolved; the model calls the tool live (owner scope); the sole-writer AST guard fails on a planted violation; migration `057` applied.
```
```
