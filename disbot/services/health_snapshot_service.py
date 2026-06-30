"""Operational bot-health aggregation (read model).

PR1 of the bot-awareness programme.  Builds a typed, bounded,
audience-projected :class:`~services.health_contracts.HealthSnapshot`
from the observability seams the bot already exposes — it adds no new
collection mechanism and owns no durable state.

Two lanes:

* :func:`collect_cached_snapshot` — **sync**, process-local facts only
  (diagnostics registry, lifecycle, tasks, cached consistency, startup
  outcomes, AI read-model, and gateway when a bot is supplied).
* :func:`collect_snapshot` — **async**, the sync lane plus bounded async
  checks (database ping, optional fresh consistency, optional
  guild-local resource health), each isolated with its own per-source
  timeout so one slow check never blocks the command.

Invariants (pinned by tests):

* never mutates anything — purely observational;
* one failed source degrades only its own subsystem, mirroring the sync
  provider registry's per-provider ``_error`` isolation;
* heavy / cycle-sensitive sources are imported **function-locally** so
  importing this module does not eagerly pull the AI/DB graph
  (``tests/unit/services/test_health_import_safety.py``);
* :func:`project_for_audience` is a **pure** transform tested for the
  *omission* of seeded secrets / IDs per audience
  (``tests/unit/services/test_health_redaction.py``).

The deterministic severity mapping lives in
:mod:`services.health_contracts`; this module only classifies each
source and folds the results.
"""

from __future__ import annotations

import asyncio
import datetime
import logging
import os
import time
import uuid
from collections.abc import Awaitable, Callable, Iterable
from dataclasses import replace
from typing import Any

from services import health_observations, metrics
from services.health_contracts import (
    FindingSeverity,
    HealthAudience,
    HealthSnapshot,
    HealthSnapshotRequest,
    OperationalHealthFinding,
    SnapshotStatus,
    SubsystemHealth,
    derive_overall_status,
    status_for_severity,
    worst_status,
)

logger = logging.getLogger("bot.health_snapshot")

# --- bounds & thresholds ---------------------------------------------------
MAX_SUBSYSTEM_FINDINGS = 5
MAX_TOTAL_FINDINGS = 12
MAX_MESSAGE_CHARS = 180
STALE_SECONDS = 300.0  # cached consistency older than this is flagged stale

# Per-source async timeouts (seconds) — bounded so a wedged check never
# blocks the whole command.
DB_TIMEOUT = 2.0
CONSISTENCY_TIMEOUT = 5.0
RESOURCE_TIMEOUT = 3.0

# Stable render/aggregation order for subsystems.
_SUBSYSTEM_ORDER: dict[str, int] = {
    "runtime": 0,
    "gateway": 1,
    "database": 2,
    "consistency": 3,
    "startup": 4,
    "extensions": 5,
    "tasks": 6,
    "diagnostics": 7,
    "ai": 8,
    "resources": 9,
    "errors": 10,
}

# Extensions whose load failure is a CRITICAL whole-bot signal (D3). Only the
# load-first command-access gate qualifies; every other cog degrades gracefully.
REQUIRED_EXTENSIONS: frozenset[str] = frozenset({"cogs.bootstrap_access_cog"})

_SEVERITY_RANK: dict[FindingSeverity, int] = {
    FindingSeverity.INFO: 0,
    FindingSeverity.WARNING: 1,
    FindingSeverity.ERROR: 2,
    FindingSeverity.CRITICAL: 3,
}


def _now() -> datetime.datetime:
    return datetime.datetime.now(tz=datetime.timezone.utc)


# ---------------------------------------------------------------------------
# Sanitization — applied to ALL free text before it enters a finding, at
# every audience.  Delegates to :mod:`services.health_observations` (the
# single source of truth, shared with fingerprinting) so a secret / long ID /
# hash / multi-line traceback is stripped identically everywhere — in a
# finding, a fingerprint, an embed, or AI context.  ``project_for_audience``
# then removes owner-only *fields* on top of this.
# ---------------------------------------------------------------------------


def _scrub(text: str | None, *, limit: int = MAX_MESSAGE_CHARS) -> str:
    """Collapse, redact, and bound free text (see ``health_observations``)."""
    return health_observations.normalize_text(text, limit=limit)


# ---------------------------------------------------------------------------
# Status maps from existing source vocabularies → SnapshotStatus
# ---------------------------------------------------------------------------

