# AI-Assisted Bot Awareness and Diagnostics: Repository Map and Delivery Plan

**Status:** planning and brainstorming document; no implementation is authorized by
this document alone  
**Verified against:** the current repository worktree on 2026-06-06  
**Audience:** maintainers and follow-up implementation agents

## 1. Executive decision

SuperBot should implement **AI-assisted diagnostics over the existing observability
stack**, not a parallel `bot_awareness_service` and not an AI cog that inspects raw
internals.

The target architecture is:

```text
existing diagnostics providers / startup outcomes / metrics / domain health readers
                                  |
                                  v
                    typed health snapshot service
                (aggregation, severity, bounds, redaction)
                                  |
                +-----------------+------------------+
                |                                    |
                v                                    v
     deterministic DiagnosticCog / Platform UI     read-only AI tools
                |                                    |
                v                                    v
       operator-visible facts              optional AI explanation
```

The AI remains an interpreter. Deterministic services remain the source of facts,
and deterministic commands remain usable when AI is disabled or unhealthy.

The repository is **foundation-ready but not feature-ready**. It already contains
most of the collection seams and operator surfaces. It does not yet contain a
unified operational `HealthSnapshot`, cross-source severity/redaction rules,
recurring operational finding history, grouped failure fingerprints, or AI tools
for operational diagnostics.

## 2. Non-negotiable architecture rules

1. Keep `services.diagnostics_service` as the process-local, synchronous,
   read-only provider registry. Do not add a second registry named
   `bot_awareness_service`.
2. Add a typed aggregation/read-model layer above existing sources. It may collect
   asynchronous checks, but it must not turn `diagnostics_service.snapshot_all()`
   into a blocking or mutating operation.
3. Put deterministic operator UX in the existing `DiagnosticCog` / Platform hub.
   Do not create a separate `/bot` diagnostics island.
4. AI diagnostic tools must use the existing `services.ai_tools` contract: offered
   only at sufficient `AIScope`, read-only, bounded, JSON-serializable, and
   redacted **before** model input.
5. AI explanations are additive. Snapshot generation, startup reports, findings,
   and operator commands must work without an AI provider.
6. Prefer structured provider outputs, startup outcomes, task snapshots, metrics,
   and domain health readers over parsing log text. Treat log inspection as a
   bounded fallback/legacy source.
7. The AI may suggest what to inspect next. It may not restart the bot, alter
   configuration, edit files, query arbitrary tables, acknowledge findings, or
   resolve findings.
8. New durable state must have one service owner, additive/idempotent migrations,
   bounded retention, and documented readers/writers.
9. New EventBus events are for durable lifecycle transitions, not every warning or
   log line. Every event must be catalogued, documented, and tested.
10. Do not expose raw stack traces, environment values, tokens, message content,
    or unbounded identifiers to the model or Discord surfaces.

## 3. Verification of the draft claims

### 3.1 Claims that are correct

| Draft claim | Verdict | Repository evidence / implication |
|---|---|---|
| AI should interpret structured health rather than inspect internals directly. | Correct | `services.ai_tools` already defines tools as read-only, small, JSON-serializable, and scope-gated. This is the contract diagnostics tools should extend. |
| One failed diagnostics provider must not break a full snapshot. | Already implemented | `diagnostics_service.snapshot_all()` catches provider exceptions and substitutes an `_error` payload. The future aggregator must preserve this isolation. |
| Deterministic diagnostics must work without AI. | Correct and repository-aligned | The AI integration map explicitly requires raw platform embeds and deterministic recent-error lists as fallbacks. |
| Health collection should be reusable by commands, panels, startup reports, and AI. | Correct | Existing provider, platform embed, startup outcome, and AI tool seams support this shape. A typed aggregate is the missing connector. |
| AI health and whole-bot health are different. | Correct | AI already has separate configuration projections, diagnostics counters, readiness, and decision-audit services. These should feed an AI subsystem summary rather than define global health. |
| Repeated failures should be grouped by fingerprint. | Correct but absent | The current recent-log ring buffer is bounded but stores only timestamp, level, and message; it does not fingerprint or persist recurrence. |
| Redaction and permission tiers must be explicit. | Correct but incomplete today | `AIScope` gating exists, but there is no diagnostics-specific redaction policy or unified redacted health snapshot. |

### 3.2 Claims that need correction

