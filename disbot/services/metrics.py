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

task_outcome_total = Counter(
    "task_outcome_total",
    "Outcomes of managed background tasks spawned via core.runtime.tasks",
    ["name", "outcome"],  # outcome: ok | error | cancelled
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
# the lock (single observation followed immediately by os._exit).
# A sustained non-zero ``error`` rate indicates DB connectivity issues;
# any ``lost`` observation indicates a split-brain that was just resolved.
runtime_lock_heartbeat_total = Counter(
    "runtime_lock_heartbeat_total",
    "Runtime-lock heartbeat refresh attempts by outcome.",
    ["outcome"],  # ok | error | lost
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
