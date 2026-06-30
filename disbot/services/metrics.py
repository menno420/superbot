"""Prometheus metrics for SuperBot.

All metrics are module-level singletons created once on import.
Collect and expose via the /metrics endpoint in healthserver.py.

When prometheus_client is not installed the module still imports cleanly
and all metric objects become silent no-ops, so callers never need to
guard metric calls individually.

Usage:
    from services import metrics
    metrics.governance_cache_hits.labels(guild_id=str(guild_id)).inc()
"""

from __future__ import annotations

try:
    from prometheus_client import Counter, Gauge, Histogram

    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False

    class _NoOp:
        """Silent no-op that accepts any attribute access or call."""

        def labels(self, **_: object) -> _NoOp:
            return self

        def inc(self, *_: object, **__: object) -> None:
            pass

        def observe(self, *_: object, **__: object) -> None:
            pass

        def set(self, *_: object, **__: object) -> None:
            pass

    def Counter(  # type: ignore[no-redef]  # noqa: N802
        name: str,
        doc: str,
        labelnames: object = (),
        **_: object,
    ) -> _NoOp:
        return _NoOp()

    def Gauge(  # type: ignore[no-redef]  # noqa: N802
        name: str,
        doc: str,
        labelnames: object = (),
        **_: object,
    ) -> _NoOp:
        return _NoOp()

    def Histogram(  # type: ignore[no-redef]  # noqa: N802
        name: str,
        doc: str,
        labelnames: object = (),
        buckets: object = (),
        **_: object,
    ) -> _NoOp:
        return _NoOp()


governance_cache_hits = Counter(
    "governance_cache_hits_total",
    "Governance resolution results served from cache",
    ["guild_id"],
)

governance_cache_misses = Counter(
    "governance_cache_misses_total",
    "Governance resolution results computed (cache miss)",
    ["guild_id"],
)

governance_resolution_seconds = Histogram(
    "governance_resolution_seconds",
    "Duration of governance resolution operations",
    ["operation"],
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0],
)

command_total = Counter(
    "command_total",
    "Total bot commands processed",
    ["cog", "command", "result"],  # result: success | error | denied
)

session_active_count = Gauge(
    "session_active_count",
    "Current number of non-expired runtime sessions in the DB",
)

panel_refresh_total = Counter(
    "panel_refresh_total",
    # `result` label values:  ok / skipped / channel_missing /
    # message_not_found / forbidden / http_error / refresh_fn_error.
    "Total panel edits triggered by the live update scheduler.",
    ["subsystem", "result"],
)

governance_denials_total = Counter(
    "governance_denials_total",
    "Total governance execution denials by subsystem and scope",
    ["subsystem", "scope"],
)

# Command-access onboarding PR-8 — per-decision counter for the
# central command-access resolver (prefix + slash share the same
# admission path).  The breakdown lets operators see, at scrape time,
# how many denials a given guild is producing and why.
#
# Label cardinality is bounded:
#   * invocation: "prefix" | "slash" (2)
#   * decision:   "allow" | "deny"    (2)
#   * reason:     DecisionReason enum (6 values today)
#   * mode:       AccessMode enum + "none" for the lifecycle/DM/default
#                 branches that don't carry a mode (4)
#   * source:     DecisionSource enum (4)
#
# At most 2 × 2 × 6 × 4 × 4 = 384 label combinations.
command_access_decisions_total = Counter(
    "command_access_decisions_total",
    "Command-access resolver decisions broken down by invocation, "
    "decision, reason, mode, and source.",
    ["invocation", "decision", "reason", "mode", "source"],
)

task_outcome_total = Counter(
    "task_outcome_total",
    "Outcomes of managed background tasks spawned via core.runtime.tasks",
    ["name", "outcome"],  # outcome: ok | error | cancelled
)