| Draft claim | Correction |
|---|---|
| “Add a central `bot_awareness_service`.” | Do not add it. `services.diagnostics_service` is already the central process-local provider registry. Add `health_snapshot_service` as an aggregator/read model above it. |
| “Add a health provider registry.” | A general registry already exists. Add adapters/providers incrementally; do not create a competing `HealthProvider` registry in the first phase. Revisit a typed provider protocol only if normalization proves too fragile. |
| “Add `/bot health`, `/bot logs recent`, `/bot cogs`, `/bot startup-report`.” | Extend `!platform` and the existing privileged `/platform` entry/panel. Existing commands already include status, runtime, lifecycle, tasks, consistency, readiness, and standalone recent-log/error commands. |
| “Add a new admin diagnostics panel.” | Extend `views.diagnostic.platform_panel` first. It already groups platform diagnostics and renders existing embed builders. |
| “Add startup self-review/reporting.” | SuperBot already records a subset of startup outcomes, composes `platform_readiness`, and sends a deterministic startup-summary webhook before Discord connects. The new work is to broaden and normalize that report, not invent it. |
| “Add recent log inspection.” | Recent logs and recent errors already use a bounded in-process ring buffer. The missing work is safe classification/grouping and structured observations, not basic access. |
| “Add AI self-awareness.” | AI diagnostics/config/readiness projections already exist. Build an adapter from those canonical read models; do not independently inspect AI configuration/provider state. |
| “Add structured lifecycle events for every important observation.” | Add only a small set of durable transition events. High-volume observations belong in metrics/logs/providers. |
| “HealthSnapshot should list all loaded cogs and raw findings.” | Snapshot output must be bounded and scope-redacted. Counts and compact summaries should be default; detailed names/hints should require elevated scope and explicit drilldown. |

### 3.3 Claims that are only partly true

- **Startup report coverage:** a deterministic summary exists, but the recorder only
  covers four catalogue-build phases. Cog load failures are reported separately by
  webhook and are not normalized into the startup outcome/readiness model. Gateway
  readiness, slash sync, DB availability, persistent view registration, and AI
  state are not all represented in one startup snapshot.
- **Cog status:** loaded cog names are logged at `on_ready`, and individual load
  failures trigger webhook reporting, but there is no durable/bounded cog-health
  read model with expected/missing/failed distinctions.
- **Metrics health:** Prometheus metrics and HTTP `/health`, `/ready`, `/lifecycle`,
  and `/metrics` endpoints exist, but there is no safe metric snapshot/derived
  summary API for Discord or AI use.
- **Findings:** domain-specific findings already exist, especially
  `ResourceHealthFinding`, while platform consistency has typed section results.
  There is no single operational finding contract or persistent finding lifecycle.
- **Scopes:** `AIScope` supports user, moderator, admin, server owner, platform
  owner, and system ranks. Existing deterministic platform commands are generally
  administrator-gated; the proposed diagnostics redaction/access matrix still
  needs a deliberate product decision.

## 4. Current repository capability map

### 4.1 Collection and observation sources

| Existing source | What it provides now | Readiness for aggregation | Important constraint |
|---|---|---:|---|
| `services.diagnostics_service` | Registered synchronous provider snapshots and fail-isolated `snapshot_all()` | High | Providers are sync and process-local; async DB/API probes must live elsewhere. |
| Registered diagnostics providers | Runtime lock, lifecycle, managed tasks, slow paths, caches, bindings, schemas, feature flags, platform readiness, server logging, automation, and more | High | Shapes are heterogeneous and not all payloads are safe for every scope. |
| `services.platform_consistency` | Typed consistency report, blocking sections, cached readiness snapshot, startup outcomes, catalogue state, task names | High | Fresh consistency collection is async; provider exposes cached/read-only state. |
| `core.runtime.startup_outcome` | Bounded, typed, short-error startup phase results and deterministic summary status | High but narrow | Only four known phases are currently recorded. |
| `core.runtime.lifecycle` | Phase, pending transition, recent events, startup duration observation | High | Process-local lifecycle only. |
| `core.runtime.tasks` | Managed task state and task outcome metrics | High | Needs safe summary rules; task names can be useful but potentially verbose. |
| `services.metrics` | Prometheus counters, gauges, and histograms for runtime/platform/AI behavior | Medium | There is no canonical bounded “metrics snapshot” read model. Prometheus collectors are not automatically safe AI context. |
| `healthserver.py` | HTTP liveness, readiness, lifecycle, and Prometheus endpoints | Medium | It directly knows the bot object; it should consume a shared safe summary later rather than become the aggregation owner. |
| Diagnostic log ring buffer | Last 500 `bot.*` INFO+ records; recent level-filtered reads | Medium | Plain messages, process-local only, no exception metadata/fingerprint/category, and current helpers can expose message text. |
| AI config/diagnostics/readiness/audit services | Canonical operator-facing AI configuration and provider counters/readiness | High | Must be adapted from canonical read models, never re-resolved independently. |
| `services.resource_health` / setup readiness | Typed guild binding/resource findings and summaries | High for guild-local health | This is setup/resource health, not a global operational finding model. Preserve that distinction. |
| Webhook reporter | Startup summary, cog load failures, identity findings, task failures, lifecycle alerts | Medium | It is an output/reporting surface, not a source of truth. |

### 4.2 Existing deterministic operator surfaces

The existing `DiagnosticCog` and Platform hub already cover much of the proposed
command set:

