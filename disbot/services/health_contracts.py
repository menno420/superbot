"""Typed read-model contracts for operational bot-health diagnostics.

PR1 of the bot-awareness programme. These frozen dataclasses are the
shared language between:

* ``services.health_snapshot_service`` — the aggregator that builds them;
* the deterministic ``!platform health`` command / Platform panel embeds;
* and (later) the read-only AI diagnostics tool.

Deliberately dependency-light: this module imports only stdlib, so cogs,
views, and services can all import it at module top without pulling a
heavy graph, **and** so the deterministic health surface never depends on
AI request-scope vocabulary.  ``AIScope`` lives in
``core.runtime.ai.contracts`` and is mapped to :class:`HealthAudience`
only inside the AI tool adapter (PR5) — never here.

Nothing in this module performs I/O, mutation, or redaction policy.
Collection lives in ``services.health_snapshot_service``; the redaction
transform is ``health_snapshot_service.project_for_audience``.

The deterministic mapping helpers (:func:`worst_status`,
:func:`status_for_severity`, :func:`derive_overall_status`) are pinned by
``tests/unit/services/test_health_snapshot_service.py`` so severity
aggregation stays stable across refactors.
"""

from __future__ import annotations

import datetime
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Literal


class SnapshotStatus(str, Enum):
    """Coarse health status for a subsystem or the whole snapshot."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


class FindingSeverity(str, Enum):
    """Severity of a single operational finding."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class HealthAudience(str, Enum):
    """Who a projected snapshot is rendered for.

    Deterministic surfaces derive this from Discord context directly
    (administrator → ``GUILD_ADMIN``; bot owner → ``PLATFORM_OWNER``).
    The AI tool adapter maps ``AIScope`` → ``HealthAudience`` at its
    boundary; this module never imports ``AIScope``.
    """

    PUBLIC = "public"
    GUILD_ADMIN = "guild_admin"
    PLATFORM_OWNER = "platform_owner"


# Audience privilege ranking — a higher rank sees strictly more detail.
_AUDIENCE_RANK: dict[HealthAudience, int] = {
    HealthAudience.PUBLIC: 0,
    HealthAudience.GUILD_ADMIN: 1,
    HealthAudience.PLATFORM_OWNER: 2,
}


def audience_allows(audience: HealthAudience, required: HealthAudience) -> bool:
    """True if ``audience`` is privileged enough to see ``required`` detail."""
    return _AUDIENCE_RANK[audience] >= _AUDIENCE_RANK[required]


# Worst-of ranking used when folding finding severities / source statuses
# into one subsystem status.  ``UNKNOWN`` deliberately ranks *below*
# ``DEGRADED``: missing information is less alarming than a confirmed
# problem, and one unknown optional source must never mask a real
# degradation elsewhere.
_STATUS_RANK: dict[SnapshotStatus, int] = {
    SnapshotStatus.HEALTHY: 0,
    SnapshotStatus.UNKNOWN: 1,
    SnapshotStatus.DEGRADED: 2,
    SnapshotStatus.CRITICAL: 3,
}

# Deterministic finding-severity → subsystem-status contribution.
_SEVERITY_TO_STATUS: dict[FindingSeverity, SnapshotStatus] = {
    FindingSeverity.INFO: SnapshotStatus.HEALTHY,
    FindingSeverity.WARNING: SnapshotStatus.DEGRADED,
    FindingSeverity.ERROR: SnapshotStatus.DEGRADED,
    FindingSeverity.CRITICAL: SnapshotStatus.CRITICAL,
}


def worst_status(statuses: Iterable[SnapshotStatus]) -> SnapshotStatus:
    """Return the most-alarming status in ``statuses`` (HEALTHY if empty)."""
    result = SnapshotStatus.HEALTHY
    best = _STATUS_RANK[result]
    for status in statuses:
        rank = _STATUS_RANK[status]
        if rank > best:
            result, best = status, rank
    return result


def status_for_severity(severity: FindingSeverity) -> SnapshotStatus:
    """Map a single finding severity to its subsystem-status contribution."""
    return _SEVERITY_TO_STATUS[severity]