_PHASE_STATUS: dict[str, SnapshotStatus] = {
    "STARTING": SnapshotStatus.UNKNOWN,
    "RUNNING": SnapshotStatus.HEALTHY,
    "DRAINING": SnapshotStatus.DEGRADED,
    "SHUTTING_DOWN": SnapshotStatus.DEGRADED,
    "RESTARTING": SnapshotStatus.DEGRADED,
    "STOPPED": SnapshotStatus.DEGRADED,
    "FAILED_STARTUP": SnapshotStatus.CRITICAL,
}

# platform_consistency.SectionStatus values (clean|warning|fatal|skipped).
_SECTION_STATUS: dict[str, SnapshotStatus] = {
    "clean": SnapshotStatus.HEALTHY,
    "warning": SnapshotStatus.DEGRADED,
    "fatal": SnapshotStatus.CRITICAL,
    "skipped": SnapshotStatus.UNKNOWN,
}

# startup_outcome.SummaryStatus values (ok|degraded|failed|empty).
_SUMMARY_STATUS: dict[str, SnapshotStatus] = {
    "ok": SnapshotStatus.HEALTHY,
    "degraded": SnapshotStatus.DEGRADED,
    "failed": SnapshotStatus.CRITICAL,
    "empty": SnapshotStatus.UNKNOWN,
}

# resource_health severity values (info|warn|error) → FindingSeverity.
_RESOURCE_SEVERITY: dict[str, FindingSeverity] = {
    "info": FindingSeverity.INFO,
    "warn": FindingSeverity.WARNING,
    "error": FindingSeverity.ERROR,
}


def _is_stale(report_at: datetime.datetime | None) -> bool:
    if report_at is None:
        return False
    return (_now() - report_at).total_seconds() > STALE_SECONDS


# ---------------------------------------------------------------------------
# Sync subsystem adapters (each builds one SubsystemHealth; never raises —
# _safe() wraps them and substitutes an UNKNOWN subsystem on failure).
# ---------------------------------------------------------------------------


def _runtime_subsystem() -> SubsystemHealth:
    from core.runtime import lifecycle

    snap = lifecycle.diagnostics_snapshot()
    phase = str(snap.get("phase", "UNKNOWN"))
    status = _PHASE_STATUS.get(phase, SnapshotStatus.UNKNOWN)
    findings: tuple[OperationalHealthFinding, ...] = ()
    if phase == "FAILED_STARTUP":
        findings = (
            OperationalHealthFinding(
                fingerprint="runtime.failed_startup",
                severity=FindingSeverity.CRITICAL,
                category="runtime.failed_startup",
                message="Runtime reported a failed startup.",
                related_subsystem="runtime",
                suggested_next_step="Inspect `!platform lifecycle` and boot logs.",
                source="lifecycle",
            ),
        )
    return SubsystemHealth(
        name="runtime",
        status=status,
        summary=f"Lifecycle phase: {phase}",
        generated_at=_now(),
        findings=findings,
        facts={
            "phase": phase,
            "can_accept_commands": bool(snap.get("can_accept_commands")),
            "uptime_seconds": round(float(snap.get("module_load_age_seconds", 0.0))),
        },
        source="lifecycle",
        required=True,
    )


def _tasks_subsystem() -> SubsystemHealth:
    from core.runtime import tasks

    active = tasks.count()
    return SubsystemHealth(
        name="tasks",
        status=SnapshotStatus.HEALTHY,
        summary=f"{active} managed task(s) active",
        generated_at=_now(),
        facts={"active_count": active},
        source="tasks",
        required=True,
    )


def _diagnostics_subsystem() -> SubsystemHealth:
    from services import diagnostics_service

    snap = diagnostics_service.snapshot_all()
    failed = [
        (name, str(payload.get("_error")))
        for name, payload in sorted(snap.items())
        if isinstance(payload, dict) and "_error" in payload
    ]
    findings = tuple(
        OperationalHealthFinding(
            fingerprint=f"diagnostics.provider_failed:{name}",
            severity=FindingSeverity.ERROR,
            category="diagnostics.provider_failed",
            message="A diagnostics provider reported an error.",
            related_subsystem="diagnostics",
            related_provider=name,  # owner-only (stripped for admins)
            file_hint=_scrub(err),  # owner-only (stripped for admins)
            source="diagnostics_service",
        )
        for name, err in failed[:MAX_SUBSYSTEM_FINDINGS]
    )
    status = SnapshotStatus.DEGRADED if failed else SnapshotStatus.HEALTHY
    summary = (
        f"{len(failed)} of {len(snap)} providers failing"
        if failed
        else f"{len(snap)} providers healthy"
    )
    return SubsystemHealth(
        name="diagnostics",
        status=status,
        summary=summary,
        generated_at=_now(),
        findings=findings,
        facts={"provider_count": len(snap), "failed_count": len(failed)},
        source="diagnostics_service",
        required=True,
    )