- general diagnostics hub;
- bot status, latency, system information, database checks, command inventory;
- bounded recent logs and recent errors;
- `!platform status`, `setup-readiness`, `runtime`, `lifecycle`, `tasks`, `slow`,
  `consistency`, and many registry/resource/platform diagnostics;
- a privileged `/platform` slash entry that opens the Platform hub;
- a Platform panel with categorized read-only selections and shared embed builders.

This means the first UX increment should be small and repo-consistent:

- `!platform health` and a matching Platform panel item;
- `!platform startup`;
- `!platform findings` only after a stable finding read model exists;
- `!platform ai-health` as a normalized subsystem drilldown;
- `!platform subsystem <name>` only if a bounded generic drilldown is safe.

Do not duplicate existing `runtime`, `lifecycle`, `tasks`, `consistency`,
`setup-readiness`, `query_logs`, or `recent_errors` behavior. Link or compose it.

### 4.3 Existing AI seam

`services.ai_tools` is the correct tool registry. It already:

- ranks `AIScope` values;
- omits tools above the caller's privilege entirely;
- attaches pure `AIToolSpec` data to requests;
- requires read-only, bounded, JSON-serializable responses;
- rejects write-capable tools as out of scope.

No operational diagnostics tools exist yet. The documented AI integration map
already identifies this connector path:

```text
Platform panel -> AI monitor service -> diagnostics snapshots -> AIGateway
               -> read-only summary embed
```

A future `services.ai_monitor_service` should orchestrate optional explanation of
already-redacted snapshot data. It must not collect raw facts itself.

### 4.4 Existing persistence and ownership seam

The migration sequence currently ends at `056_role_threshold_role_id.sql`.
Persistent operational findings would therefore need a new additive migration and
an explicit owner such as `services.health_findings_service`.

The ownership contract requires one write owner. Diagnostic commands, embeds, the
AI monitor, and tools may read through that service; they must not write the table
directly.

### 4.5 Existing event and observability seam

The EventBus is in-process and catalogue-enforced. Unknown event use warns and
increments a metric. New events require:

1. a literal in `core.events_catalogue.KNOWN_EVENTS`;
2. an ownership/payload row in `docs/ownership.md`;
3. a payload contract in the emitter module;
4. tests that prevent catalogue drift;
5. idempotent/best-effort consumers because event handlers are isolated and timed.

The observability contract already requires managed tasks, warning logs for
recoverable anomalies, and metrics for silent failure paths. Health work should
consume and extend this contract, not bypass it.

## 5. Important design collisions to resolve before coding

### 5.1 “Health finding” already means more than one thing

`ResourceHealthFinding` is a mature guild resource/setup contract. A new global
`HealthFinding` name risks ambiguity. Choose one of these options in the first ADR
or implementation PR:

- **Recommended:** name the global contract `OperationalHealthFinding`, leaving
  `ResourceHealthFinding` untouched; or
- use `HealthFinding` only inside a dedicated `models/operational_health.py` module
  and document the distinction prominently.

Do not silently retrofit resource findings into a global schema. Adapt them at the
aggregation boundary.

### 5.2 Severity vocabulary is inconsistent

The drafts use `healthy`, `degraded`, `attention`, and `critical`; existing
resource findings use `info`, `warn`, and `error`; startup uses `ok`, `degraded`,
`failed`, and `empty`; platform consistency uses its own section statuses.

Define two separate canonical concepts:

- **snapshot status:** `healthy | degraded | critical | unknown`;
- **finding severity:** `info | warning | error | critical`.

Then publish deterministic mapping rules from each existing source. Avoid
`attention` because it blurs status and severity.

### 5.3 Sync provider registry versus async checks

`diagnostics_service` providers are intentionally synchronous. Database ping,
external API probes, fresh platform consistency checks, and guild-resource health
are asynchronous. The aggregator must therefore have two lanes:

- `collect_cached_snapshot()` for sync/process-local facts;
- `async collect_snapshot(request)` for bounded async checks selected by scope and
  purpose.

The async collector may call `diagnostics_service.snapshot_all()` as one input.
It must apply timeouts and isolate every async source just as the registry isolates
sync providers.

### 5.4 Process-local versus durable truth

Diagnostics providers, log ring buffers, lifecycle state, and startup outcomes are
process-local. A persistent findings table survives restarts. Snapshots and
findings must label their source and process/session identity so operators do not
mistake an old durable recurrence count for a current-process error count.

A future design should reuse the existing runtime/session identity where possible
rather than invent an unrelated boot identifier.

## 6. Proposed contracts

The exact module location should follow existing repository conventions; a single
`models/` package does not currently appear to be the dominant pattern. Prefer
service-local frozen dataclasses unless maintainers intentionally establish a
shared model package.

### 6.1 `SubsystemHealth`

Suggested minimum fields:

```python
@dataclass(frozen=True)
class SubsystemHealth:
    name: str
    status: SnapshotStatus
    summary: str
    generated_at: datetime
    findings: tuple[OperationalHealthFinding, ...] = ()
    facts: Mapping[str, JsonValue] = field(default_factory=dict)
    source: str = "unknown"
    stale: bool = False
```

Rules:

- `facts` is bounded and allowlisted, never an arbitrary provider dump;
- `summary` is deterministic, not AI-generated;
- a failed provider produces `unknown` or `degraded`, not an exception;
- source timestamps/staleness are explicit;
- detailed drilldown is a separate operation, not an unbounded `facts` field.

### 6.2 `OperationalHealthFinding`

Suggested minimum fields:

```python
@dataclass(frozen=True)
class OperationalHealthFinding:
    fingerprint: str
    severity: FindingSeverity
    category: str
    message: str
    first_seen_at: datetime | None = None
    last_seen_at: datetime | None = None
    occurrence_count: int = 1
    related_subsystem: str | None = None
    related_command: str | None = None
    related_provider: str | None = None
    file_hint: str | None = None
    suggested_next_step: str | None = None
    source: str = "unknown"
```

Rules:

- `message`, `file_hint`, and `suggested_next_step` are short and sanitized;
- no raw traceback or raw environment/config value;
- fingerprints are deterministic and exclude volatile IDs/timestamps;
- file hints should come from trusted mappings/structured exception metadata, not
  AI guesses presented as facts;
- persistent status (`open | resolved | ignored`) belongs to the findings service
  record/read model, not necessarily the immutable observation itself.

### 6.3 `HealthSnapshot`

Suggested minimum fields:

```python
@dataclass(frozen=True)
class HealthSnapshot:
    snapshot_id: str
    generated_at: datetime
    purpose: str
    status: SnapshotStatus
    summary: str
    subsystems: tuple[SubsystemHealth, ...]
    findings: tuple[OperationalHealthFinding, ...]
    partial: bool = False
    redaction_scope: AIScope | None = None
```

Rules:

- stable ordering for deterministic tests and diffs;
- bounded number of subsystems/findings/facts;
- `partial=True` if any requested source timed out, failed, or was omitted;
- do not store raw provider snapshots inside the public object;
- snapshot IDs should support comparison/persistence without leaking secrets;
- an AI-facing projection is generated from this object after redaction.

### 6.4 Collection request

Use an explicit request object rather than a loose `scope` string:

```python
@dataclass(frozen=True)
class HealthSnapshotRequest:
    purpose: Literal["summary", "startup", "guild", "subsystem", "ai_context"]
    ai_scope: AIScope
    guild_id: int | None = None
    subsystem: str | None = None
    include_recent_logs: bool = False
    include_persistent_findings: bool = True
```

This makes expensive checks, data boundaries, and redaction intent testable.

## 7. Source adapters and initial health areas

Do not make every subsystem implement a new provider before delivering value.
Build adapters around existing sources first.

| Health area | Initial source | First-phase output |
|---|---|---|
| Runtime/lifecycle | lifecycle diagnostics, runtime lock, uptime/health facts | lifecycle phase, readiness, uptime, pending transition, compact lock state |
| Diagnostics registry | `registered_names()` + `snapshot_all()` | provider count, provider failures, allowlisted compact facts |
| Managed tasks | tasks diagnostics + task metrics | active count, known failed outcomes where derivable, compact names at elevated scope |
| Platform readiness | cached `platform_readiness` provider | startup phase outcomes, catalogue readiness, cached consistency blockers |
| Platform consistency | existing report/cache | compact blocker summary; fresh async collection only on explicit operator request |
| Discord/guild | bot/guild cache adapter | guild count, unavailable count, latency; guild-local facts only when authorized |
| Cogs/extensions | `config.INITIAL_EXTENSIONS` plus a new small recorder/adapter around the load path | loaded count and failed/missing configured extensions; blocking versus optional still needs an explicit contract |
| Database | bounded ping/schema/migration adapter | reachable/timeout/unknown, migration readiness; no arbitrary table inspection |
| AI | AI config projection + AI diagnostics/readiness/audit summaries | configured/readiness/provider counters/last bounded failure summary |
| Logs | ring-buffer grouping adapter | counts and sanitized grouped fingerprints; raw recent messages remain deterministic operator-only fallback initially |
| Resource/setup | resource health and setup readiness adapters | guild-local blockers summarized separately from process health |
| External APIs | opt-in subsystem adapters | configured/degraded/unknown and last structured failure; never probe every API on every summary |

## 8. Deterministic severity aggregation

The aggregator must use published rules, not intuition or AI interpretation.
Recommended initial rules:

1. `critical` if a required runtime invariant is failed: lifecycle failed,
   database unavailable when required for serving, no gateway readiness after
   startup, or a required startup phase/cog failure classified as blocking.