# Bot-awareness PR6: persistent operational-health findings. Labels are
# deliberately low-cardinality (category/severity/outcome) — the unbounded
# `fingerprint` is NEVER a label; it lives only in the DB row.
health_finding_recorded_total = Counter(
    "health_finding_recorded_total",
    "Operational-health findings upserted into the persistent store.",
    ["category", "severity"],
)

health_finding_retention_pruned_total = Counter(
    "health_finding_retention_pruned_total",
    "Resolved/ignored health-finding rows pruned by the retention sweep.",
)

# Bot-awareness §3.6: the health-collection observability metrics promised by
# the plan (collection duration, source-failure counts, redaction outcomes).
# Labels are deliberately low-cardinality (a fixed lane / source-name set / the
# three HealthAudience values) — never an unbounded value.
health_snapshot_collection_seconds = Histogram(
    "health_snapshot_collection_seconds",
    "Wall-clock time to collect a health snapshot, by collection lane.",
    ["lane"],  # sync | async
    buckets=(0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0, 2.5, 5.0),
)

health_snapshot_source_failure_total = Counter(
    "health_snapshot_source_failure_total",
    "Health-adapter sources that errored or timed out during collection "
    "(per-source isolation kept the rest of the snapshot intact).",
    ["source"],
)

health_snapshot_redaction_total = Counter(
    "health_snapshot_redaction_total",
    "Health snapshots projected for a viewer audience (redaction outcomes).",
    ["audience"],  # public | guild_admin | platform_owner
)

# LP-4: rolling-deploy handoff for the runtime lock. ``acquired_immediate``
# is the happy path (no peer held the lock); ``acquired_after_wait`` means
# the old replica drained and we took over; ``timeout`` means the boot
# wait budget elapsed and this replica exited idle.
runtime_lock_boot_handoff_total = Counter(
    "runtime_lock_boot_handoff_total",
    "Outcome of the boot-time runtime-lock acquisition loop.",
    ["outcome"],  # acquired_immediate | acquired_after_wait | timeout
)

runtime_lock_boot_wait_seconds = Histogram(
    "runtime_lock_boot_wait_seconds",
    "Time spent waiting for the runtime lock during boot (acquired or timed out).",
    buckets=(0.1, 0.5, 1.0, 5.0, 15.0, 30.0, 60.0, 120.0, 300.0),
)

# Runtime-lock heartbeat refresh attempts.  ``ok`` = lock still owned by
# this boot; ``error`` = transient DB exception (retried up to
# _HEARTBEAT_FAILURE_LIMIT before force-exit); ``lost`` = a peer reclaimed
# the lock (single observation followed immediately by os._exit);
# ``released`` = the shutdown path dropped the lock on purpose for a fast
# deploy handoff and the heartbeat loop exited cleanly (NOT a split-brain).
# A sustained non-zero ``error`` rate indicates DB connectivity issues;
# any ``lost`` observation indicates a split-brain that was just resolved.
runtime_lock_heartbeat_total = Counter(
    "runtime_lock_heartbeat_total",
    "Runtime-lock heartbeat refresh attempts by outcome.",
    ["outcome"],  # ok | error | lost | released
)

# Current lifecycle phase, encoded as a multi-series gauge: exactly one
# ``phase`` label has value 1.0 at any moment; the rest are 0.0.  This
# is the canonical Prometheus state-machine encoding (cf.
# ``node_systemd_unit_state``).  In Grafana, ``max by (phase)
# (lifecycle_phase)`` renders the current phase as a single-stat panel;
# ``max_over_time(lifecycle_phase[5m])`` surfaces any phase the bot
# passed through in the last 5 minutes.
lifecycle_phase = Gauge(
    "lifecycle_phase",
    "Current lifecycle phase as a multi-series gauge (1=current, 0=other).",
    ["phase"],  # STARTING | RUNNING | DRAINING | SHUTTING_DOWN |
    #             RESTARTING | STOPPED | FAILED_STARTUP
)

