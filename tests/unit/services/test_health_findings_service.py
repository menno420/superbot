"""Tests for services.health_findings_service — PR6 (bot awareness).

The sole writer of the persistent findings store. These tests mock ``svc._db``
to pin the *service* contract: it records each finding through
utils.db.health_findings with the right arguments, is best-effort (swallows DB
errors), and runs retention as roll-up-then-prune.

The SQL itself — the ON CONFLICT dedupe / occurrence delta-add / reopen-on-
recurrence / keep-ignored / roll-up-then-prune — is exercised against a real
Postgres in ``tests/unit/db/test_health_findings_integration.py`` (which skips
cleanly when no database is reachable, e.g. in CI), and the migration's static
SQL shape is pinned by
``tests/unit/db/test_migration_057_operational_health_findings.py``.
"""

from __future__ import annotations

import datetime

from services import health_findings_service as svc
from services.health_contracts import (
    FindingSeverity,
    HealthAudience,
    HealthSnapshot,
    OperationalHealthFinding,
    SnapshotStatus,
)


def _snapshot(*findings: OperationalHealthFinding) -> HealthSnapshot:
    return HealthSnapshot(
        snapshot_id="snap1",
        generated_at=datetime.datetime(2026, 6, 6, tzinfo=datetime.timezone.utc),
        purpose="startup",
        status=SnapshotStatus.DEGRADED,
        summary="x",
        subsystems=(),
        findings=tuple(findings),
        redaction_audience=HealthAudience.PLATFORM_OWNER,
    )


def _finding(fp: str = "errors:x", count: int = 1) -> OperationalHealthFinding:
    return OperationalHealthFinding(
        fingerprint=fp,
        severity=FindingSeverity.ERROR,
        category="runtime.log_error",
        message="boom",
        occurrence_count=count,
        related_subsystem="errors",
        source="log_buffer",
    )


async def test_record_findings_upserts_each(monkeypatch) -> None:
    calls: list[dict] = []

    async def fake_upsert(**kwargs):
        calls.append(kwargs)

    monkeypatch.setattr(svc._db, "upsert_finding", fake_upsert)
    n = await svc.record_findings(
        _snapshot(_finding("a", 2), _finding("b", 1)),
        session_id="boot-1",
    )
    assert n == 2
    assert {c["fingerprint"] for c in calls} == {"a", "b"}
    first = next(c for c in calls if c["fingerprint"] == "a")
    assert first["session_id"] == "boot-1"
    assert first["snapshot_id"] == "snap1"
    assert first["occurrence_count"] == 2
    assert first["severity"] == "error"  # enum -> value
    assert first["seen_at"].year == 2026


async def test_record_findings_swallows_db_error(monkeypatch) -> None:
    async def boom(**kwargs):
        raise RuntimeError("db down")

    monkeypatch.setattr(svc._db, "upsert_finding", boom)
    # Must not raise; nothing recorded.
    assert await svc.record_findings(_snapshot(_finding())) == 0


async def test_record_findings_empty_snapshot_writes_nothing(monkeypatch) -> None:
    async def fake_upsert(**kwargs):
        raise AssertionError("should not be called for an empty snapshot")

    monkeypatch.setattr(svc._db, "upsert_finding", fake_upsert)
    assert await svc.record_findings(_snapshot()) == 0


async def test_run_retention_rolls_up_then_prunes(monkeypatch) -> None:
    order: list[tuple[str, datetime.datetime]] = []

    async def fake_rollup(cutoff):
        order.append(("rollup", cutoff))

    async def fake_prune(cutoff):
        order.append(("prune", cutoff))
        return 3

    monkeypatch.setattr(svc._db, "roll_up_to_aggregates", fake_rollup)
    monkeypatch.setattr(svc._db, "prune_expired", fake_prune)

    pruned = await svc.run_retention(ttl_days=30)
    assert pruned == 3
    assert [step[0] for step in order] == ["rollup", "prune"]  # roll up BEFORE prune
    age = datetime.datetime.now(tz=datetime.timezone.utc) - order[0][1]
    assert 29 <= age.days <= 30  # cutoff is ~ttl_days ago


async def test_run_retention_swallows_error(monkeypatch) -> None:
    async def boom(cutoff):
        raise RuntimeError("db down")

    monkeypatch.setattr(svc._db, "roll_up_to_aggregates", boom)
    assert await svc.run_retention() == 0


# ---------------------------------------------------------------------------
# set_status — operator-managed lifecycle transitions (Q-0097)
# ---------------------------------------------------------------------------


def _patch_audit(monkeypatch) -> list[dict]:
    """Capture emit_audit_action calls; return the recorded kwargs list."""
    from services import audit_events

    emitted: list[dict] = []

    async def fake_emit(**kwargs):
        emitted.append(kwargs)
        return True

    monkeypatch.setattr(audit_events, "emit_audit_action", fake_emit)
    return emitted


async def test_set_status_applied_emits_audit(monkeypatch) -> None:
    async def fake_set(fp, status):
        assert fp == "errors:x"
        assert status == "resolved"
        return "open"  # previous status

    monkeypatch.setattr(svc._db, "set_finding_status", fake_set)
    emitted = _patch_audit(monkeypatch)

    result = await svc.set_status("errors:x", "resolved", actor_id=42)

    assert result.outcome == "applied"
    assert result.previous_status == "open"
    assert len(emitted) == 1
    rec = emitted[0]
    assert rec["subsystem"] == "health"
    assert rec["mutation_type"] == "finding_resolved"
    assert rec["target"] == "finding:errors:x"
    assert rec["prev_value"] == "open"
    assert rec["new_value"] == "resolved"
    assert rec["actor_id"] == 42
    assert rec["actor_type"] == "user"
    assert rec["scope"] == "global"
    assert rec["guild_id"] is None


async def test_set_status_not_found_does_not_emit(monkeypatch) -> None:
    async def fake_set(fp, status):
        return None  # no row

    monkeypatch.setattr(svc._db, "set_finding_status", fake_set)
    emitted = _patch_audit(monkeypatch)

    result = await svc.set_status("missing", "resolved", actor_id=1)

    assert result.outcome == "not_found"
    assert result.previous_status is None
    assert emitted == []  # no mutation -> no audit


async def test_set_status_unchanged_does_not_emit(monkeypatch) -> None:
    async def fake_set(fp, status):
        return "resolved"  # already in the requested status

    monkeypatch.setattr(svc._db, "set_finding_status", fake_set)
    emitted = _patch_audit(monkeypatch)

    result = await svc.set_status("errors:x", "resolved", actor_id=1)

    assert result.outcome == "unchanged"
    assert result.previous_status == "resolved"
    assert emitted == []  # idempotent no-op -> no audit


async def test_set_status_rejects_invalid_status(monkeypatch) -> None:
    async def fake_set(fp, status):  # pragma: no cover - must not be reached
        raise AssertionError("DB must not be called for an invalid status")

    monkeypatch.setattr(svc._db, "set_finding_status", fake_set)

    import pytest

    with pytest.raises(ValueError, match="invalid finding status"):
        await svc.set_status("errors:x", "bogus", actor_id=1)