2. `degraded` if at least one non-blocking provider/check fails, a managed task has
   a recent terminal failure, unavailable guilds are non-zero, AI is unhealthy but
   AI is optional, or warning/error findings exist without a critical blocker.
3. `unknown` if no reliable core sources are available or the snapshot is too
   partial to classify.
4. `healthy` only if all requested core sources completed and no degraded/critical
   rule matched.

Open questions that must be encoded explicitly:

- Is database availability always critical, or does it depend on lifecycle/purpose?
- Which cogs/extensions are required versus optional?
- Does one unavailable guild degrade global health?
- How old may a cached consistency/startup/API result be before it becomes unknown?
- Does an unhealthy optional AI provider degrade whole-bot health? Recommended:
  report AI as degraded while leaving whole-bot health healthy unless an AI-required
  capability is being evaluated.

## 9. Redaction and access model

Redaction is a transformation of trusted structured data **before** Discord render
or model input. It is not a prompt instruction asking the model to hide secrets.

| Scope | Proposed visibility |
|---|---|
| Public/user | Basic online/healthy/degraded/offline-style status only; no provider names, IDs, logs, configuration, or findings. |
| Moderator | Optional guild-local availability/command summary only; no logs, cross-guild data, provider details, or file hints. |
| Admin | Guild-local setup/resource/command health and bounded findings; no cross-guild data, raw logs, stack traces, env/config values, or sensitive provider internals. |
| Server owner | Deeper guild-local diagnostics, bounded command/config health, and sanitized fingerprints. |
| Platform owner/system | Cross-guild/process/provider summaries, sanitized file/function hints, and fingerprints; still no tokens, raw env, raw config, arbitrary DB rows, or raw stack traces in AI context. |

Initial recommendation:

- ship deterministic platform health to current administrator-gated surfaces;
- ship AI diagnostic tools only for `PLATFORM_OWNER` first;
- expand to server-owner/admin scopes after redaction tests and live verification;
- keep stack traces in logs/webhook incident channels, not AI context or normal
  Discord diagnostic embeds.

Required redaction tests should seed secret-like tokens, Discord IDs, SQL text,
multiline exceptions, and message content into source payloads and prove that each
projection removes or replaces them.

## 10. Log grouping and failure fingerprints

The current ring buffer is useful but not a durable observability backbone. Improve
it incrementally:

### Near-term safe classifier

- classify only bounded recent in-memory records;
- count levels over a fixed window or available buffer horizon;
- normalize known structured patterns (provider failure, cog load failure, DB
  timeout, command failure, AI provider failure, rate limit);
- strip volatile IDs, timestamps, and quoted user content before fingerprinting;
- return grouped counts and short sanitized summaries;
- do not send raw log messages to AI.

### Preferred structured path

Add structured operational observations at the original failure boundaries where
possible. A structured observation may contain category, exception type, trusted
subsystem/command/provider identifiers, occurred-at time, and sanitized summary.
It should feed metrics/current snapshots first. Persistence is a later, explicit
step.

### Fingerprint shape

```text
<category>:<subsystem-or-provider>:<operation>:<exception-type>:<normalized-code>
```

Examples:

```text
diagnostics.provider_failed:platform_readiness:snapshot:RuntimeError
cog.load_failed:cogs.btd6_cog:load_extension:ImportError
database.timeout:btd6_context:get_fact_context:TimeoutError
ai.provider_failed:openai:request:rate_limit
```

Never include raw user text, guild/channel/user IDs, tokens, full SQL, or complete
exception messages in fingerprints.

## 11. Persistent finding lifecycle (later phase)

Persistence should not block the first useful health summary. Once observation and
fingerprinting contracts are stable, add an additive table owned only by
`services.health_findings_service`.

Suggested logical fields:

- `id`, `fingerprint`, `status` (`open | resolved | ignored`);
- severity, category, sanitized message;
- related subsystem/cog/command/provider;
- first/last seen timestamps and occurrence count;
- last process/runtime-session identity and last snapshot ID;
- bounded `metadata_json` with an explicit schema/version;
- resolved/ignored timestamps and actor IDs only if manual lifecycle actions are
  later approved.

Required behavior:

- dedupe recurring open findings by fingerprint;
- atomically increment count/update last-seen;
- reopen resolved findings when recurrence policy says so;
- ignored findings remain hidden by default but keep aggregate counts;
- TTL-prune detailed history and/or cap per-fingerprint records;
- keep occurrence aggregates without retaining unbounded raw observations;
- all writes through the owner service;
- deterministic commands and AI tools read through bounded service methods.

Recommended retention decision: retain open findings, retain resolved/ignored
records for a configurable TTL, and preserve only aggregate recurrence counters
after detail expiry.

## 12. Startup health: extend, do not replace

The repository already posts a deterministic startup-summary webhook before
`bot.start()` and separately reports cog load failures. A broader startup report
should unify these facts after the bot reaches a stable readiness point.