# Lifecycle close-driver invocations: increments once each time the watchdog
# in bot1 drives bot.close() from a pending lifecycle request.  ``shutdown``
# is SIGTERM-driven; ``restart`` is !restart-driven.  Use this to alert on
# unexpected close rates (e.g. a sustained non-zero ``restart`` rate without
# operator action indicates a restart loop).
lifecycle_close_driver_total = Counter(
    "lifecycle_close_driver_total",
    "Lifecycle close-driver invocations by pending request kind.",
    ["kind"],  # shutdown | restart
)

# Duration of bot.close() invoked by the close-driver above.  The 20 s
# bucket aligns with LIFECYCLE_CLOSE_TIMEOUT_SECONDS so a single observation
# in the topmost bucket is the canonical "close hit the timeout and the
# driver force-exited" signature.  Sub-second buckets capture the
# normal-path close.  Sustained drift towards higher buckets is the
# leading indicator of an unhealthy close path before it actually hits
# the timeout.
lifecycle_close_duration_seconds = Histogram(
    "lifecycle_close_duration_seconds",
    "Duration of bot.close() invoked by the lifecycle close-driver.",
    ["kind"],  # shutdown | restart
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 15.0, 20.0),
)

# Wall-clock seconds between Python interpreter handing control to
# ``core.runtime.lifecycle`` (module import) and the first
# STARTING → RUNNING transition (``on_ready`` returning success).
# Observed exactly once per process: a second on_ready (e.g. after a
# Discord gateway reconnect) does NOT re-observe, so the histogram
# represents cold-boot health, not connection churn.  Buckets span
# sub-second (cached cog graph, no DB migrations) to 60 s (cold pool +
# many migrations + slow gateway handshake); anything past 30 s is a
# leading indicator the next deploy may breach the orchestrator's boot
# deadline.
lifecycle_startup_seconds = Histogram(
    "lifecycle_startup_seconds",
    "Time from process import to first STARTING → RUNNING transition.",
    buckets=(0.5, 1.0, 2.5, 5.0, 10.0, 20.0, 30.0, 60.0),
)

# Duration of each ``runtime_lock.heartbeat`` UPDATE call.  Observed on
# every attempt — success and exception alike — so operators can graph
# DB latency trends without being blinded by exception-path samples
# being skipped.  Buckets stop at 30 s (the heartbeat interval) since a
# single heartbeat exceeding the interval is already pathological.
runtime_lock_heartbeat_seconds = Histogram(
    "runtime_lock_heartbeat_seconds",
    "Duration of the runtime-lock heartbeat UPDATE call (success or error).",
    buckets=(0.005, 0.025, 0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0),
)

governance_fail_open_total = Counter(
    "governance_fail_open_total",
    "Interaction-router governance gate fell open due to resolver error. "
    "A sustained non-zero rate indicates the governance layer is failing to "
    "resolve visibility and interactions are being allowed without checks.",
    ["subsystem"],
)

interaction_unhandled_total = Counter(
    "interaction_unhandled_total",
    "Interactions routed to a custom_id prefix with no registered handler. "
    "Indicates a typo in a cog's register() call or a leftover button from a "
    "removed cog.",
    ["prefix"],
)

anchor_restore_total = Counter(
    "anchor_restore_total",
    # `result` label values:  ok / view_missing / restore_failed.
    "Outcomes of PersistentView restoration during on_ready.",
    ["subsystem", "result"],
)

unknown_event_total = Counter(
    "unknown_event_total",
    "EventBus emit/on calls referencing an event name not in the catalogue "
    "(disbot/core/events_catalogue.py). A non-zero count indicates an "
    "emitter/listener has drifted from the catalogue — likely a typo or "
    "leftover from a removed cog.",
    ["event", "op"],  # op: emit | on
)

event_handler_failures_total = Counter(
    "event_handler_failures_total",
    "EventBus subscriber failures (RS05). emit() is publish-accepted — a "
    "failing/timed-out handler never raises into the emitter — so this "
    "counter (plus the `event_bus` diagnostics provider) is how delivery "
    "problems become visible. A non-zero count means a subscriber (audit "
    "routing, server logging, cache invalidation, ...) is dropping events.",
    ["event", "kind"],  # kind: error | timeout
)

