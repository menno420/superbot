"""Operator readiness aggregation for BTD6 ingestion.

Pure read-side aggregation: collapses the env gate, supervisor state,
source-registry counts, per-source freshness, open circuit breakers, and
recent ingestion-run outcomes into a single :class:`ReadinessVerdict` that
the operator surface (the ``!btd6ops readiness`` command + the admin panel)
renders.

Reads only — never mutates. Imports services / utils / db (never views or
cogs). The env-disabled case is reported as a distinct ``"disabled"``
status, *not* folded into a generic ``"not_ready"``, so operators can tell
"switched off" from "switched on but broken".
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal

from services import (
    btd6_fetch_service,
    btd6_ingestion_supervisor,
    btd6_source_registry,
)
from utils.db import btd6_sources as btd6_db

ReadinessStatus = Literal["ready", "partial", "not_ready", "disabled"]

# Ingestion-run statuses that count as a failure for the recent-window
# health signal. "interrupted" is included: a supervisor restart left the
# row unfinished, which an operator should see.
_FAILED_RUN_STATUSES = frozenset(
    {"fetch_error", "parse_error", "store_error", "interrupted"},
)

# How many recent runs to scan for the failure signal / last-run time.
_RECENT_RUN_WINDOW = 25

# Upper bound on sources scanned for counts + freshness buckets.
_SCAN_LIMIT = 200


@dataclass(frozen=True)
class ReadinessVerdict:
    """Structured readiness snapshot. Presentation copy lives in _builders."""

    status: ReadinessStatus
    ingestion_enabled: bool
    supervisor_running: bool
    sources_total: int
    sources_enabled: int
    sources_disabled: int
    enabled_missing_base_url: int
    open_breakers: tuple[str, ...]
    fresh: int
    aging: int
    stale: int
    never: int
    recent_runs_total: int
    recent_failures: int
    last_run_at: datetime | None


def _classify(
    *,
    ingestion_enabled: bool,
    supervisor_running: bool,
    sources_enabled: int,
    enabled_missing_base_url: int,
    open_breakers: tuple[str, ...],
    stale: int,
    never: int,
) -> ReadinessStatus:
    """Collapse the signals into a single verdict.

    Order matters: env-off is reported distinctly *before* any other check,
    so "disabled" never masquerades as "not_ready".
    """
    if not ingestion_enabled:
        return "disabled"
    if sources_enabled == 0:
        return "not_ready"
    has_problem = (
        bool(open_breakers)
        or enabled_missing_base_url > 0
        or stale > 0
        or never > 0
        or not supervisor_running
    )
    return "partial" if has_problem else "ready"


async def evaluate() -> ReadinessVerdict:
    """Aggregate the current ingestion readiness picture (read-only)."""
    ingestion_enabled = btd6_ingestion_supervisor.is_enabled()
    supervisor_running = btd6_ingestion_supervisor.is_running()

    sources = await btd6_db.list_sources(limit=_SCAN_LIMIT)
    sources_total = len(sources)
    sources_enabled = sum(1 for s in sources if s.get("enabled"))
    sources_disabled = sources_total - sources_enabled
    enabled_missing_base_url = sum(
        1 for s in sources if s.get("enabled") and not s.get("base_url")
    )

    health = await btd6_source_registry.list_health(enabled=True, limit=_SCAN_LIMIT)
    fresh = sum(1 for h in health if h.bucket == "fresh")
    aging = sum(1 for h in health if h.bucket == "aging")
    stale = sum(1 for h in health if h.bucket == "stale")
    never = sum(1 for h in health if h.bucket == "never")

    open_breakers = tuple(b.source_key for b in btd6_fetch_service.breaker_status())

    runs = await btd6_db.list_ingestion_runs(limit=_RECENT_RUN_WINDOW)
    recent_runs_total = len(runs)
    recent_failures = sum(1 for r in runs if r.get("status") in _FAILED_RUN_STATUSES)
    last_run_at = runs[0].get("started_at") if runs else None

    status = _classify(
        ingestion_enabled=ingestion_enabled,
        supervisor_running=supervisor_running,
        sources_enabled=sources_enabled,
        enabled_missing_base_url=enabled_missing_base_url,
        open_breakers=open_breakers,
        stale=stale,
        never=never,
    )

    return ReadinessVerdict(
        status=status,
        ingestion_enabled=ingestion_enabled,
        supervisor_running=supervisor_running,
        sources_total=sources_total,
        sources_enabled=sources_enabled,
        sources_disabled=sources_disabled,
        enabled_missing_base_url=enabled_missing_base_url,
        open_breakers=open_breakers,
        fresh=fresh,
        aging=aging,
        stale=stale,
        never=never,
        recent_runs_total=recent_runs_total,
        recent_failures=recent_failures,
        last_run_at=last_run_at,
    )


__all__ = ["ReadinessStatus", "ReadinessVerdict", "evaluate"]