### Proposed two-stage startup reporting

1. **Pre-connect boot summary (keep existing):** catalogue-build outcomes and
   fatal pre-connect failures through the webhook reporter.
2. **Post-ready startup health snapshot (new):** once on-ready restoration and
   lifecycle transition settle, collect a bounded `purpose="startup"` snapshot
   and publish a deterministic report. Optional AI explanation may follow only if
   AI health and policy permit it.

The post-ready snapshot should cover, where reliable:

- extension load successes/failures;
- gateway readiness and unavailable guild count;
- database reachability/migration status;
- startup outcome phases and cached platform readiness;
- persistent view/anchor restoration summary;
- managed task state;
- slash command sync state only if the repository has a canonical sync recorder;
- missing required configuration/API keys represented as sanitized subsystem
  status, not raw environment values;
- AI health as an optional subsystem;
- bounded recent startup warnings/errors or structured startup observations.

### Timing decision

Do not use an arbitrary 30–60 second sleep as the primary contract. Prefer a
specific “startup settled” composition point plus bounded per-source timeouts. A
short delayed follow-up snapshot may be useful, but it should be explicit and
managed by `core.runtime.tasks.spawn`.

## 13. Deterministic UX plan

### First useful surface

Add `!platform health` and a Platform panel item that render a compact deterministic
snapshot:

- overall status and generated time;
- runtime/lifecycle/gateway/database/platform/AI subsystem statuses;
- top bounded findings;
- partial/stale indicators;
- recommended existing diagnostic commands for drilldown.

### Follow-up surfaces

- `!platform startup`: latest deterministic startup snapshot/report;
- `!platform ai-health`: canonical AI subsystem projection;
- `!platform findings [open|resolved|ignored]`: only after persistent findings;
- `!platform subsystem <name>`: explicit bounded drilldown;
- Platform panel “Ask AI to explain” button: only after AI tools/context are safe.

The `/platform` slash command currently opens the Platform hub rather than exposing
one slash subcommand per diagnostic. Keep that pattern unless maintainers choose a
broader slash-command redesign.

### Embed bounds

Every renderer must account for Discord limits. Summaries should cap subsystem
rows/findings and offer drilldown rather than truncating arbitrary JSON. Existing
embed helpers already contain field-length defensive patterns that should be
reused.

## 14. AI diagnostics plan

### Tool sequence

Start with one coarse, safe tool rather than many overlapping tools:

1. `diagnostics_health_snapshot` (`PLATFORM_OWNER` initially): returns a redacted,
   bounded summary projection.
2. `diagnostics_subsystem_health`: explicit allowlisted subsystem drilldown.
3. `diagnostics_startup_report`: latest deterministic startup projection.
4. `diagnostics_recent_findings`: only after stable finding persistence.
5. `diagnostics_recent_grouped_errors`: only after safe grouping/redaction tests.

`diagnostics_ai_health` and `diagnostics_platform_consistency` may be useful, but
avoid duplicating data already available through the snapshot/subsystem tools
unless tool selection quality requires them.

### `ai_monitor_service` responsibility

If added, `services.ai_monitor_service` should:

- request an already-redacted AI-context snapshot;
- submit a stable task identifier such as `platform.explain_status`;
- require the response to distinguish facts from suggestions;
- append deterministic “next commands” from allowlisted mappings;
- fail back to the deterministic embed/report;
- never collect raw logs/config/database state itself;
- never execute a recommendation.

### AI response contract

AI explanations should use a simple structure:

1. overall status in plain language;
2. facts requiring attention, each tied to a snapshot finding/fingerprint;
3. impact and uncertainty;
4. suggested existing command or subsystem/file hint to inspect;
5. explicit statement that no remediation was performed.

The model must not claim a root cause when the snapshot only supports correlation.

## 15. Event strategy

Do not add events in the foundation PR unless a real subscriber or durable
transition requires one. Candidate later events:

- `platform.health.snapshot_generated` — only if another component must react to
  generated snapshots; avoid emitting on every interactive refresh if noisy;
- `platform.health.finding_recorded` — after persistent finding write succeeds;
- `platform.health.finding_resolved` — after a deterministic lifecycle transition;
- `platform.startup.health_reported` — after deterministic startup report output;
- `ai.diagnostics.explained` — audit/metric fact that an explanation completed,
  with no prompt or sensitive output payload.

Metrics are better for snapshot counts, collection durations, source failures,
redaction outcomes, and AI explanation failures.

## 16. Phased implementation roadmap

### Phase 0 — Contract/ADR decisions

**Goal:** remove ambiguity before implementation.

Decide and document:

- global operational finding name;
- snapshot/finding severity vocabularies and deterministic mapping table;
- required versus optional core health sources;
- access/redaction matrix and whether AI starts platform-owner-only;
- startup-settled collection point;
- whether persistent history is TTL-pruned, capped, or both;
- whether raw stack traces are ever permitted in Discord (recommend no).

