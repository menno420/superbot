"""Sole writer of the persistent operational-health findings store (PR6).

Records the findings carried by a :class:`~services.health_contracts.HealthSnapshot`
into ``operational_health_findings`` (through :mod:`utils.db.health_findings`,
the only module it writes via) and runs retention.

Design:

* **Best-effort** — recording and retention are wrapped so a DB hiccup is
  logged and swallowed; an observability write must never break startup-health
  collection or the running bot.
* **System-driven** — recording has no user actor, so it deliberately does NOT
  emit a ``services.audit_events`` action. Integrity comes from the sole-writer
  AST guard (``tests/unit/invariants/test_inv_health_findings_service.py``) and
  Prometheus counters. No new EventBus events.
* **Retention (D8/D11)** — open findings are retained; resolved/ignored detail
  is rolled into the aggregates table and pruned after :data:`RETENTION_DAYS`.
"""

from __future__ import annotations

import datetime
import logging
import uuid
from dataclasses import dataclass
from typing import Any

from services import metrics
from services.health_contracts import HealthSnapshot
from utils.db import health_findings as _db

logger = logging.getLogger("bot.health_findings")

RETENTION_DAYS = 30

#: Operator-managed lifecycle states. ``open`` is the initial/recurrence state;
#: ``resolved``/``ignored`` are deliberate operator transitions (Q-0097 —
#: operator-managed). Mirrors the migration-057 CHECK constraint.
VALID_STATUSES = ("open", "resolved", "ignored")


@dataclass(frozen=True)
class TransitionResult:
    """Outcome of an operator finding-status transition.

    ``outcome`` is one of ``"applied"`` (status changed), ``"unchanged"`` (the
    finding was already in the requested status), or ``"not_found"`` (no finding
    with that fingerprint). ``previous_status`` is the prior status, or ``None``
    when the finding did not exist.
    """

    outcome: str
    previous_status: str | None


def _now() -> datetime.datetime:
    return datetime.datetime.now(tz=datetime.timezone.utc)


async def record_findings(
    snapshot: HealthSnapshot,
    *,
    session_id: str | None = None,
) -> int:
    """Upsert every finding in ``snapshot`` into the persistent store.

    Idempotent (dedupe by fingerprint; recurrences bump ``occurrence_count``).
    Returns the number recorded; never raises — a per-finding failure is logged
    and skipped so one bad row cannot abort the rest or the caller.
    """
    recorded = 0
    seen_at = snapshot.generated_at or _now()
    for finding in snapshot.findings:
        try:
            await _db.upsert_finding(
                fingerprint=finding.fingerprint,
                severity=finding.severity.value,
                category=finding.category,
                message=finding.message,
                related_subsystem=finding.related_subsystem,
                related_command=finding.related_command,
                related_provider=finding.related_provider,
                file_hint=finding.file_hint,
                suggested_next_step=finding.suggested_next_step,
                occurrence_count=max(1, finding.occurrence_count),
                source=finding.source,
                session_id=session_id,
                snapshot_id=snapshot.snapshot_id,
                seen_at=seen_at,
            )
            metrics.health_finding_recorded_total.labels(
                category=finding.category,
                severity=finding.severity.value,
            ).inc()
            recorded += 1
        except Exception:  # noqa: BLE001 — observability write must never break the bot
            logger.warning(
                "health_findings: failed to record %s",
                finding.fingerprint,
                exc_info=True,
            )
    return recorded


async def list_open(*, limit: int = 25) -> list[dict[str, Any]]:
    """Currently-open findings, most-recently-seen first."""
    return await _db.list_findings("open", limit=limit)


async def list_by_status(
    status: str | None,
    *,
    limit: int = 25,
) -> list[dict[str, Any]]:
    """Findings filtered by ``status`` (``None`` → all), most-recent first."""
    return await _db.list_findings(status, limit=limit)


async def count_by_status() -> dict[str, int]:
    """``{status: count}`` across all stored findings."""
    return await _db.count_by_status()


async def set_status(
    fingerprint: str,
    status: str,
    *,
    actor_id: int | None,
    actor_type: str = "user",
) -> TransitionResult:
    """Transition a finding to ``status`` on behalf of an operator (Q-0097).

    This is the **sole** lifecycle-transition path — the operator-managed twin
    of :func:`record_findings` (which is system-driven and emits no audit). A
    deliberate transition *does* have a user actor, so on a real change it emits
    ``audit.action_recorded`` through :mod:`services.audit_events` (failure-safe;
    the DB write is authoritative regardless of the bus).

    Validates ``status`` against :data:`VALID_STATUSES` and raises ``ValueError``
    for anything else (defence-in-depth above the DB CHECK constraint). Returns a
    :class:`TransitionResult`; never raises for a missing/unchanged finding.
    """
    if status not in VALID_STATUSES:
        raise ValueError(
            f"invalid finding status {status!r}; expected one of {VALID_STATUSES}",
        )
    previous = await _db.set_finding_status(fingerprint, status)
    if previous is None:
        return TransitionResult(outcome="not_found", previous_status=None)
    if previous == status:
        return TransitionResult(outcome="unchanged", previous_status=previous)

    # A genuine operator mutation — record it on the canonical audit seam.
    from services import audit_events

    await audit_events.emit_audit_action(
        mutation_id=str(uuid.uuid4()),
        subsystem="health",
        mutation_type=f"finding_{status}",
        target=f"finding:{fingerprint}",
        scope="global",
        guild_id=None,
        prev_value=previous,
        new_value=status,
        actor_id=actor_id,
        actor_type=actor_type,
        occurred_at=_now(),
    )
    return TransitionResult(outcome="applied", previous_status=previous)


async def run_retention(*, ttl_days: int = RETENTION_DAYS) -> int:
    """Roll resolved/ignored detail older than ``ttl_days`` into the aggregates
    table, then prune it. Returns the number of rows pruned; never raises.
    """
    cutoff = _now() - datetime.timedelta(days=ttl_days)
    try:
        await _db.roll_up_to_aggregates(cutoff)
        pruned = await _db.prune_expired(cutoff)
        if pruned:
            metrics.health_finding_retention_pruned_total.inc(pruned)
        return pruned
    except Exception:  # noqa: BLE001
        logger.warning("health_findings: retention sweep failed", exc_info=True)
        return 0