identity_contract_findings_total = Counter(
    "identity_contract_findings_total",
    "Cumulative identity-contract findings detected during validation runs. "
    "Counts every finding observed across startup checks and on-demand "
    "`!platform identity` invocations.  Labels distinguish the finding "
    "kind so operators can alert on the kind that matters to them.  This "
    "is a cumulative detection count, NOT an active-state gauge.",
    ["kind"],  # entry_point_missing_command | router_prefix_unknown |
    # view_subsystem_unknown | db_anchor_subsystem_unknown
)

# Webhook reporter dispatch outcomes.  ``success`` = embed posted to
# discord.Webhook.send without exception; ``error`` = the send raised
# (network failure, 4xx/5xx, malformed payload, etc.) and was caught
# and logged at DEBUG.  Without this metric, webhook outages are silent
# — operators only notice when expected operator-channel embeds stop
# appearing in Discord.
webhook_dispatch_total = Counter(
    "webhook_dispatch_total",
    "WebhookReporter dispatch outcomes (success or caught exception).",
    ["outcome"],  # success | error
)

# Lifecycle ring-buffer events as a Prometheus counter, broken out by
# event name.  The event names are a bounded set (~10): phase:<NAME>
# for each Phase value, shutdown_requested[_coalesced],
# restart_requested[_coalesced], and close_executing.  Most valuable
# series:
#   - lifecycle_event_total{event="shutdown_requested_coalesced"} —
#     multiple SIGTERMs in quick succession (probably a healthcheck
#     spam or an orchestrator misconfiguration).
#   - lifecycle_event_total{event="restart_requested"} — operator-
#     triggered restart rate; non-zero unexpected rate = operator
#     thrashing or an automated restart loop.
lifecycle_event_total = Counter(
    "lifecycle_event_total",
    "Lifecycle events recorded in the ring buffer, by event name.",
    ["event"],
)

# Duration of each WebhookReporter._send dispatch.  Observed on every
# attempt (success AND error) so DB-style latency drift is visible
# even when most posts succeed.  Buckets stop at 10s — Discord's
# webhook API typically responds well under 1s; anything past 2s
# indicates either a slow Discord region or a stalled connection
# pool worth investigating.
webhook_dispatch_seconds = Histogram(
    "webhook_dispatch_seconds",
    "Duration of WebhookReporter._send dispatches (success or caught exception).",
    buckets=(0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0, 10.0),
)

# ---------------------------------------------------------------------------
# F-1 guild_config cache (core/runtime/guild_config.py) — Phase S1.1
# ---------------------------------------------------------------------------

guild_config_cache_hits = Counter(
    "guild_config_cache_hits_total",
    "Guild-config cache hits, labelled by the typed-accessor key.",
    ["key"],
)

guild_config_cache_misses = Counter(
    "guild_config_cache_misses_total",
    "Guild-config cache misses (loader invoked), labelled by key.",
    ["key"],
)

guild_config_cache_invalidations = Counter(
    "guild_config_cache_invalidations_total",
    "Explicit guild-config invalidations from admin write paths or "
    "guild_lifecycle teardown.  ``scope='guild'`` covers full-guild "
    "version bumps; ``scope='key'`` covers single-key deletes.",
    ["scope"],
)

guild_config_cache_size = Gauge(
    "guild_config_cache_size",
    "Current number of entries in the guild-config cache.",
)

# ---------------------------------------------------------------------------
# F-2 scope_locks (core/runtime/scope_locks.py) — Phase S1.2
# ---------------------------------------------------------------------------

scope_locks_total = Gauge(
    "scope_locks_total",
    "Current number of tracked scope locks across all subsystem prefixes.",
)

scope_locks_wait_seconds = Histogram(
    "scope_locks_wait_seconds",
    "Time spent waiting to acquire a scope lock, labelled by subsystem prefix.",
    ["prefix"],
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0),
)