**Exit criteria:** approved contract examples and test matrix; no production code
required.

### Phase 1 — Typed deterministic read model

**Goal:** deliver useful health without AI or persistence.

Implement:

- frozen typed health contracts;
- `services.health_snapshot_service` with source adapters, per-source isolation,
  timeouts for async checks, deterministic severity, stable ordering, bounds, and
  redaction projections;
- initial runtime/lifecycle, provider inventory/failure, managed-task,
  platform-readiness/consistency-cache, gateway/guild, DB, and AI adapters;
- `!platform health`, shared embed builder, and Platform panel connector;
- metrics for collection duration/source failures if needed;
- docs for service ownership/read contracts.

Avoid:

- persistent findings;
- AI tools/explanation;
- generalized log parsing;
- a second provider registry;
- emitting new events without consumers.

**Exit criteria:** deterministic health works with AI disabled; one source failure
produces a partial/degraded snapshot without breaking the command; all projections
are bounded and scope-tested.

### Phase 2 — Startup and structured failure observations

**Goal:** unify existing startup facts and improve current-process diagnosis.

Implement:

- a small extension-load outcome recorder or expansion of the existing startup
  outcome contract;
- post-ready startup health snapshot/report while retaining the existing
  pre-connect webhook summary;
- deterministic `!platform startup`;
- structured operational observations at selected high-value failure boundaries;
- safe grouped-current-error adapter over structured observations and the legacy
  ring buffer fallback.

**Exit criteria:** startup report works without AI, includes source timestamps and
partial state, and does not rely on arbitrary raw-log dumps.

### Phase 3 — Read-only AI explanation

**Goal:** allow platform owners to ask safe operational questions.

Implement:

- `diagnostics_health_snapshot` and explicit subsystem/startup tools in
  `services.ai_tools`;
- `services.ai_monitor_service` only if it adds reusable orchestration beyond tool
  calls;
- Platform panel “Ask AI to explain” flow over the same redacted snapshot;
- deterministic fallback on AI disabled/error/rate limit;
- decision-audit/metrics integration without storing sensitive context.

**Exit criteria:** tools are not offered below required scope, model input contains
only redacted bounded data, and live/manual checks show the model uses tools rather
than inventing current health.

### Phase 4 — Persistent recurring findings

**Goal:** answer recurrence/change-over-time questions deterministically.

Implement:

- additive migration for operational findings;
- `services.health_findings_service` as sole writer;
- fingerprint dedupe, recurrence counts, reopen/resolve/ignore policy, and
  retention;
- `!platform findings` and bounded tools/read APIs;
- events only for durable lifecycle transitions with catalogue/docs/tests.

**Exit criteria:** recurrence is atomic and bounded; old process-local facts are not
misrepresented as current; direct table writes are prevented by tests/architecture
rules where practical.

### Phase 5 — Broader subsystem coverage and UX

**Goal:** expand only after the contracts prove stable.

Potential work:

- external API health adapters;
- command failure aggregation;
- BTD6/Paragon/scheduler subsystem summaries;
- health comparison since previous startup;
- richer Platform panel drilldowns;
- server-owner/admin AI access after redaction review;
- optional GitHub issue handoff proposal flow, still with explicit approval and no
  direct AI remediation.

## 17. Suggested PR slices

Keep PRs reviewable and avoid mixing contracts, storage, UI, and AI in one change.

1. **PR A — Contracts and source map:** typed models, severity/redaction policy,
   source adapter interfaces, tests, and ownership docs.
2. **PR B — Snapshot aggregator:** adapters over existing sync/cached sources,
   async isolation/timeouts, bounded projections, tests.
3. **PR C — Deterministic Platform health UX:** embed + `!platform health` + panel
   connector + command/help tests.
4. **PR D — Startup integration:** extension/startup outcomes and post-ready report.
5. **PR E — Structured observations/current grouping:** selected high-value failure
   boundaries and safe grouped errors.
6. **PR F — AI diagnostics tools/explainer:** platform-owner-only tools, fallback,
   redaction/tool-scope tests.
7. **PR G — Persistent findings:** migration, owner service, retention, lifecycle,
   commands, events/docs/tests.

## 18. Test and verification matrix

### Unit and invariant tests

- diagnostics providers remain read-only;
- a failed sync provider does not break `snapshot_all()` or the aggregate;
- every async source has a timeout/failure isolation test;
- aggregation status and ordering are deterministic;
- partial/stale state is visible and does not become falsely healthy;
- severity mappings from startup/resource/consistency/provider failures are pinned;
- redaction differs by `AIScope` and strips seeded secrets/IDs/content;
- output bounds cap facts, findings, strings, and subsystem drilldowns;
- AI diagnostic tools are absent below the required scope;
- AI tools return JSON-serializable bounded projections only;
- deterministic health/startup surfaces work when AI is disabled/misconfigured;
- startup report survives missing/failed sources;
- fingerprints dedupe normalized repeats and distinguish meaningful differences;
- persistent finding recurrence/reopen/ignore/retention behavior is deterministic;
- new EventBus events are catalogued and documented;
- new table/service ownership is documented and architecture checks updated;
- Platform panel/command surfaces link to the same embed builders;
- import-cycle tests cover new service boundaries.

