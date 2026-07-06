"""Persistent operational-health findings — pool-only CRUD (bot-awareness PR6).

The DB primitive layer for ``operational_health_findings`` and its companion
``operational_health_finding_aggregates`` (migration 057). The **sole** caller
of the write primitives (:func:`upsert_finding`, :func:`roll_up_to_aggregates`,
:func:`prune_expired`) is :mod:`services.health_findings_service` — mirrors the
``economy_service`` / ``utils.db.economy`` split and is pinned by
``tests/unit/invariants/test_inv_health_findings_service.py``.

Every text field stored here is already scrubbed of secrets/IDs/traces by the
health read model before it reaches this layer.
"""

from __future__ import annotations

import datetime
from typing import Any

from utils.db import pool


async def upsert_finding(
    *,
    fingerprint: str,
    severity: str,
    category: str,
    message: str,
    related_subsystem: str | None,
    related_command: str | None,
    related_provider: str | None,
    file_hint: str | None,
    suggested_next_step: str | None,
    occurrence_count: int,
    source: str,
    session_id: str | None,
    snapshot_id: str | None,
    seen_at: datetime.datetime,
) -> None:
    """Insert a finding or bump an existing one by fingerprint.

    On conflict: add the occurrence delta, advance ``last_seen_at``, refresh
    the mutable display fields, and **reopen** a previously-``resolved`` row (a
    recurrence is news again) while leaving an ``ignored`` row ignored.
    """
    await pool.execute(
        """
        INSERT INTO operational_health_findings (
            fingerprint, status, severity, category, message,
            related_subsystem, related_command, related_provider, file_hint,
            suggested_next_step, occurrence_count, first_seen_at, last_seen_at,
            source, last_session_id, last_snapshot_id
        ) VALUES (
            $1, 'open', $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $11, $12, $13, $14
        )
        ON CONFLICT (fingerprint) DO UPDATE SET
            occurrence_count = operational_health_findings.occurrence_count
                + EXCLUDED.occurrence_count,
            last_seen_at = EXCLUDED.last_seen_at,
            severity = EXCLUDED.severity,
            category = EXCLUDED.category,
            message = EXCLUDED.message,
            related_subsystem = EXCLUDED.related_subsystem,
            related_command = EXCLUDED.related_command,
            related_provider = EXCLUDED.related_provider,
            file_hint = EXCLUDED.file_hint,
            suggested_next_step = EXCLUDED.suggested_next_step,
            source = EXCLUDED.source,
            last_session_id = EXCLUDED.last_session_id,
            last_snapshot_id = EXCLUDED.last_snapshot_id,
            status = CASE
                WHEN operational_health_findings.status = 'ignored' THEN 'ignored'
                ELSE 'open'
            END
        """,
        (
            fingerprint,
            severity,
            category,
            message,
            related_subsystem,
            related_command,
            related_provider,
            file_hint,
            suggested_next_step,
            occurrence_count,
            seen_at,
            source,
            session_id,
            snapshot_id,
        ),
    )


async def list_findings(
    status: str | None = None,
    *,
    limit: int = 25,
) -> list[dict[str, Any]]:
    """Return findings (optionally filtered by status), most-recent first."""
    if status is None:
        return await pool.fetchall(
            "SELECT * FROM operational_health_findings "
            "ORDER BY last_seen_at DESC LIMIT $1",
            (limit,),
        )
    return await pool.fetchall(
        "SELECT * FROM operational_health_findings WHERE status = $1 "
        "ORDER BY last_seen_at DESC LIMIT $2",
        (status, limit),
    )


async def count_by_status() -> dict[str, int]:
    """Return ``{status: count}`` across all findings."""
    rows = await pool.fetchall(
        "SELECT status, COUNT(*) AS n FROM operational_health_findings GROUP BY status",
    )
    return {str(r["status"]): int(r["n"]) for r in rows}


async def set_finding_status(fingerprint: str, status: str) -> str | None:
    """Transition one finding to ``status`` (``open`` / ``resolved`` / ``ignored``).

    Returns the finding's **previous** status, or ``None`` if no row with that
    fingerprint exists. The ``status`` CHECK constraint (migration 057) rejects
    any value outside the allowed set, so an invalid status surfaces as a DB
    error rather than a silent write — the calling service validates first.

    Unlike :func:`upsert_finding`'s recurrence rule (which keeps an ``ignored``
    row ignored), this is a *deliberate operator transition*: it always sets the
    requested status. Re-opening an ``ignored`` finding is therefore an explicit
    operator action here, never an automatic recurrence.
    """
    row = await pool.fetchone(
        """
        WITH prev AS (
            SELECT status AS previous_status
            FROM operational_health_findings
            WHERE fingerprint = $1
        )
        UPDATE operational_health_findings AS t
        SET status = $2
        FROM prev
        WHERE t.fingerprint = $1
        RETURNING prev.previous_status
        """,
        (fingerprint, status),
    )
    return str(row["previous_status"]) if row else None


async def roll_up_to_aggregates(cutoff: datetime.datetime) -> None:
    """Fold soon-to-be-pruned resolved/ignored detail into the aggregates
    table so per-fingerprint occurrence counters survive expiry.
    """
    await pool.execute(
        """
        INSERT INTO operational_health_finding_aggregates (
            fingerprint, category, severity, total_occurrences,
            first_seen_at, last_seen_at
        )
        SELECT fingerprint, category, severity, occurrence_count,
               first_seen_at, last_seen_at
        FROM operational_health_findings
        WHERE status IN ('resolved', 'ignored') AND last_seen_at < $1
        ON CONFLICT (fingerprint) DO UPDATE SET
            total_occurrences = operational_health_finding_aggregates.total_occurrences
                + EXCLUDED.total_occurrences,
            first_seen_at = LEAST(
                operational_health_finding_aggregates.first_seen_at,
                EXCLUDED.first_seen_at
            ),
            last_seen_at = GREATEST(
                operational_health_finding_aggregates.last_seen_at,
                EXCLUDED.last_seen_at
            ),
            category = EXCLUDED.category,
            severity = EXCLUDED.severity
        """,
        (cutoff,),
    )


async def prune_expired(cutoff: datetime.datetime) -> int:
    """Delete resolved/ignored findings whose ``last_seen_at`` is before
    ``cutoff``; return the number pruned. Open findings are never pruned.

    Call :func:`roll_up_to_aggregates` first so the counters survive.
    """
    row = await pool.fetchone(
        """
        WITH deleted AS (
            DELETE FROM operational_health_findings
            WHERE status IN ('resolved', 'ignored') AND last_seen_at < $1
            RETURNING 1
        )
        SELECT COUNT(*) AS n FROM deleted
        """,
        (cutoff,),
    )
    return int(row["n"]) if row else 0
