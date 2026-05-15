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

        def labels(self, **_: object) -> "_NoOp":
            return self

        def inc(self, *_: object, **__: object) -> None:
            pass

        def observe(self, *_: object, **__: object) -> None:
            pass

        def set(self, *_: object, **__: object) -> None:
            pass

    def Counter(name: str, doc: str, labelnames: object = (), **_: object) -> _NoOp:  # type: ignore[no-redef]
        return _NoOp()

    def Gauge(name: str, doc: str, labelnames: object = (), **_: object) -> _NoOp:  # type: ignore[no-redef]
        return _NoOp()

    def Histogram(name: str, doc: str, labelnames: object = (), buckets: object = (), **_: object) -> _NoOp:  # type: ignore[no-redef]
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
    "Total panel edits triggered by the live update scheduler",
    ["subsystem"],
)

governance_denials_total = Counter(
    "governance_denials_total",
    "Total governance execution denials by subsystem and scope",
    ["subsystem", "scope"],
)