### Live/manual verification required

Source review and unit tests cannot prove:

- the chosen post-ready timing captures real startup failures without racing;
- live Discord embed limits/layout remain usable;
- the AI reliably calls diagnostics tools instead of answering from prior context;
- redaction prevents sensitive leakage in real prompts and provider traces;
- real logs/structured observations produce useful, stable fingerprints;
- DB/API health checks have safe latency and do not create incident-time load;
- the Platform panel remains understandable after new entries;
- webhook/admin channel routing is correct in production;
- multi-reconnect behavior does not duplicate startup reports.

## 19. Risks and mitigations

| Risk | Mitigation |
|---|---|
| A “health god service” learns every subsystem's internals. | Use small adapters over canonical read seams; keep domain logic in domain services. |
| Heterogeneous provider payloads leak sensitive/unbounded data. | Never expose raw `snapshot_all()` outside trusted aggregation; allowlist facts and redact before render/model input. |
| Async probes make health commands slow or worsen incidents. | Purpose-based checks, strict per-source/overall timeouts, cached results, and partial snapshots. |
| AI explanation becomes required for diagnosis. | Deterministic command/embed/report first; AI always optional with explicit fallback. |
| Log parsing becomes permanent fragile infrastructure. | Use bounded fallback only; add structured observations at high-value failure boundaries. |
| Severity is arbitrary or unstable. | Publish mapping rules and pin them in deterministic tests. |
| Persistent findings grow forever. | TTL/caps, aggregate counters, no raw payload retention, explicit owner service. |
| Existing `ResourceHealthFinding` semantics are broken. | Adapt at boundary; do not rename or silently widen the domain contract. |
| Startup report duplicates on gateway reconnect. | Tie reporting to a one-shot startup-settled/session guard, not every `on_ready`. |
| New events create noise and drift. | Emit only durable transitions; catalogue/docs/tests; use metrics for volume. |
| Platform-owner facts leak to guild admins or model context. | Scope-gated tools plus projection-level redaction; test omission, not only masking. |

## 20. Product decisions still required

1. **Initial access:** platform-owner-only AI diagnostics is recommended. Should
   deterministic `!platform health` remain administrator-accessible with a
   guild-local/redacted projection?
2. **Global health semantics:** should optional AI failure degrade whole-bot health,
   or only the AI subsystem? Recommended: only AI subsystem unless evaluating an
   AI-required feature.
3. **Database criticality:** is DB unavailability globally critical or purpose
   dependent?
4. **Required cogs:** `config.INITIAL_EXTENSIONS` is the configured expected list,
   but which extension failures are blocking versus optional?
5. **Stack traces:** should Discord ever display them? Recommended: no; retain in
   existing logs/incident webhook only.
6. **Finding retention:** recommended TTL plus aggregate recurrence counters. What
   TTL and per-fingerprint caps are acceptable?
7. **Startup output destination:** existing webhook, configured admin log channel,
   Platform panel history, or a combination?
8. **Freshness:** how stale may cached consistency/API/AI health be before status
   becomes `unknown`?
9. **Slash UX:** preserve the current `/platform` hub pattern, or later add typed
   slash subcommands?

## 21. Immediate next-agent brief

The next implementation agent should begin with **Phase 0 / PR A**, not AI tools
or persistence.

Required first task:

1. inspect existing repository dataclass/module placement conventions and propose
   exact module names;
2. define typed operational snapshot/subsystem/finding contracts without colliding
   with `ResourceHealthFinding`;
3. define deterministic status/severity mapping and redaction projections;
4. define adapter boundaries for `diagnostics_service`, `platform_readiness`,
   lifecycle/tasks, gateway/guild, DB, and canonical AI read models;
5. add tests for deterministic aggregation, source isolation, bounds, and scope
   redaction;
6. document ownership and async/sync boundaries.

Do **not** in the first implementation PR:

- create `bot_awareness_service`;
- add AI tools;
- add the findings table;
- parse raw files or arbitrary logs;
- add broad EventBus emissions;
- add remediation actions;
- refactor existing domain health contracts unnecessarily.

## 22. Definition of success

The feature is successful when an authorized operator can ask “How healthy is the
bot?” and receive the same trustworthy, bounded facts through a deterministic
Platform surface or optional AI explanation; when one provider, database check, or
AI provider fails, diagnostics remain available; when sensitive data is omitted
before reaching Discord/model context; and when the recommended next action is
advisory, traceable to structured facts, and never executed automatically.