@dataclass(frozen=True)
class OperationalHealthFinding:
    """One bounded, sanitized operational observation.

    ``message``/``file_hint``/``suggested_next_step`` are short and must
    never contain raw tracebacks, tokens, raw SQL, message content, or
    unbounded identifiers.  ``fingerprint`` is deterministic and excludes
    volatile IDs/timestamps so recurring problems group.  Persistent
    lifecycle (``open|resolved|ignored``) belongs to the later findings
    service record, not to this immutable observation.
    """

    fingerprint: str
    severity: FindingSeverity
    category: str
    message: str
    first_seen_at: datetime.datetime | None = None
    last_seen_at: datetime.datetime | None = None
    occurrence_count: int = 1
    related_subsystem: str | None = None
    related_command: str | None = None
    related_provider: str | None = None
    file_hint: str | None = None
    suggested_next_step: str | None = None
    source: str = "unknown"


@dataclass(frozen=True)
class SubsystemHealth:
    """Health of one subsystem, composed from a canonical read seam.

    ``facts`` is a small allowlisted scalar mapping — never an arbitrary
    provider dump.  ``required`` marks core subsystems whose failure can
    drive the overall snapshot to ``CRITICAL``; optional subsystems
    (AI, external APIs, guild-local resources) never do.
    """

    name: str
    status: SnapshotStatus
    summary: str
    generated_at: datetime.datetime
    findings: tuple[OperationalHealthFinding, ...] = ()
    facts: Mapping[str, Any] = field(default_factory=dict)
    source: str = "unknown"
    stale: bool = False
    required: bool = False


@dataclass(frozen=True)
class HealthSnapshot:
    """A bounded, ordered, audience-projected view of bot health."""

    snapshot_id: str
    generated_at: datetime.datetime
    purpose: str
    status: SnapshotStatus
    summary: str
    subsystems: tuple[SubsystemHealth, ...]
    findings: tuple[OperationalHealthFinding, ...]
    partial: bool = False
    redaction_audience: HealthAudience | None = None


@dataclass(frozen=True)
class HealthSnapshotRequest:
    """Explicit request describing scope, audience, and which expensive
    checks the collector may run.
    """

    purpose: Literal["summary", "startup", "guild", "subsystem", "ai_context"] = (
        "summary"
    )
    audience: HealthAudience = HealthAudience.GUILD_ADMIN
    guild_id: int | None = None
    subsystem: str | None = None
    include_recent_logs: bool = False
    include_fresh_consistency: bool = False


def derive_overall_status(
    subsystems: tuple[SubsystemHealth, ...],
    *,
    partial: bool = False,
) -> SnapshotStatus:
    """Deterministically fold subsystem statuses into one overall status.

    Rules (pinned in tests):

    1. ``CRITICAL`` if any **required** subsystem is critical.
    2. ``UNKNOWN`` if every subsystem is unknown (no reliable signal).
    3. ``DEGRADED`` if any subsystem is degraded, any subsystem is
       critical-but-optional, or any **required** subsystem is unknown
       (a core source we could not read).
    4. ``HEALTHY`` otherwise — but a ``partial`` snapshot never reports
       ``HEALTHY`` (it is downgraded to ``DEGRADED`` so missing data is
       never mistaken for confirmed health).
    """
    if not subsystems:
        return SnapshotStatus.UNKNOWN
    required = [s for s in subsystems if s.required]
    if any(s.status is SnapshotStatus.CRITICAL for s in required):
        return SnapshotStatus.CRITICAL
    if all(s.status is SnapshotStatus.UNKNOWN for s in subsystems):
        return SnapshotStatus.UNKNOWN

    result = SnapshotStatus.HEALTHY
    if (
        any(s.status is SnapshotStatus.CRITICAL for s in subsystems)
        or any(s.status is SnapshotStatus.DEGRADED for s in subsystems)
        or any(s.status is SnapshotStatus.UNKNOWN for s in required)
    ):
        result = SnapshotStatus.DEGRADED

    if partial and result is SnapshotStatus.HEALTHY:
        result = SnapshotStatus.DEGRADED
    return result


__all__ = [
    "FindingSeverity",
    "HealthAudience",
    "HealthSnapshot",
    "HealthSnapshotRequest",
    "OperationalHealthFinding",
    "SnapshotStatus",
    "SubsystemHealth",
    "audience_allows",
    "derive_overall_status",
    "status_for_severity",
    "worst_status",
]