def _grouped_findings_enabled() -> bool:
    """Opt-in flag for the grouped recent-error subsystem (PR4).

    Default OFF: deterministic surfaces and the legacy ``!recent_errors``
    command are unchanged until an operator sets ``HEALTH_GROUPED_FINDINGS``
    truthy, so flipping it off is a complete, code-free rollback.
    """
    return os.getenv("HEALTH_GROUPED_FINDINGS", "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def _errors_subsystem() -> SubsystemHealth:
    """Group the recent runtime-error stream into a few counted findings.

    Reads the bounded ``recent_errors`` diagnostics provider (registered by
    the DiagnosticCog from its in-memory log ring buffer — cogs register
    *into* the registry, so this never imports cogs) and folds it through
    :func:`health_observations.group_log_errors`.  Only added to a snapshot
    when ``HEALTH_GROUPED_FINDINGS`` is on; an absent provider yields no
    errors rather than an exception.
    """
    from services import diagnostics_service

    try:
        payload = diagnostics_service.snapshot("recent_errors")
    except KeyError:
        payload = None
    if isinstance(payload, dict):
        entries = payload.get("recent", [])
    elif isinstance(payload, list):
        entries = payload
    else:
        entries = []
    findings = tuple(
        health_observations.group_log_errors(
            entries,
            subsystem="errors",
            max_findings=MAX_SUBSYSTEM_FINDINGS,
        ),
    )
    total = sum(f.occurrence_count for f in findings)
    if findings:
        status = worst_status(status_for_severity(f.severity) for f in findings)
        summary = f"{total} recent error(s) in {len(findings)} group(s)"
    else:
        status = SnapshotStatus.HEALTHY
        summary = "No recent errors"
    return SubsystemHealth(
        name="errors",
        status=status,
        summary=summary,
        generated_at=_now(),
        findings=findings,
        facts={"recent_error_count": total, "group_count": len(findings)},
        source="log_buffer",
        required=False,
    )


def _build_consistency_subsystem(
    *,
    overall_value: str | None,
    report_at: datetime.datetime | None,
    blocking: tuple[Any, ...],
    source: str,
) -> SubsystemHealth:
    status = (
        _SECTION_STATUS.get(overall_value, SnapshotStatus.UNKNOWN)
        if overall_value is not None
        else SnapshotStatus.UNKNOWN
    )
    stale = _is_stale(report_at)
    # A SKIPPED section means "not applicable / no data / no context" — e.g.
    # Bindings checked from a DM (no guild), or no `binding_backfill` checkpoint
    # rows because no backfill has run.  That is NOT something that "needs
    # attention", so only WARNING/FATAL sections become findings; SKIPPED ones
    # are recorded in facts.  Otherwise a benign "not applicable" state reads as
    # a problem and inflates the "N blocking sections need attention" count.
    actionable = tuple(
        s for s in blocking if getattr(s.status, "value", "") in ("warning", "fatal")
    )
    skipped = tuple(s for s in blocking if getattr(s.status, "value", "") == "skipped")
    findings = tuple(
        OperationalHealthFinding(
            fingerprint=(
                "consistency.blocking:"
                f"{getattr(getattr(s, 'kind', None), 'value', None) or s.name}"
            ),
            severity=(
                FindingSeverity.CRITICAL
                if getattr(s.status, "value", "") == "fatal"
                else FindingSeverity.WARNING
            ),
            category="consistency.blocking_section",
            message=_scrub(f"Consistency check needs attention: {s.name}"),
            related_subsystem="consistency",
            file_hint=_scrub(getattr(s, "summary", "")),  # owner-only
            source=source,
        )
        for s in actionable[:MAX_SUBSYSTEM_FINDINGS]
    )
    age = None if report_at is None else round((_now() - report_at).total_seconds())
    return SubsystemHealth(
        name="consistency",
        status=status,
        summary=(
            f"Consistency: {overall_value or 'not yet collected'}"
            + (" (stale)" if stale else "")
        ),
        generated_at=_now(),
        findings=findings,
        facts={
            "consistency_status": overall_value,
            # Only WARNING/FATAL sections count as "needs attention"; SKIPPED
            # ("not applicable") are reported separately so they never inflate
            # the actionable count.
            "blocking_sections": len(actionable),
            "skipped_sections": len(skipped),
            "skipped_section_names": ", ".join(s.name for s in skipped),
            "report_age_seconds": age,
        },
        source=source,
        stale=stale,
        required=True,
    )


def _consistency_subsystem() -> SubsystemHealth:
    from services import platform_consistency as pc

    snap = pc.build_readiness_snapshot()
    overall = snap.consistency_overall_status
    return _build_consistency_subsystem(
        overall_value=overall.value if overall is not None else None,
        report_at=snap.consistency_report_at,
        blocking=tuple(snap.consistency_blocking_sections),
        source="platform_readiness_cache",
    )


def _startup_subsystem() -> SubsystemHealth:
    from core.runtime import startup_outcome as so

    outcomes = so.all_outcomes()
    summary_status = so.summary_status(outcomes)
    status = _SUMMARY_STATUS.get(summary_status.value, SnapshotStatus.UNKNOWN)
    failed = [o for o in outcomes if not o.success]
    findings = tuple(
        OperationalHealthFinding(
            fingerprint=f"startup.phase_failed:{o.name}",
            severity=FindingSeverity.ERROR,
            category="startup.phase_failed",
            message=_scrub(f"Startup phase '{o.name}' did not complete."),
            related_subsystem="startup",
            file_hint=_scrub(o.error),  # owner-only
            source="startup_outcome",
        )
        for o in failed[:MAX_SUBSYSTEM_FINDINGS]
    )
    return SubsystemHealth(
        name="startup",
        status=status,
        summary=f"Startup phases: {summary_status.value}",
        generated_at=_now(),
        findings=findings,
        facts={
            "phases_recorded": len(outcomes),
            "phases_failed": len(failed),
        },
        source="startup_outcome",
        required=True,
    )


def _extensions_subsystem() -> SubsystemHealth:
    from core.runtime import startup_outcome as so

    outcomes = so.all_extension_outcomes()
    if not outcomes:
        return SubsystemHealth(
            name="extensions",
            status=SnapshotStatus.UNKNOWN,
            summary="Extension load not yet recorded",
            generated_at=_now(),
            source="startup_outcome",
            required=True,
        )
    failed = [o for o in outcomes if not o.success]
    critical = [o for o in failed if o.name in REQUIRED_EXTENSIONS]
    if critical:
        status = SnapshotStatus.CRITICAL
    elif failed:
        status = SnapshotStatus.DEGRADED
    else:
        status = SnapshotStatus.HEALTHY
    findings = tuple(
        OperationalHealthFinding(
            fingerprint=f"extension.load_failed:{o.name}",
            severity=(
                FindingSeverity.CRITICAL
                if o.name in REQUIRED_EXTENSIONS
                else FindingSeverity.ERROR
            ),
            category="extension.load_failed",
            message=_scrub(f"Extension '{o.name}' failed to load."),
            related_subsystem="extensions",
            file_hint=_scrub(o.error),  # owner-only
            source="startup_outcome",
        )
        for o in failed[:MAX_SUBSYSTEM_FINDINGS]
    )
    return SubsystemHealth(
        name="extensions",
        status=status,
        summary=f"{len(outcomes) - len(failed)} of {len(outcomes)} extensions loaded",
        generated_at=_now(),
        findings=findings,
        facts={"loaded": len(outcomes) - len(failed), "failed": len(failed)},
        source="startup_outcome",
        required=True,
    )


def _ai_subsystem() -> SubsystemHealth:
    from services import ai_diagnostics_service

    d = ai_diagnostics_service.snapshot_for_cog()
    enabled = bool(d.get("enabled"))
    degraded = bool(d.get("degraded"))
    if not enabled:
        status = SnapshotStatus.UNKNOWN
        summary = "AI disabled"
    elif degraded:
        status = SnapshotStatus.DEGRADED
        summary = "AI provider degraded"
    else:
        status = SnapshotStatus.HEALTHY
        summary = "AI healthy"
    findings: tuple[OperationalHealthFinding, ...] = ()
    if degraded:
        findings = (
            OperationalHealthFinding(
                fingerprint="ai.provider_degraded",
                severity=FindingSeverity.WARNING,
                category="ai.provider_degraded",
                message="The AI provider is degraded; deterministic paths unaffected.",
                related_subsystem="ai",
                file_hint=_scrub(  # owner-only
                    f"{d.get('last_error_type')} / {d.get('last_fallback_reason')}",
                ),
                source="ai_diagnostics_service",
            ),
        )
    return SubsystemHealth(
        name="ai",
        status=status,
        summary=summary,
        generated_at=_now(),
        findings=findings,
        facts={
            "enabled": enabled,
            "degraded": degraded,
            "requests_observed": int(d.get("requests_observed") or 0),
            "failures_observed": int(d.get("failures_observed") or 0),
        },
        source="ai_diagnostics_service",
        required=False,  # AI is optional — never drives whole-bot CRITICAL
    )


def _gateway_subsystem(bot: Any) -> SubsystemHealth:
    is_ready = bool(getattr(bot, "is_ready", lambda: False)())
    guilds = list(getattr(bot, "guilds", []) or [])
    unavailable = sum(1 for g in guilds if getattr(g, "unavailable", False))
    latency = getattr(bot, "latency", None)
    latency_ms: float | None = None
    if isinstance(latency, (int, float)) and latency == latency:  # not NaN
        latency_ms = round(float(latency) * 1000.0, 1)

    status = SnapshotStatus.HEALTHY if is_ready else SnapshotStatus.UNKNOWN
    findings: tuple[OperationalHealthFinding, ...] = ()
    if unavailable:
        status = SnapshotStatus.DEGRADED
        findings = (
            OperationalHealthFinding(
                fingerprint="gateway.unavailable_guilds",
                severity=FindingSeverity.WARNING,
                category="gateway.unavailable_guilds",
                message=f"{unavailable} guild(s) currently unavailable.",
                related_subsystem="gateway",
                source="gateway",
            ),
        )
    return SubsystemHealth(
        name="gateway",
        status=status,
        summary="Gateway ready" if is_ready else "Gateway not ready",
        generated_at=_now(),
        findings=findings,
        facts={
            "ready": is_ready,
            "latency_ms": latency_ms,
            "guild_count": len(guilds),
            "unavailable_guilds": unavailable,
        },
        source="gateway",
        required=True,
    )


# ---------------------------------------------------------------------------
# Async subsystem adapters
# ---------------------------------------------------------------------------


async def _database_subsystem() -> SubsystemHealth:
    from utils.db import health as db_health

    ok = await db_health.ping()
    return SubsystemHealth(
        name="database",
        status=SnapshotStatus.HEALTHY if ok else SnapshotStatus.CRITICAL,
        summary="Database reachable" if ok else "Database unreachable",
        generated_at=_now(),
        facts={"reachable": ok},
        source="utils.db.health",
        required=True,
    )


async def _fresh_consistency_subsystem(bot: Any) -> SubsystemHealth:
    from services import platform_consistency as pc

    report = await pc.collect_report(bot=bot)
    blocking = pc.iter_blocking_sections(report)
    return _build_consistency_subsystem(
        overall_value=report.overall_status.value,
        report_at=report.generated_at,
        blocking=tuple(blocking),
        source="platform_consistency_fresh",
    )


async def _resources_subsystem(bot: Any, guild_id: int) -> SubsystemHealth:
    from services import resource_health

    guild = bot.get_guild(guild_id) if bot is not None else None
    if guild is None:
        return SubsystemHealth(
            name="resources",
            status=SnapshotStatus.UNKNOWN,
            summary="Guild not available for resource health",
            generated_at=_now(),
            source="resource_health",
            required=False,
        )
    raw = await resource_health.inspect(guild)
    problems = [f for f in raw if f.severity in ("warn", "error")]
    findings = tuple(
        OperationalHealthFinding(
            fingerprint=f"resource.{f.status}:{f.subsystem}:{f.binding_name}",
            severity=_RESOURCE_SEVERITY.get(f.severity, FindingSeverity.INFO),
            category=f"resource.{f.status}",
            message=_scrub(f"{f.subsystem}/{f.binding_name}: {f.message}"),
            related_subsystem="resources",
            source="resource_health",
        )
        for f in problems[:MAX_SUBSYSTEM_FINDINGS]
    )
    status = (
        worst_status(status_for_severity(x.severity) for x in findings)
        if findings
        else SnapshotStatus.HEALTHY
    )
    return SubsystemHealth(
        name="resources",
        status=status,
        summary=f"{len(problems)} of {len(raw)} bindings need attention",
        generated_at=_now(),
        findings=findings,
        facts={"bindings_checked": len(raw), "problems": len(problems)},
        source="resource_health",
        required=False,  # guild-local; never drives whole-bot CRITICAL
    )


# ---------------------------------------------------------------------------
# Isolation wrappers
# ---------------------------------------------------------------------------


def _safe(
    builder: Callable[[], SubsystemHealth],
    name: str,
    *,
    required: bool,
    failure_status: SnapshotStatus = SnapshotStatus.UNKNOWN,
) -> SubsystemHealth:
    try:
        return builder()
    except Exception as exc:  # noqa: BLE001 — one source must not break the rest
        logger.warning("health adapter %r failed: %s", name, exc, exc_info=True)
        metrics.health_snapshot_source_failure_total.labels(source=name).inc()
        return SubsystemHealth(
            name=name,
            status=failure_status,
            summary=f"{name} health unavailable",
            generated_at=_now(),
            source=name,
            required=required,
        )


async def _safe_async(
    name: str,
    factory: Callable[[], Awaitable[SubsystemHealth]],
    *,
    required: bool,
    failure_status: SnapshotStatus,
    timeout: float,
) -> tuple[SubsystemHealth, bool]:
    """Run an async adapter with a per-source timeout.

    Returns ``(subsystem, degraded_visibility)`` — the boolean is ``True``
    when the source timed out or errored, so the caller can flag the
    whole snapshot ``partial``.
    """
    try:
        sub = await asyncio.wait_for(factory(), timeout=timeout)
        return sub, False
    except (asyncio.TimeoutError, Exception) as exc:  # noqa: BLE001
        logger.warning("health async adapter %r failed: %s", name, exc, exc_info=True)
        metrics.health_snapshot_source_failure_total.labels(source=name).inc()
        return (
            SubsystemHealth(
                name=name,
                status=failure_status,
                summary=f"{name} check unavailable",
                generated_at=_now(),
                source=name,
                required=required,
            ),
            True,
        )


# ---------------------------------------------------------------------------
# Finalize + projection
# ---------------------------------------------------------------------------


def _group_findings(
    findings: list[OperationalHealthFinding],
) -> list[OperationalHealthFinding]:
    """Collapse findings sharing a fingerprint, summing ``occurrence_count``.

    Order-preserving (the first occurrence wins for display fields); a
    defensive correctness invariant so the same problem surfaced by two
    sources counts once.  A no-op for the already-unique per-source
    fingerprints, and the basis PR6 dedupes / persists on.
    """
    grouped: dict[str, OperationalHealthFinding] = {}
    for finding in findings:
        existing = grouped.get(finding.fingerprint)
        if existing is None:
            grouped[finding.fingerprint] = finding
        else:
            grouped[finding.fingerprint] = replace(
                existing,
                occurrence_count=existing.occurrence_count + finding.occurrence_count,
            )
    return list(grouped.values())


def _finalize(
    subsystems: Iterable[SubsystemHealth],
    *,
    purpose: str,
    partial: bool,
) -> HealthSnapshot:
    ordered = tuple(sorted(subsystems, key=lambda s: _SUBSYSTEM_ORDER.get(s.name, 99)))
    overall = derive_overall_status(ordered, partial=partial)
    all_findings = _group_findings([f for s in ordered for f in s.findings])
    all_findings.sort(
        key=lambda f: (
            -_SEVERITY_RANK[f.severity],
            f.related_subsystem or "",
            f.fingerprint,
        ),
    )
    return HealthSnapshot(
        snapshot_id=uuid.uuid4().hex[:12],
        generated_at=_now(),
        purpose=purpose,
        status=overall,
        summary=_overall_summary(overall, ordered),
        subsystems=ordered,
        findings=tuple(all_findings[:MAX_TOTAL_FINDINGS]),
        partial=partial,
        redaction_audience=None,
    )


def _overall_summary(
    status: SnapshotStatus,
    subsystems: tuple[SubsystemHealth, ...],
) -> str:
    bad = [
        s.name
        for s in subsystems
        if s.status in (SnapshotStatus.DEGRADED, SnapshotStatus.CRITICAL)
    ]
    if not bad:
        return f"Overall status: {status.value}."
    return f"Overall status: {status.value} — attention: {', '.join(bad)}."


def project_for_audience(
    snapshot: HealthSnapshot,
    audience: HealthAudience,
) -> HealthSnapshot:
    """Pure downscoping transform.

    * ``PLATFORM_OWNER`` — full detail (findings already scrubbed of
      secrets/IDs at adapter time).
    * ``GUILD_ADMIN`` — strips owner-only finding fields (``file_hint``,
      ``related_provider``); keeps statuses, summaries, admin-safe facts,
      and scrubbed messages.
    * ``PUBLIC`` — only subsystem name + status; no findings, no facts.
    """
    metrics.health_snapshot_redaction_total.labels(audience=audience.value).inc()
    subs = tuple(_project_subsystem(s, audience) for s in snapshot.subsystems)
    if audience is HealthAudience.PUBLIC:
        top: tuple[OperationalHealthFinding, ...] = ()
    else:
        top = tuple(_project_finding(f, audience) for f in snapshot.findings)
    return replace(
        snapshot,
        subsystems=subs,
        findings=top,
        redaction_audience=audience,
    )


def _project_subsystem(
    subsystem: SubsystemHealth,
    audience: HealthAudience,
) -> SubsystemHealth:
    if audience is HealthAudience.PUBLIC:
        return replace(
            subsystem,
            summary=f"{subsystem.name}: {subsystem.status.value}",
            findings=(),
            facts={},
        )
    findings = tuple(_project_finding(f, audience) for f in subsystem.findings)
    return replace(subsystem, findings=findings)


def _project_finding(
    finding: OperationalHealthFinding,
    audience: HealthAudience,
) -> OperationalHealthFinding:
    if audience is HealthAudience.PLATFORM_OWNER:
        return finding
    # GUILD_ADMIN: drop owner-only internals.
    return replace(finding, file_hint=None, related_provider=None)


# ---------------------------------------------------------------------------
# Bounded JSON payload — for the read-only AI diagnostics tool (PR5).
# ---------------------------------------------------------------------------

_PAYLOAD_SCHEMA_VERSION = 1
_PAYLOAD_MAX_SUBSYSTEMS = 16
_PAYLOAD_MAX_FINDINGS = 12


def _finding_payload(finding: OperationalHealthFinding) -> dict[str, Any]:
    out: dict[str, Any] = {
        "fingerprint": finding.fingerprint,
        "severity": finding.severity.value,
        "category": finding.category,
        "message": finding.message,
        "occurrence_count": finding.occurrence_count,
    }
    # Optional, already-scrubbed/projected fields — included only when present
    # (``file_hint``/``related_provider`` survive only at PLATFORM_OWNER).
    for key in (
        "related_subsystem",
        "related_provider",
        "file_hint",
        "suggested_next_step",
    ):
        value = getattr(finding, key)
        if value:
            out[key] = value
    return out


def snapshot_to_payload(snapshot: HealthSnapshot) -> dict[str, Any]:
    """Serialize an (already audience-projected) snapshot to a bounded,
    JSON-serializable dict for the read-only AI diagnostics tool.

    Enums → ``.value``; datetimes → ISO-8601; only the allowlisted ``facts``
    and the short ``suggested_next_step`` suggestion travel.  No raw provider
    dumps, tokens, SQL, traces, or unbounded IDs: the snapshot is already
    scrubbed (:func:`_scrub`) and projected (:func:`project_for_audience`), and
    the gateway redacts the serialized JSON once more before the model sees it.
    ``schema_version`` lets a future descriptor/result-contract tool migrate
    the shape without breaking callers.
    """
    return {
        "schema_version": _PAYLOAD_SCHEMA_VERSION,
        "snapshot_id": snapshot.snapshot_id,
        "generated_at": snapshot.generated_at.isoformat(),
        "purpose": snapshot.purpose,
        "status": snapshot.status.value,
        "summary": snapshot.summary,
        "partial": snapshot.partial,
        "audience": (
            snapshot.redaction_audience.value
            if snapshot.redaction_audience is not None
            else None
        ),
        "subsystems": [
            {
                "name": sub.name,
                "status": sub.status.value,
                "summary": sub.summary,
                "stale": sub.stale,
                "required": sub.required,
                "facts": dict(sub.facts),
                "findings": [
                    _finding_payload(f) for f in sub.findings[:_PAYLOAD_MAX_FINDINGS]
                ],
            }
            for sub in snapshot.subsystems[:_PAYLOAD_MAX_SUBSYSTEMS]
        ],
        "findings": [
            _finding_payload(f) for f in snapshot.findings[:_PAYLOAD_MAX_FINDINGS]
        ],
    }


# ---------------------------------------------------------------------------
# Public collection entry points
# ---------------------------------------------------------------------------


async def resolve_audience(bot: Any, user: Any) -> HealthAudience:
    """Map a Discord invoker to a :class:`HealthAudience`.

    The deterministic command/panel surfaces are administrator-gated, so a
    non-owner caller is a guild admin (``GUILD_ADMIN``); the bot/platform
    owner gets the full cross-process view (``PLATFORM_OWNER``).  Centralised
    here so the cog and the panel never diverge on the owner check.  Falls
    back to ``GUILD_ADMIN`` (the safer, more-redacted projection) if the
    owner check is unavailable.
    """
    try:
        if await bot.is_owner(user):
            return HealthAudience.PLATFORM_OWNER
    except Exception:  # noqa: BLE001 — never widen access on a failed check
        logger.debug("resolve_audience: is_owner check failed", exc_info=True)
    return HealthAudience.GUILD_ADMIN


# Process-local cache of the settled-startup snapshot (PLATFORM_OWNER-level,
# re-projected per viewer by ``!platform startup``).  Mirrors the benign
# read-side cache pattern of ``platform_consistency._LAST_REPORT`` — it is not
# durable/domain state, just the last startup report this process produced.
_LAST_STARTUP_SNAPSHOT: HealthSnapshot | None = None


def record_startup_snapshot(snapshot: HealthSnapshot) -> None:
    """Cache the settled-startup snapshot for ``!platform startup`` to render.

    Called once per process from ``bot1.on_ready`` after startup settles.
    Store the full (PLATFORM_OWNER) snapshot; the command re-projects it to
    each viewer's audience.
    """
    global _LAST_STARTUP_SNAPSHOT
    _LAST_STARTUP_SNAPSHOT = snapshot


def get_last_startup_snapshot() -> HealthSnapshot | None:
    """Return the cached settled-startup snapshot, or ``None`` if not yet set."""
    return _LAST_STARTUP_SNAPSHOT


def _sync_subsystems(
    request: HealthSnapshotRequest,
    bot: Any,
) -> list[SubsystemHealth]:
    subs = [
        _safe(_runtime_subsystem, "runtime", required=True),
        _safe(_tasks_subsystem, "tasks", required=True),
        _safe(_diagnostics_subsystem, "diagnostics", required=True),
        _safe(_startup_subsystem, "startup", required=True),
        _safe(_extensions_subsystem, "extensions", required=True),
        _safe(_ai_subsystem, "ai", required=False),
    ]
    # Cached consistency only when a fresh collection was not requested
    # (the async lane substitutes the fresh subsystem to avoid duplicates).
    if not request.include_fresh_consistency:
        subs.append(_safe(_consistency_subsystem, "consistency", required=True))
    if bot is not None:
        subs.append(_safe(lambda: _gateway_subsystem(bot), "gateway", required=True))
    # Opt-in (PR4): grouped recent-error findings over the log ring buffer.
    if _grouped_findings_enabled():
        subs.append(_safe(_errors_subsystem, "errors", required=False))
    return subs


def collect_cached_snapshot(
    request: HealthSnapshotRequest,
    *,
    bot: Any = None,
) -> HealthSnapshot:
    """Sync, process-local snapshot. Safe from any sync render path."""
    started = time.monotonic()
    subs = _sync_subsystems(replace(request, include_fresh_consistency=False), bot)
    snap = _finalize(subs, purpose=request.purpose, partial=False)
    projected = project_for_audience(snap, request.audience)
    metrics.health_snapshot_collection_seconds.labels(lane="sync").observe(
        time.monotonic() - started,
    )
    return projected


async def collect_snapshot(
    request: HealthSnapshotRequest,
    *,
    bot: Any = None,
) -> HealthSnapshot:
    """Async snapshot: the sync lane plus bounded, isolated async checks."""
    started = time.monotonic()
    subs = _sync_subsystems(request, bot)
    partial = False

    async_specs: list[
        tuple[
            str,
            Callable[[], Awaitable[SubsystemHealth]],
            bool,
            SnapshotStatus,
            float,
        ]
    ] = [
        ("database", _database_subsystem, True, SnapshotStatus.CRITICAL, DB_TIMEOUT),
    ]
    if request.include_fresh_consistency:
        async_specs.append(
            (
                "consistency",
                lambda: _fresh_consistency_subsystem(bot),
                True,
                SnapshotStatus.UNKNOWN,
                CONSISTENCY_TIMEOUT,
            ),
        )
    if bot is not None and request.guild_id is not None:
        guild_id = request.guild_id
        async_specs.append(
            (
                "resources",
                lambda: _resources_subsystem(bot, guild_id),
                False,
                SnapshotStatus.UNKNOWN,
                RESOURCE_TIMEOUT,
            ),
        )

    results = await asyncio.gather(
        *(
            _safe_async(
                name,
                factory,
                required=required,
                failure_status=failure_status,
                timeout=timeout,
            )
            for name, factory, required, failure_status, timeout in async_specs
        ),
    )
    for sub, degraded in results:
        subs.append(sub)
        partial = partial or degraded

    snap = _finalize(subs, purpose=request.purpose, partial=partial)
    projected = project_for_audience(snap, request.audience)
    metrics.health_snapshot_collection_seconds.labels(lane="async").observe(
        time.monotonic() - started,
    )
    return projected