scope_locks_idle_swept_total = Counter(
    "scope_locks_idle_swept_total",
    "Scope locks reclaimed by session_gc's idle sweep — non-zero indicates "
    "cogs are missing explicit forget() calls on edge teardown paths.",
)

# ---------------------------------------------------------------------------
# Latency histograms — Phase S3.1 / O-2
# Three slot-bucketed histograms for the three hot-path timing surfaces:
# commands, DB queries, and interaction handlers.  Buckets span 1 ms → 10 s
# so they accommodate both fast cache hits and slow DB / Discord roundtrips.
# ---------------------------------------------------------------------------

command_latency_seconds = Histogram(
    "command_latency_seconds",
    "End-to-end command handler time (on_command → on_command_completion).",
    ["cog", "command"],
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)

db_query_seconds = Histogram(
    "db_query_seconds",
    "Per-query database time, labelled by a low-cardinality query_name "
    "of the form `<op>:<table>` (e.g. `select:xp`, `insert:guild_settings`).",
    ["query_name"],
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0),
)

interaction_handler_seconds = Histogram(
    "interaction_handler_seconds",
    "Interaction callback total time, labelled by the custom_id prefix "
    "(== subsystem identity per INV-B).",
    ["prefix"],
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0),
)

message_pipeline_stage_seconds = Histogram(
    "message_pipeline_stage_seconds",
    "Per-stage process() time inside the core/runtime/message_pipeline "
    "orchestrator (§3.2).  One observation per (stage, message) pair "
    "regardless of stage outcome.",
    ["stage"],
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0),
)

# ---------------------------------------------------------------------------
# Process memory RSS — Phase S3.3 / O-4
# Sampled every PROCESS_MEMORY_SAMPLE_INTERVAL seconds by a supervised
# background task in bot1.main.  Catches slow memory leaks that would
# escape every other alert path until OOM.
# ---------------------------------------------------------------------------

process_memory_rss_bytes = Gauge(
    "process_memory_rss_bytes",
    "Resident set size of the bot process in bytes, sampled periodically.",
)

# ---------------------------------------------------------------------------
# AI gateway — core/runtime/ai/gateway.py
# Every request that reaches the gateway lands one observation on the
# histogram (success and failure alike) and increments the counter with
# the outcome label.  ``outcome`` values: success | timeout | error |
# unavailable | deterministic.  Sustained non-zero ``timeout``/``error``
# rates indicate provider-side instability; sustained ``deterministic``
# is expected when ``AI_DEFAULT_PROVIDER=deterministic`` (the safe
# default for CI and operators who have not opted in).
# ---------------------------------------------------------------------------

ai_request_seconds = Histogram(
    "ai_request_seconds",
    "Duration of AI provider calls dispatched through the gateway "
    "(measured around asyncio.wait_for, includes timeout cases).",
    ["task", "provider"],
    buckets=(0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 20.0, 60.0),
)

ai_request_total = Counter(
    "ai_request_total",
    "AI gateway requests by task and outcome.",
    ["task", "outcome"],
)

# ---------------------------------------------------------------------------
# Media / YouTube provider requests — services/youtube_fetch_service.py
# Every metadata fetch lands one observation, categorised into the bounded
# content-free outcome taxonomy (see services/youtube_diagnostics.py):
# success | key_missing | private_or_deleted | quota_limited | timeout |
# fetch_error.  Sustained non-zero ``quota_limited`` indicates the daily
# YouTube Data API quota is exhausted; ``timeout``/``fetch_error`` indicate
# provider-side instability; ``key_missing`` means the credential is absent.
# Content-free: only the outcome category is a label — never a video id,
# title, or any provider content.
# ---------------------------------------------------------------------------

youtube_provider_request_total = Counter(
    "youtube_provider_request_total",
    "YouTube metadata-fetch requests by content-free outcome category.",
    ["outcome"],
)
